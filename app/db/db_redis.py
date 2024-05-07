from contextlib import asynccontextmanager

import redis.asyncio as aioredis

from fastapi import FastAPI

from app.core.settings import redis_conf

redis_url = f"redis://{redis_conf.REDIS_HOST}:{redis_conf.REDIS_PORT}"


async def get_redis_client() -> aioredis.Redis:
    return await aioredis.from_url(redis_url, decode_responses=True)


@asynccontextmanager
async def lifespan_redis(app: FastAPI):
    try:
        app.redis = await get_redis_client()
        await app.redis.ping()
        yield
    finally:
        if app.redis:
            await app.redis.close()
