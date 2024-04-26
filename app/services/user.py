import datetime
import uuid
from logging import getLogger
from typing import NoReturn

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import SecretStr
from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import app_settings, auth0_config, gwt_config
from app.db.models import User
from app.db.postgres import get_async_session
from app.schemas.user import (
    TokenUserDataScheme,
    UserDetailResponseScheme,
    UserHTTPBearer,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
)
from app.utils.exceptions.user import (
    DecodeUserTokenError,
    PasswordVerificationError,
    UserNotFoundException,
)
from app.utils.generics import Password

logger = getLogger(__name__)


class PasswordManager:  # todo mb refactor to async
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _hashed_password = None

    def __init__(self, password: str | Password):
        if isinstance(password, SecretStr):
            self.password = str(password.get_secret_value())
        else:
            self.password = password

    def _get_hash(self, var: str) -> str:
        return self._pwd_context.hash(var)

    @property
    def hash(self) -> str:
        if self._hashed_password is None:
            self._hashed_password = self._get_hash(self.password)
        return self._hashed_password

    def verify_password(self, hashed_password: str) -> bool:
        return self._pwd_context.verify(self.password, hashed_password)


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
        async with UserService(db) as service:
            if token_data := JWTService.decode_token(token=token):
                email = token_data.email
                user = await service.get_user_by_attributes(email=email)
            elif token_data := Auth0Service.decode_token(token=token):
                email = token_data.email
                try:
                    user = await service.get_user_by_attributes(email=email)
                except UserNotFoundException:
                    user = await service.create_and_get_auth0_user(email=email)
            else:
                raise DecodeUserTokenError()
            return user


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._queries = []

    @property
    def queries(self):
        return self._queries

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Exception | None, exc_val, exc_tb):
        if exc_type is None:
            # todo add SQLAlchemy error interception
            if self._queries is not None:
                for query in self.queries:
                    await self.session.execute(query)
            await self.session.commit()
        else:
            await self.session.rollback()
            logger.error(f"Error occurred {exc_type}, {exc_val}, {exc_tb}")
            raise exc_type
        return False  # mb True?

    @staticmethod
    def verify_user_password(
        user: User,
        password: Password | str,
    ) -> NoReturn | None:
        hashed_password = user.hashed_password
        if PasswordManager(password).verify_password(hashed_password) is False:
            raise PasswordVerificationError(user=user)

    async def _add_query(self, query):
        self._queries.append(query)

    async def get_user_by_attributes(
        self,
        is_active=True,
        **kwargs,
    ) -> User:
        kwargs.update(is_active=is_active)

        query = select(User).where(
            and_(
                *(
                    getattr(User, attr) == value
                    for attr, value in kwargs.items()
                )
            )
        )
        result = await self.session.execute(query)
        user = result.scalar()
        if not user:
            raise UserNotFoundException(**kwargs)
        return user

    async def create_default_user(self, scheme: UserSignUpRequestScheme):
        password_hash = PasswordManager(scheme.password).hash
        new_user = User(
            email=scheme.email,
            username=scheme.username,
            hashed_password=password_hash,
        )
        self.session.add(new_user)

    async def create_and_get_auth0_user(self, email: str) -> User:
        query = insert(User).values(email=email).returning(User)
        res = await self.session.execute(query)
        return res.scalar()

    async def self_user_update(
        self, user: User, scheme: UserUpdateRequestScheme
    ) -> UserDetailResponseScheme:
        if scheme.password:
            scheme.password = PasswordManager(scheme.password).hash

        query = (
            update(User)
            .where(and_(User.user_id == user.user_id, User.is_active == True))
            .values(scheme.dict(exclude_unset=True))
            .returning(User)
        )
        user = await self.session.execute(query)
        user = user.scalar()
        return UserDetailResponseScheme.from_orm(user)

    async def self_user_delete(self, user: User):
        query = (
            update(User)
            .where(and_(User.user_id == user.user_id, User.is_active == True))
            .values(is_active=False)
        )
        await self._add_query(query)

    async def get_all_users(self, page, limit) -> UsersListResponseScheme:
        if page < 1:
            raise AttributeError(f"Page must be >= 1, page: {page}")
        elif limit < 1:
            raise AttributeError(f"Limit must be >= 1, limit: {limit}")

        query = (
            select(User)
            .where(User.is_active == True)
            .limit(limit)
            .offset(page - 1 if page == 1 else (page - 1) * limit)
            .order_by(User.username)
        )
        result = await self.session.execute(query)
        raw_users = result.scalars().all()
        users = [UserDetailResponseScheme.from_orm(user) for user in raw_users]
        return UsersListResponseScheme(users=users)
