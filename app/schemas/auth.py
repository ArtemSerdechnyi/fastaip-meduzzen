from pydantic import BaseModel, EmailStr

from app.utils.generics import Password


class TokenUserDataScheme(BaseModel):
    email: EmailStr


class OAuth2RequestFormScheme:
    def __init__(self, email: EmailStr, password: Password):
        self.email = email
        self.password = password


class UserTokenScheme(BaseModel):
    access_token: str
    token_type: str
