"""Password-reset routes — admin-initiated password reset workflow.

All operations require admin role.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin
from backend.app.models.user import User
from backend.app.schemas.password import PasswordResetRequest as PasswordResetRequestSchema
from backend.app.schemas.password import PasswordResetProcess
from backend.app.services import password_service

router = APIRouter()


@router.get("/resets")
def list_reset_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List password-reset requests (admin only)."""
    return password_service.list_reset_requests(db, status=status)


@router.post("/resets")
def create_reset_request(
    payload: PasswordResetRequestSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a password-reset request for a user (admin only)."""
    ip_address = request.client.host if request.client else None
    try:
        req = password_service.create_reset_request(
            db, user_id=payload.user_id, ip_address=ip_address, current_user=current_user,
        )
        return {
            "id": req.id,
            "user_id": req.user_id,
            "username": req.username,
            "status": req.status,
            "requested_at": str(req.requested_at) if req.requested_at else None,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/resets/{request_id}/reset")
def process_reset_request(
    request_id: int,
    payload: PasswordResetProcess,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Process (complete) a password-reset request (admin only).

    If ``new_password`` is not provided a random one is generated.
    Returns the new password in plain text so the admin can relay it.
    """
    try:
        new_password = password_service.process_reset_request(
            db, request_id, new_password=payload.new_password, current_user=current_user,
        )
        return {"status": "completed", "new_password": new_password}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/resets/{request_id}/cancel")
def cancel_reset_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Cancel a pending password-reset request (admin only)."""
    try:
        password_service.cancel_reset_request(db, request_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "cancelled"}
