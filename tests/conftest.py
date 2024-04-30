import asyncio
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import postgres_config_test as conf
from app.db.models import Base
from app.db.postgres import get_async_session
from app.main import app as _app
from app.services.company import CompanyService
from app.services.user import UserService

DATABASE_URL_TEST = (
    f"postgresql+asyncpg://{conf.POSTGRES_USER_TEST}:{conf.POSTGRES_PASSWORD_TEST}@"
    f"{conf.POSTGRES_SERVER_TEST}:{conf.POSTGRES_PORT_TEST}/{conf.POSTGRES_DB_TEST}"
)
engine = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
metadata = Base.metadata


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


_app.dependency_overrides[get_async_session] = override_get_async_session


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def app() -> FastAPI:
    return _app


@pytest.fixture(scope="module")
def event_loop(request):
    """
    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def ac(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def user_service(session: AsyncSession) -> UserService:
    async with UserService(session=session) as service:
        yield service


@pytest.fixture(scope="function")
async def company_service(session: AsyncSession) -> CompanyService:
    async with CompanyService(session=session) as service:
        yield service


@pytest.fixture(autouse=True, scope="session")
# @pytest.fixture(autouse=True, scope="module")
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
