"""Password-reset service — admin-initiated password reset workflow.

Allows administrators to request a password reset for a user, and to
process (complete) the reset by setting a new password.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.core.security import get_password_hash
from backend.app.models.password_reset import PasswordResetRequest
from backend.app.models.user import User
from backend.app.services.audit_service import log_action
from backend.app.services.user_service import generate_random_password


# ── Query ──────────────────────────────────────────────────────────────────


def list_reset_requests(
    db: Session,
    *,
    status: Optional[str] = None,
) -> List[PasswordResetRequest]:
    """Return password-reset requests, optionally filtered by status."""
    q = db.query(PasswordResetRequest)
    if status:
        q = q.filter(PasswordResetRequest.status == status)
    return q.order_by(PasswordResetRequest.requested_at.desc()).all()


def get_reset_request(db: Session, request_id: int) -> PasswordResetRequest:
    """Return a password-reset request or raise ``ValueError``."""
    req = db.query(PasswordResetRequest).filter(PasswordResetRequest.id == request_id).first()
    if not req:
        raise ValueError("Password reset request not found")
    return req


# ── Create / Process ───────────────────────────────────────────────────────


def create_reset_request(
    db: Session,
    *,
    user_id: int,
    ip_address: Optional[str] = None,
    current_user: User,
) -> PasswordResetRequest:
    """Create a password-reset request for the given user.

    The target user must exist and be active.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise ValueError("User not found")
    if target.status != "active":
        raise ValueError("User is not active")

    request = PasswordResetRequest(
        user_id=user_id,
        username=target.username,
        ip_address=ip_address,
    )
    db.add(request)
    db.flush()

    log_action(
        db,
        current_user.username,
        "create_password_reset",
        "password_reset",
        request.id,
        f"申请重置用户 {target.username} 的密码",
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(request)
    return request


def process_reset_request(
    db: Session,
    request_id: int,
    *,
    new_password: Optional[str] = None,
    current_user: User,
) -> str:
    """Process a pending password-reset request.

    If *new_password* is not provided, a random one is generated.
    Sets the user's ``must_change_password`` flag to ``True``.

    Returns the new password (plain text) so the admin can relay it.
    """
    req = get_reset_request(db, request_id)
    if req.status != "pending":
        raise ValueError("Request is not in pending status")

    target = db.query(User).filter(User.id == req.user_id).first()
    if not target:
        raise ValueError("Target user not found")

    if not new_password:
        new_password = generate_random_password()

    target.password = get_password_hash(new_password)
    target.must_change_password = True

    req.status = "completed"
    req.processed_by = current_user.username
    req.processed_at = datetime.utcnow()

    log_action(
        db,
        current_user.username,
        "process_password_reset",
        "password_reset",
        request_id,
        f"处理用户 {target.username} 的密码重置",
    )
    db.commit()
    return new_password


def cancel_reset_request(
    db: Session,
    request_id: int,
    *,
    current_user: User,
) -> None:
    """Cancel a pending password-reset request."""
    req = get_reset_request(db, request_id)
    if req.status != "pending":
        raise ValueError("Only pending requests can be cancelled")
    req.status = "cancelled"
    req.processed_by = current_user.username
    req.processed_at = datetime.utcnow()
    log_action(
        db,
        current_user.username,
        "cancel_password_reset",
        "password_reset",
        request_id,
        f"取消用户 {req.username} 的密码重置请求",
    )
    db.commit()
