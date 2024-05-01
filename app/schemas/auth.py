from pydantic import BaseModel, EmailStr

from app.schemas.user import _UserEmailSchemeMixin
from app.utils.generics import Password


class TokenUserDataScheme(_UserEmailSchemeMixin, BaseModel):
    pass


class OAuth2RequestFormScheme:
    def __init__(self, email: EmailStr, password: Password):
        self.email = email
        self.password = password


class UserTokenScheme(BaseModel):
    access_token: str
    token_type: str
