import datetime
import uuid
from typing import NoReturn, Annotated

from fastapi import Depends
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import SecretStr
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants
from app.core.settings import app_settings
from app.db.models import User
from app.db.postgres import get_async_session
from app.schemas.user import (
    OAuth2PasswordRequestScheme,
    UserDetailResponseScheme,
    UserOauth2Scheme,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserTokenScheme,
    UserUpdateRequestScheme,
)
from app.utils.exceptions.user import (
    PasswordVerificationError,
    UserNotFoundException,
)
from app.utils.generics import Password



class PasswordManager:  # todo mb refactor to async
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _hashed_password = None

    def __init__(self, password: str | Password):
        if isinstance(password, SecretStr):
            self.password = str(password.get_secret_value())
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
            minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    @staticmethod
    def get_user_id_from_token(token: str) -> str:
        payload = jwt.decode(
            token, app_settings.SECRET_KEY, algorithms=[constants.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError
        return user_id

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
                minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, app_settings.SECRET_KEY, algorithm=constants.ALGORITHM
        )
        return encoded_jwt

    @classmethod
    async def get_current_user_from_token(
        cls,
        token: Annotated[str, Depends(UserOauth2Scheme)],
        db: AsyncSession = Depends(get_async_session),
    ) -> UserDetailResponseScheme:
        async with UserService(db) as service:
            user_id = cls.get_user_id_from_token(token)
            user = await service.get_user_by_attributes(user_id=user_id)
            return UserDetailResponseScheme.from_orm(user)


class UserService:
    def __init__(self, session: AsyncSession):  # todo refactor to async
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

    async def verify_user_by_email(self, email) -> User | NoReturn:
        user = await self.get_user_by_attributes(email=email)
        if user is None:
            raise UserNotFoundException(email=email)
        return user

    async def add_query(self, query):
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

    async def create_user(self, scheme: UserSignUpRequestScheme):
        password_hash = PasswordManager(
            str(scheme.password.get_secret_value())
        ).hash
        new_user = User(
            email=scheme.email,
            username=scheme.username,
            hashed_password=password_hash,
        )
        self.session.add(new_user)

    async def update_user(
        self, id: uuid.UUID, scheme: UserUpdateRequestScheme
    ):
        query = (
            update(User)
            .where(and_(User.user_id == id, User.is_active == True))
            .values(scheme.dict(exclude_unset=True))
            .returning(User.user_id)
        )
        await self.add_query(query)

    async def delete_user(self, id: uuid.UUID):
        query = (
            update(User)
            .where(and_(User.user_id == id, User.is_active == True))
            .values(is_active=False)
        )
        await self.add_query(query)

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

    async def user_authentication_check(
        self, scheme: OAuth2PasswordRequestScheme
    ) -> User | NoReturn:
        user = await self.get_user_by_attributes(email=scheme.username)
        self.verify_user_password(user, scheme.password)
        return user

    async def get_access_token(
        self, scheme: OAuth2PasswordRequestScheme
    ) -> UserTokenScheme:  # todo move to JWRService
        user: User = await self.user_authentication_check(scheme)
        token = JWTService.create_access_token(data={"sub": str(user.user_id)})
        return UserTokenScheme(access_token=token, token_type="bearer")
