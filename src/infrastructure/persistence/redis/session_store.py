from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

import redis.asyncio as redis


class RedisSessionStore:
    def __init__(self, client: redis.Redis, *, ttl_seconds: int = 3600, key_prefix: str = "transport:session:"):
        self._client = client
        self._ttl = ttl_seconds
        self._prefix = key_prefix

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        raw = await self._client.get(self._key(session_id))
        if not raw:
            return None
        return json.loads(raw)

    async def set(self, session_id: str, state: Dict[str, Any]) -> None:
        state["updated_at"] = datetime.utcnow().isoformat()
        await self._client.set(self._key(session_id), json.dumps(state, ensure_ascii=False), ex=self._ttl)

    async def delete(self, session_id: str) -> None:
        await self._client.delete(self._key(session_id))

    async def find_all_keys(self, pattern: str = "*") -> list:
        """
        Find all session keys matching the pattern

        Args:
            pattern: Redis key pattern (default: "*")

        Returns:
            List of session keys
        """
        full_pattern = f"{self._prefix}{pattern}"
        keys = await self._client.keys(full_pattern)
        return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
