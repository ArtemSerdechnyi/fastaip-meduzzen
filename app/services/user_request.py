from uuid import UUID

from sqlalchemy import update, and_

from app.db.models import UserRequestStatus, UserRequest
from app.services.base import Service
from app.utils.exceptions.user import UserRequestNotFoundException


class UserRequestService(Service):

    async def _update_user_request_status(
        self, request_id: UUID, status: UserRequestStatus
    ) -> UserRequest:
        query = (
            update(UserRequest)
            .where(
                and_(
                    UserRequest.request_id == request_id,
                    UserRequest.is_active == True,
                )
            )
            .values(status=status)
            .returning(UserRequest)
        )
        result = await self.session.execute(query)
        if request := result.scalar():
            return request
        raise UserRequestNotFoundException(
            request_id=request_id, status=status
        )