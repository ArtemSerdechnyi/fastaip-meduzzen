from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CompanyRequestStatus, CompanyRole, User
from app.db.postgres import get_async_session
from app.schemas.company import (
    CompanyListMemberDetailResponseScheme,
    CompanyMemberDetailResponseScheme,
)
from app.schemas.company_request import (
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user_request import UserRequestDetailResponseScheme
from app.services.auth import GenericAuthService
from app.services.company_action import CompanyActionService
from app.utils.company import (
    get_companies_members_page_limit,
    get_companies_users_request_page_limit,
)

company_action_router = APIRouter()


@company_action_router.post("/{company_id}/invite/{user_id}")
async def company_user_invite(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    user_id: UUID,
    company_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> CompanyRequestDetailResponseScheme:
    async with CompanyActionService(db) as service:
        request = await service.create_company_user_invite(
            user_id=user_id,
            company_id=company_id,
            owner=owner,
        )
    return request


@company_action_router.delete("/{request_id}")
async def company_user_remove_invite(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    request_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    async with CompanyActionService(db) as service:
        request = await service.remove_user_invite(
            request_id=request_id,
            owner=owner,
        )
    return request


@company_action_router.delete("/{company_id}/user/{user_id}")
async def company_remove_user(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    user_id: UUID,
    company_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> CompanyMemberDetailResponseScheme:
    async with CompanyActionService(db) as service:
        member = await service.remove_user_from_company(
            user_id=user_id,
            company_id=company_id,
            owner=owner,
        )
    return member


@company_action_router.get("/confirm_user_request/{request_id}")  # todo
async def confirm_user_request(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    request_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> UserRequestDetailResponseScheme:
    async with CompanyActionService(db) as service:
        user_request = await service.confirm_user_request(
            request_id=request_id,
            owner=owner,
        )
    return user_request


@company_action_router.get("/deny_user_request/{request_id}")  # todo
async def deny_user_request(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    request_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> UserRequestDetailResponseScheme:
    async with CompanyActionService(db) as service:
        user_request = await service.deny_user_request(
            request_id=request_id,
            owner=owner,
        )
    return user_request


@company_action_router.get("/all_members/{company_id}")
async def get_company_members(
    company_id: UUID,
    role: CompanyRole = None,
    page: int = 1,
    limit: int = Depends(get_companies_members_page_limit),
    db: AsyncSession = Depends(get_async_session),
) -> CompanyListMemberDetailResponseScheme:
    async with CompanyActionService(db) as service:
        members = await service.get_company_members(
            company_id=company_id,
            page=page,
            limit=limit,
            role=role,
        )
    return members


@company_action_router.get("/users_request")
async def get_company_users_request(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    status: CompanyRequestStatus = None,
    page: int = 1,
    limit: int = Depends(get_companies_users_request_page_limit),
    db: AsyncSession = Depends(get_async_session),
) -> CompanyRequestListDetailResponseScheme:
    async with CompanyActionService(db) as service:
        invitations = await service.get_company_users_request(
            company_id=company_id,
            owner=owner,
            status=status,
            page=page,
            limit=limit,
        )
    return invitations
