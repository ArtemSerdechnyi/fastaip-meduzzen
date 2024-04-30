from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, CompanyRequestStatus, CompanyRole
from app.db.postgres import get_async_session
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyListResponseScheme,
    CompanyUpdateRequestScheme,
    OwnerCompanyDetailResponseScheme,
    CompanyRequestDetailResponseScheme,
    CompanyMemberDetailResponseScheme,
    CompanyListMemberDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user import UserRequestDetailResponseScheme
from app.services.company import CompanyService
from app.services.user import GenericAuthService
from app.utils.company import (
    get_companies_page_limit,
    get_companies_members_page_limit,
    get_companies_users_request_page_limit,
)

company_router = APIRouter()
company_action_router = APIRouter()


@company_router.post("/", status_code=201)
async def create_company(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    body: CompanyCreateRequestScheme,
    db: AsyncSession = Depends(get_async_session),
):
    async with CompanyService(db) as service:
        new_company = await service.create_company(
            owner=owner,
            scheme=body,
        )
    return new_company


@company_router.get("/all", response_model=CompanyListResponseScheme)
async def list_companies(
    page: int = 1,
    db: AsyncSession = Depends(get_async_session),
    limit: int = Depends(get_companies_page_limit),
) -> CompanyListResponseScheme:
    async with CompanyService(db) as service:
        companies = await service.get_all_companies(page, limit)
    return companies


@company_router.get("/my_all", response_model=CompanyListResponseScheme)
async def my_companies(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    page: int = 1,
    limit: int = Depends(get_companies_page_limit),
    db: AsyncSession = Depends(get_async_session),
) -> CompanyListResponseScheme:
    async with CompanyService(db) as service:
        companies = await service.get_user_self_companies(
            page=page,
            limit=limit,
            user=owner,
        )
    return companies


@company_router.patch(
    "/visibility/", response_model=OwnerCompanyDetailResponseScheme
)
async def my_companies(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> OwnerCompanyDetailResponseScheme:
    async with CompanyService(db) as service:
        updated_company = await service.change_user_self_company_visibility(
            company_id=company_id,
            user=owner,
        )
    return updated_company


@company_router.get(
    "/{company_id}", response_model=CompanyDetailResponseScheme
)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> CompanyDetailResponseScheme:
    async with CompanyService(db) as service:
        company = await service.get_company_by_attributes(
            company_id=company_id
        )
    return company


@company_router.patch(
    "/{company_id}", response_model=CompanyDetailResponseScheme
)
async def update_company(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    body: CompanyUpdateRequestScheme,
    db: AsyncSession = Depends(get_async_session),
) -> CompanyDetailResponseScheme:
    async with CompanyService(db) as service:
        updated_company = await service.update_user_self_company(
            company_id=company_id,
            user=owner,
            scheme=body,
        )
    return updated_company


@company_router.delete("/{company_id}", status_code=204)
async def delete_company(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    async with CompanyService(db) as service:
        await service.delete_self_company(company_id=company_id, owner=owner)
    return {"status_code": 204, "detail": "Company deleted"}


# company actions routers


@company_action_router.post("/{company_id}/invite/{user_id}")
async def company_user_invite(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    user_id: UUID,
    company_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> CompanyRequestDetailResponseScheme:
    async with CompanyService(db) as service:
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
    async with CompanyService(db) as service:
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
    async with CompanyService(db) as service:
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
    async with CompanyService(db) as service:
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
    async with CompanyService(db) as service:
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
    async with CompanyService(db) as service:
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
    async with CompanyService(db) as service:
        invitations = await service.get_company_users_request(
            company_id=company_id,
            owner=owner,
            status=status,
            page=page,
            limit=limit,
        )
    return invitations
