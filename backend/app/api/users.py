"""User management routes — CRUD operations for admin users.

All business logic is delegated to :mod:`backend.app.services.user_service`.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate, UserOut, UserListOut
from backend.app.services import user_service

router = APIRouter()


@router.get("/", response_model=List[UserListOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    """Return all users (lightweight list)."""
    users = user_service.list_users(db)
    return [UserListOut.model_validate(u) for u in users]


@router.post("/", response_model=UserOut, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Create a new user.  If password is omitted a random one is generated."""
    try:
        user = user_service.create_user(
            db,
            username=payload.username,
            password=payload.password,
            role=payload.role,
            email=payload.email,
            display_name=payload.display_name,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Return a single user by ID."""
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Update an existing user."""
    try:
        user = user_service.update_user(
            db,
            user_id,
            username=payload.username,
            password=payload.password or "__KEEP__",
            role=payload.role,
            email=payload.email,
            display_name=payload.display_name,
            status=payload.status,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Delete a user."""
    try:
        user_service.delete_user(db, user_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return None
