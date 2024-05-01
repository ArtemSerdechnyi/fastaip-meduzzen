from logging import getLogger
from typing import NoReturn
from uuid import UUID

from passlib.context import CryptContext
from pydantic import SecretStr
from sqlalchemy import and_, insert, select, update

from app.db.models import (
    CompanyRequest,
    CompanyRequestStatus,
    User,
    UserRequest,
)
from app.schemas.company import (
    CompanyMemberDetailResponseScheme,
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user import (
    UserDetailResponseScheme,
    UserRequestDetailResponseScheme,
    UserRequestListDetailResponseScheme,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
)
from app.services.base import Service
from app.services.comapny_member import CompanyMemberService
from app.services.company_request import CompanyRequestService
from app.utils.exceptions.company import CompanyRequestNotFoundException
from app.utils.exceptions.user import (
    PasswordVerificationError,
    UserNotFoundException,
)
from app.utils.generics import Password
from app.utils.validators import UserValidator


class UserActionService(Service):
    validator = UserValidator()

    @validator.validate_check_user_not_in_company
    @validator.validate_user_request_non_existing
    @validator.validate_exist_company_is_active
    async def create_user_request(
        self, company_id: UUID, user: User
    ) -> UserRequestDetailResponseScheme:
        query = (
            insert(UserRequest)
            .values(company_id=company_id, user_id=user.user_id)
            .returning(UserRequest)
        )

        result = await self.session.execute(query)
        request = result.scalar()
        return UserRequestDetailResponseScheme.from_orm(request)

    async def cancel_user_request(self, request_id: UUID, user: User):
        query = (
            update(UserRequest)
            .where(
                and_(
                    UserRequest.request_id == request_id,
                    UserRequest.user_id == user.user_id,
                    UserRequest.is_active == True,
                )
            )
            .values(is_active=False)
            .returning(UserRequest)
        )
        result = await self.session.execute(query)
        request = result.scalar()
        return UserRequestDetailResponseScheme.from_orm(request)

    async def list_user_requests(self, user: User, page: int, limit: int):
        query = select(UserRequest).where(UserRequest.user_id == user.user_id)
        query = self.apply_pagination(query=query, page=page, limit=limit)

        result = await self.session.execute(query)
        raw_requests = result.scalars().all()
        requests = [
            UserRequestDetailResponseScheme.from_orm(request)
            for request in raw_requests
        ]
        return UserRequestListDetailResponseScheme(requests=requests)

    async def list_user_invitations(self, user: User, page: int, limit: int):
        query = select(CompanyRequest).where(
            and_(
                CompanyRequest.user_id == user.user_id,
                CompanyRequest.status == CompanyRequestStatus.pending.value,
                CompanyRequest.is_active == True,
            )
        )
        query = self.apply_pagination(query, page, limit)
        result = await self.session.execute(query)
        raw_requests = result.scalars().all()
        requests = [
            CompanyRequestDetailResponseScheme.from_orm(request)
            for request in raw_requests
        ]
        return CompanyRequestListDetailResponseScheme(requests=requests)

    @validator.validate_company_invitation
    async def accept_invitation(
        self, request_id: UUID, user: User
    ) -> CompanyRequestDetailResponseScheme:
        pending_status = CompanyRequestStatus.pending.value

        query = select(CompanyRequest).where(
            and_(
                CompanyRequest.request_id == request_id,
                CompanyRequest.user_id == user.user_id,
                CompanyRequest.status == pending_status,
                CompanyRequest.is_active == True,
            )
        )

        result = await self.session.execute(query)
        company_request = result.scalar()
        if not company_request:
            raise CompanyRequestNotFoundException(
                request_id=request_id, user_id=user.user_id
            )

        cms = CompanyMemberService(session=self.session)

        # add user to company
        await cms._add_user_to_company(
            company_id=company_request.company_id,
            user_id=user.user_id,
        )

        # update company request status
        crs = CompanyRequestService(session=self.session)
        accept_status = CompanyRequestStatus.accepted.value
        request = await crs._update_company_request_status(
            request_id=request_id,
            status=accept_status,
        )
        return CompanyRequestDetailResponseScheme.from_orm(request)

    @validator.validate_company_invitation
    async def reject_invitation(self, request_id: UUID, user: User):
        status = CompanyRequestStatus.denied.value
        crs = CompanyRequestService(session=self.session)
        request = await crs._update_company_request_status(
            request_id=request_id,
            status=status,
        )
        return CompanyRequestDetailResponseScheme.from_orm(request)

    @validator.validate_user_leave_from_company
    async def leave_company(self, company_id: UUID, user: User):
        cms = CompanyMemberService(session=self.session)
        member = await cms._remove_user_from_company(
            company_id=company_id,
            user_id=user.user_id,
        )
        return CompanyMemberDetailResponseScheme.from_orm(member)
