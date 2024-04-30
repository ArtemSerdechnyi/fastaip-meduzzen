from uuid import UUID

from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import (
    Company,
    User,
    CompanyRequest,
    CompanyMember,
    CompanyRequestStatus,
    CompanyRole,
    UserRequest,
    UserRequestStatus,
)
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyListResponseScheme,
    CompanyUpdateRequestScheme,
    OwnerCompanyDetailResponseScheme,
    CompanyRequestDetailResponseScheme,
    CompanyMemberDetailResponseScheme,
    CompanyListMemberDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user import UserRequestDetailResponseScheme
from app.services.base import Service

from app.utils.exceptions.company import (
    CompanyNotFoundException,
    CompanyMemberNotFoundException,
    CompanyRequestNotFoundException,
)
from app.utils.exceptions.user import UserRequestNotFoundException
from app.utils.validators import CompanyValidator


class CompanyService(Service):
    validator = CompanyValidator()

    async def create_company(
        self,
        owner: User,
        scheme: CompanyCreateRequestScheme,
    ) -> CompanyDetailResponseScheme:
        query = (
            insert(Company)
            .values(
                name=scheme.name,
                description=scheme.description,
                visibility=scheme.visibility,
                owner_id=owner.user_id,
            )
            .returning(Company)
        )
        result = await self.session.execute(query)
        company = result.scalar()
        return CompanyDetailResponseScheme.from_orm(company)

    async def get_company_by_attributes(
        self,
        visibility=True,
        is_active=True,
        **kwargs,
    ) -> Company:
        kwargs.update(visibility=visibility)
        kwargs.update(is_active=is_active)
        query = select(Company).where(
            and_(
                *(
                    getattr(Company, attr) == value
                    for attr, value in kwargs.items()
                )
            )
        )
        result = await self.session.execute(query)
        if company := result.scalar():
            return company
        raise CompanyNotFoundException(**kwargs)

    async def update_user_self_company(
        self, company_id: UUID, user: User, scheme: CompanyUpdateRequestScheme
    ):
        query = (
            update(Company)
            .where(
                and_(
                    Company.company_id == company_id,
                    Company.owner_id == user.user_id,
                )
            )
            .values(scheme.dict(exclude_unset=True))
            .returning(Company)
        )
        result = await self.session.execute(query)
        if company := result.scalar():
            return company
        raise CompanyNotFoundException(
            company_id=company_id, owner_id=user.user_id
        )

    async def delete_self_company(self, company_id: UUID, user: User):
        query = (
            update(Company)
            .where(
                and_(
                    Company.company_id == company_id,
                    Company.owner_id == user.user_id,
                )
            )
            .values(is_active=False)
        )
        await self._add_query(query)

    async def get_all_companies(
        self, page, limit
    ) -> CompanyListResponseScheme:
        query = (
            select(Company)
            .where(and_(Company.visibility == True, Company.is_active == True))
            .order_by(Company.name)
        )
        query = self.apply_pagination(query=query, page=page, limit=limit)

        result = await self.session.execute(query)
        raw_companies = result.scalars().all()
        companies = [
            CompanyDetailResponseScheme.from_orm(company)
            for company in raw_companies
        ]
        return CompanyListResponseScheme(companies=companies)

    async def get_user_self_companies(
        self, page, limit, user: User
    ) -> CompanyListResponseScheme:
        query = (
            select(Company)
            .where(
                and_(
                    Company.owner_id == user.user_id, Company.is_active == True
                )
            )
            .order_by(Company.name)
        )
        query = self.apply_pagination(query=query, page=page, limit=limit)

        result = await self.session.execute(query)
        raw_companies = result.scalars().all()
        companies = [
            OwnerCompanyDetailResponseScheme.from_orm(company)
            for company in raw_companies
        ]
        return CompanyListResponseScheme(companies=companies)

    async def change_user_self_company_visibility(
        self, company_id: UUID, user: User
    ) -> OwnerCompanyDetailResponseScheme:
        query = (
            update(Company)
            .where(
                and_(
                    Company.company_id == company_id,
                    Company.owner_id == user.user_id,
                )
            )
            .values(visibility=~Company.visibility)
            .returning(Company)
        )
        result = await self.session.execute(query)
        if company := result.scalar():
            return OwnerCompanyDetailResponseScheme.from_orm(company)
        raise CompanyNotFoundException(
            company_id=company_id, owner_id=user.user_id
        )

    # company actions

    async def _update_company_request_status(
        self, request_id: UUID, status: CompanyRequestStatus
    ) -> CompanyRequest:
        query = (
            update(CompanyRequest)
            .where(
                and_(
                    CompanyRequest.request_id == request_id,
                    CompanyRequest.is_active == True,
                )
            )
            .values(status=status)
            .returning(CompanyRequest)
        )
        result = await self.session.execute(query)
        if request := result.scalar():
            return request
        raise CompanyRequestNotFoundException(request_id=request_id)

    async def _add_user_to_company(
        self, company_id: UUID, user_id: UUID
    ) -> CompanyMember:
        query = (
            insert(CompanyMember)
            .values(
                company_id=company_id,
                user_id=user_id,
            )
            .returning(CompanyMember)
        )
        result = await self.session.execute(query)
        company_member = result.scalar()
        return company_member

    async def _remove_user_from_company(
        self, company_id: UUID, user_id: UUID
    ) -> CompanyMember:
        query = (
            update(CompanyMember)
            .where(
                and_(
                    CompanyMember.company_id == company_id,
                    CompanyMember.user_id == user_id,
                    CompanyMember.is_active == True,
                )
            )
            .values(is_active=False)
            .returning(CompanyMember)
        )
        result = await self.session.execute(query)
        if company_member := result.scalar():
            return company_member
        raise CompanyMemberNotFoundException(
            company_id=company_id, user_id=user_id
        )

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
        company_member = await self._remove_user_from_company(
            company_id=company_id, user_id=user_id
        )
        return CompanyMemberDetailResponseScheme.from_orm(company_member)

    async def get_company_members(
        self,
        company_id: UUID,
        page: int,
        limit: int,
        role: str = None,
    ) -> CompanyListMemberDetailResponseScheme:
        query = (
            select(CompanyMember)
            .join(User)
            .where(
                and_(
                    CompanyMember.company_id == company_id,
                    CompanyMember.is_active == True,
                    User.is_active == True,
                )
            )
            .options(selectinload(CompanyMember.user))
        )
        query = self.apply_pagination(query=query, page=page, limit=limit)

        if role is not None:
            query = query.where(CompanyMember.role == role)

        result = await self.session.execute(query)
        raw_members = result.scalars().all()
        members = [
            CompanyMemberDetailResponseScheme.from_orm(member)
            for member in raw_members
        ]
        return CompanyListMemberDetailResponseScheme(members=members)

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

        await self._add_user_to_company(
            company_id=user_request.company_id, user_id=user_request.user_id
        )

        # user service logic
        from app.services.user import UserService

        accept_status = CompanyRequestStatus.accepted.value
        us = UserService(session=self.session)
        user_request = await us._update_user_request_status(
            request_id=request_id, status=accept_status
        )
        return UserRequestDetailResponseScheme.from_orm(user_request)

    @validator.validate_user_request_by_request_id
    @validator.validate_company_owner_by_user_request_id
    async def deny_user_request(
        self, request_id: UUID, owner: User
    ) -> UserRequestDetailResponseScheme:
        from app.services.user import UserService

        deny_status = CompanyRequestStatus.denied.value
        us = UserService(session=self.session)
        user_request = await us._update_user_request_status(
            request_id=request_id, status=deny_status
        )
        return UserRequestDetailResponseScheme.from_orm(user_request)
