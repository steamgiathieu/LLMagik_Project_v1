from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent


def _persistent_data_root() -> Path:
    """Pick a persistent data root for SQLite/uploads when possible."""
    candidates = [
        os.getenv("PERSISTENT_DATA_DIR", "").strip(),
        os.getenv("RENDER_DISK_MOUNT_PATH", "").strip(),
        os.getenv("RENDER_DISK_PATH", "").strip(),
        os.getenv("DATA_DIR", "").strip(),
    ]
    for candidate in candidates:
        if candidate:
            return Path(candidate)

    # Common persistent disk path on Render.
    render_default = Path("/var/data")
    if render_default.exists() and os.access(render_default, os.W_OK):
        return render_default

    # Render fallback when the disk mount env is not explicitly set.
    if os.getenv("RENDER", "").strip().lower() == "true":
        return Path("/var/data")

    # Local dev fallback: keep current behavior (backend directory).
    return _BASE_DIR


def get_persistent_data_root() -> Path:
    """Public helper for other modules needing persistent file storage."""
    root = _persistent_data_root().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _default_database_url() -> str:
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return env_url

    sqlite_db_path = os.getenv("SQLITE_DB_PATH", "").strip()
    if sqlite_db_path:
        return f"sqlite:///{sqlite_db_path}"

    db_file_name = os.getenv("SQLITE_DB_FILENAME", "app.db").strip() or "app.db"
    db_dir = (get_persistent_data_root() / "llmagik").resolve()
    db_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(db_dir / db_file_name).as_posix()}"


def _resolve_database_url(raw_url: str) -> str:
    # Render/Heroku style postgres:// URL compatibility.
    if raw_url.startswith("postgres://"):
        return "postgresql+psycopg://" + raw_url[len("postgres://"):]

    if not raw_url.startswith("sqlite:///"):
        return raw_url

    path_part = raw_url[len("sqlite:///"):]
    if not path_part:
        return raw_url

    db_path = Path(path_part)
    if not db_path.is_absolute():
        persistent_root = get_persistent_data_root().resolve()
        if persistent_root != _BASE_DIR.resolve():
            db_path = (persistent_root / "llmagik" / db_path.name).resolve()
        else:
            db_path = (_BASE_DIR / db_path).resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


DATABASE_URL = _resolve_database_url(_default_database_url())

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
