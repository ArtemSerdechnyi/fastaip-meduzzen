from uuid import UUID

from sqlalchemy import and_, insert, select, update
from sqlalchemy.orm import selectinload

from app.db.models import (
    Company,
    CompanyMember,
    CompanyRequest,
    CompanyRequestStatus,
    User,
    UserRequest,
    UserRequestStatus,
)
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyListMemberDetailResponseScheme,
    CompanyListResponseScheme,
    CompanyMemberDetailResponseScheme,
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
    CompanyUpdateRequestScheme,
    OwnerCompanyDetailResponseScheme,
)
from app.schemas.user import UserRequestDetailResponseScheme
from app.services.base import Service
from app.services.comapny_member import CompanyMemberService
from app.services.user_request import UserRequestService
from app.utils.exceptions.company import (
    CompanyMemberNotFoundException,
    CompanyNotFoundException,
    CompanyRequestNotFoundException,
)
from app.utils.exceptions.user import UserRequestNotFoundException
from app.utils.validators import CompanyValidator


class CompanyService(Service):

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
