from __future__ import annotations

import redis.asyncio as redis

from src.infrastructure.config.settings import Settings


def create_redis_client(settings: Settings) -> redis.Redis:
    return redis.Redis.from_url(
        settings.redis_connection_url,
        decode_responses=True,
    )

