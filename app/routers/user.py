import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.postgres import get_async_session
from app.schemas.user import (
    OAuth2RequestFormScheme,
    UserDetailResponseScheme,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
)
from app.services.user import (
    GenericAuthService,
    JWTService,
    UserService,
)
from app.utils.user import get_users_page_limit

user_router = APIRouter()


@user_router.get("/example_both_token_autn")
async def example_both_token_autn(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
):
    user = UserDetailResponseScheme.from_orm(user)
    return user


@user_router.post("/token")
async def get_user_token(
    body: OAuth2RequestFormScheme = Depends(),
):
    token = JWTService.create_access_token(data={"email": str(body.email)})
    return token


@user_router.post("/")
async def create_new_user(
    body: UserSignUpRequestScheme,
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        await service.create_default_user(body)
    return {"status_code": 201, "detail": "User created"}


@user_router.get("/{user_id}", response_model=UserDetailResponseScheme)
async def get_user(
    user_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)
):
    async with UserService(db) as service:
        user = await service.get_user_by_attributes(user_id=user_id)
    return user


@user_router.patch("/")
async def update_user(
    body: UserUpdateRequestScheme,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        user = await service.self_user_update(user, body)
    return {"status_code": 200, "detail": user}


@user_router.delete("/")
async def delete_user(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        await service.self_user_delete(user)
    return {"status_code": 204, "detail": "User deleted"}


@user_router.get("/all/{page}", response_model=UsersListResponseScheme)
async def get_all_users(
    page: int,
    db: AsyncSession = Depends(get_async_session),
    limit: int = Depends(get_users_page_limit),
):
    async with UserService(db) as service:
        user_list = await service.get_all_users(page, limit)
    return user_list
