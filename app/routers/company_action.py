from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.constants import COMPANIES_MEMBERS_PAGE_LIMIT, COMPANIES_USERS_REQUEST_PAGE_LIMIT
from app.db.models import CompanyRequestStatus, CompanyRole, User
from app.schemas.company_member import (
    CompanyMemberDetailResponseScheme,
    ListNestedCompanyMemberDetailResponseScheme,
)
from app.schemas.company_request import (
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user_request import UserRequestDetailResponseScheme
from app.services.auth import GenericAuthService
from app.services.company_action import CompanyActionService

from app.utils.services import get_company_action_service

company_action_router = APIRouter()


@company_action_router.post("/{company_id}/invite/{user_id}")
async def company_user_invite(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    user_id: UUID,
    company_id: UUID,
) -> CompanyRequestDetailResponseScheme:
    request = await service.create_company_request(
        user_id=user_id, company_id=company_id, owner=owner
    )
    return request


@company_action_router.delete("/{request_id}")
async def company_user_remove_invite(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    request_id: UUID,
) -> CompanyRequestDetailResponseScheme:
    request = await service.remove_company_request(
        request_id=request_id, owner=owner
    )
    return request


@company_action_router.delete("/{company_id}/user/{user_id}")
async def company_remove_user(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    user_id: UUID,
    company_id: UUID,
) -> CompanyMemberDetailResponseScheme:
    member = await service.remove_user_from_company(
        user_id=user_id, company_id=company_id, owner=owner
    )
    return member


@company_action_router.get("/confirm_user_request/{request_id}")
async def confirm_user_request(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    request_id: UUID,
) -> CompanyMemberDetailResponseScheme:
    user_request = await service.confirm_user_request(
        request_id=request_id, owner=owner
    )
    return user_request


@company_action_router.get("/deny_user_request/{request_id}")
async def deny_user_request(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    request_id: UUID,
) -> UserRequestDetailResponseScheme:
    user_request = await service.deny_user_request(
        request_id=request_id, owner=owner
    )
    return user_request


@company_action_router.get("/all_members/{company_id}")
async def get_company_members(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    company_id: UUID,
    role: CompanyRole = None,
    page: int = 1,
    limit: int = COMPANIES_MEMBERS_PAGE_LIMIT,
) -> ListNestedCompanyMemberDetailResponseScheme:
    members = await service.get_company_members(
        company_id=company_id,
        page=page,
        limit=limit,
        role=role,
    )
    return members


@company_action_router.get("/users_request")
async def get_company_users_request(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    status: CompanyRequestStatus = None,
    page: int = 1,
    limit: int = COMPANIES_USERS_REQUEST_PAGE_LIMIT,
) -> CompanyRequestListDetailResponseScheme:
    invitations = await service.get_company_users_request(
        company_id=company_id,
        owner=owner,
        status=status,
        page=page,
        limit=limit,
    )
    return invitations


@company_action_router.patch("/{company_id}/appoint/{user_id}")
async def appoint_administrator(
    service: Annotated[
        CompanyActionService, Depends(get_company_action_service)
    ],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    user_id: UUID,
) -> CompanyMemberDetailResponseScheme:
    member = await service.appoint_administrator(
        company_id=company_id,
        user_id=user_id,
        owner=owner,
    )
    return member
