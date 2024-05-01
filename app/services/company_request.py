from uuid import UUID

from sqlalchemy import update, and_

from app.db.models import CompanyRequestStatus, CompanyRequest
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