from uuid import UUID

from sqlalchemy import and_, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import CompanyRequest
from app.schemas.company_request import CompanyRequestCreateScheme
from app.utils.exceptions.company import CompanyRequestNotFoundException
from app.utils.paginator import Paginator


class CompanyRequestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_company_request_by_attributes(
        self,
        is_active: bool = True,
        **kwargs,
    ) -> CompanyRequest:
        kwargs.update(is_active=is_active)

        query = select(CompanyRequest).where(
            *(
                getattr(CompanyRequest, attr) == value
                for attr, value in kwargs.items()
            )
        )
        result = await self.session.execute(query)
        if request := result.scalar():
            return request
        raise CompanyRequestNotFoundException(**kwargs)

    async def get_company_requests_list_by_attributes(
        self,
        page: int,
        limit: int,
        is_active: bool = True,
        **kwargs,
    ) -> list[CompanyRequest]:
        kwargs.update(is_active=is_active)

        filter_condition = [
            getattr(CompanyRequest, attr) == value
            for attr, value in kwargs.items()
        ]
        paginator = Paginator(
            model=CompanyRequest,
            session=self.session,
            filter_condition=filter_condition,
        )
        requests = await paginator.paginate(page=page, limit=limit)
        return requests

    async def create_company_request(
        self,
        scheme: CompanyRequestCreateScheme,
    ) -> CompanyRequest:
        query = (
            insert(CompanyRequest)
            .values(scheme.model_dump())
            .returning(CompanyRequest)
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def update_company_request_status(
        self,
        request_id: UUID,
        status: str,
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
        raise CompanyRequestNotFoundException(
            request_id=request_id, is_active=True
        )

    async def inactive_company_request(
        self,
        request_id: UUID,
    ) -> CompanyRequest:
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
        if request := result.scalar():
            return request
        raise CompanyRequestNotFoundException(
            request_id=request_id, is_active=True
        )
