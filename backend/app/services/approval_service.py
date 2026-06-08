"""Approval service — approval workflow with electronic-signature integration.

Handles creating approval requests, approving/rejecting them, and
recording audit logs.  When an approval is completed the associated
document status is updated accordingly.
"""

from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from backend.app.models.approval import ApprovalRequest, ApprovalStep
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Query ──────────────────────────────────────────────────────────────────


def list_pending_requests(db: Session) -> List[Tuple[ApprovalRequest, str]]:
    """Return pending approval requests with the associated document name.

    Returns a list of ``(ApprovalRequest, doc_name)`` tuples.
    """
    results = (
        db.query(ApprovalRequest, Document.doc_name)
        .join(Document, Document.id == ApprovalRequest.doc_id)
        .filter(ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.id.desc())
        .all()
    )
    return results


def get_request(db: Session, request_id: int) -> ApprovalRequest:
    """Return an approval request or raise ``ValueError``."""
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not req:
        raise ValueError("Request not found")
    return req


# ── Approval / Rejection ──────────────────────────────────────────────────


def approve_request(db: Session, request_id: int, *, current_user: User) -> None:
    """Approve the current pending step of an approval request.

    If all steps are approved, the request is marked as approved and the
    associated document is activated (old active versions are archived).
    """
    req = get_request(db, request_id)

    step = (
        db.query(ApprovalStep)
        .filter(
            ApprovalStep.request_id == request_id,
            ApprovalStep.status == "pending",
        )
        .order_by(ApprovalStep.step_order.asc())
        .first()
    )
    if not step:
        raise ValueError("No pending approval step")

    step.status = "approved"
    step.decided_by = current_user.username
    req.status = "approved"

    # Activate the document and archive old versions
    doc = db.query(Document).filter(Document.id == req.doc_id).first()
    if doc:
        db.query(Document).filter(
            Document.device_id == doc.device_id,
            Document.doc_type == doc.doc_type,
            Document.status == "active",
            Document.id != doc.id,
        ).update({"status": "archived"})
        doc.status = "active"

    log_action(db, current_user.username, "approve_request", "approval", request_id,
               f"批准审批请求 {request_id}")
    db.commit()


def reject_request(db: Session, request_id: int, *, current_user: User) -> None:
    """Reject the current pending step of an approval request.

    The document is reverted to ``draft`` status.
    """
    req = get_request(db, request_id)

    step = (
        db.query(ApprovalStep)
        .filter(
            ApprovalStep.request_id == request_id,
            ApprovalStep.status == "pending",
        )
        .order_by(ApprovalStep.step_order.asc())
        .first()
    )
    if step:
        step.status = "rejected"
        step.decided_by = current_user.username

    req.status = "rejected"

    # Revert document to draft
    doc = db.query(Document).filter(Document.id == req.doc_id).first()
    if doc:
        doc.status = "draft"

    log_action(db, current_user.username, "reject_request", "approval", request_id,
               f"拒绝审批请求 {request_id}")
    db.commit()
