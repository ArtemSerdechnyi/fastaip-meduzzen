import uuid
from logging import getLogger

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import and_, select, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import query

from app.db.models import User
from app.schemas.user import (
    UserDetailResponseScheme,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
)
from app.utils.generics import Hash, Password

logger = getLogger(__name__)


class PasswordManager:  # todo mb refactor to async
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _hashed_password = None

    def __init__(self, password: Password | str):
        self.password = str(password)

    def _get_hash(self, var: Password | str) -> Hash:
        return self._pwd_context.hash(str(var))

    @property
    def hash(self) -> Hash:
        if not self._hashed_password:
            self._hashed_password = self._get_hash(self.password)
        return self._hashed_password

    def verify_password(
        self, plain_password: Password, hashed_password: Hash
    ) -> bool:
        plain_password = str(plain_password)
        return self._pwd_context.verify(plain_password, hashed_password)


class UserService:
    def __init__(self, session: AsyncSession):  # todo refactor to async
        self.session = session
        self._query = None

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, value):
        if self._query is not None and value is not None:
            raise AttributeError("Query already exists")
        self._query = value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self._query is not None:
                res = await self.session.execute(self._query)
            await self.session.commit()
        else:
            await self.session.rollback()
            logger.error(f"Error occurred {exc_type}, {exc_val}, {exc_tb}")
            raise HTTPException(status_code=500)
        return False  # mb True?

    async def create_user(self, scheme: UserSignUpRequestScheme):
        password_hash = PasswordManager(scheme.password).hash
        new_user = User(
            email=scheme.email,
            username=scheme.username,
            hashed_password=password_hash,
        )
        self.session.add(new_user)

    async def get_user_by_id(self, id: uuid.UUID) -> UserDetailResponseScheme:
        user = await self.session.get_one(User, id)
        return UserDetailResponseScheme.from_orm(user)

    async def update_user(
        self, id: uuid.UUID, scheme: UserUpdateRequestScheme
    ):
        self.query = (
            update(User)
            .where(and_(User.user_id == id, User.is_active == True))
            .values(scheme.dict(exclude_unset=True))
            .returning(User.user_id)
        )

    async def delete_user(self, id: uuid.UUID):
        self.query = (
            update(User)
            .where(and_(User.user_id == id, User.is_active == True))
            .values(is_active=False)
        )

    async def get_all_users(self, page, limit) -> UsersListResponseScheme:
        if page < 1:
            raise AttributeError(f"Page must be >= 1, page: {page}")

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
