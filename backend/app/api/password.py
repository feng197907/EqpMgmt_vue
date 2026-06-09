"""Password-reset routes — both self-service and admin-initiated workflows.

Public endpoint (no auth):
    POST /api/v1/password/request-reset   — user submits username to request reset

Admin-only endpoints:
    GET  /api/v1/password/resets          — list all reset requests
    POST /api/v1/password/resets          — admin creates a reset for any user
    POST /api/v1/password/resets/{id}/reset   — admin processes (completes) reset
    POST /api/v1/password/resets/{id}/cancel  — admin cancels reset
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin
from backend.app.models.user import User
from backend.app.models.password_reset import PasswordResetRequest
from backend.app.schemas.password import (
    PasswordResetRequest as PasswordResetRequestSchema,
    UserSelfResetRequest,
    PasswordResetProcess,
)
from backend.app.services import password_service

router = APIRouter()


# ── Public: Self-service reset request ────────────────────────────────────

@router.post("/request-reset")
def user_request_reset(
    payload: UserSelfResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Public endpoint — no authentication required.

    A user submits their username to request a password reset.
    The backend creates a pending PasswordResetRequest.
    Returns a generic success message regardless of whether the user exists
    (prevents username enumeration attacks).
    """
    ip_address = request.client.host if request.client else None

    # Look up user by username
    target = db.query(User).filter(User.username == payload.username).first()

    if target and target.status == "active":
        # Check if there's already a pending request for this user
        existing = (
            db.query(PasswordResetRequest)
            .filter(
                PasswordResetRequest.user_id == target.id,
                PasswordResetRequest.status == "pending",
            )
            .first()
        )
        if not existing:
            new_req = PasswordResetRequest(
                user_id=target.id,
                username=target.username,
                ip_address=ip_address,
                status="pending",
            )
            db.add(new_req)
            db.commit()

    # Always return same message (security: don't reveal if username exists)
    return {"message": "已通知管理员，请等待处理后联系管理员获取新密码"}


# ── Admin-only endpoints ───────────────────────────────────────────────────

@router.get("/resets/count")
def get_pending_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Return count of pending password-reset requests (admin only)."""
    count = (
        db.query(PasswordResetRequest)
        .filter(PasswordResetRequest.status == "pending")
        .count()
    )
    return {"count": count}


@router.get("/resets")
def list_reset_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List password-reset requests (admin only)."""
    requests = password_service.list_reset_requests(db, status=status)
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "username": r.username,
            "ip_address": r.ip_address,
            "status": r.status,
            "requested_at": str(r.requested_at) if r.requested_at else None,
            "processed_by": r.processed_by,
            "processed_at": str(r.processed_at) if r.processed_at else None,
        }
        for r in requests
    ]


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
