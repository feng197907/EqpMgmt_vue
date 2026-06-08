"""ElectronicSignature ORM model.

Records electronic signatures for regulatory compliance (21 CFR Part 11).
Each signature is immutable after creation — the ``is_deleted`` flag is the
only soft-delete mechanism.  The composite index on ``(record_type,
record_id)`` serves as a "locking table" to prevent duplicate signatures
for the same meaning on the same record.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, func

from backend.app.db.session import Base


class ElectronicSignature(Base):
    __tablename__ = "electronic_signatures"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(64), nullable=False)       # e.g. maintenance_plan, document, device_change
    record_id = Column(Integer, nullable=False)
    signed_by = Column(String(128), nullable=False)        # signer username
    signed_by_display = Column(String(100), nullable=False) # signer display name snapshot
    sign_meaning = Column(String(32), nullable=False)      # approved / reviewed / executed / released
    sign_meaning_label = Column(String(50), nullable=False) # Chinese label for the meaning
    signed_at = Column(DateTime, server_default=func.current_timestamp())
    ip_address = Column(String(50), nullable=True)
    remark = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_esign_record", "record_type", "record_id"),
    )
