"""User Pydantic schemas.

Provides request/response schemas for the user management API.
"""

from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    password: Optional[str] = None
    role: str = "equipment_engineer"
    email: Optional[str] = None
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    status: Optional[str] = None


class UserOut(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    role: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    status: Optional[str] = None
    must_change_password: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserListOut(BaseModel):
    """Lightweight schema for user list views."""
    id: int
    username: str
    role: Optional[str] = None
    display_name: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
