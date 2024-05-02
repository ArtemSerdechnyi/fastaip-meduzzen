from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.utils.schemas import optionalise_fields


class BaseCompanyScheme(BaseModel):
    name: str


class CompanyCreateRequestScheme(BaseCompanyScheme):
    description: Optional[str]


class CompanyCreateScheme(CompanyCreateRequestScheme):
    owner_id: UUID


class CompanyDetailResponseScheme(CompanyCreateRequestScheme):
    model_config = ConfigDict(from_attributes=True)

    visibility: bool


@optionalise_fields
class CompanyUpdateRequestScheme(CompanyCreateRequestScheme):
    visibility: Optional[bool]
    is_active: Optional[bool]


class CompanyListResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    companies: list[CompanyDetailResponseScheme]
