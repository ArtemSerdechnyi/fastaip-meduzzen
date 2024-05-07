from contextlib import asynccontextmanager

import redis.asyncio as aioredis

from app.core.constants import REDIS_MAX_CONNECTIONS
from app.core.settings import redis_conf

redis_url = f"redis://{redis_conf.REDIS_HOST}:{redis_conf.REDIS_PORT}"


class RedisConnection:
    def __init__(self, url):
        self.url = url
        self._redis: aioredis.Redis = None

    async def init_redis(self):
        pool = aioredis.ConnectionPool(
            max_connections=REDIS_MAX_CONNECTIONS
        ).from_url(self.url, decode_responses=True)
        pool.get_available_connection()
        self._redis = aioredis.Redis(
            connection_pool=pool, decode_responses=True
        )
        await self._redis.ping()

    async def get_redis(self):
        if self._redis is None:
            await self.init_redis()
        return self._redis

    async def close_redis(self):
        if self._redis is not None:
            await self._redis.close()


redis = RedisConnection(redis_url)


@asynccontextmanager
async def lifespan_redis(app):
    try:
        await redis.init_redis()
        yield
    finally:
        await redis.close_redis()


def get_redis_connection() -> aioredis.Redis:
    return redis._redis
