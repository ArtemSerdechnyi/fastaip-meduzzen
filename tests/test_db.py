import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_async_session


@pytest.mark.anyio
async def test_postgres_db_connection():
    async for session in get_async_session():
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1;"))
        value = result.scalar_one()
        assert value == 1


@pytest.mark.anyio
async def test_check_user_table_exist():
    async for session in get_async_session():
        assert isinstance(session, AsyncSession)
        query = text(
            "SELECT EXISTS (SELECT FROM pg_tables "
            "WHERE schemaname = 'public' "
            "AND tablename  = 'users');"
        )
        result = await session.execute(query)
        exists = result.scalar_one()
        assert exists is True
