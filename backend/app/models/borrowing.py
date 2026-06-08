from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date, datetime
from backend.app.db.session import Base


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    borrower = Column(String(50), nullable=False)
    department = Column(String(100), nullable=True)
    borrow_date = Column(Date, default=date.today)
    expected_return_date = Column(Date, nullable=True)
    actual_return_date = Column(Date, nullable=True)
    status = Column(String(20), default="borrowed")
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    document = relationship("Document", backref="borrow_records")
