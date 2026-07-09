"""MongoDB-backed cache with TTL. Lets us cache API-Football responses so the
free-tier daily quota (100 requests) stretches across the whole tournament.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
import logging
import asyncio

log = logging.getLogger(__name__)


class MongoCache:
    """Simple key/value cache backed by a MongoDB collection (`api_cache`)."""

    def __init__(self, collection):
        self.col = collection

    async def get(self, key: str) -> Optional[Any]:
        try:
            doc = await asyncio.wait_for(
                self.col.find_one({"_id": key}),
                timeout=2.0
            )
            if not doc:
                return None
            expires_at = doc.get("expires_at")
            if expires_at and datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
                return None
            return doc.get("data")
        except Exception as e:
            log.warning("MongoDB cache read failed: %s", e)
            return None

    async def set(self, key: str, data: Any, ttl_seconds: int) -> None:
        try:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
            await asyncio.wait_for(
                self.col.update_one(
                    {"_id": key},
                    {"$set": {"data": data, "expires_at": expires_at, "updated_at": datetime.now(timezone.utc).isoformat()}},
                    upsert=True,
                ),
                timeout=2.0
            )
        except Exception as e:
            log.warning("MongoDB cache write failed: %s", e)

    async def last_sync(self, key: str) -> Optional[str]:
        try:
            doc = await asyncio.wait_for(
                self.col.find_one({"_id": key}, {"updated_at": 1, "_id": 0}),
                timeout=2.0
            )
            return doc.get("updated_at") if doc else None
        except Exception as e:
            log.warning("MongoDB cache last_sync check failed: %s", e)
            return None


_CACHE: Optional[MongoCache] = None


def bind(collection) -> None:
    global _CACHE
    _CACHE = MongoCache(collection)


def instance() -> Optional[MongoCache]:
    return _CACHE
