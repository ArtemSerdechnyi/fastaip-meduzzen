from typing import Type

from sqlalchemy import select, BinaryExpression
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base


class Paginator[Model: Type[Base]]:
    def __init__(
        self,
        model: Model,
        session: AsyncSession,
        filter_condition: list[BinaryExpression] | None = None,
    ):
        self._model = model
        self._session = session
        self._filter_condition = filter_condition

    async def paginate(self, page: int, limit: int) -> list[Model]:
        if page < 1:
            raise AttributeError(f"Page must be >= 1, page: {page}")
        elif limit < 1:
            raise AttributeError(f"Limit must be >= 1, limit: {limit}")

        skip = page - 1 if page == 1 else (page - 1) * limit
        query = select(self._model).limit(limit).offset(skip)
        if self._filter_condition:
            query = query.where(*(self._filter_condition))
        result = await self._session.execute(query)
        entities = result.scalars().all()
        return entities
