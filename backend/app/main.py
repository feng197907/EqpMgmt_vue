"""FastAPI application entry point.

Registers all API routers, middleware, and startup/shutdown lifecycle
hooks.  Legacy Flask compatibility code has been removed.
"""

import logging
import os
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.db.session import engine, Base
from backend.app.middleware.audit import AuditMiddleware
from backend.app.middleware.rbac import RBACMiddleware

# ── Logging Configuration ─────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_log_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Console handler
_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(_log_formatter)

# Rotating file handler — all levels (max 10 MB × 5 files)
_app_file = RotatingFileHandler(
    LOG_DIR / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_app_file.setLevel(logging.DEBUG)
_app_file.setFormatter(_log_formatter)

# Error-only rotating file (max 5 MB × 3 files)
_err_file = RotatingFileHandler(
    LOG_DIR / "error.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_err_file.setLevel(logging.ERROR)
_err_file.setFormatter(_log_formatter)

# Configure root logger
_root = logging.getLogger()
_root.setLevel(logging.DEBUG)
_root.handlers.clear()
_root.addHandler(_console)
_root.addHandler(_app_file)
_root.addHandler(_err_file)

# Silence noisy third-party loggers
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").handlers.clear()
logging.getLogger("uvicorn.access").addHandler(_app_file)
logging.getLogger("uvicorn.access").propagate = False

logger = logging.getLogger(__name__)
logger.info("Logging configured — app.log / error.log -> %s", LOG_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create DB tables on startup."""
    # Import all models so Base.metadata.create_all discovers every table
    import backend.app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="DMS FastAPI Backend", lifespan=lifespan)


# ── Global Exception Handlers ──────────────────────────────────────────────
# Catch ALL unhandled exceptions so they are logged to error.log with full
# stack traces, instead of silently going to uvicorn's default handler.

from fastapi.exceptions import RequestValidationError

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    """Attach a unique trace_id to every request for log correlation."""
    trace_id = uuid.uuid4().hex[:12]
    request.state.trace_id = trace_id
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "[%s] %s %s → %d (%.3fs)",
        trace_id,
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex[:12])
    logger.error(
        "[%s] Unhandled exception | %s %s | %s: %s\n%s",
        trace_id,
        request.method,
        request.url.path,
        type(exc).__name__,
        exc,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "trace_id": trace_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log request-body validation errors at WARNING level."""
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex[:12])
    logger.warning(
        "[%s] Validation error | %s %s | errors=%s",
        trace_id,
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": exc.errors(),
            "trace_id": trace_id,
        },
    )

# ── Middleware (order matters: last added = first executed) ─────────────────
# Place CORSMiddleware LAST so it wraps everything — every response,
# including 401/403 from RBAC, gets CORS headers.
app.add_middleware(RBACMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

from backend.app.api import log as log_router
app.include_router(log_router.router, prefix="/api/v1/log", tags=["log"])


@app.get("/")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
