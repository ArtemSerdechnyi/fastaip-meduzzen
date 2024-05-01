import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.company import _CompanyIdSchemeMixin
from app.schemas.user import _UserIDSchemeMixin


class _UserRequestIDSchemeMixin:
    request_id: uuid.UUID


class _UserRequestStatusSchemeMixin:
    status: str


class UserRequestDetailResponseScheme(
    _UserRequestIDSchemeMixin,
    _CompanyIdSchemeMixin,
    _UserIDSchemeMixin,
    _UserRequestStatusSchemeMixin,
    BaseModel,
):
    model_config = ConfigDict(from_attributes=True)


class UserRequestListDetailResponseScheme(BaseModel):
    requests: list[UserRequestDetailResponseScheme]
