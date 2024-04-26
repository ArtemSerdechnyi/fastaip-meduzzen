import uuid
from abc import ABC

from fastapi.security import HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, model_validator
from typing_extensions import Optional, Self

from app.utils.generics import Name, Password
from app.utils.schemas import optionalise_fields


class _UserBaseScheme(BaseModel, ABC):
    pass


class _UserIDSchemeMixin:
    user_id: uuid.UUID


class _UsernameSchemeMixin:
    username: Name


class _UserAllNamesSchemeMixin(_UsernameSchemeMixin):
    first_name: Optional[Name]
    last_name: Optional[Name]


class _UserEmailSchemeMixin:
    email: EmailStr


class _UserPasswordSchemeMixin:
    password: Password


class _UserPasswordConfirmSchemeMixin(_UserPasswordSchemeMixin):
    password_confirm: Password

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        pw1 = self.password
        pw2 = self.password_confirm
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("passwords do not match")
        return self


# using schemas


@optionalise_fields
class UserDetailResponseScheme(
    _UserIDSchemeMixin,
    _UserAllNamesSchemeMixin,
    _UserEmailSchemeMixin,
    _UserBaseScheme,
):
    model_config = ConfigDict(from_attributes=True)


class UserSignUpRequestScheme(
    _UserPasswordConfirmSchemeMixin,
    _UsernameSchemeMixin,
    _UserEmailSchemeMixin,
    _UserBaseScheme,
):
    password_confirm: Password


class UserSignInRequestScheme(
    _UserEmailSchemeMixin, _UserPasswordSchemeMixin, _UserBaseScheme
):
    pass


@optionalise_fields
class UserUpdateRequestScheme(
    _UserAllNamesSchemeMixin,
    _UserEmailSchemeMixin,
    _UserPasswordConfirmSchemeMixin,
    _UserBaseScheme,
):
    pass


class UsersListResponseScheme(_UserBaseScheme):
    model_config = ConfigDict(from_attributes=True)

    users: list[UserDetailResponseScheme]


class TokenUserDataScheme(_UserEmailSchemeMixin, BaseModel):
    pass


class OAuth2RequestFormScheme:
    def __init__(self, email: EmailStr, password: Password):
        self.email = email
        self.password = password


class Auth0UserScheme(_UserEmailSchemeMixin, _UserBaseScheme):
    pass


class UserHTTPBearer(HTTPBearer):
    pass


class UserTokenScheme(BaseModel):
    access_token: str
    token_type: str
