from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.core.settings import redis_conf


async def get_redis_client() -> aioredis.Redis:
    return await aioredis.from_url(
        f"redis://{redis_conf.REDIS_HOST}:{redis_conf.REDIS_PORT}"
    )


@asynccontextmanager
async def lifespan_redis(app: FastAPI):
    try:
        app.redis = await get_redis_client()
        yield
    finally:
        if app.redis:
            await app.redis.close()
