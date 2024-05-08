from abc import ABC
from functools import wraps
from uuid import UUID

from sqlalchemy import ClauseElement, Select, and_, exists, select
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from app.db.models import Company


class BaseValidator(ABC):
    @staticmethod
    def _build_where_exist_select_query(
        *args: _ColumnExpressionArgument[bool],
    ) -> Select:
        return select(exists().where(and_(*args)))

    @staticmethod
    def _build_where_not_exist_select_query(
        *args: _ColumnExpressionArgument[bool],
    ) -> Select:
        return select(~exists().where(and_(*args)))

    def validate_exist_company_is_active(self, func):
        """
        Check company is exist and active.

        Depends: company_id
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]

            query = self._build_where_exist_select_query(
                Company.company_id == company_id,
                Company.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. Company is not exist."
                )
            return await func(self_service, **kwargs)

        return wrapper
