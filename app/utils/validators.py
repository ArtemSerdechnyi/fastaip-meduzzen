from abc import ABC
from functools import wraps
from uuid import UUID

from sqlalchemy import select, exists, and_, not_, Select

from app.db.models import (
    Company,
    CompanyRequest,
    User,
    UserRequest,
    CompanyMember,
    CompanyRequestStatus,
)


class BaseValidator(ABC):
    @staticmethod
    def _get_where_exist_query(*args):
        return not_(
            exists().where(
                and_(
                    *args
                )
            )
        )


class UserValidator(BaseValidator):

    def validate_exist_company_is_active(self, func):
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]

            query = select(
                exists().where(
                    and_(
                        Company.company_id == company_id,
                        Company.is_active == True,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user: User = kwargs["user"]

            query = select(
                exists().where(
                    and_(
                        UserRequest.company_id == company_id,
                        UserRequest.user_id == user.user_id,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user: User = kwargs["user"]

            check_user_in_company = select(
                exists().where(
                    and_(
                        CompanyMember.company_id == company_id,
                        CompanyMember.user_id == User.user_id,
                        CompanyMember.is_active == True,
                    )
                )
            )

            query = select(
                exists().where(
                    and_(
                        CompanyMember.company_id == company_id,
                        CompanyMember.user_id == User.user_id,
                        User.user_id == user.user_id,
                        User.is_active == True,
                        check_user_in_company,
                    )
                )
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error.")

            return await func(self_service, **kwargs)

        return wrapper

    def validate_company_invitation(self, func):
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            request_id: UUID = kwargs["request_id"]
            user: User = kwargs["user"]

            check_user_in_company = select(
                exists().where(
                    and_(
                        CompanyMember.company_id == CompanyRequest.company_id,
                        CompanyMember.user_id == CompanyRequest.user_id,
                        CompanyMember.is_active == True,
                    )
                )
            )

            query = select(
                exists().where(
                    and_(
                        CompanyRequest.request_id == request_id,
                        CompanyRequest.user_id == user.user_id,
                        CompanyRequest.status
                        == CompanyRequestStatus.pending.value,
                        CompanyRequest.is_active == True,
                        Company.is_active == True,
                        Company.owner_id != CompanyRequest.user_id,
                        User.is_active == True,
                        not_(check_user_in_company),
                    )
                )
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error.")

            return await func(self_service, **kwargs)

        return wrapper

    def validate_user_request_non_existing(self, func):
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user: User = kwargs["user"]
            company_id: UUID = kwargs["company_id"]
            user_id: UUID = user.user_id

            pending_status = CompanyRequestStatus.pending.value

            query = select(
                ~exists().where(
                    and_(
                        UserRequest.user_id == user_id,
                        UserRequest.company_id == company_id,
                        UserRequest.status == pending_status,
                        UserRequest.is_active == True,
                    )
                )
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User request is exist."
                )

            return await func(self_service, **kwargs)

        return wrapper

    def validate_check_user_not_in_company(self, func):
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user: User = kwargs["user"]

            query = select(
                ~exists().where(
                    and_(
                        CompanyMember.company_id == company_id,
                        CompanyMember.user_id == user.user_id,
                        CompanyMember.is_active == True,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            owner: User = kwargs["owner"]

            query = select(
                exists().where(
                    and_(
                        Company.company_id == company_id,
                        Company.owner_id == owner.user_id,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_request_id: UUID = kwargs["request_id"]
            owner: User = kwargs["owner"]

            query = select(
                exists().where(
                    and_(
                        CompanyRequest.request_id == company_request_id,
                        Company.company_id == CompanyRequest.company_id,
                        Company.owner_id == owner.user_id,
                        Company.is_active == True,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_request_id: UUID = kwargs["request_id"]
            owner: User = kwargs["owner"]

            query = select(
                exists().where(
                    and_(
                        UserRequest.request_id == user_request_id,
                        Company.company_id == UserRequest.company_id,
                        Company.owner_id == owner.user_id,
                        Company.is_active == True,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_id: UUID = kwargs["user_id"]

            query = select(
                exists().where(
                    and_(
                        User.user_id == user_id,
                        User.is_active == True,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_request_id: UUID = kwargs["request_id"]

            query = select(
                exists().where(
                    and_(
                        UserRequest.request_id == user_request_id,
                        UserRequest.is_active == True,
                        User.user_id == UserRequest.user_id,
                        User.is_active == True,
                        Company.company_id == UserRequest.company_id,
                        Company.is_active == True,
                        Company.owner_id != UserRequest.user_id,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            user_id: UUID = kwargs["user_id"]
            company_id: UUID = kwargs["company_id"]

            pending_status = CompanyRequestStatus.pending.value

            query = select(
                ~exists().where(
                    and_(
                        CompanyRequest.user_id == user_id,
                        CompanyRequest.company_id == company_id,
                        CompanyRequest.status == pending_status,
                        CompanyRequest.is_active == True,
                    )
                )
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
        @wraps(func)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user_id: UUID = kwargs["user_id"]
            query = select(
                ~exists().where(
                    and_(
                        CompanyMember.company_id == company_id,
                        CompanyMember.user_id == user_id,
                        CompanyMember.is_active == True,
                    )
                )
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User is company member."
                )
            return await func(self_service, **kwargs)

        return wrapper
