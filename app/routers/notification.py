from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.models import User
from app.schemas.notification import (
    ListNotificationsDetailScheme,
    NotificationDetailScheme,
)
from app.services.auth import GenericAuthService
from app.services.notification import NotificationSrvice
from app.utils.services import get_notification_service

notification_router = APIRouter()


@notification_router.get("/my_notifications")
async def get_my_notifications(
    service: Annotated[NotificationSrvice, Depends(get_notification_service)],
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> ListNotificationsDetailScheme:
    notifications = await service.get_user_notifications(user=user)
    return notifications


@notification_router.get("/mark_as_read/{notification_id}")
async def mark_as_read(
    service: Annotated[NotificationSrvice, Depends(get_notification_service)],
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    notification_id: UUID,
) -> NotificationDetailScheme:
    notification = await service.mark_self_notification_as_read(
        notification_id=notification_id, user=user
    )
    return notification
