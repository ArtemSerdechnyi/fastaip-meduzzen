from contextlib import asynccontextmanager

from app.core.settings import redis_conf
from app.services.redis import RedisService

redis_url = f"redis://{redis_conf.REDIS_HOST}:{redis_conf.REDIS_PORT}"


@asynccontextmanager
async def lifespan_redis(app):
    rs = RedisService()
    try:
        rs._init_redis(url=redis_url)
        redis = rs._get_redis()
        await redis.ping()
        yield
    finally:
        if rs is not None:
            await rs._close_redis()
