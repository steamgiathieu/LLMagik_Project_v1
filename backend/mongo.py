from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException, status
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database
from pymongo.errors import InvalidURI

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=False)
load_dotenv(override=False)

logger = logging.getLogger(__name__)
_mongo_client: MongoClient | None = None
_mongo_db: Database | None = None
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


def _resolve_uri() -> str:
    return (
        os.getenv("MONGODB_URI", "").strip()
        or os.getenv("MONGODB_URL", "").strip()
        or os.getenv("MONGO_URI", "").strip()
        or os.getenv("MONGO_URL", "").strip()
    )


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
    global _mongo_client, _mongo_db

    uri = _resolve_uri()
    if not uri:
        logger.warning("MongoDB disabled: missing URI (MONGODB_URI/MONGODB_URL/MONGO_URI/MONGO_URL)")
        _mongo_client = None
        _mongo_db = None
        return

    try:
        _mongo_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "8000")),
        )
        _mongo_client.admin.command("ping")
        _mongo_db = _mongo_client[_db_name_from_uri(uri)]
        _ensure_indexes(_mongo_db)
        logger.info("MongoDB initialized: db=%s", _mongo_db.name)
    except InvalidURI as exc:
        _mongo_client = None
        _mongo_db = None
        logger.warning("MongoDB disabled due to invalid URI: %s", exc)
    except Exception:
        _mongo_client = None
        _mongo_db = None
        logger.exception("MongoDB init failed")


def close_mongo() -> None:
    global _mongo_client, _mongo_db
    if _mongo_client is not None:
        _mongo_client.close()
    _mongo_client = None
    _mongo_db = None


def get_mongo_db() -> Database:
    if _mongo_db is None:
        raise RuntimeError("MongoDB is not initialized")
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
        "mongo_connection_ok": connection_ok,
        "mongo_db_name": db_name,
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
