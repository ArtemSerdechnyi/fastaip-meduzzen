from uuid import UUID

from sqlalchemy import and_, update

from app.db.models import CompanyRequest, CompanyRequestStatus
from app.services.base import Service
from app.utils.exceptions.company import CompanyRequestNotFoundException


class CompanyRequestService(Service):
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
