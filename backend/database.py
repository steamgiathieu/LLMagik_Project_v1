from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import hashlib
import sqlite3
import logging
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone
from time import monotonic
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.errors import InvalidURI
from pymongo.uri_parser import parse_uri
from gridfs import GridFS
from gridfs.errors import NoFile
from dotenv import load_dotenv

_THIS_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=_THIS_DIR / ".env", override=False)
load_dotenv(override=False)

_BASE_DIR = Path(__file__).resolve().parent
_MONGO_SNAPSHOT_COLLECTION = "sqlite_snapshots"
_MONGO_SNAPSHOT_META_COLLECTION = "sqlite_snapshot_meta"
_MONGO_SNAPSHOT_FILES_BUCKET = "sqlite_snapshot_files"
_SNAPSHOT_DOC_ID = "llmagik_main"
_BACKUP_MIN_INTERVAL_SECONDS = float(os.getenv("SQLITE_BACKUP_INTERVAL_SECONDS", "8"))
_MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "8000"))
_MONGO_RESTORE_RETRIES = int(os.getenv("MONGO_RESTORE_RETRIES", "4"))
_MONGO_RESTORE_RETRY_DELAY_SECONDS = float(os.getenv("MONGO_RESTORE_RETRY_DELAY_SECONDS", "1.5"))

logger = logging.getLogger(__name__)

_mongo_snapshot_client: MongoClient | None = None
_last_backup_monotonic: float = 0.0


def _ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return os.access(path, os.W_OK)
    except OSError:
        return False


def _mongo_uri() -> str:
    candidates = [
        os.getenv("MONGODB_URI", "").strip(),
        os.getenv("MONGODB_URL", "").strip(),
        os.getenv("MONGO_URI", "").strip(),
        os.getenv("MONGO_URL", "").strip(),
    ]
    db_url = os.getenv("DATABASE_URL", "").strip()
    if db_url.startswith("mongodb://") or db_url.startswith("mongodb+srv://"):
        candidates.append(db_url)

    raw = next((x for x in candidates if x), "")
    if not raw:
        return ""

    # Keep valid URIs unchanged.
    try:
        parse_uri(raw)
        return raw
    except Exception:
        pass

    # Best-effort fix for unescaped special chars in username/password.
    try:
        if "://" not in raw or "@" not in raw:
            return raw
        scheme, rest = raw.split("://", 1)
        auth, tail = rest.split("@", 1)
        if ":" not in auth:
            return raw
        username, password = auth.split(":", 1)
        repaired = f"{scheme}://{quote_plus(username)}:{quote_plus(password)}@{tail}"
        parse_uri(repaired)
        return repaired
    except (ValueError, InvalidURI):
        return raw


def _mongo_db_name_from_uri(uri: str) -> str:
    tail = uri.split("://", 1)[-1]
    path = tail.split("/", 1)[-1] if "/" in tail else ""
    db_part = path.split("?", 1)[0].strip()
    # Atlas SRV URIs often omit explicit DB in path.
    if not db_part or db_part in ("",):
        db_part = ""
    return db_part or os.getenv("MONGODB_DB_NAME", "llmagik")


def _sqlite_has_user_data(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 4096:
        return False

    conn = None
    try:
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cur.fetchone():
            return False
        cur.execute("SELECT COUNT(*) FROM users")
        users_count = int(cur.fetchone()[0])
        return users_count > 0
    except Exception:
        return False
    finally:
        if conn is not None:
            conn.close()


def _sqlite_path_from_url(url: str) -> Path | None:
    if not url.startswith("sqlite:///"):
        return None
    raw = url[len("sqlite:///"):]
    if not raw:
        return None
    return Path(raw)


def _get_mongo_snapshot_db(force_reconnect: bool = False):
    global _mongo_snapshot_client
    uri = _mongo_uri()
    if not uri:
        return None

    try:
        if force_reconnect and _mongo_snapshot_client is not None:
            try:
                _mongo_snapshot_client.close()
            except Exception:
                pass
            _mongo_snapshot_client = None

        if _mongo_snapshot_client is None:
            _mongo_snapshot_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=_MONGO_SERVER_SELECTION_TIMEOUT_MS,
            )
        _mongo_snapshot_client.admin.command("ping")
        db_name = _mongo_db_name_from_uri(uri)
        return _mongo_snapshot_client[db_name]
    except Exception:
        logger.exception("Mongo snapshot DB is unavailable")
        return None


def _sqlite_snapshot_bytes(path: Path) -> bytes:
    """
    Get a consistent SQLite snapshot including WAL changes.
    """
    tmp_path: Path | None = None
    src = None
    dst = None
    try:
        with tempfile.NamedTemporaryFile(prefix="llmagik_snapshot_", suffix=".db", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        src = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        dst = sqlite3.connect(tmp_path.as_posix())
        src.backup(dst)
        dst.commit()
        return tmp_path.read_bytes()
    except Exception:
        logger.exception("SQLite backup API failed, falling back to direct file read")
        return path.read_bytes()
    finally:
        try:
            if src is not None:
                src.close()
        except Exception:
            pass
        try:
            if dst is not None:
                dst.close()
        except Exception:
            pass
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass


def _restore_sqlite_from_mongo_if_needed(sqlite_path: Path) -> None:
    # Restore when DB file is missing or has no user data (fresh/ephemeral reset).
    if sqlite_path.exists() and _sqlite_has_user_data(sqlite_path):
        return

    for attempt in range(_MONGO_RESTORE_RETRIES):
        db = _get_mongo_snapshot_db(force_reconnect=(attempt > 0))
        if db is None:
            if attempt < _MONGO_RESTORE_RETRIES - 1:
                time.sleep(_MONGO_RESTORE_RETRY_DELAY_SECONDS)
            continue

        try:
            payload = None

            # Preferred storage: GridFS + metadata doc.
            meta_col = db[_MONGO_SNAPSHOT_META_COLLECTION]
            meta = meta_col.find_one({"_id": _SNAPSHOT_DOC_ID})
            if meta and meta.get("file_id") is not None:
                fs = GridFS(db, collection=_MONGO_SNAPSHOT_FILES_BUCKET)
                try:
                    payload = fs.get(meta["file_id"]).read()
                except NoFile:
                    payload = None

            # Backward compatibility with old inline payload document.
            if payload is None:
                legacy_col = db[_MONGO_SNAPSHOT_COLLECTION]
                legacy_doc = legacy_col.find_one({"_id": _SNAPSHOT_DOC_ID})
                payload = legacy_doc.get("payload") if legacy_doc else None

            if not payload:
                return

            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            with open(sqlite_path, "wb") as f:
                f.write(bytes(payload))
        except Exception:
            logger.exception("Mongo restore attempt %s/%s failed", attempt + 1, _MONGO_RESTORE_RETRIES)
            if attempt < _MONGO_RESTORE_RETRIES - 1:
                time.sleep(_MONGO_RESTORE_RETRY_DELAY_SECONDS)
            continue

        # Sanity-check restored DB and avoid keeping a corrupt/empty payload.
        if _sqlite_has_user_data(sqlite_path):
            logger.info("SQLite restored from Mongo snapshot: %s", sqlite_path)
            return

        try:
            sqlite_path.unlink(missing_ok=True)
        except Exception:
            pass

    logger.warning("No valid Mongo snapshot restore was applied for SQLite path: %s", sqlite_path)


def _backup_sqlite_to_mongo(sqlite_path: Path) -> None:
    global _last_backup_monotonic

    if not sqlite_path.exists():
        return

    # Safety guard: never overwrite remote snapshot with an empty/new DB.
    if not _sqlite_has_user_data(sqlite_path):
        return

    # Throttle to reduce write load when multiple commits happen quickly.
    now = monotonic()
    if (now - _last_backup_monotonic) < _BACKUP_MIN_INTERVAL_SECONDS:
        return

    db = _get_mongo_snapshot_db()
    if db is None:
        return

    try:
        payload = _sqlite_snapshot_bytes(sqlite_path)
        payload_hash = hashlib.sha256(payload).hexdigest()
        size_bytes = len(payload)
        now_dt = datetime.now(timezone.utc)

        meta_col = db[_MONGO_SNAPSHOT_META_COLLECTION]
        prev_meta = meta_col.find_one({"_id": _SNAPSHOT_DOC_ID}) or {}
        if prev_meta.get("sha256") == payload_hash:
            _last_backup_monotonic = now
            return

        fs = GridFS(db, collection=_MONGO_SNAPSHOT_FILES_BUCKET)
        new_file_id = fs.put(
            payload,
            filename="llmagik_sqlite.db",
            contentType="application/octet-stream",
            metadata={
                "sha256": payload_hash,
                "size_bytes": size_bytes,
                "saved_at": now_dt,
            },
        )

        meta_col.update_one(
            {"_id": _SNAPSHOT_DOC_ID},
            {
                "$set": {
                    "file_id": new_file_id,
                    "sha256": payload_hash,
                    "size_bytes": size_bytes,
                    "db_path": str(sqlite_path),
                    "saved_at": now_dt,
                }
            },
            upsert=True,
        )

        old_file_id = prev_meta.get("file_id")
        if old_file_id and old_file_id != new_file_id:
            try:
                fs.delete(old_file_id)
            except Exception:
                pass

        _last_backup_monotonic = now
    except Exception:
        # Best-effort backup; do not fail request lifecycle.
        logger.exception("Failed to back up SQLite snapshot to Mongo")
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


def _is_render_runtime() -> bool:
    return (
        os.getenv("RENDER", "").strip().lower() == "true"
        or bool(os.getenv("RENDER_SERVICE_ID", "").strip())
    )


def _enforce_durable_storage_requirements() -> None:
    # Postgres or other external DB is already durable by design.
    if not DATABASE_URL.startswith("sqlite:///"):
        return

    if not _is_render_runtime():
        return

    mongo_ok = bool(_mongo_uri())
    sqlite_path = _sqlite_path_from_url(DATABASE_URL)
    sqlite_in_repo = (
        sqlite_path is not None
        and sqlite_path.resolve().as_posix().startswith(_BASE_DIR.resolve().as_posix())
    )

    # On Render, repository filesystem is ephemeral.
    if sqlite_in_repo and not mongo_ok:
        raise RuntimeError(
            "Unsafe persistence config: SQLite is on ephemeral Render filesystem and Mongo backup is not configured. "
            "Set MONGODB_URI (or MONGODB_URL/MONGO_URI/MONGO_URL) or mount persistent disk and set SQLITE_DB_PATH/DATA_DIR."
        )


def get_persistence_status() -> dict:
    sqlite_path = _sqlite_path_from_url(DATABASE_URL)
    mongo_uri_present = bool(_mongo_uri())
    mongo_db = _get_mongo_snapshot_db()
    snapshot_available = False

    if mongo_db is not None:
        try:
            meta = mongo_db[_MONGO_SNAPSHOT_META_COLLECTION].find_one({"_id": _SNAPSHOT_DOC_ID})
            legacy = mongo_db[_MONGO_SNAPSHOT_COLLECTION].find_one({"_id": _SNAPSHOT_DOC_ID})
            snapshot_available = bool((meta and meta.get("file_id")) or (legacy and legacy.get("payload")))
        except Exception:
            snapshot_available = False

    return {
        "database_url": DATABASE_URL,
        "sqlite_path": str(sqlite_path) if sqlite_path is not None else None,
        "sqlite_exists": bool(sqlite_path and sqlite_path.exists()),
        "sqlite_has_user_data": bool(sqlite_path and _sqlite_has_user_data(sqlite_path)),
        "mongo_uri_present": mongo_uri_present,
        "mongo_connection_ok": mongo_db is not None,
        "mongo_snapshot_available": snapshot_available,
        "render_runtime": _is_render_runtime(),
    }


DATABASE_URL = _resolve_database_url(_default_database_url())
_SQLITE_PATH = _sqlite_path_from_url(DATABASE_URL)

_enforce_durable_storage_requirements()

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
