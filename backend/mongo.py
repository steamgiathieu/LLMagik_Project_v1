from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import InvalidURI

_mongo_client: AsyncIOMotorClient | None = None
_mongo_db: AsyncIOMotorDatabase | None = None
logger = logging.getLogger(__name__)


def _db_name_from_uri(uri: str) -> str:
    # mongodb+srv://user:pass@cluster/dbname?params
    tail = uri.split("://", 1)[-1]
    path = tail.split("/", 1)[-1] if "/" in tail else ""
    db_part = path.split("?", 1)[0].strip()
    return db_part or os.getenv("MONGODB_DB_NAME", "llmagik")


def init_mongo() -> None:
    global _mongo_client, _mongo_db
    uri = os.getenv("MONGODB_URI", "").strip() or os.getenv("MONGODB_URL", "").strip()
    if not uri:
        return
    try:
        _mongo_client = AsyncIOMotorClient(uri)
        _mongo_db = _mongo_client[_db_name_from_uri(uri)]
    except InvalidURI as exc:
        # Mongo is optional; keep API alive even when URI is malformed.
        _mongo_client = None
        _mongo_db = None
        logger.warning("MongoDB disabled due to invalid MONGODB_URI: %s", exc)


def close_mongo() -> None:
    global _mongo_client, _mongo_db
    if _mongo_client is not None:
        _mongo_client.close()
    _mongo_client = None
    _mongo_db = None


def mongo_enabled() -> bool:
    return _mongo_db is not None


async def save_analysis_snapshot(payload: dict[str, Any]) -> None:
    if _mongo_db is None:
        return
    doc = {
        **payload,
        "saved_at": datetime.now(timezone.utc),
        "source": "analysis_router",
    }
    await _mongo_db["analysis_results"].insert_one(doc)
