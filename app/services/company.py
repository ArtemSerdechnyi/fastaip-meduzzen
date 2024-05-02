from uuid import UUID


from app.db.models import (
    User,
)
from app.repositories.company import CompanyRepository
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyListResponseScheme,
    CompanyUpdateRequestScheme,
    CompanyCreateScheme,
)
from app.services.base import Service


class CompanyService(Service):
    def __init__(self, session):
        self.company_repository = CompanyRepository(session)
        super().__init__(session)

    async def create_company(
        self,
        owner: User,
        scheme: CompanyCreateRequestScheme,
    ) -> CompanyDetailResponseScheme:
        dump = scheme.model_dump(exclude_unset=True)
        company_create_scheme = CompanyCreateScheme(
            owner_id=owner.user_id, **dump
        )
        company = self.company_repository.create_company(company_create_scheme)
        return CompanyDetailResponseScheme.from_orm(company)

    async def update_user_self_company(
        self, company_id: UUID, user: User, scheme: CompanyUpdateRequestScheme
    ):
        company = await self.company_repository.update_company(
            scheme=scheme, company_id=company_id, owner_id=user.user_id
        )
        return CompanyDetailResponseScheme.from_orm(company)

    async def delete_self_company(self, company_id: UUID, user: User):
        scheme = CompanyUpdateRequestScheme(is_active=False)
        company = await self.company_repository.update_company(
            scheme=scheme, company_id=company_id, owner_id=user.user_id
        )
        return CompanyDetailResponseScheme.from_orm(company)

    async def get_all_companies(
        self, page: int, limit: int
    ) -> CompanyListResponseScheme:
        raw_companies = (
            await self.company_repository.get_companies_list_by_attributes(
                page=page, limit=limit
            )
        )
        companies = [
            CompanyDetailResponseScheme.from_orm(company)
            for company in raw_companies
        ]
        return CompanyListResponseScheme(companies=companies)

    async def get_user_self_companies(
        self, page, limit, user: User
    ) -> CompanyListResponseScheme:
        raw_companies = (
            await self.company_repository.get_companies_list_by_attributes(
                page=page, limit=limit, owner_id=user.user_id, visibility=None
            )
        )
        companies = [
            CompanyDetailResponseScheme.from_orm(company)
            for company in raw_companies
        ]
        return CompanyListResponseScheme(companies=companies)

    async def change_user_self_company_visibility(
        self, company_id: UUID, user: User
    ) -> CompanyDetailResponseScheme:
        scheme = CompanyUpdateRequestScheme(visibility=False)
        company = await self.company_repository.update_company(
            scheme=scheme, company_id=company_id, owner_id=user.user_id
        )
        return CompanyDetailResponseScheme.from_orm(company)

    async def get_company_by_id(
        self, company_id: UUID
    ) -> CompanyDetailResponseScheme:
        company = await self.company_repository.get_company_by_attributes(
            company_id=company_id
        )
        return CompanyDetailResponseScheme.from_orm(company)
