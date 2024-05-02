from uuid import UUID

from sqlalchemy import select, and_, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Company
from app.schemas.company import (
    CompanyCreateScheme,
    CompanyUpdateRequestScheme,
)
from app.utils.exceptions.company import CompanyNotFoundException
from app.utils.paginator import Paginator


class CompanyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_company_by_attributes(
        self,
        visibility: bool | None = True,
        is_active: bool = True,
        **kwargs,
    ) -> Company:
        kwargs.update(is_active=is_active)
        if visibility is not None:
            kwargs.update(visibility=visibility)

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

    async def get_companies_list_by_attributes(
        self,
        page: int,
        limit: int,
        visibility: bool | None = True,
        is_active: bool = True,
        **kwargs,
    ) -> list[Company]:
        kwargs.update(is_active=is_active)
        if visibility is not None:
            kwargs.update(visibility=visibility)

        filter_condition = [
            getattr(Company, attr) == value for attr, value in kwargs.items()
        ]
        paginator = Paginator(
            model=Company,
            session=self.session,
            filter_condition=filter_condition,
        )
        companies = await paginator.paginate(page=page, limit=limit)
        return companies

    async def create_company(
        self,
        scheme: CompanyCreateScheme,
    ) -> Company:
        query = (
            insert(Company)
            .values(scheme.model_dump(exclude_unset=True))
            .returning(Company)
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def update_company(
        self,
        scheme: CompanyUpdateRequestScheme,
        company_id: UUID,
        owner_id: UUID,
    ) -> Company:
        dump = scheme.model_dump(exclude_unset=True)
        query = (
            update(Company)
            .where(
                and_(
                    Company.company_id == company_id,
                    Company.owner_id == owner_id,
                    Company.is_active == True,
                )
            )
            .values(dump)
            .returning(Company)
        )
        result = await self.session.execute(query)
        if company := result.scalar():
            return company
        raise CompanyNotFoundException(
            company_id=company_id, owner_id=owner_id, is_active=True
        )
