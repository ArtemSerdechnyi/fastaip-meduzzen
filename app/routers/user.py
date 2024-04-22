import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_async_session
from app.schemas.user import (
    OAuth2PasswordRequestScheme,
    UserDetailResponseScheme,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserTokenScheme,
    UserUpdateRequestScheme,
)
from app.services.user import JWTService, UserService
from app.utils.user import get_users_page_limit

user_router = APIRouter()
logging.basicConfig(level=logging.DEBUG)

@user_router.post("/")
async def create_new_user(
    body: UserSignUpRequestScheme,
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        await service.create_user(body)
    return {"status_code": 201, "detail": "User created"}


@user_router.get("/{user_id}", response_model=UserDetailResponseScheme)
async def get_user(
    user_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)
):
    async with UserService(db) as service:
        user = await service.get_user_by_attributes(user_id=user_id)
    return user


@user_router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequestScheme,
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        await service.update_user(user_id, body)
    return {"status_code": 200, "detail": "User updated"}


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        await service.delete_user(user_id)
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


@user_router.post("/token", response_model=UserTokenScheme)
async def login_for_access_token(
    body: OAuth2PasswordRequestScheme = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        token = await service.get_access_token(body)
    return token


@user_router.post("/me", response_model=UserDetailResponseScheme)
async def get_current_user(
    current_user: Annotated[UserDetailResponseScheme, Depends(JWTService.get_current_user_from_token)]
):
    return current_user
