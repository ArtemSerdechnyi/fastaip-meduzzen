from abc import ABC
from functools import wraps
from uuid import UUID

from sqlalchemy import and_, exists, not_, select, Select, BinaryExpression

from app.db.models import (
    Company,
    CompanyMember,
    CompanyRequest,
    CompanyRequestStatus,
    User,
    UserRequest,
)


class BaseValidator(ABC):
    @staticmethod
    def _build_where_exist_select_query(*args: BinaryExpression) -> Select:
        return select(exists().where(and_(*args)))

    @staticmethod
    def _build_where_not_exist_select_query(*args: BinaryExpression) -> Select:
        return select(~exists().where(and_(*args)))


class UserValidator(BaseValidator):
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

    def validate_request_id_belongs_to_user(self, func):
        """
        Check request_id belongs to user.

        Depends: request_id, user
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user: User = kwargs["user"]

            query = self._build_where_exist_select_query(
                UserRequest.company_id == company_id,
                UserRequest.user_id == user.user_id,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. No request found or request not belong to user."
                )
            return await func(self_service, **kwargs)

        return wrapper

    def validate_user_leave_from_company(self, func):
        """
        Validate user is active member of the specified company.

        Depends: company_id, user
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user: User = kwargs["user"]

            check_user_in_company = self._build_where_exist_select_query(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == User.user_id,
                CompanyMember.is_active == True,
            )

            query = self._build_where_exist_select_query(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == User.user_id,
                User.user_id == user.user_id,
                User.is_active == True,
                check_user_in_company,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error.")

            return await func(self_service, **kwargs)

        return wrapper

    def validate_company_invitation(self, func):
        """
        Validate the company invitation  for a user.
        Check user and company is exist.
        Check user not a member of the company.

        Depends: request_id, user
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            request_id: UUID = kwargs["request_id"]
            user: User = kwargs["user"]

            check_user_in_company = self._build_where_exist_select_query(
                CompanyMember.company_id == CompanyRequest.company_id,
                CompanyMember.user_id == CompanyRequest.user_id,
                CompanyMember.is_active == True,
            )

            query = self._build_where_exist_select_query(
                CompanyRequest.request_id == request_id,
                CompanyRequest.user_id == user.user_id,
                CompanyRequest.status == CompanyRequestStatus.pending.value,
                CompanyRequest.is_active == True,
                Company.is_active == True,
                Company.owner_id != CompanyRequest.user_id,
                User.is_active == True,
                not_(check_user_in_company),
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error.")

            return await func(self_service, **kwargs)

        return wrapper

    def validate_user_request_non_existing(self, func):
        """
        Validate that a user request does not already exist base on attributes.

        Depends: user, company_id
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user: User = kwargs["user"]
            company_id: UUID = kwargs["company_id"]
            user_id: UUID = user.user_id

            pending_status = CompanyRequestStatus.pending.value
            query = self._build_where_not_exist_select_query(
                UserRequest.user_id == user_id,
                UserRequest.company_id == company_id,
                UserRequest.status == pending_status,
                UserRequest.is_active == True,
            )
            print(query)

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User request is exist."
                )

            return await func(self_service, **kwargs)

        return wrapper

    def validate_check_user_not_in_company(self, func):
        """
        Validate that the user is not a member of the company.

        Depends: company_id, user
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user: User = kwargs["user"]

            query = self._build_where_not_exist_select_query(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user.user_id,
                CompanyMember.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User is company member."
                )
            return await func(self_service, **kwargs)

        return wrapper


class CompanyValidator(BaseValidator):
    def validate_company_id_by_owner(self, func):
        """
        Validate that the user is the owner of the company.

        Depends: company_id, owner
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            owner: User = kwargs["owner"]

            query = self._build_where_exist_select_query(
                Company.company_id == company_id,
                Company.owner_id == owner.user_id,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User does not own this "
                    "company or company does not exist"
                )
            return await func(self_service, **kwargs)

        return wrapper

    def validate_company_owner_by_company_request_id(self, func):
        """
        Validate that the user is the owner of the company base on given company request.

        Depends: request_id, owner
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_request_id: UUID = kwargs["request_id"]
            owner: User = kwargs["owner"]

            query = self._build_where_exist_select_query(
                CompanyRequest.request_id == company_request_id,
                Company.company_id == CompanyRequest.company_id,
                Company.owner_id == owner.user_id,
                Company.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. The invitation does not belong "
                    "to any company owned by the user or does not exist."
                )

            return await func(self_service, **kwargs)

        return wrapper

    def validate_company_owner_by_user_request_id(self, func):
        """
        Validate that the user is the owner of the company base on given user request.

        Depends: request_id, owner
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_request_id: UUID = kwargs["request_id"]
            owner: User = kwargs["owner"]

            query = self._build_where_exist_select_query(
                UserRequest.request_id == user_request_id,
                Company.company_id == UserRequest.company_id,
                Company.owner_id == owner.user_id,
                Company.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. The invitation does not belong "
                    "to any company owned by the user or does not exist."
                )

            return await func(self_service, **kwargs)

        return wrapper

    def validate_user_exist_and_active_by_user_id(self, func):
        """
        Validate that the user exists and is active based on user_id.

        Depends: user_id
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_id: UUID = kwargs["user_id"]

            query = self._build_where_exist_select_query(
                User.user_id == user_id,
                User.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User does not exist or not active."
                )

            return await func(self_service, **kwargs)

        return wrapper

    def validate_user_request_by_request_id(self, func):
        """
        Validate the user request based on the provided request_id.

        Depends: request_id
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_request_id: UUID = kwargs["request_id"]

            query = self._build_where_exist_select_query(
                UserRequest.request_id == user_request_id,
                UserRequest.is_active == True,
                User.user_id == UserRequest.user_id,
                User.is_active == True,
                Company.company_id == UserRequest.company_id,
                Company.is_active == True,
                Company.owner_id != UserRequest.user_id,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User request is not valid."
                )

            return await func(self_service, **kwargs)

        return wrapper

    def validate_company_request_non_existing(self, func):
        """
        Validate company request does not already exist base on user_id and company_id.

        Depends: user_id, company_id
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_id: UUID = kwargs["user_id"]
            company_id: UUID = kwargs["company_id"]

            pending_status = CompanyRequestStatus.pending.value

            query = self._build_where_not_exist_select_query(
                CompanyRequest.user_id == user_id,
                CompanyRequest.company_id == company_id,
                CompanyRequest.status == pending_status,
                CompanyRequest.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. Company request is exist."
                )

            return await func(self_service, **kwargs)

        return wrapper

    def validate_check_user_not_in_company(self, func):
        """
        Validate that the user is not a member of the given company.

        Depends: company_id, user_id
        """

        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user_id: UUID = kwargs["user_id"]

            query = self._build_where_not_exist_select_query(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
                CompanyMember.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User is company member."
                )
            return await func(self_service, **kwargs)

        return wrapper
