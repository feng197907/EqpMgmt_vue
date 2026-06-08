from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func

from backend.app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)
    status = Column(String(32), nullable=True)
    permissions = Column(String(500), nullable=True)

    # ── Enhanced fields (T02) ────────────────────────────────────────
    email = Column(String(256), nullable=True)
    display_name = Column(String(128), nullable=True)
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
