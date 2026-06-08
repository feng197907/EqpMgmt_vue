"""PasswordResetRequest ORM model.

Tracks password-reset requests initiated by administrators.  Each request
captures who requested it, from which IP, and who processed it.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from backend.app.db.session import Base


class PasswordResetRequest(Base):
    __tablename__ = "password_reset_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(128), nullable=False)
    ip_address = Column(String(64), nullable=True)
    status = Column(String(32), default="pending")  # pending / completed / expired / cancelled
    requested_at = Column(DateTime, server_default=func.current_timestamp())
    processed_by = Column(String(128), nullable=True)
    processed_at = Column(DateTime, nullable=True)
