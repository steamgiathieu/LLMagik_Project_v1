from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_RAW_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
_BASE_DIR = Path(__file__).resolve().parent


def _resolve_database_url(raw_url: str) -> str:
    if not raw_url.startswith("sqlite:///"):
        return raw_url

    path_part = raw_url[len("sqlite:///"):]
    if not path_part:
        return raw_url

    db_path = Path(path_part)
    if db_path.is_absolute():
        return raw_url

    absolute_path = (_BASE_DIR / db_path).resolve()
    return f"sqlite:///{absolute_path.as_posix()}"


DATABASE_URL = _resolve_database_url(_RAW_DATABASE_URL)

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
