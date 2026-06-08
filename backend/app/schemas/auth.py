"""Authentication Pydantic schemas.

Enhanced with ``must_change_password`` support per the architecture design.
"""

from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    role: Optional[str] = None
    must_change_password: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
