from uuid import UUID

from sqlalchemy import select, update, and_, insert, not_

from app.db.models import Company, User
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyUpdateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyListResponseScheme,
    UserCompanyDetailResponseScheme,
)
from app.services.base import Service
from app.utils.exceptions.company import CompanyNotFoundException


class CompanyService(Service):
    async def create_company(
        self,
        owner: User,
        scheme: CompanyCreateRequestScheme,
    ) -> UUID:
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
        return company.company_id

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
        if page < 1:
            raise AttributeError("Page must be >= 1")
        elif limit < 1:
            raise AttributeError("Limit must be >= 1")

        query = (
            select(Company)
            .where(and_(Company.visibility == True, Company.is_active == True))
            .limit(limit)
            .offset((page - 1) * limit)
            .order_by(Company.name)
        )
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
        if page < 1:
            raise AttributeError("Page must be >= 1")
        elif limit < 1:
            raise AttributeError("Limit must be >= 1")

        query = (
            select(Company)
            .where(
                and_(
                    Company.owner_id == user.user_id, Company.is_active == True
                )
            )
            .limit(limit)
            .offset((page - 1) * limit)
            .order_by(Company.name)
        )
        result = await self.session.execute(query)
        raw_companies = result.scalars().all()
        companies = [
            UserCompanyDetailResponseScheme.from_orm(company)
            for company in raw_companies
        ]
        return CompanyListResponseScheme(companies=companies)

    async def change_user_self_company_visibility(
        self, company_id: UUID, user: User
    ) -> UserCompanyDetailResponseScheme:
        query = select(Company).where(
            and_(
                Company.company_id == company_id,
                Company.owner_id == user.user_id,
            )
        )
        result = await self.session.execute(query)
        if company := result.scalar():
            if company.visibility is True:
                company.visibility = False
            else:
                company.visibility = True
            query = (
                update(Company)
                .where(
                    and_(
                        Company.company_id == company_id,
                        Company.owner_id == user.user_id,
                    )
                )
                .values(visibility=company.visibility)
                .returning(Company)
            )
            result = await self.session.execute(query)
            if company := result.scalar():
                return UserCompanyDetailResponseScheme.from_orm(company)

        raise CompanyNotFoundException(
            company_id=company_id, owner_id=user.user_id
        )
