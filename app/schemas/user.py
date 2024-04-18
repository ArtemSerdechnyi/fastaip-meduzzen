import uuid
from abc import ABC

from pydantic import EmailStr, Field, BaseModel, SecretStr

from app.utils.generics import Name
from app.utils.schemas import optionalise_fields


class _UserBaseScheme(BaseModel, ABC):
    pass


class _UserNamesSchemeMixin:
    username: Name
    first_name: Name
    last_name: Name


class _UserEmailSchemeMixin:
    email: EmailStr


class _UserPasswordSchemeMixin:
    password: SecretStr = Field(min_length=8, max_length=25)


# using schemas


class UserDetailResponseScheme(
    _UserNamesSchemeMixin, _UserEmailSchemeMixin, _UserBaseScheme
):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class UserSignUpRequestScheme(
    _UserEmailSchemeMixin,
    _UserPasswordSchemeMixin,
    _UserBaseScheme,
):
    password_confirm: SecretStr = _UserPasswordSchemeMixin.password


class UserSignInRequestScheme(_UserPasswordSchemeMixin, _UserBaseScheme):
    email_or_username: EmailStr | Name


@optionalise_fields
class UserUpdateRequestScheme(
    _UserNamesSchemeMixin,
    _UserEmailSchemeMixin,
    _UserPasswordSchemeMixin,
    _UserBaseScheme,
):
    pass


class UsersListResponseScheme(_UserBaseScheme):
    users: list[UserDetailResponseScheme]
