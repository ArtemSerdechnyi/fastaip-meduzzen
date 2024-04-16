from typing import AsyncGenerator


from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from pydantic_settings import BaseSettings
class _PostgresConfig(BaseSettings):
    POSTGRES_SERVER: str = "localhost"





    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    class Config:
        env_file = ".env.docker"
        env_file_encoding = "utf-8"
        extra = "ignore"


_conf = _PostgresConfig()
_DATABASE_URL = (
    f"postgresql+asyncpg://{_conf.POSTGRES_USER}:{_conf.POSTGRES_PASSWORD}@"
    f"{_conf.POSTGRES_SERVER}:{_conf.POSTGRES_PORT}/{_conf.POSTGRES_DB}"
)

_engine = create_async_engine(_DATABASE_URL, poolclass=NullPool)
_async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_maker() as session:
        yield session
