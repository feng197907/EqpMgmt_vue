"""Test configuration and shared fixtures.

Uses an in-memory SQLite database for fast, isolated test runs.  Each test
function gets a fresh database schema and a clean session.
"""

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── Patch config BEFORE importing modules that depend on it ──────────────
# We patch Settings.__init__ to skip the SQLite rejection check so that
# an in-memory SQLite engine can be used for tests without needing MySQL.
import backend.app.core.config as _config_mod

_original_settings_init = _config_mod.Settings.__init__


def _patched_settings_init(self) -> None:
    """Settings.__init__ that allows SQLite URLs (for testing)."""
    import os
    self.SECRET_KEY: str = os.environ.get("SECRET_KEY", "test-secret-key")
    self.ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )
    self.REFRESH_TOKEN_EXPIRE_MINUTES: int = int(
        os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)
    )
    # Use SQLite in-memory for tests (skip the MySQL-only validation)
    self.SQLALCHEMY_DATABASE_URL: str = "sqlite:///:memory:"
    self.DB_POOL_SIZE: int = 5
    self.DB_MAX_OVERFLOW: int = 10
    self.DB_POOL_RECYCLE: int = 3600
    self.DB_POOL_PRE_PING: bool = False
    self.PASSWORD_MIN_LENGTH: int = 8


_config_mod.Settings.__init__ = _patched_settings_init

# Now we can safely import the rest — the patched Settings will use SQLite
from backend.app.db.session import Base
from backend.app.main import app
from backend.app.api.deps import get_db
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.user import User


# ── Test Database Engine ───────────────────────────────────────────────────
# StaticPool + :memory: ensures a single connection is shared across the
# session, preventing "database is locked" errors with SQLite in-memory.

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _setup_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db():
    """Yield a test database session, rolling back after each test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """Return a FastAPI ``TestClient`` that uses the test database.

    Overrides the ``get_db`` dependency to use the SQLite test session
    and disables the MySQL-dependent lifespan to avoid connection errors.
    """
    def _override_get_db():
        try:
            yield db
        finally:
            pass  # session lifecycle managed by the `db` fixture

    # Override lifespan to skip MySQL table creation (SQLite tables are
    # created by the _setup_db autouse fixture).
    @asynccontextmanager
    async def _test_lifespan(application: FastAPI):
        yield

    original_router_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _test_lifespan

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_router_lifespan


@pytest.fixture()
def test_user(db):
    """Create and return an admin test user."""
    user = User(
        username="admin_test",
        password=get_password_hash("Admin@1234"),
        role="admin",
        status="active",
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def test_normal_user(db):
    """Create and return a normal (equipment_engineer) test user."""
    user = User(
        username="engineer_test",
        password=get_password_hash("Engineer@1234"),
        role="equipment_engineer",
        status="active",
        must_change_password=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def test_must_change_user(db):
    """Create and return a test user who must change their password."""
    user = User(
        username="mustchange_test",
        password=get_password_hash("OldPass@1234"),
        role="equipment_engineer",
        status="active",
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def auth_headers(test_user):
    """Return Authorization headers for the admin test user."""
    token = create_access_token({"sub": str(test_user.id), "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def normal_auth_headers(test_normal_user):
    """Return Authorization headers for the normal test user."""
    token = create_access_token({"sub": str(test_normal_user.id), "role": test_normal_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def must_change_auth_headers(test_must_change_user):
    """Return Authorization headers for the must-change-password test user."""
    token = create_access_token({"sub": str(test_must_change_user.id), "role": test_must_change_user.role})
    return {"Authorization": f"Bearer {token}"}
