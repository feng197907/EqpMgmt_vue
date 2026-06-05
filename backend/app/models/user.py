from sqlalchemy import Column, Integer, String, Text
from backend.app.db.session import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    role = Column(String(64), nullable=True)
    status = Column(String(32), nullable=True)
    permissions = Column(Text, nullable=True)
