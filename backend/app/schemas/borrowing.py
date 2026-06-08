from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class BorrowCreate(BaseModel):
    doc_id: int
    borrower: str
    department: Optional[str] = None
    expected_return_date: Optional[str] = None
    remarks: Optional[str] = None


class BorrowOut(BaseModel):
    id: int
    doc_id: int
    borrower: str
    department: Optional[str] = None
    borrow_date: Optional[date] = None
    expected_return_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    status: str
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    # joined from documents
    doc_name: Optional[str] = None
    doc_type: Optional[str] = None
    version: Optional[str] = None
    device_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
