"""Audit service — centralised audit logging.

Provides :func:`log_action` that all other services call to record
audit entries.  Also exposes query helpers for the audit-log API.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.audit import AuditLog
from backend.app.models.user import User


def log_action(
    db: Session,
    user: str,
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    details: Optional[str] = None,
    *,
    before_value: Optional[str] = None,
    after_value: Optional[str] = None,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Persist a single audit-log entry and return it.

    This is the **single source of truth** for audit logging across the
    entire Service layer.  Callers are responsible for committing the
    transaction (i.e. ``db.commit()``) as part of their own unit of work.
    """
    entry = AuditLog(
        user=user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        before_value=before_value,
        after_value=after_value,
        reason=reason,
        ip_address=ip_address,
    )
    db.add(entry)
    return entry


def query_audit_logs(
    db: Session,
    *,
    user: Optional[str] = None,
    action: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> List[AuditLog]:
    """Return paginated audit logs, newest first."""
    q = db.query(AuditLog)
    if user:
        q = q.filter(AuditLog.user.ilike(f"%{user}%"))
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    return (
        q.order_by(AuditLog.log_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
