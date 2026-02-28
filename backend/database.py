from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _resolve_database_url(raw_url: str) -> str:
    """
    Resolve DATABASE_URL reliably across different working directories.

    For sqlite relative paths (e.g. sqlite:///./app.db), always anchor to
    backend directory so running `python backend/main.py` from repo root and
    running uvicorn inside backend use the same DB file.
    """
    url = (raw_url or "").strip() or "sqlite:///./app.db"

    if not url.startswith("sqlite:///"):
        return url

    sqlite_path = url.replace("sqlite:///", "", 1)
    if os.path.isabs(sqlite_path):
        return url

    backend_dir = Path(__file__).resolve().parent
    abs_sqlite_path = (backend_dir / sqlite_path).resolve()
    return f"sqlite:///{abs_sqlite_path.as_posix()}"


DATABASE_URL = _resolve_database_url(os.getenv("DATABASE_URL", "sqlite:///./app.db"))

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
