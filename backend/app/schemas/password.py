"""Password management Pydantic schemas.

Provides schemas for password-reset and password-change APIs.
"""

from typing import Optional

from pydantic import BaseModel


class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset (admin initiates)."""
    user_id: int


class UserSelfResetRequest(BaseModel):
    """Schema for a user self-requesting a password reset (no auth required)."""
    username: str


class PasswordResetProcess(BaseModel):
    """Schema for processing (completing) a password reset request."""
    new_password: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for a user changing their own password."""
    old_password: str
    new_password: str
