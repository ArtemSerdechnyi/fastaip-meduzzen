from logging import getLogger
from uuid import UUID

from app.db.models import (
    User,
)
from app.repositories.user import UserRepository
from app.schemas.user import (
    UserSchemeDetailResponseScheme,
    UserSchemeSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
)
from app.services.base import Service

logger = getLogger(__name__)


class UserService(Service):
    def __init__(self, session):
        self.user_repository = UserRepository(session)
        super().__init__(session)

    async def create_default_user(
        self, scheme: UserSchemeSignUpRequestScheme
    ) -> UserSchemeDetailResponseScheme:
        new_user = await self.user_repository.create_user(scheme=scheme)
        return UserSchemeDetailResponseScheme.from_orm(new_user)

    async def get_user_by_id(
        self, user_id: UUID
    ) -> UserSchemeDetailResponseScheme:
        user = await self.user_repository.get_user_by_attributes(
            user_id=user_id
        )
        return UserSchemeDetailResponseScheme.from_orm(user)

    async def get_user_by_email(
        self, email: str
    ) -> UserSchemeDetailResponseScheme:
        user = await self.user_repository.get_user_by_attributes(email=email)
        return UserSchemeDetailResponseScheme.from_orm(user)

    async def self_user_update(
        self, user: User, scheme: UserUpdateRequestScheme
    ) -> UserSchemeDetailResponseScheme:
        user = await self.user_repository.update_user_by_id(
            user_id=user.user_id, scheme=scheme
        )
        return UserSchemeDetailResponseScheme.from_orm(user)

    async def self_user_delete(self, user: User):
        scheme = UserUpdateRequestScheme(is_active=False)
        user = await self.user_repository.update_user_by_id(
            user_id=user.user_id, scheme=scheme
        )
        return UserSchemeDetailResponseScheme.from_orm(user)

    async def get_all_users(self, page, limit) -> UsersListResponseScheme:
        raw_users = await self.user_repository.get_users_list_by_attributes(
            page=page, limit=limit
        )
        users = [
            UserSchemeDetailResponseScheme.from_orm(user) for user in raw_users
        ]
        return UsersListResponseScheme(users=users)
