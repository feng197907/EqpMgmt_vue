import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env 文件（使用绝对路径，避免依赖当前工作目录）
_project_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_project_root / ".env")


class Settings:
    """Application settings loaded from environment variables.

    MySQL is the sole supported database backend.  SQLite support has been
    removed; any ``DATABASE_URL`` that starts with ``sqlite`` will raise a
    ``ValueError`` at startup.
    """

    def __init__(self) -> None:
        # ── Security ──────────────────────────────────────────────────
        self.SECRET_KEY: str = os.environ.get("SECRET_KEY", "please-change-this-secret")
        self.ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
        )
        self.REFRESH_TOKEN_EXPIRE_MINUTES: int = int(
            os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)
        )

        # ── MySQL Connection Pool ─────────────────────────────────────
        # Default DATABASE_URL points to a local MySQL instance.
        # Override via the DATABASE_URL environment variable in production.
        default_mysql_url = "mysql+pymysql://root:password@127.0.0.1:3306/dms_db"
        self.SQLALCHEMY_DATABASE_URL: str = os.environ.get(
            "DATABASE_URL", default_mysql_url
        )

        # Reject SQLite URLs explicitly
        if self.SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
            raise ValueError(
                "SQLite is no longer supported. "
                "Please set DATABASE_URL to a MySQL connection string, "
                "e.g. mysql+pymysql://user:pass@host:3306/dbname"
            )

        # ── MySQL Pool Settings ───────────────────────────────────────
        self.DB_POOL_SIZE: int = int(os.environ.get("DB_POOL_SIZE", 10))
        self.DB_MAX_OVERFLOW: int = int(os.environ.get("DB_MAX_OVERFLOW", 20))
        self.DB_POOL_RECYCLE: int = int(os.environ.get("DB_POOL_RECYCLE", 3600))
        self.DB_POOL_PRE_PING: bool = os.environ.get("DB_POOL_PRE_PING", "true").lower() == "true"

        # ── Password Policy ───────────────────────────────────────────
        self.PASSWORD_MIN_LENGTH: int = int(os.environ.get("PASSWORD_MIN_LENGTH", 8))


settings = Settings()
