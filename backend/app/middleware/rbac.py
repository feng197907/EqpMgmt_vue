"""RBAC middleware — automatic role-based access control for API routes.

This middleware inspects incoming requests to API endpoints and enforces
role-based access control based on a configurable route-role mapping.
Unauthenticated requests to protected routes are rejected with 401.
Authenticated requests from users without the required role are rejected
with 403.

Public paths (e.g. ``/api/v1/auth/login``, ``/docs``, health checks) are
always allowed.
"""

import logging
from typing import Dict, FrozenSet, Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.app.core.security import decode_token
from backend.app.core.permissions import ROLES

logger = logging.getLogger("rbac_middleware")


# ── Default Public Paths ──────────────────────────────────────────────────
# These paths never require authentication or role checks.

PUBLIC_PATHS: FrozenSet[str] = frozenset(
    {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }
)

# Prefixes that are always public (e.g. static assets)
PUBLIC_PREFIXES: FrozenSet[str] = frozenset(
    {
        "/static/",
    }
)

# ── Route-Role Mapping ────────────────────────────────────────────────────
# Maps URL path prefixes to the set of roles allowed to access them.
# Paths not listed here are accessible to any authenticated user.

ROUTE_ROLE_MAP: Dict[str, Set[str]] = {
    "/api/v1/users": {"admin"},
    "/api/v1/approvals": {"admin", "qa_manager", "validation_engineer"},
    "/api/v1/maintenance": {"admin", "equipment_engineer", "metrology_engineer"},
    "/api/v1/spare-parts": {"admin", "equipment_engineer", "production_supervisor"},
    "/api/v1/borrowing": {"admin", "archivist"},
    "/api/v1/esign": {"admin", "qa_manager", "validation_engineer"},
    "/api/v1/device-changes": {"admin", "equipment_engineer", "qa_manager"},
    "/api/v1/password/resets": {"admin"},
}


class RBACMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that enforces RBAC on API routes."""

    def __init__(
        self,
        app,
        public_paths: Optional[FrozenSet[str]] = None,
        public_prefixes: Optional[FrozenSet[str]] = None,
        route_role_map: Optional[Dict[str, Set[str]]] = None,
    ) -> None:
        super().__init__(app)
        self.public_paths: FrozenSet[str] = public_paths or PUBLIC_PATHS
        self.public_prefixes: FrozenSet[str] = public_prefixes or PUBLIC_PREFIXES
        self.route_role_map: Dict[str, Set[str]] = route_role_map or ROUTE_ROLE_MAP

    async def dispatch(self, request: Request, call_next):
        path: str = request.url.path

        # ── Skip non-API / public paths ────────────────────────────────
        if self._is_public(path):
            return await call_next(request)

        # ── Skip non-API paths ─────────────────────────────────────────
        if not path.startswith("/api/"):
            return await call_next(request)

        # ── Extract Bearer token ───────────────────────────────────────
        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        token = auth_header.split(" ", 1)[1]

        # ── Decode token ───────────────────────────────────────────────
        try:
            payload = decode_token(token)
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        # ── Check role-based access ────────────────────────────────────
        user_role: Optional[str] = payload.get("role")
        required_roles = self._get_required_roles(path)

        if required_roles is not None and user_role not in required_roles:
            logger.warning(
                "RBAC denied: user_id=%s role=%s path=%s required=%s",
                payload.get("sub"),
                user_role,
                path,
                required_roles,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Insufficient permissions"},
            )

        # ── authorised — proceed ───────────────────────────────────────
        return await call_next(request)

    # ── Helpers ────────────────────────────────────────────────────────

    def _is_public(self, path: str) -> bool:
        """Return True if the path is in the public whitelist."""
        if path in self.public_paths:
            return True
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return True
        return False

    def _get_required_roles(self, path: str) -> Optional[Set[str]]:
        """Return the set of roles required for *path*, or ``None`` if the
        path has no role restriction (any authenticated user may access).
        """
        for prefix, roles in self.route_role_map.items():
            if path.startswith(prefix):
                return roles
        return None
