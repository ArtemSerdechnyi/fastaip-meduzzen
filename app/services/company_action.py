from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, insert, select, update
from sqlalchemy.orm import selectinload, joinedload

from app.db.models import (
    CompanyMember,
    CompanyRequest,
    CompanyRequestStatus,
    User,
    UserRequest,
    UserRequestStatus,
    Company,
)
from app.schemas.company_member import (
    CompanyListMemberDetailResponseScheme,
    CompanyMemberDetailResponseScheme, NestedCompanyMemberDetailResponseScheme,
    ListNestedCompanyMemberDetailResponseScheme,
)
from app.schemas.company_request import (
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user_request import UserRequestDetailResponseScheme
from app.services.base import Service
from app.services.comapny_member import CompanyMemberService
from app.services.user_request import UserRequestService
from app.utils.exceptions.company import (
    CompanyRequestNotFoundException,
)
from app.utils.exceptions.user import UserRequestNotFoundException
from app.utils.validators import CompanyValidator


class CompanyActionService(Service):
    validator: CompanyValidator = CompanyValidator()

    @validator.validate_check_user_not_in_company
    @validator.validate_company_request_non_existing
    @validator.validate_user_exist_and_active_by_user_id
    @validator.validate_company_id_by_owner
    async def create_company_user_invite(
        self, user_id: UUID, company_id: UUID, owner: User
    ) -> CompanyRequestDetailResponseScheme:
        query = (
            insert(CompanyRequest)
            .values(
                user_id=user_id,
                company_id=company_id,
            )
            .returning(CompanyRequest)
        )
        result = await self.session.execute(query)
        company_request = result.scalar()
        return CompanyRequestDetailResponseScheme.from_orm(company_request)

    @validator.validate_company_owner_by_company_request_id
    async def remove_user_invite(self, request_id: UUID, owner: User):
        query = (
            update(CompanyRequest)
            .where(
                and_(
                    CompanyRequest.request_id == request_id,
                    CompanyRequest.is_active == True,
                )
            )
            .values(is_active=False)
            .returning(CompanyRequest)
        )
        result = await self.session.execute(query)
        if company_request := result.scalar():
            return CompanyRequestDetailResponseScheme.from_orm(company_request)
        raise CompanyRequestNotFoundException(request_id=request_id)

    @validator.validate_user_exist_and_active_by_user_id
    @validator.validate_company_id_by_owner
    async def remove_user_from_company(
        self, user_id: UUID, company_id: UUID, owner: User
    ) -> CompanyMemberDetailResponseScheme:
        cms = CompanyMemberService(session=self.session)
        company_member = await cms._remove_user_from_company(
            company_id=company_id, user_id=user_id
        )
        return CompanyMemberDetailResponseScheme.from_orm(company_member)

    async def get_company_members(
        self,
        company_id: UUID,
        page: int,
        limit: int,
        role: str = None,
    ) -> ListNestedCompanyMemberDetailResponseScheme:

        query = (
            select(CompanyMember, Company, User)
            .join(
                User, CompanyMember.user_id == User.user_id
            )
            .join(
                Company, CompanyMember.company_id == Company.company_id
            )
            .options(
                joinedload(
                    CompanyMember.user
                ),
                joinedload(
                    CompanyMember.company
                ),
            )
            .where(
                and_(
                    CompanyMember.company_id == company_id,
                    CompanyMember.is_active == True,
                    User.is_active == True,
                )
            )
        )
        query = self.apply_pagination(query=query, page=page, limit=limit)

        if role is not None:
            query = query.where(CompanyMember.role == role)

        result = await self.session.execute(query)
        raw_members = result.scalars().all()
        members = [
            NestedCompanyMemberDetailResponseScheme(email=m.user.email, name=m.company.name, role=m.role)
            for m in raw_members
        ]
        return ListNestedCompanyMemberDetailResponseScheme(members=members)

    @validator.validate_company_id_by_owner
    async def get_company_users_request(
        self,
        company_id: UUID,
        owner: User,
        page: int,
        limit: int,
        status: str = None,
    ) -> CompanyRequestListDetailResponseScheme:
        query = (
            select(CompanyRequest)
            .where(
                and_(
                    CompanyRequest.company_id == company_id,
                    CompanyRequest.is_active == True,
                )
            )
            .options(selectinload(CompanyRequest.user))
        )
        query = self.apply_pagination(query=query, page=page, limit=limit)

        if status is not None:
            query = query.where(CompanyRequest.status == status)

        result = await self.session.execute(query)
        raw_requests = result.scalars().all()

        requests = [
            CompanyRequestDetailResponseScheme.from_orm(request)
            for request in raw_requests
        ]
        return CompanyRequestListDetailResponseScheme(requests=requests)

    @validator.validate_user_request_by_request_id
    @validator.validate_company_owner_by_user_request_id
    async def confirm_user_request(
        self, request_id: UUID, owner: User
    ) -> UserRequestDetailResponseScheme:
        pending_status = UserRequestStatus.pending.value
        query = select(UserRequest).where(
            and_(
                UserRequest.request_id == request_id,
                UserRequest.status == pending_status,
                UserRequest.is_active == True,
            )
        )
        result = await self.session.execute(query)
        user_request = result.scalar()
        if not user_request:
            raise UserRequestNotFoundException(request_id=request_id)

        cms = CompanyMemberService(session=self.session)
        await cms._add_user_to_company(
            company_id=user_request.company_id, user_id=user_request.user_id
        )

        accept_status = CompanyRequestStatus.accepted.value
        urs = UserRequestService(session=self.session)
        user_request = await urs._update_user_request_status(
            request_id=request_id, status=accept_status
        )
        return UserRequestDetailResponseScheme.from_orm(user_request)

    @validator.validate_user_request_by_request_id
    @validator.validate_company_owner_by_user_request_id
    async def deny_user_request(
        self, request_id: UUID, owner: User
    ) -> UserRequestDetailResponseScheme:
        deny_status = CompanyRequestStatus.denied.value
        urs = UserRequestService(session=self.session)
        user_request = await urs._update_user_request_status(
            request_id=request_id, status=deny_status
        )
        return UserRequestDetailResponseScheme.from_orm(user_request)
