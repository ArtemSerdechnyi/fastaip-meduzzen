from uuid import UUID

from sqlalchemy import select, and_, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas.user import (
    UserSchemeSignUpRequestScheme,
    UserSchemeSignUpAuth0RequestScheme,
    UserUpdateRequestScheme,
)
from app.utils.exceptions.user import UserNotFoundException

from app.utils.paginator import Paginator
from app.utils.user import PasswordManager


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

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

    async def get_users_list_by_attributes(
        self,
        page: int,
        limit: int,
        is_active=True,
        **kwargs,
    ) -> list[User]:
        kwargs.update(is_active=is_active)
        filter_condition = [
            getattr(User, attr) == value for attr, value in kwargs.items()
        ]
        paginator = Paginator(
            model=User,
            session=self.session,
            filter_condition=filter_condition,
        )
        users = await paginator.paginate(page=page, limit=limit)
        return users

    async def create_user(
        self,
        scheme: UserSchemeSignUpRequestScheme
        | UserSchemeSignUpAuth0RequestScheme,
    ) -> User:
        query = (
            insert(User)
            .values(scheme.model_dump(exclude_unset=True))
            .returning(User)
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def update_user_by_id(
        self, user_id: UUID, scheme: UserUpdateRequestScheme
    ) -> User:
        if scheme.passwords:
            scheme.hashed_password = PasswordManager(
                scheme.passwords.password
            ).hash
        query = (
            update(User)
            .where(and_(User.user_id == user_id, User.is_active == True))
            .values(scheme.model_dump(exclude_unset=True))
            .returning(User)
        )
        result = await self.session.execute(query)
        if user := result.scalar():
            return user
        raise UserNotFoundException(user_id=user_id, is_active=True)
