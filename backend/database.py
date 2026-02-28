from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from pathlib import Path
from datetime import datetime, timezone
from time import monotonic

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent
_MONGO_SNAPSHOT_COLLECTION = "sqlite_snapshots"
_SNAPSHOT_DOC_ID = "llmagik_main"
_BACKUP_MIN_INTERVAL_SECONDS = float(os.getenv("SQLITE_BACKUP_INTERVAL_SECONDS", "8"))

_mongo_snapshot_client: MongoClient | None = None
_last_backup_monotonic: float = 0.0


def _ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return os.access(path, os.W_OK)
    except OSError:
        return False


def _mongo_uri() -> str:
    return (os.getenv("MONGODB_URI", "").strip() or os.getenv("MONGODB_URL", "").strip())


def _mongo_db_name_from_uri(uri: str) -> str:
    tail = uri.split("://", 1)[-1]
    path = tail.split("/", 1)[-1] if "/" in tail else ""
    db_part = path.split("?", 1)[0].strip()
    return db_part or os.getenv("MONGODB_DB_NAME", "llmagik")


def _sqlite_path_from_url(url: str) -> Path | None:
    if not url.startswith("sqlite:///"):
        return None
    raw = url[len("sqlite:///"):]
    if not raw:
        return None
    return Path(raw)


def _get_mongo_snapshot_collection():
    global _mongo_snapshot_client
    uri = _mongo_uri()
    if not uri:
        return None

    try:
        if _mongo_snapshot_client is None:
            _mongo_snapshot_client = MongoClient(uri, serverSelectionTimeoutMS=2500)
        db_name = _mongo_db_name_from_uri(uri)
        return _mongo_snapshot_client[db_name][_MONGO_SNAPSHOT_COLLECTION]
    except Exception:
        return None


def _restore_sqlite_from_mongo_if_needed(sqlite_path: Path) -> None:
    if sqlite_path.exists():
        return

    col = _get_mongo_snapshot_collection()
    if col is None:
        return

    try:
        doc = col.find_one({"_id": _SNAPSHOT_DOC_ID})
        payload = doc.get("payload") if doc else None
        if not payload:
            return

        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with open(sqlite_path, "wb") as f:
            f.write(bytes(payload))
    except Exception:
        # Mongo snapshot restore is best-effort and must never block app start.
        return


def _backup_sqlite_to_mongo(sqlite_path: Path) -> None:
    global _last_backup_monotonic

    if not sqlite_path.exists():
        return

    # Throttle to reduce write load when multiple commits happen quickly.
    now = monotonic()
    if (now - _last_backup_monotonic) < _BACKUP_MIN_INTERVAL_SECONDS:
        return

    col = _get_mongo_snapshot_collection()
    if col is None:
        return

    try:
        payload = sqlite_path.read_bytes()
        col.update_one(
            {"_id": _SNAPSHOT_DOC_ID},
            {
                "$set": {
                    "payload": payload,
                    "db_path": str(sqlite_path),
                    "saved_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        _last_backup_monotonic = now
    except Exception:
        # Best-effort backup; do not fail request lifecycle.
        return


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
            c = Path(candidate)
            if _ensure_dir(c):
                return c

    # Common persistent disk path on Render.
    render_default = Path("/var/data")
    if _ensure_dir(render_default):
        return render_default

    # Render fallback when the disk mount env is not explicitly set.
    if os.getenv("RENDER", "").strip().lower() == "true":
        return Path("/var/data")

    # Local dev fallback: keep current behavior (backend directory).
    return _BASE_DIR


def get_persistent_data_root() -> Path:
    """Public helper for other modules needing persistent file storage."""
    root = _persistent_data_root().resolve()
    if _ensure_dir(root):
        return root
    # Never crash app startup if host mount path is not writable.
    _ensure_dir(_BASE_DIR)
    return _BASE_DIR


def _default_database_url() -> str:
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return env_url

    sqlite_db_path = os.getenv("SQLITE_DB_PATH", "").strip()
    if sqlite_db_path:
        return f"sqlite:///{sqlite_db_path}"

    db_file_name = os.getenv("SQLITE_DB_FILENAME", "app.db").strip() or "app.db"
    db_dir = (get_persistent_data_root() / "llmagik").resolve()
    if not _ensure_dir(db_dir):
        db_dir = _BASE_DIR
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

    if not _ensure_dir(db_path.parent):
        db_path = (_BASE_DIR / db_path.name).resolve()
        _ensure_dir(db_path.parent)
    return f"sqlite:///{db_path.as_posix()}"


DATABASE_URL = _resolve_database_url(_default_database_url())
_SQLITE_PATH = _sqlite_path_from_url(DATABASE_URL)

if _SQLITE_PATH is not None:
    _restore_sqlite_from_mongo_if_needed(_SQLITE_PATH)

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
        if _SQLITE_PATH is not None:
            _backup_sqlite_to_mongo(_SQLITE_PATH)
    finally:
        db.close()
