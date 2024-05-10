from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.utils.schemas import optionalise_fields


class BaseCompanyScheme(BaseModel):
    name: str


class CompanyCreateRequestScheme(BaseCompanyScheme):
    description: Optional[str]


class CompanyCreateScheme(CompanyCreateRequestScheme):
    owner_id: UUID


class CompanyDetailResponseScheme(CompanyCreateRequestScheme):
    model_config = ConfigDict(from_attributes=True)

    company_id: UUID
    visibility: bool


@optionalise_fields
class CompanyUpdateRequestScheme(CompanyCreateRequestScheme):
    visibility: Optional[bool]
    is_active: Optional[bool]


class CompanyListResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    companies: List[CompanyDetailResponseScheme]
