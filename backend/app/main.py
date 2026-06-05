from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import auth as auth_router

app = FastAPI(title="DMS FastAPI Backend")

# Allow local frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])

# include users management
from backend.app.api import users as users_router
app.include_router(users_router.router, prefix="/api/v1/users", tags=["users"])


@app.get("/")
def health():
    return {"status": "ok"}
