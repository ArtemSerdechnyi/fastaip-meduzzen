import logging
from typing import AsyncGenerator

from pydantic_settings import BaseSettings
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declarative_base

from sqlalchemy.pool import NullPool


class _PostgresConfig(BaseSettings):
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    class Config:
        env_file = ".env.docker"
        env_file_encoding = "utf-8"
        extra = "ignore"


_pg_conf = _PostgresConfig()
_DATABASE_URL = (
    f"postgresql+asyncpg://{_pg_conf.POSTGRES_USER}:{_pg_conf.POSTGRES_PASSWORD}@"
    f"{_pg_conf.POSTGRES_SERVER}:{_pg_conf.POSTGRES_PORT}/{_pg_conf.POSTGRES_DB}"
)
_engine = create_async_engine(_DATABASE_URL, poolclass=NullPool)
_async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)

logging.info(f"Database URL: {_DATABASE_URL}")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_maker() as session:
        yield session
