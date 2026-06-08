from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import auth as auth_router
from backend.app.middleware.audit import AuditMiddleware

app = FastAPI(title="DMS FastAPI Backend")

# Allow local frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# audit middleware logs requests and user info (when available)
app.add_middleware(AuditMiddleware)

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])

# include users management
from backend.app.api import users as users_router
app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"])

# devices API
from backend.app.api import devices as devices_router
app.include_router(devices_router.router, prefix="/api/v1/devices", tags=["devices"])

# documents API
from backend.app.api import documents as documents_router
app.include_router(documents_router.router, prefix="/api/v1/documents", tags=["documents"])

# approvals
from backend.app.api import approvals as approvals_router
app.include_router(approvals_router.router, prefix="/api/v1/approvals", tags=["approvals"])


@app.get("/")
def health():
    return {"status": "ok"}
