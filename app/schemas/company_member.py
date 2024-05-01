from pydantic import BaseModel, ConfigDict

from app.db.models import CompanyRole
from app.schemas.company import _CompanyIdSchemeMixin, _CompanyNameSchemeMixin
from app.schemas.user import _UserIDSchemeMixin, _UserEmailSchemeMixin


class _BaseCompanyMember(BaseModel):
    pass


class _CompanyMemberRoleSchemeMixin:
    role: str


class CompanyMemberDetailResponseScheme(
    _CompanyIdSchemeMixin, _UserIDSchemeMixin, _BaseCompanyMember
):
    model_config = ConfigDict(from_attributes=True)

    role: CompanyRole


class CompanyListMemberDetailResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    members: list[CompanyMemberDetailResponseScheme]


class NestedCompanyMemberDetailResponseScheme(
    _UserEmailSchemeMixin,
    _CompanyNameSchemeMixin,
    _CompanyMemberRoleSchemeMixin,
    BaseModel,
):
    model_config = ConfigDict(from_attributes=True)


class ListNestedCompanyMemberDetailResponseScheme(BaseModel):
    members: list[NestedCompanyMemberDetailResponseScheme]
