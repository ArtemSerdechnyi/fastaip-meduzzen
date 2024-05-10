from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.company import (
    CompanyDetailResponseScheme,
)
from app.schemas.user import (
    UserSchemeDetailResponseScheme,
)


class CompanyMemberDetailResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: UUID
    user_id: UUID
    role: str
    is_active: bool


class CompanyListMemberDetailResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    members: List[CompanyMemberDetailResponseScheme]


class NestedCompanyMemberDetailResponseScheme(
    BaseModel,
):
    model_config = ConfigDict(from_attributes=True)

    user: UserSchemeDetailResponseScheme
    company: CompanyDetailResponseScheme
    role: str


class ListNestedCompanyMemberDetailResponseScheme(BaseModel):
    members: List[NestedCompanyMemberDetailResponseScheme]
