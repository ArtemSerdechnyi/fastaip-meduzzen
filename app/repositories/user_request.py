from uuid import UUID

from sqlalchemy import and_, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import UserRequest
from app.schemas.user_request import UserRequestCreateScheme
from app.utils.exceptions.user import UserRequestNotFoundException


class UserRequestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_request_by_attributes(
        self,
        is_active: bool = True,
        **kwargs,
    ) -> UserRequest:
        kwargs.update(is_active=is_active)

        query = select(UserRequest).where(
            *(
                getattr(UserRequest, attr) == value
                for attr, value in kwargs.items()
            )
        )
        result = await self.session.execute(query)
        if request := result.scalar():
            return request
        raise UserRequestNotFoundException(**kwargs)

    async def get_user_requests_list_by_attributes(
        self,
        page: int,
        limit: int,
        is_active: bool = True,
        **kwargs,
    ) -> list[UserRequest]:
        kwargs.update(is_active=is_active)

        query = select(UserRequest).where(
            and_(
                *(
                    getattr(UserRequest, attr) == value
                    for attr, value in kwargs.items()
                )
            )
        )
        query = query.limit(limit).offset(
            page - 1 if page == 1 else (page - 1) * limit
        )
        res = await self.session.execute(query)
        return res.scalars().all()

    async def create_user_request(
        self,
        scheme: UserRequestCreateScheme,
    ) -> UserRequest:
        query = (
            insert(UserRequest)
            .values(scheme.model_dump())
            .returning(UserRequest)
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def update_user_request_status(
        self,
        request_id: UUID,
        status: str,
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
            request_id=request_id, is_active=True
        )

    async def inactive_user_request(
        self,
        request_id: UUID,
        user_id: UUID,
    ) -> UserRequest:
        query = (
            update(UserRequest)
            .where(
                and_(
                    UserRequest.request_id == request_id,
                    UserRequest.user_id == user_id,
                    UserRequest.is_active == True,
                )
            )
            .values(is_active=False)
            .returning(UserRequest)
        )
        result = await self.session.execute(query)
        if request := result.scalar():
            return request
        raise UserRequestNotFoundException(
            request_id=request_id, is_active=True
        )
