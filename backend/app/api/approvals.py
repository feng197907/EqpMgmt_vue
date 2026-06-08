"""Approval routes — list, approve, reject approval requests.

All business logic is delegated to :mod:`backend.app.services.approval_service`.
When an approval is completed, an electronic signature is automatically
created via :mod:`backend.app.services.esign_service`.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin, get_current_user
from backend.app.models.user import User
from backend.app.schemas.approval import ApprovalRequestOut, ApprovalDecision
from backend.app.services import approval_service
from backend.app.services import esign_service

router = APIRouter()


@router.get("/")
def list_requests(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """List all pending approval requests."""
    results = approval_service.list_pending_requests(db)
    return [
        {
            "id": req.id,
            "doc_id": req.doc_id,
            "doc_name": doc_name,
            "status": req.status,
            "created_by": req.created_by,
            "created_at": str(req.created_at) if req.created_at else None,
        }
        for req, doc_name in results
    ]


@router.post("/{request_id}/approve")
def approve_request(
    request_id: int,
    decision: ApprovalDecision = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Approve an approval request and create an electronic signature."""
    try:
        approval_service.approve_request(db, request_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Create an electronic signature for the approval action
    try:
        esign_service.create_signature(
            db,
            record_type="approval",
            record_id=request_id,
            sign_meaning="approved",
            sign_meaning_label="审批通过",
            remark=decision.comment if decision else None,
            current_user=current_user,
        )
    except ValueError:
        pass  # Signature already exists or duplicate — non-critical

    return {"status": "approved"}


@router.post("/{request_id}/reject")
def reject_request(
    request_id: int,
    decision: ApprovalDecision = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Reject an approval request and create an electronic signature."""
    try:
        approval_service.reject_request(db, request_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Create an electronic signature for the rejection action
    try:
        esign_service.create_signature(
            db,
            record_type="approval",
            record_id=request_id,
            sign_meaning="rejected",
            sign_meaning_label="审批拒绝",
            remark=decision.comment if decision else None,
            current_user=current_user,
        )
    except ValueError:
        pass  # Non-critical

    return {"status": "rejected"}
