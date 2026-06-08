"""Authentication service — thin facade over ``core.security``.

All password-hashing and JWT logic has been extracted to
:mod:`backend.app.core.security`.  This module re-exports those functions
for backward compatibility and retains the ``authenticate_user`` service
function which depends on the database session.
"""

from typing import Optional

from sqlalchemy.orm import Session

from backend.app.core.security import (  # noqa: F401 — re-exports for backward compat
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_refresh_token,
    is_access_token,
)
from backend.app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Look up a user by *username* and verify the password.

    Returns the ``User`` object on success, or ``None`` if the user does
    not exist, is inactive, or the password is incorrect.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or user.status != "active":
        return None
    if not verify_password(password, user.password):
        return None
    return user
