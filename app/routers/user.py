from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.postgres import get_async_session
from app.schemas.auth import OAuth2RequestFormScheme
from app.schemas.user import (
    UserSchemeDetailResponseScheme,
    UserSchemeSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
)
from app.services.auth import GenericAuthService, JWTService
from app.services.user import (
    UserService,
)
from app.utils.services import get_user_service
from app.utils.user import get_users_page_limit

user_router = APIRouter()


@user_router.get("/token")
async def get_user_token(
    body: OAuth2RequestFormScheme = Depends(),
):
    token = JWTService.create_access_token(data={"email": str(body.email)})
    return token


@user_router.post("/")
async def create_new_user(
    body: UserSchemeSignUpRequestScheme,
    service: Annotated[UserService, Depends(get_user_service)],
):
    user = await service.create_default_user(scheme=body)
    return UserSchemeDetailResponseScheme.from_orm(user)


@user_router.get("/me")
async def get_user_me(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> UserSchemeDetailResponseScheme:
    return UserSchemeDetailResponseScheme.from_orm(user)


@user_router.get("/{user_id}")
async def get_user(
    user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]
) -> UserSchemeDetailResponseScheme:
    user = await service.get_user_by_id(user_id=user_id)
    return UserSchemeDetailResponseScheme.from_orm(user)


@user_router.patch("/")
async def update_user(
    body: UserUpdateRequestScheme,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchemeDetailResponseScheme:
    updated_user = await service.self_user_update(user, body)
    return updated_user


@user_router.delete("/")
async def delete_user(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserSchemeDetailResponseScheme:
    user = await service.self_user_delete(user)
    return user


@user_router.get("/all/")
async def get_all_users(
    service: Annotated[UserService, Depends(get_user_service)],
    page: int = 1,
    limit: int = Depends(get_users_page_limit),
) -> UsersListResponseScheme:
    user_list = await service.get_all_users(page, limit)
    return user_list
