from redis.asyncio import Redis


class RedisService:
    def __init__(self):
        from app.core.application import get_app

        app = get_app()
        self._redis: Redis = app.redis

    async def set_value(self, key, value: str, expire: int = None):
        key = str(key)
        await self._redis.set(key, value)
        if expire:
            await self._redis.expire(key, expire)

    async def get_value(self, key):
        key = str(key)
        return await self._redis.get(key)
