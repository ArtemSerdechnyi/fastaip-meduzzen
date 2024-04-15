import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import get_async_session


@pytest.mark.anyio
async def test_postgres_db_connection():
    async for session in get_async_session():
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1;"))
        value = result.scalar_one()
        assert value == 1
