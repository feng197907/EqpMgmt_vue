"""Search service — global search across devices, documents, and borrow records.

Provides a unified search API that queries multiple models and returns
categorised results.
"""

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models.device import Device
from backend.app.models.document import Document
from backend.app.models.borrowing import BorrowRecord


def global_search(
    db: Session,
    *,
    q: str,
    type: Optional[str] = None,
) -> dict:
    """Search across devices, documents, and borrow records.

    Args:
        q: Search query string.
        type: Optional filter — ``devices``, ``documents``, or
            ``borrow_records``.  ``None`` means search all.

    Returns:
        A dict with keys ``devices``, ``documents``, ``borrow_records``,
        each containing a list of matching items.
    """
    results: dict = {"devices": [], "documents": [], "borrow_records": []}
    like = f"%{q}%"

    if not type or type == "devices":
        devices = (
            db.query(Device)
            .filter(
                Device.is_deleted == False,
                or_(
                    Device.device_code.ilike(like),
                    Device.device_name.ilike(like),
                    Device.model.ilike(like),
                    Device.location.ilike(like),
                ),
            )
            .limit(20)
            .all()
        )
        results["devices"] = [
            {
                "id": d.id,
                "device_code": d.device_code,
                "device_name": d.device_name,
                "model": d.model,
                "location": d.location,
                "status": d.status,
            }
            for d in devices
        ]

    if not type or type == "documents":
        docs = (
            db.query(Document)
            .filter(
                Document.is_deleted == False,
                or_(
                    Document.doc_name.ilike(like),
                    Document.doc_type.ilike(like),
                    Document.uploaded_by.ilike(like),
                ),
            )
            .limit(20)
            .all()
        )
        results["documents"] = [
            {
                "id": d.id,
                "doc_name": d.doc_name,
                "doc_type": d.doc_type,
                "version": str(d.version) if d.version else None,
                "status": d.status,
                "uploaded_by": d.uploaded_by,
                "device_id": d.device_id,
            }
            for d in docs
        ]

    if not type or type == "borrow_records":
        records = (
            db.query(BorrowRecord)
            .filter(
                or_(
                    BorrowRecord.borrower.ilike(like),
                    BorrowRecord.department.ilike(like),
                ),
            )
            .limit(20)
            .all()
        )
        results["borrow_records"] = [
            {
                "id": r.id,
                "doc_id": r.doc_id,
                "borrower": r.borrower,
                "department": r.department,
                "status": r.status,
                "borrow_date": str(r.borrow_date) if r.borrow_date else None,
            }
            for r in records
        ]

    return results
