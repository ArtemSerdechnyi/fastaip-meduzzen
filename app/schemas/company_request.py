from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models import CompanyRequestStatus
from app.schemas.company import _CompanyIdSchemeMixin
from app.schemas.user import _UserIDSchemeMixin


class _RequestIdSchemeMixin:
    request_id: UUID


class _StatusSchemeMixin(BaseModel):
    status: CompanyRequestStatus


class CompanyRequestDetailResponseScheme(
    _RequestIdSchemeMixin,
    _CompanyIdSchemeMixin,
    _UserIDSchemeMixin,
    _StatusSchemeMixin,
    BaseModel,
):
    model_config = ConfigDict(from_attributes=True)


class CompanyRequestListDetailResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requests: list[CompanyRequestDetailResponseScheme]
