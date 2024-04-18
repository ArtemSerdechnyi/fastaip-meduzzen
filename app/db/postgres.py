import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.settings import _PostgresConfig, postgres_config


class PostgresDB:
    _pg_conf = postgres_config
    _DATABASE_URL = (
        f"postgresql+asyncpg://{_pg_conf.POSTGRES_USER}:{_pg_conf.POSTGRES_PASSWORD}@"
        f"{_pg_conf.POSTGRES_SERVER}:{_pg_conf.POSTGRES_PORT}/{_pg_conf.POSTGRES_DB}"
    )

    @property
    def config(self) -> _PostgresConfig:
        return self._pg_conf

    @property
    def url(self) -> str:
        return self._DATABASE_URL


_engine = create_async_engine(PostgresDB().url, poolclass=NullPool)
_async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)

logging.info(f"Database URL: {PostgresDB().url}")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_maker() as session:
        yield session
