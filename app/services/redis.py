from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from pydantic_settings import BaseSettings


class _RedisConfig(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env.docker"
        env_file_encoding = "utf-8"
        extra = "ignore"


_conf = _RedisConfig()


async def get_redis_client() -> aioredis.Redis:
    return await aioredis.from_url(f"redis://{_conf.REDIS_HOST}:{_conf.REDIS_PORT}")


@asynccontextmanager
async def lifespan_redis(app: FastAPI):
    try:

        app.redis = await get_redis_client()
        yield
    finally:
        if app.redis:
            await app.redis.close()
