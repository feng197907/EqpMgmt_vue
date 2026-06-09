"""Document service — document upload/query, submit for approval, and audit.

All database mutations go through this module so that audit logging is
enforced consistently.
"""

import os
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.models.approval import ApprovalRequest, ApprovalStep
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Helpers ────────────────────────────────────────────────────────────────

_APPROVAL_STEPS = [{"role": "admin"}]


def _get_system_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    """Read a system setting value from the database."""
    from backend.app.models.audit import SystemSetting
    setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
    return setting.setting_value if setting else default


# ── CRUD ───────────────────────────────────────────────────────────────────


def list_documents(
    db: Session,
    *,
    q: Optional[str] = None,
    device_id: Optional[int] = None,
    uploader: Optional[str] = None,
) -> List[Document]:
    """Return non-deleted documents, optionally filtered."""
    qset = db.query(Document).filter(Document.is_deleted == False)
    if q:
        qset = qset.filter(Document.doc_name.ilike(f"%{q}%"))
    if device_id:
        qset = qset.filter(Document.device_id == device_id)
    if uploader:
        qset = qset.filter(Document.uploaded_by.ilike(f"%{uploader}%"))
    return qset.order_by(Document.upload_time.desc()).all()


def get_document(db: Session, doc_id: int) -> Document:
    """Return a single document by ID."""
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc:
        raise ValueError("Document not found")
    return doc


def upload_document(
    db: Session,
    *,
    device_id: int,
    doc_type: str,
    version: str,
    file_content: bytes,
    file_name: str,
    remarks: Optional[str] = None,
    calibration_due_date=None,
    current_user: Optional[User] = None,
) -> Document:
    """Upload a new document.  The caller is responsible for reading the
    uploaded file and passing its content as ``file_content``.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    uploads_dir = os.path.join(repo_root, "uploads", f"device_{device_id}")
    os.makedirs(uploads_dir, exist_ok=True)

    safe_name = file_name.replace("..", ".").replace("/", "_").replace("\\", "_")
    stored_name = f"{doc_type}_{version}_{safe_name}"
    file_path = os.path.join(uploads_dir, stored_name)
    with open(file_path, "wb") as fh:
        fh.write(file_content)

    relative_path = os.path.relpath(file_path, repo_root)
    operator = current_user.username if current_user else "system"

    doc = Document(
        device_id=device_id,
        doc_type=doc_type,
        doc_name=safe_name,
        version=version,
        file_path=relative_path,
        uploaded_by=operator,
        upload_time=datetime.utcnow(),
        remarks=remarks,
        status="draft",
        calibration_due_date=calibration_due_date,
    )
    db.add(doc)
    db.flush()

    log_action(db, operator, "upload_document", "document", doc.id,
               f"上传 {doc.doc_name} v{doc.version}")

    db.commit()
    db.refresh(doc)
    return doc


def download_document(db: Session, doc_id: int, *, current_user: Optional[User] = None) -> Document:
    """Increment download count and return the document for download."""
    doc = get_document(db, doc_id)
    # draft 文档仅上传者本人或管理员可下载；active/archived 所有人可下载
    if doc.status not in {"active", "archived", "draft"}:
        raise PermissionError("Document status does not allow download")
    if doc.status == "draft":
        is_owner = current_user and (doc.uploaded_by == current_user.username)
        is_admin = current_user and getattr(current_user, "role", None) in {"admin", "superadmin"}
        if not (is_owner or is_admin):
            raise PermissionError("Draft document can only be downloaded by the uploader or admin")

    doc.download_count = (doc.download_count or 0) + 1
    operator = current_user.username if current_user else "system"
    log_action(db, operator, "download_document", "document", doc.id,
               f"下载 {doc.doc_name} v{doc.version}")
    db.commit()
    return doc


def submit_document(db: Session, doc_id: int, *, current_user: User) -> dict:
    """Submit a draft document for approval.

    Returns a dict ``{"status": ..., "request_id": ...}``.
    """
    doc = get_document(db, doc_id)
    if doc.status != "draft":
        raise ValueError("Document status does not allow submit")

    approval_enabled = _get_system_setting(db, "approval_enabled", "true")
    if approval_enabled != "true":
        doc.status = "active"
        log_action(db, current_user.username, "submit_document", "document", doc.id,
                   "提交（审批禁用，直接生效）")
        db.commit()
        return {"status": "active"}

    # Create approval request and steps
    request = ApprovalRequest(
        doc_id=doc.id,
        status="pending",
        created_by=current_user.username,
        current_step=1,
    )
    db.add(request)
    db.flush()

    for idx, step_config in enumerate(_APPROVAL_STEPS, start=1):
        step = ApprovalStep(
            request_id=request.id,
            step_order=idx,
            approver_role=step_config.get("role"),
            status="pending",
        )
        db.add(step)

    doc.status = "pending"
    log_action(db, current_user.username, "submit_document", "document", doc.id, "提交审批")
    db.commit()
    return {"status": "pending", "request_id": request.id}


def delete_document(db: Session, doc_id: int, *, current_user: Optional[User] = None) -> None:
    """Soft-delete a document."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise ValueError("Document not found")
    doc.is_deleted = True

    operator = current_user.username if current_user else "system"
    log_action(db, operator, "delete_document", "document", doc.id,
               f"删除 {doc.doc_name} v{doc.version}")
    db.commit()
