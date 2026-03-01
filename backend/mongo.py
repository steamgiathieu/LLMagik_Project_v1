from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from dotenv import load_dotenv
from fastapi import HTTPException, status
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database
from pymongo.errors import InvalidURI
from pymongo.uri_parser import parse_uri

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)
load_dotenv(override=False)

logger = logging.getLogger(__name__)
_mongo_client: MongoClient | None = None
_mongo_db: Database | None = None
_last_mongo_init_error: str | None = None
_last_mongo_uri_source: str | None = None
_BASE_DIR = Path(__file__).resolve().parent


def _ensure_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return os.access(path, os.W_OK)
    except OSError:
        return False


def _persistent_data_root() -> Path:
    """Pick a persistent data root for uploads/cache when possible."""
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

    render_default = Path("/var/data")
    if _ensure_dir(render_default):
        return render_default

    if os.getenv("RENDER", "").strip().lower() == "true":
        return Path("/var/data")

    return _BASE_DIR


def get_persistent_data_root() -> Path:
    root = _persistent_data_root().resolve()
    if _ensure_dir(root):
        return root
    _ensure_dir(_BASE_DIR)
    return _BASE_DIR


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _db_name_from_uri(uri: str) -> str:
    # mongodb+srv://user:pass@cluster/dbname?params
    tail = uri.split("://", 1)[-1]
    path = tail.split("/", 1)[-1] if "/" in tail else ""
    db_part = path.split("?", 1)[0].strip()
    return db_part or os.getenv("MONGODB_DB_NAME", "llmagik")


def _normalize_mongo_uri(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""

    # Common deployment copy/paste issue: wrapping URI in quotes or angle brackets.
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1].strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1].strip()

    try:
        parse_uri(value)
        return value
    except Exception:
        pass

    # Best-effort fix for unescaped special chars in username/password.
    try:
        if "://" in value and "@" in value:
            scheme, rest = value.split("://", 1)
            auth, tail = rest.split("@", 1)
            if ":" in auth:
                username, password = auth.split(":", 1)
                repaired = f"{scheme}://{quote_plus(username)}:{quote_plus(password)}@{tail}"
                parse_uri(repaired)
                return repaired
    except Exception:
        pass

    return value


def _extract_mongo_uri_candidate(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""

    lower = value.lower()
    if lower.startswith("mongodb://") or lower.startswith("mongodb+srv://"):
        return value

    # Handle env-style payload pasted as value, e.g.:
    # "MONGODB_URL=mongodb+srv://..." or "export MONGODB_URL=..."
    if lower.startswith("export "):
        value = value[7:].strip()

    if "=" in value:
        _, rhs = value.split("=", 1)
        rhs = rhs.strip()
        rhs_lower = rhs.lower()
        if rhs_lower.startswith("mongodb://") or rhs_lower.startswith("mongodb+srv://"):
            return rhs

    return ""


def _read_secret_file(path: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists() or not p.is_file():
            return ""
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _get_env_case_insensitive(name: str) -> tuple[str, str | None]:
    exact = os.getenv(name)
    if exact is not None and str(exact).strip():
        return str(exact).strip(), name

    target = name.lower()
    for k, raw in os.environ.items():
        if k.strip().lower() == target and str(raw).strip():
            return str(raw).strip(), k
    return "", None


def _get_env_or_file(name: str) -> tuple[str, str | None]:
    value, source = _get_env_case_insensitive(name)
    if value:
        return value, source

    file_value, file_source = _get_env_case_insensitive(f"{name}_FILE")
    if file_value:
        from_file = _read_secret_file(file_value)
        if from_file:
            return from_file, file_source
    return "", None


def _present_mongo_related_env_keys() -> list[str]:
    expected = {
        "MONGODB_URI",
        "MONGODB_URL",
        "MONGO_URI",
        "MONGO_URL",
        "DATABASE_URL",
        "MONGODB_URI_FILE",
        "MONGODB_URL_FILE",
        "MONGO_URI_FILE",
        "MONGO_URL_FILE",
        "DATABASE_URL_FILE",
    }
    keys = [k for k in os.environ.keys() if k.strip().upper() in expected]
    keys.sort()
    return keys


def _resolve_uri() -> str:
    global _last_mongo_uri_source

    for key in ("MONGODB_URI", "MONGODB_URL", "MONGO_URI", "MONGO_URL", "DATABASE_URL"):
        raw, source = _get_env_or_file(key)
        if not raw:
            continue
        candidate = _extract_mongo_uri_candidate(raw)
        if candidate:
            _last_mongo_uri_source = source or key
            return _normalize_mongo_uri(candidate)

    _last_mongo_uri_source = None
    return ""


def _ensure_indexes(db: Database) -> None:
    db["users"].create_index([("username", ASCENDING)], unique=True)
    db["users"].create_index([("email", ASCENDING)], unique=True)
    db["user_profiles"].create_index([("user_id", ASCENDING)], unique=True)

    db["documents"].create_index([("document_id", ASCENDING)], unique=True)
    db["documents"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db["paragraphs"].create_index([("document_id", ASCENDING), ("index", ASCENDING)])
    db["paragraphs"].create_index([("document_id", ASCENDING), ("paragraph_id", ASCENDING)])

    db["analyses"].create_index([("analysis_id", ASCENDING)], unique=True)
    db["analyses"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db["analyses"].create_index([("document_id", ASCENDING), ("created_at", DESCENDING)])

    db["rewrites"].create_index([("rewrite_id", ASCENDING)], unique=True)
    db["rewrites"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db["rewrites"].create_index([("document_id", ASCENDING), ("created_at", DESCENDING)])

    db["chat_sessions"].create_index([("session_id", ASCENDING)], unique=True)
    db["chat_sessions"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db["chat_sessions"].create_index([("document_id", ASCENDING), ("created_at", DESCENDING)])

    db["chat_messages"].create_index([("session_id", ASCENDING), ("message_id", ASCENDING)])
    db["chat_messages"].create_index([("session_id", ASCENDING), ("created_at", ASCENDING)])


def init_mongo() -> None:
    global _mongo_client, _mongo_db, _last_mongo_init_error

    uri = _resolve_uri()
    if not uri:
        logger.warning("MongoDB disabled: missing URI (MONGODB_URI/MONGODB_URL/MONGO_URI/MONGO_URL)")
        _mongo_client = None
        _mongo_db = None
        checked = "MONGODB_URI/MONGODB_URL/MONGO_URI/MONGO_URL/DATABASE_URL (+ *_FILE)"
        present = _present_mongo_related_env_keys()
        present_suffix = f"; present keys={present}" if present else ""
        _last_mongo_init_error = f"Missing MongoDB URI env variable (checked {checked}){present_suffix}"
        return

    try:
        _mongo_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "15000")),
        )
        _mongo_client.admin.command("ping")
        _mongo_db = _mongo_client[_db_name_from_uri(uri)]
        _ensure_indexes(_mongo_db)
        _last_mongo_init_error = None
        logger.info("MongoDB initialized: db=%s", _mongo_db.name)
    except InvalidURI as exc:
        _mongo_client = None
        _mongo_db = None
        _last_mongo_init_error = f"Invalid MongoDB URI: {exc}"
        logger.warning("MongoDB disabled due to invalid URI: %s", exc)
    except Exception as exc:
        _mongo_client = None
        _mongo_db = None
        _last_mongo_init_error = str(exc)
        logger.exception("MongoDB init failed")


def close_mongo() -> None:
    global _mongo_client, _mongo_db
    if _mongo_client is not None:
        _mongo_client.close()
    _mongo_client = None
    _mongo_db = None


def get_mongo_db() -> Database:
    if _mongo_db is None:
        # Lazy re-init: useful when startup init failed due to cold-start/network race.
        init_mongo()
    if _mongo_db is None:
        detail = "MongoDB is not initialized"
        if _last_mongo_init_error:
            detail = f"{detail}: {_last_mongo_init_error}"
        raise RuntimeError(detail)
    return _mongo_db


def get_mongo_db_dependency() -> Database:
    try:
        return get_mongo_db()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


def mongo_enabled() -> bool:
    return _mongo_db is not None


def get_persistence_status() -> dict[str, Any]:
    root = get_persistent_data_root()
    uri_present = bool(_resolve_uri())
    connection_ok = mongo_enabled()
    db_name = _mongo_db.name if _mongo_db is not None else None
    return {
        "mongo_uri_present": uri_present,
        "mongo_uri_source": _last_mongo_uri_source,
        "mongo_connection_ok": connection_ok,
        "mongo_db_name": db_name,
        "mongo_init_error": _last_mongo_init_error,
        "mongo_present_env_keys": _present_mongo_related_env_keys(),
        "persistent_data_root": str(root),
    }


def next_sequence(name: str) -> int:
    db = get_mongo_db()
    doc = db["counters"].find_one_and_update(
        {"_id": name},
        {"$inc": {"value": 1}, "$setOnInsert": {"created_at": utcnow()}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["value"])


def ensure_default_profile(user_id: int) -> dict[str, Any]:
    db = get_mongo_db()
    existing = db["user_profiles"].find_one({"user_id": user_id})
    if existing:
        return existing
    profile = {
        "user_id": user_id,
        "language": "vi",
        "role": "reader",
        "age_group": "adult",
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    db["user_profiles"].insert_one(profile)
    return profile
