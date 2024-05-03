from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    model_validator,
)
from typing_extensions import Optional, Self

from app.utils.generics import Password
from app.utils.schemas import optionalise_fields
from app.utils.user import PasswordManager


class BaseUserScheme(BaseModel):
    email: EmailStr


class UserPasswordsScheme(BaseModel):
    password: Password
    password_confirm: Password

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        pw1 = self.password
        pw2 = self.password_confirm
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("passwords do not match")
        return self


class UserSchemeDetailResponseScheme(BaseUserScheme):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    is_active: Optional[bool]
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class UserSchemeSignUpRequestScheme(BaseUserScheme):
    passwords: UserPasswordsScheme = Field(exclude=True)

    @computed_field
    @property
    def hashed_password(self) -> str:
        return PasswordManager(self.passwords.password).hash


class UserSchemeSignUpAuth0RequestScheme(BaseUserScheme):
    pass


class UserSchemeSignInRequestScheme(BaseUserScheme):
    password: Password


@optionalise_fields
class UserUpdateRequestScheme(UserSchemeDetailResponseScheme):
    is_active: Optional[bool]


class UsersListResponseScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    users: list[UserSchemeDetailResponseScheme]
