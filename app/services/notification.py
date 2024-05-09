from uuid import UUID

from app.db.models import User
from app.repositories.notification import NotificationRepository
from app.repositories.user_quiz import UserQuizRepository
from app.schemas.notification import (
    ListNotificationsDetailScheme,
    NotificationDetailScheme,
)
from app.services.base import Service


class NotificationSrvice(Service):
    def __init__(self, session):
        self.notification_repo = NotificationRepository(session)
        self.user_quiz_repo = UserQuizRepository(session)
        super().__init__(session)

    async def get_user_notifications(
        self, user: User
    ) -> ListNotificationsDetailScheme:
        raw_notifications = (
            await self.notification_repo.get_user_notifications(
                user_id=user.user_id
            )
        )
        list_notifications = [
            NotificationDetailScheme.from_orm(n) for n in raw_notifications
        ]
        return ListNotificationsDetailScheme(notifications=list_notifications)

    async def mark_self_notification_as_read(
        self, notification_id: UUID, user: User
    ):
        raw_notification = (
            await self.notification_repo.update_user_notification_status(
                notification_id=notification_id,
                user_id=user.user_id,
                status=False,
            )
        )
        return NotificationDetailScheme.from_orm(raw_notification)
