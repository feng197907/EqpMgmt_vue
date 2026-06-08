"""Borrowing routes — borrow, return, list.

All business logic is delegated to :mod:`backend.app.services.borrowing_service`.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.schemas.borrowing import BorrowCreate, BorrowOut
from backend.app.services import borrowing_service

router = APIRouter()


@router.get("/")
def list_borrow_records(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Return borrow records, optionally filtered by status."""
    return borrowing_service.list_borrow_records(db, status=status)


@router.get("/my")
def my_borrow_records(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return borrow records for the current user."""
    return borrowing_service.my_borrow_records(db, current_user)


@router.post("/")
def borrow_document(
    payload: BorrowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Borrow a document."""
    try:
        return borrowing_service.borrow_document(
            db,
            doc_id=payload.doc_id,
            borrower=payload.borrower,
            department=payload.department,
            expected_return_date=payload.expected_return_date,
            remarks=payload.remarks,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{record_id}/return")
def return_document(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a borrowed document."""
    try:
        borrowing_service.return_document(db, record_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "returned"}


@router.delete("/{record_id}")
def delete_borrow_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a borrow record."""
    try:
        borrowing_service.delete_borrow_record(db, record_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted"}
