"""Borrowing service — borrow/return workflow and audit.

All database mutations go through this module so that audit logging is
enforced consistently.
"""

from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.borrowing import BorrowRecord
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.services.audit_service import log_action


# ── Helpers ────────────────────────────────────────────────────────────────


def _borrow_to_out(record: BorrowRecord) -> dict:
    """Convert a BorrowRecord to a dict with joined document fields."""
    doc = record.document
    return {
        "id": record.id,
        "doc_id": record.doc_id,
        "borrower": record.borrower,
        "department": record.department,
        "borrow_date": record.borrow_date,
        "expected_return_date": record.expected_return_date,
        "actual_return_date": record.actual_return_date,
        "status": record.status,
        "remarks": record.remarks,
        "created_at": record.created_at,
        "doc_name": doc.doc_name if doc else None,
        "doc_type": doc.doc_type if doc else None,
        "version": str(doc.version) if doc and doc.version else None,
        "device_id": doc.device_id if doc else None,
    }


# ── Query ──────────────────────────────────────────────────────────────────


def list_borrow_records(db: Session, *, status: Optional[str] = None) -> List[dict]:
    """Return borrow records, optionally filtered by status."""
    q = db.query(BorrowRecord).order_by(BorrowRecord.borrow_date.desc())
    if status:
        q = q.filter(BorrowRecord.status == status)
    return [_borrow_to_out(r) for r in q.all()]


def my_borrow_records(db: Session, current_user: User) -> List[dict]:
    """Return borrow records for the current user."""
    records = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.borrower == current_user.username)
        .order_by(BorrowRecord.borrow_date.desc())
        .all()
    )
    return [_borrow_to_out(r) for r in records]


# ── Borrow / Return ────────────────────────────────────────────────────────


def borrow_document(
    db: Session,
    *,
    doc_id: int,
    borrower: Optional[str] = None,
    department: Optional[str] = None,
    expected_return_date: Optional[str] = None,
    remarks: Optional[str] = None,
    current_user: User,
) -> dict:
    """Borrow a document.  Returns the enriched borrow-record dict."""
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == False).first()
    if not doc:
        raise ValueError("Document not found")
    if doc.status != "active":
        raise ValueError("Only active documents can be borrowed")

    # Check for existing active borrow
    existing = (
        db.query(BorrowRecord)
        .filter(BorrowRecord.doc_id == doc_id, BorrowRecord.status == "borrowed")
        .first()
    )
    if existing:
        raise ValueError("Document already borrowed")

    expected_date = None
    if expected_return_date:
        try:
            expected_date = date.fromisoformat(expected_return_date)
        except ValueError:
            raise ValueError("Invalid date format")

    record = BorrowRecord(
        doc_id=doc_id,
        borrower=borrower or current_user.username,
        department=department,
        borrow_date=date.today(),
        expected_return_date=expected_date,
        remarks=remarks,
        status="borrowed",
    )
    db.add(record)
    log_action(db, current_user.username, "borrow_document", "borrow_record", record.id,
               f"借阅文档 {doc_id}")
    db.commit()
    db.refresh(record)
    return _borrow_to_out(record)


def return_document(db: Session, record_id: int, *, current_user: User) -> None:
    """Return a borrowed document."""
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record:
        raise ValueError("Borrow record not found")
    if record.status == "returned":
        raise ValueError("Already returned")
    record.status = "returned"
    record.actual_return_date = date.today()
    log_action(db, current_user.username, "return_document", "borrow_record", record_id, "归还文档")
    db.commit()


def delete_borrow_record(db: Session, record_id: int, *, current_user: User) -> None:
    """Hard-delete a borrow record."""
    record = db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()
    if not record:
        raise ValueError("Borrow record not found")
    log_action(db, current_user.username, "delete_borrow_record", "borrow_record", record_id, "删除借阅记录")
    db.delete(record)
    db.commit()
