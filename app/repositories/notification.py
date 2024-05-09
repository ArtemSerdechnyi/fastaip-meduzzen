from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update, and_, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification
from app.schemas.notification import NotificationCreateScheme


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(
        self, scheme: NotificationCreateScheme
    ) -> Notification:
        data = scheme.model_dump(exclude_unset=True)
        query = insert(Notification).values(**data).returning(Notification)
        result = await self.session.execute(query)
        return result.scalar()

    async def get_user_notifications(
        self, user_id: UUID
    ) -> Sequence[Notification]:
        query = select(Notification).where(
            and_(Notification.user_id == user_id, Notification.status == True)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_user_notification_status(
        self, notification_id: UUID, user_id: UUID, status: bool
    ) -> Notification:
        query = (
            update(Notification)
            .where(
                and_(
                    Notification.notification_id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            .values(status=status)
            .returning(Notification)
        )
        result = await self.session.execute(query)
        return result.scalar()
