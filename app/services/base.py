from abc import ABC
from logging import getLogger

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_redis import get_redis_client
from app.utils.validators import BaseValidator

logger = getLogger(__name__)


class Service(ABC):
    validator: BaseValidator  # service validator

    def __init__(self, session: AsyncSession):
        self.session = session
        # self.redis = get_redis_client()
        self._queries = []

    @property
    def queries(self):
        return self._queries

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Exception | None, exc_val, exc_tb):
        if exc_type is None:
            # todo add SQLAlchemy error interception
            if self._queries is not None:
                for query in self.queries:
                    await self.session.execute(query)
            await self.session.commit()
        else:
            await self.session.rollback()
            logger.error(f"Error occurred {exc_type}, {exc_val}, {exc_tb}")
            raise exc_type
        return False  # mb True?

    async def _add_query(self, query):
        self._queries.append(query)
