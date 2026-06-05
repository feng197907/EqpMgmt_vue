from pathlib import Path
import os


class Settings:
    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "please-change-this-secret")
        self.ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
        self.REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))
        repo_root = Path(__file__).resolve().parents[3]
        db_path = os.environ.get("SQLITE_DB_PATH") or (repo_root / "equipment.db")
        self.SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")


settings = Settings()
