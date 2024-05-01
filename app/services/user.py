from logging import getLogger
from typing import NoReturn

from passlib.context import CryptContext
from pydantic import SecretStr
from sqlalchemy import and_, insert, select, update

from app.db.models import (
    User,
)
from app.schemas.user import (
    UserDetailResponseScheme,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
)
from app.services.base import Service
from app.utils.exceptions.user import (
    PasswordVerificationError,
    UserNotFoundException,
)
from app.utils.generics import Password

logger = getLogger(__name__)


class PasswordManager:
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


class UserService(Service):
    @staticmethod
    def verify_user_password(
        user: User,
        password: Password | str,
    ) -> NoReturn | None:
        hashed_password = user.hashed_password
        if PasswordManager(password).verify_password(hashed_password) is False:
            raise PasswordVerificationError(user=user)

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
        if user := result.scalar():
            return user
        raise UserNotFoundException(**kwargs)

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
        query = (
            select(User).where(User.is_active == True).order_by(User.username)
        )
        query = self.apply_pagination(query=query, page=page, limit=limit)

        result = await self.session.execute(query)
        raw_users = result.scalars().all()
        users = [UserDetailResponseScheme.from_orm(user) for user in raw_users]
        return UsersListResponseScheme(users=users)
