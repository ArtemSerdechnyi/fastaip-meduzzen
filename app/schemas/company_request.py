from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models import CompanyRequestStatus


class CompanyRequestCreateScheme(BaseModel):
    company_id: UUID
    user_id: UUID
    status: str = CompanyRequestStatus.pending.value


class CompanyRequestDetailResponseScheme(CompanyRequestCreateScheme):
    model_config = ConfigDict(from_attributes=True)

    status: str


class CompanyRequestListDetailResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requests: list[CompanyRequestDetailResponseScheme]
