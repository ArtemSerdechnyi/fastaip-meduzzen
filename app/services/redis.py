from redis.asyncio import Redis
import redis.asyncio as aioredis

from app.core.constants import REDIS_MAX_CONNECTIONS


class RedisService:
    _instance = None
    _redis: Redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _init_redis(self, url):
        if self._redis is None:
            pool = aioredis.ConnectionPool(
                max_connections=REDIS_MAX_CONNECTIONS
            ).from_url(url, decode_responses=True)
            pool.get_available_connection()
            self._redis = aioredis.Redis(
                connection_pool=pool, decode_responses=True
            )

    def _get_redis(self):
        if self._redis is None:
            raise Exception("Redis not initialized")
        return self._redis

    async def _close_redis(self):
        if self._redis is not None:
            await self._redis.aclose()

    async def set_value(self, key, value: str, expire: int = None):
        key = str(key)
        await self._redis.set(key, value)
        if expire:
            await self._redis.expire(key, expire)

    async def get_value(self, key):
        key = str(key)
        return await self._redis.get(key)
