from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models import UserRequestStatus


class UserRequestCreateScheme(BaseModel):
    company_id: UUID
    user_id: UUID
    status: str = UserRequestStatus.pending.value


class UserRequestDetailResponseScheme(
    BaseModel,
):
    model_config = ConfigDict(from_attributes=True)

    request_id: UUID
    company_id: UUID
    user_id: UUID
    status: str


class UserRequestListDetailResponseScheme(BaseModel):
    requests: list[UserRequestDetailResponseScheme]
