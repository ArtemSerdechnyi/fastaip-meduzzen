from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.models import User
from app.schemas.company_member import CompanyMemberDetailResponseScheme
from app.schemas.company_request import (
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user_request import (
    UserRequestDetailResponseScheme,
    UserRequestListDetailResponseScheme,
)
from app.services.auth import GenericAuthService
from app.services.user_action import UserActionService
from app.utils.services import get_user_action_service
from app.utils.user import get_users_page_limit

user_action_router = APIRouter()


@user_action_router.post("/requests/{company_id}")
async def send_join_request(
    service: Annotated[UserActionService, Depends(get_user_action_service)],
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    company_id: UUID,
) -> UserRequestDetailResponseScheme:
    request = await service.create_user_request(
        company_id=company_id, user=user
    )
    return request


@user_action_router.delete("/requests/{request_id}")
async def cancel_join_request(
    request_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserActionService, Depends(get_user_action_service)],
) -> UserRequestDetailResponseScheme:
    request = await service.cancel_user_request(
        request_id=request_id, user=user
    )
    return request


@user_action_router.get("/requests")
async def list_user_requests(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserActionService, Depends(get_user_action_service)],
    page: int = 1,
    limit: int = Depends(get_users_page_limit),
) -> UserRequestListDetailResponseScheme:
    requests = await service.list_user_requests(
        user=user, page=page, limit=limit
    )
    return requests


@user_action_router.get("/invitations")
async def list_user_invitations(
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserActionService, Depends(get_user_action_service)],
    page: int = 1,
    limit: int = Depends(get_users_page_limit),
) -> CompanyRequestListDetailResponseScheme:
    invitations = await service.list_company_requests_for_user(
        user=user, page=page, limit=limit
    )
    return invitations


@user_action_router.post("/accept/{request_id}")
async def accept_invite(
    request_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserActionService, Depends(get_user_action_service)],
) -> CompanyMemberDetailResponseScheme:
    request = await service.accept_company_request(
        request_id=request_id, user=user
    )
    return request


@user_action_router.post("/reject/{request_id}")
async def reject_invite(
    request_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserActionService, Depends(get_user_action_service)],
) -> CompanyRequestDetailResponseScheme:
    request = await service.reject_invitation(request_id=request_id, user=user)
    return request


@user_action_router.delete("/leave/{company_id}")
async def leave_company(
    company_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    service: Annotated[UserActionService, Depends(get_user_action_service)],
) -> CompanyMemberDetailResponseScheme:
    member = await service.leave_company(company_id=company_id, user=user)
    return member
