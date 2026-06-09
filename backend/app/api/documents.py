"""Document management routes — upload, query, download, submit for approval.

All business logic is delegated to :mod:`backend.app.services.document_service`.
Legacy Flask imports have been removed.
"""

import os
import csv
from io import StringIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_admin, get_current_user
from backend.app.models.user import User
from backend.app.schemas.document import DocumentCreate, DocumentOut
from backend.app.services import document_service

router = APIRouter()


@router.get("/", response_model=List[DocumentOut])
def list_documents(
    q: Optional[str] = None,
    device_id: Optional[int] = None,
    uploader: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return non-deleted documents with optional filters."""
    return document_service.list_documents(db, q=q, device_id=device_id, uploader=uploader)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Return a single document by ID."""
    try:
        return document_service.get_document(db, doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    device_id: int = Form(...),
    doc_type: str = Form(...),
    version: str = Form(...),
    remarks: Optional[str] = Form(None),
    calibration_due_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a new document file."""
    file_content = file.file.read()
    try:
        return document_service.upload_document(
            db,
            device_id=device_id,
            doc_type=doc_type,
            version=version,
            file_content=file_content,
            file_name=file.filename,
            remarks=remarks,
            calibration_due_date=calibration_due_date,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download a document file."""
    try:
        doc = document_service.download_document(db, doc_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    # Resolve the file path
    # __file__ = backend/app/api/documents.py → 上4层才是项目根（与 document_service.py 上传时保持一致）
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    path = doc.file_path
    if not os.path.isabs(path):
        path = os.path.join(repo_root, path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path, filename=doc.doc_name, media_type="application/octet-stream")


@router.post("/{doc_id}/submit")
def submit_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a draft document for approval."""
    try:
        result = document_service.submit_document(db, doc_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.delete("/{doc_id}", dependencies=[Depends(require_admin)])
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Soft-delete a document."""
    try:
        document_service.delete_document(db, doc_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted"}


@router.get("/export")
def export_documents(
    q: Optional[str] = None,
    device_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Export documents as a CSV stream."""
    rows = document_service.list_documents(db, q=q, device_id=device_id)

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
