"""FastAPI dependency injection helpers.

Provides database session management, current-user extraction, and a
generic ``require_role()`` RBAC dependency.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.security import decode_token
from backend.app.core.permissions import ROLES
from backend.app.db.session import SessionLocal
from backend.app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Database Session ──────────────────────────────────────────────────────


def get_db():
    """Yield a SQLAlchemy database session and ensure it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Current User ──────────────────────────────────────────────────────────


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and return the authenticated ``User`` from the JWT token.

    Raises:
        HTTPException: 401 if the token is invalid or the user does not exist.
    """
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Legacy Admin Dependency (kept for backward compatibility) ─────────────


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow only admin users.  Prefer ``require_role("admin")`` for new code."""
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


# ── Generic RBAC Dependency ───────────────────────────────────────────────


def require_role(*allowed_roles: str) -> Depends:
    """FastAPI dependency that restricts access to the given roles.

    Usage::

        @router.get("/qa-only")
        def qa_endpoint(user: User = Depends(require_role("admin", "qa_manager"))):
            ...

    Args:
        *allowed_roles: One or more role strings from :data:`ROLES`.

    Returns:
        A FastAPI ``Depends`` that resolves to the authenticated ``User``
        if authorised, or raises HTTP 403 otherwise.
    """

    # Validate role names at import time to catch typos early
    for role in allowed_roles:
        if role not in ROLES:
            raise ValueError(
                f"Unknown role '{role}'. Valid roles: {', '.join(ROLES)}"
            )

    def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = getattr(current_user, "role", None)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not permitted. Required: {', '.join(allowed_roles)}",
            )
        return current_user

    return Depends(_role_checker)
