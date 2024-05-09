from abc import ABC
from datetime import datetime
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

    def validate_from_date_and_to_date(self, func):
        """
        Validate that from_date is before to_date.

        Depends: from_date, to_date
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            from_date: datetime = kwargs["from_date"]
            to_date: datetime = kwargs["to_date"]

            exist = from_date < to_date

            if not exist:
                error_message = "Validation error. Invalid date range: from_date must be before to_date."
                raise PermissionError(error_message)
            return await func(self_service, **kwargs)

        return wrapper
