from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine.url import make_url
from backend.app.core.config import settings


db_url = make_url(settings.SQLALCHEMY_DATABASE_URL)
if db_url.get_backend_name() == 'sqlite':
	engine = create_engine(settings.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)
else:
	engine = create_engine(settings.SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
