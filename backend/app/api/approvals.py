from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin, get_current_user
from backend.app.models.approval import ApprovalRequest, ApprovalStep
from backend.app.models.document import Document
from backend.app.models.user import User
from utils.audit import log_action

router = APIRouter()


@router.get("/")
def list_requests(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    """列出所有待处理的审批请求"""
    requests = (
        db.query(ApprovalRequest, Document.doc_name)
        .join(Document, Document.id == ApprovalRequest.doc_id)
        .filter(ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.id.desc())
        .all()
    )
    result = []
    for req, doc_name in requests:
        result.append({
            "id": req.id,
            "doc_id": req.doc_id,
            "doc_name": doc_name,
            "status": req.status,
            "created_by": req.created_by,
            "created_at": str(req.created_at) if req.created_at else None,
        })
    return result


@router.post("/{request_id}/approve")
def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """批准审批请求"""
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # 找到下一个待处理的审批步骤
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
        raise HTTPException(status_code=400, detail="No pending approval step")

    # 标记步骤为已批准
    step.status = "approved"
    step.decided_by = current_user.username

    # 批准请求并将文档设为 active，归档旧版本
    req.status = "approved"

    doc = db.query(Document).filter(Document.id == req.doc_id).first()
    if doc:
        # 归档同设备同类型的所有 active 版本
        db.query(Document).filter(
            Document.device_id == doc.device_id,
            Document.doc_type == doc.doc_type,
            Document.status == "active",
            Document.id != doc.id,
        ).update({"status": "archived"})
        doc.status = "active"

    db.commit()
    log_action(
        current_user.username, "approve_request", "approval", request_id,
        f"批准审批请求 {request_id}"
    )
    return {"status": "approved"}


@router.post("/{request_id}/reject")
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """拒绝审批请求"""
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # 标记当前待处理步骤为拒绝
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

    # 文档退回 draft 状态
    doc = db.query(Document).filter(Document.id == req.doc_id).first()
    if doc:
        doc.status = "draft"

    db.commit()
    log_action(
        current_user.username, "reject_request", "approval", request_id,
        f"拒绝审批请求 {request_id}"
    )
    return {"status": "rejected"}
