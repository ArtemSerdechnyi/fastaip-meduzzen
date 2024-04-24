from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_async_session

from .conftest import override_get_async_session


async def test_postgres_db_connection(session=get_async_session):
    async for session in session():
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1;"))
        value = result.scalar_one()
        assert value == 1


async def test_check_user_table_exist(session=get_async_session):
    async for session in session():
        assert isinstance(session, AsyncSession)
        query = text(
            "SELECT EXISTS (SELECT FROM pg_tables "
            "WHERE schemaname = 'public' "
            "AND tablename  = 'users');"
        )
        result = await session.execute(query)
        exists = result.scalar_one()
        assert exists is True


async def test_postgres_test_db_connection():
    await test_postgres_db_connection(override_get_async_session)


async def test_check_user_table_test_db_exist():
    await test_check_user_table_exist(override_get_async_session)
