from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationCreateScheme(BaseModel):
    text: str
    user_id: UUID


class NotificationDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: UUID
    text: str
    user_id: UUID
    time: datetime
    status: bool


class ListNotificationsDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notifications: list[NotificationDetailScheme]
