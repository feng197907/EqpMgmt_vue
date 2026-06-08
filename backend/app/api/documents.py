from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from sqlalchemy.orm import Session
import os
import csv
from io import StringIO

from backend.app.api.deps import get_db, require_admin, get_current_user
from backend.app.models.document import Document
from backend.app.models.approval import ApprovalRequest, ApprovalStep
from backend.app.schemas.document import DocumentCreate, DocumentOut
from backend.app.models.device import Device
from backend.app.models.user import User

from datetime import datetime
from utils.audit import log_action
from database import get_system_setting

router = APIRouter()


@router.get("/", response_model=List[DocumentOut])
def list_documents(q: Optional[str] = None, device_id: Optional[int] = None, uploader: Optional[str] = None, db: Session = Depends(get_db)):
    qset = db.query(Document).filter(Document.is_deleted == False)
    if q:
        qset = qset.filter(Document.doc_name.ilike(f"%{q}%"))
    if device_id:
        qset = qset.filter(Document.device_id == device_id)
    if uploader:
        qset = qset.filter(Document.uploaded_by.ilike(f"%{uploader}%"))
    qset = qset.order_by(Document.upload_time.desc())
    return qset.all()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    device_id: int = Form(...),
    doc_type: str = Form(...),
    version: str = Form(...),
    remarks: Optional[str] = Form(None),
    calibration_due_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # save file under uploads/device_{id}/
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    uploads_dir = os.path.join(repo_root, "uploads", f"device_{device_id}")
    os.makedirs(uploads_dir, exist_ok=True)
    safe_name = file.filename.replace('..', '.').replace('/', '_').replace('\\', '_')
    stored_name = f"{doc_type}_{version}_{safe_name}"
    file_path = os.path.join(uploads_dir, stored_name)
    with open(file_path, "wb") as fh:
        fh.write(file.file.read())

    relative_path = os.path.relpath(file_path, repo_root)
    doc = Document(
        device_id=device_id,
        doc_type=doc_type,
        doc_name=safe_name,
        version=version,
        file_path=relative_path,
        uploaded_by=getattr(current_user, 'username', 'system'),
        upload_time=datetime.utcnow(),
        remarks=remarks,
        status="draft",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    log_action(getattr(current_user, 'username', 'system'), "upload_document", "document", doc.id, f"上传 {doc.doc_name} v{doc.version}")
    return doc


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status not in {"active", "archived"}:
        raise HTTPException(status_code=403, detail="Document status does not allow download")
    # increment download_count
    doc.download_count = (doc.download_count or 0) + 1
    db.commit()
    # resolve absolute path
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = doc.file_path
    if not os.path.isabs(path):
        path = os.path.join(repo_root, path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    log_action(getattr(current_user, 'username', 'system'), "download_document", "document", doc.id, f"下载 {doc.doc_name} v{doc.version}")
    return FileResponse(path, filename=doc.doc_name, media_type='application/octet-stream')


@router.post("/{doc_id}/submit")
def submit_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.is_deleted == False
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "draft":
        raise HTTPException(status_code=400, detail="Document status does not allow submit")

    approval_enabled = get_system_setting("approval_enabled", "true")
    if approval_enabled != "true":
        doc.status = "active"
        db.commit()
        log_action(
            current_user.username, "submit_document", "document", doc.id,
            "提交（审批禁用，直接生效）"
        )
        return {"status": "active"}

    # 创建审批请求和审批步骤
    request = ApprovalRequest(
        doc_id=doc.id,
        status="pending",
        created_by=current_user.username,
        current_step=1,
    )
    db.add(request)
    db.flush()  # 获取 request.id

    try:
        from config import APPROVAL_STEPS
        for idx, step_config in enumerate(APPROVAL_STEPS, start=1):
            step = ApprovalStep(
                request_id=request.id,
                step_order=idx,
                approver_role=step_config.get("role"),
                status="pending",
            )
            db.add(step)
    except Exception:
        pass

    doc.status = "pending"
    db.commit()
    log_action(
        current_user.username, "submit_document", "document", doc.id,
        "提交审批"
    )
    return {"status": "pending", "request_id": request.id}


@router.delete("/{doc_id}", dependencies=[Depends(require_admin)])
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.is_deleted = True
    db.commit()
    log_action(getattr(current_user, 'username', 'system'), "delete_document", "document", doc.id, f"删除 {doc.doc_name} v{doc.version}")
    return {"status": "deleted"}


@router.get("/export")
def export_documents(q: Optional[str] = None, device_id: Optional[int] = None, db: Session = Depends(get_db)):
    qset = db.query(Document).filter(Document.is_deleted == False)
    if q:
        qset = qset.filter(Document.doc_name.ilike(f"%{q}%"))
    if device_id:
        qset = qset.filter(Document.device_id == device_id)
    rows = qset.order_by(Document.upload_time.desc()).all()
    # stream CSV
    def iter_csv():
        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow(["device_id", "doc_name", "doc_type", "version", "status", "uploaded_by", "upload_time"])
        yield sio.getvalue()
        sio.seek(0)
        sio.truncate(0)
        for r in rows:
            writer.writerow([r.device_id, r.doc_name, r.doc_type, r.version, r.status, r.uploaded_by, r.upload_time or ""])
            yield sio.getvalue()
            sio.seek(0)
            sio.truncate(0)

    return StreamingResponse(iter_csv(), media_type="text/csv")
