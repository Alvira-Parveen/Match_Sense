"""MongoDB-backed cache with TTL. Lets us cache API-Football responses so the
free-tier daily quota (100 requests) stretches across the whole tournament.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import logging

log = logging.getLogger(__name__)


class MongoCache:
    """Simple key/value cache backed by a MongoDB collection (`api_cache`)."""

    def __init__(self, collection):
        self.col = collection

    async def get(self, key: str) -> Optional[Any]:
        doc = await self.col.find_one({"_id": key})
        if not doc:
            return None
        expires_at = doc.get("expires_at")
        if expires_at and datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
            return None
        return doc.get("data")

    async def set(self, key: str, data: Any, ttl_seconds: int) -> None:
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        await self.col.update_one(
            {"_id": key},
            {"$set": {"data": data, "expires_at": expires_at, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )

    async def last_sync(self, key: str) -> Optional[str]:
        doc = await self.col.find_one({"_id": key}, {"updated_at": 1, "_id": 0})
        return doc.get("updated_at") if doc else None


_CACHE: Optional[MongoCache] = None


def bind(collection) -> None:
    global _CACHE
    _CACHE = MongoCache(collection)


def instance() -> Optional[MongoCache]:
    return _CACHE
