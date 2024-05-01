from pydantic import BaseModel, ConfigDict

from app.db.models import CompanyRole
from app.schemas.company import _CompanyIdSchemeMixin
from app.schemas.user import _UserIDSchemeMixin


class _BaseCompanyMember(BaseModel):
    pass


class CompanyMemberDetailResponseScheme(
    _CompanyIdSchemeMixin, _UserIDSchemeMixin, _BaseCompanyMember
):
    model_config = ConfigDict(from_attributes=True)

    role: CompanyRole


class CompanyListMemberDetailResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    members: list[CompanyMemberDetailResponseScheme]
