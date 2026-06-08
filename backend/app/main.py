"""FastAPI application entry point.

Registers all API routers, middleware, and startup/shutdown lifecycle
hooks.  Legacy Flask compatibility code has been removed.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.session import engine, Base
from backend.app.middleware.audit import AuditMiddleware
from backend.app.middleware.rbac import RBACMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create DB tables on startup."""
    # Import all models so Base.metadata.create_all discovers every table
    import backend.app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="DMS FastAPI Backend", lifespan=lifespan)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Middleware (order matters: last added = first executed) ─────────────────
app.add_middleware(AuditMiddleware)
app.add_middleware(RBACMiddleware)

# ── API Routers ────────────────────────────────────────────────────────────

from backend.app.api import auth as auth_router
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])

from backend.app.api import users as users_router
app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"])

from backend.app.api import devices as devices_router
app.include_router(devices_router.router, prefix="/api/v1/devices", tags=["devices"])

from backend.app.api import documents as documents_router
app.include_router(documents_router.router, prefix="/api/v1/documents", tags=["documents"])

from backend.app.api import approvals as approvals_router
app.include_router(approvals_router.router, prefix="/api/v1/approvals", tags=["approvals"])

from backend.app.api import maintenance as maintenance_router
app.include_router(maintenance_router.router, prefix="/api/v1/maintenance", tags=["maintenance"])

from backend.app.api import spare_parts as spare_parts_router
app.include_router(spare_parts_router.router, prefix="/api/v1/spare-parts", tags=["spare_parts"])

from backend.app.api import borrowing as borrowing_router
app.include_router(borrowing_router.router, prefix="/api/v1/borrowing", tags=["borrowing"])

from backend.app.api import audit as audit_router
app.include_router(audit_router.router, prefix="/api/v1", tags=["audit"])

# ── New Routers (T03) ─────────────────────────────────────────────────────

from backend.app.api import esign as esign_router
app.include_router(esign_router.router, prefix="/api/v1/esign", tags=["esign"])

from backend.app.api import device_changes as device_changes_router
app.include_router(device_changes_router.router, prefix="/api/v1/device-changes", tags=["device_changes"])

from backend.app.api import dashboard as dashboard_router
app.include_router(dashboard_router.router, prefix="/api/v1/dashboard", tags=["dashboard"])

from backend.app.api import password as password_router
app.include_router(password_router.router, prefix="/api/v1/password", tags=["password"])


@app.get("/")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
