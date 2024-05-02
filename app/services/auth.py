import datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import app_settings, auth0_config, gwt_config
from app.db.models import User
from app.db.postgres import get_async_session
from app.repositories.user import UserRepository
from app.schemas.auth import TokenUserDataScheme
from app.schemas.user import UserSchemeSignUpAuth0RequestScheme
from app.utils.exceptions.user import (
    DecodeUserTokenError,
    UserNotFoundException,
)


class UserHTTPBearer(HTTPBearer):
    pass


class JWTService:
    @staticmethod
    def get_expires_delta() -> datetime.timedelta:
        return datetime.timedelta(
            minutes=gwt_config.GWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        expires_delta = cls.get_expires_delta()
        to_encode = data.copy()
        if expires_delta:
            expire = (
                datetime.datetime.now(datetime.timezone.utc) + expires_delta
            )
        else:
            expire = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(
                minutes=gwt_config.GWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            app_settings.SECRET_KEY,
            algorithm=gwt_config.GWT_ALGORITHMS,
        )
        return encoded_jwt

    @classmethod
    def decode_token(
        cls,
        token: str,
    ) -> TokenUserDataScheme:
        try:
            payload = jwt.decode(
                token,
                app_settings.SECRET_KEY,
                algorithms=[gwt_config.GWT_ALGORITHMS],
            )
        except JWTError:
            pass
        else:
            user_email = payload.get("email")
            return TokenUserDataScheme(email=user_email)


class Auth0Service:
    @classmethod
    def decode_token(
        cls,
        token: str,
    ) -> TokenUserDataScheme:
        try:
            payload = jwt.decode(
                token,
                auth0_config.AUTH0_API_SECRET,
                algorithms=[auth0_config.AUTH0_ALGORITHMS],
                audience=auth0_config.AUTH0_API_AUDIENCE,
            )
        except JWTError:
            pass
        else:
            user_email = payload.get("email")
            return TokenUserDataScheme(email=user_email)


class GenericAuthService:
    @classmethod
    async def get_user_from_any_token(
        cls,
        credentials: HTTPAuthorizationCredentials = Depends(UserHTTPBearer()),
        db: AsyncSession = Depends(get_async_session),
    ) -> User:
        token = credentials.credentials
        ur = UserRepository(session=db)
        if token_data := JWTService.decode_token(token=token):
            email = token_data.email
            user = await ur.get_user_by_attributes(email=email)
        elif token_data := Auth0Service.decode_token(token=token):
            email = token_data.email
            try:
                user = await ur.get_user_by_attributes(email=email)
            except UserNotFoundException:
                scheme = UserSchemeSignUpAuth0RequestScheme(email=email)
                user = await ur.create_user(scheme=scheme)
        else:
            raise DecodeUserTokenError()
        return user

        # async with UserService(db) as service:
        #     if token_data := JWTService.decode_token(token=token):
        #         email = token_data.email
        #         user = await service.get_user_by_attributes(email=email)
        #     elif token_data := Auth0Service.decode_token(token=token):
        #         email = token_data.email
        #         try:
        #             user = await service.get_user_by_attributes(email=email)
        #         except UserNotFoundException:
        #             user = await service.create_and_get_auth0_user(email=email)
        #     else:
        #         raise DecodeUserTokenError()
        #     return user
