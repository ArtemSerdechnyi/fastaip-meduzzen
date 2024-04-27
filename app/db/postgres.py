import logging
from typing import AsyncGenerator

from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.settings import app_settings, postgres_config


class PostgresDB[T: BaseSettings]:
    def __init__(self, config: [T]):
        self._pg_conf = config
        self._DATABASE_URL = (
            f"postgresql+asyncpg://{self._pg_conf.POSTGRES_USER}:{self._pg_conf.POSTGRES_PASSWORD}@"
            f"{self._pg_conf.POSTGRES_SERVER}:{self._pg_conf.POSTGRES_PORT}/{self._pg_conf.POSTGRES_DB}"
        )

    @property
    def config(self) -> [T]:
        return self._pg_conf

    @property
    def url(self) -> str:
        return self._DATABASE_URL


_engine = create_async_engine(
    PostgresDB(postgres_config).url,
    poolclass=NullPool,
    echo=True if app_settings.DEBUG is True else False,
)
_async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)

logging.info(f"Database URL: {PostgresDB(postgres_config).url}")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_maker() as session:
        yield session
