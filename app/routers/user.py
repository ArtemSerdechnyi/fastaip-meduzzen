from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.postgres import get_async_session
from app.schemas.company import (
    CompanyRequestListDetailResponseScheme,
    CompanyRequestDetailResponseScheme,
)
from app.schemas.user import (
    OAuth2RequestFormScheme,
    UserDetailResponseScheme,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
    UserRequestDetailResponseScheme,
    UserRequestListDetailResponseScheme,
)
from app.services.user import (
    GenericAuthService,
    JWTService,
    UserService,
)
from app.utils.user import get_users_page_limit

user_router = APIRouter()
user_action_router = APIRouter()


@user_router.get("/token")
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


@user_router.get("/{user_id}")
async def get_user(
    user_id: UUID, db: AsyncSession = Depends(get_async_session)
) -> UserDetailResponseScheme:
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


@user_router.get("/all/")
async def get_all_users(
    page: int = 1,
    db: AsyncSession = Depends(get_async_session),
    limit: int = Depends(get_users_page_limit),
) -> UsersListResponseScheme:
    async with UserService(db) as service:
        user_list = await service.get_all_users(page, limit)
    return user_list


# user actions


@user_action_router.post("/requests/{company_id}")
async def send_join_request(
    company_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
) -> UserRequestDetailResponseScheme:
    async with UserService(db) as service:
        request = await service.create_user_request(
            company_id=company_id, user=user
        )
    return request


@user_action_router.delete("/requests/{request_id}")
async def cancel_join_request(
    request_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
) -> UserRequestDetailResponseScheme:
    async with UserService(db) as service:
        request = await service.cancel_user_request(
            request_id=request_id, user=user
        )
    return request


@user_action_router.get("/requests")
async def list_user_requests(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
    page: int = 1,
    limit: int = Depends(get_users_page_limit),
) -> UserRequestListDetailResponseScheme:
    async with UserService(db) as service:
        requests = await service.list_user_requests(
            user=user, page=page, limit=limit
        )
    return requests


@user_action_router.get("/invitations")
async def list_user_invitations(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
    page: int = 1,
    limit: int = Depends(get_users_page_limit),
) -> CompanyRequestListDetailResponseScheme:
    async with UserService(db) as service:
        invitations = await service.list_user_invitations(
            user=user, page=page, limit=limit
        )
    return invitations


@user_action_router.post("/accept/{request_id}")
async def accept_invite(
    request_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
) -> CompanyRequestDetailResponseScheme:
    async with UserService(db) as service:
        request = await service.accept_invitation(
            request_id=request_id, user=user
        )
    return request


@user_action_router.post("/reject/{request_id}")
async def reject_invite(
    request_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
) -> CompanyRequestDetailResponseScheme:
    async with UserService(db) as service:
        request = await service.reject_invitation(
            request_id=request_id, user=user
        )
    return request


@user_action_router.delete("/leave/{company_id}")
async def leave_company(
    company_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    db: AsyncSession = Depends(get_async_session),
):
    async with UserService(db) as service:
        await service.leave_company(company_id=company_id, user=user)
    return {"status_code": 204, "detail": "Left the company"}
