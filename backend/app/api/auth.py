"""Authentication routes — login, token refresh, password change, profile.

All business logic is delegated to the Service layer; this module only
handles HTTP request/response concerns and exception mapping.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.schemas.auth import (
    TokenResponse,
    UserOut,
    LoginRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
)
from backend.app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_refresh_token,
)
from backend.app.services.user_service import change_password as svc_change_password, update_user
from backend.app.models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return JWT tokens."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        must_change_password=getattr(user, "must_change_password", False),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_body: dict, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair."""
    token = refresh_body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing refresh_token")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    if not is_refresh_token(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not a refresh token",
        )
    user_id = int(payload.get("sub"))
    from backend.app.services import user_service
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh = create_refresh_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        must_change_password=getattr(user, "must_change_password", False),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        must_change_password=getattr(current_user, "must_change_password", False),
    )


@router.put("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password."""
    try:
        svc_change_password(db, current_user, payload.old_password, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"detail": "密码已修改"}


@router.put("/profile", response_model=UserOut)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile (username)."""
    try:
        user = update_user(
            db,
            current_user.id,
            username=payload.username,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UserOut(
        id=user.id,
        username=user.username,
        role=user.role,
        must_change_password=getattr(user, "must_change_password", False),
    )
