from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import CompanyRole
from app.utils.schemas import optionalise_fields

# from app.schemas.user import _UserIDSchemeMixin


def lazy_import_UserIDSchemeMixin():
    from app.schemas.user import _UserIDSchemeMixin

    return _UserIDSchemeMixin


class _BaseCompany(BaseModel):
    pass


class _CompanyIdSchemeMixin:
    company_id: UUID


class _CompanyNameSchemeMixin:
    name: str


class _CompanyDescriptionSchemeMixin:
    description: Optional[str] = None


class _CompanyOwnerSchemeMixin:
    owner_id: UUID


class _CompanyVisibilitySchemeMixin:
    visibility: bool = Field(default=True)


# used schemas


class CompanyCreateRequestScheme(
    _CompanyNameSchemeMixin,
    _CompanyDescriptionSchemeMixin,
    _CompanyVisibilitySchemeMixin,
    _BaseCompany,
):
    pass


@optionalise_fields
class CompanyDetailResponseScheme(
    _CompanyNameSchemeMixin,
    _CompanyDescriptionSchemeMixin,
    _CompanyOwnerSchemeMixin,
    _BaseCompany,
):
    model_config = ConfigDict(from_attributes=True)


@optionalise_fields
class OwnerCompanyDetailResponseScheme(
    _CompanyIdSchemeMixin,
    _CompanyVisibilitySchemeMixin,
    CompanyDetailResponseScheme,
):
    model_config = ConfigDict(from_attributes=True)


@optionalise_fields
class CompanyUpdateRequestScheme(
    _CompanyNameSchemeMixin,
    _CompanyDescriptionSchemeMixin,
    _BaseCompany,
):
    pass


class CompanyListResponseScheme(_BaseCompany):
    model_config = ConfigDict(from_attributes=True)

    companies: list[
        CompanyDetailResponseScheme | OwnerCompanyDetailResponseScheme
    ]


# company member scheme


class _BaseCompanyMember(BaseModel):
    pass


_UserIDSchemeMixin = lazy_import_UserIDSchemeMixin()


class CompanyMemberDetailResponseScheme(
    _CompanyIdSchemeMixin, _UserIDSchemeMixin, _BaseCompanyMember
):
    model_config = ConfigDict(from_attributes=True)

    role: CompanyRole


class CompanyListMemberDetailResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    members: list[CompanyMemberDetailResponseScheme]



