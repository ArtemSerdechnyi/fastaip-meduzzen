from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.constants import COMPANIES_PAGE_LIMIT
from app.db.models import User
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyListResponseScheme,
    CompanyUpdateRequestScheme,
)
from app.services.auth import GenericAuthService
from app.services.company import CompanyService

from app.utils.services import get_company_service

company_router = APIRouter()


@company_router.post("/", status_code=201)
async def create_company(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    body: CompanyCreateRequestScheme,
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyDetailResponseScheme:
    new_company = await service.create_company(owner=owner, scheme=body)
    return new_company


@company_router.get("/all")
async def list_companies(
    service: Annotated[CompanyService, Depends(get_company_service)],
    page: int = 1,
    limit: int = COMPANIES_PAGE_LIMIT,
) -> CompanyListResponseScheme:
    companies = await service.get_all_companies(page=page, limit=limit)
    return companies


@company_router.get("/my_all")
async def my_companies(
    service: Annotated[CompanyService, Depends(get_company_service)],
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    page: int = 1,
    limit: int =COMPANIES_PAGE_LIMIT,
) -> CompanyListResponseScheme:
    companies = await service.get_user_self_companies(
        page=page, limit=limit, user=owner
    )
    return companies


@company_router.patch("/visibility/")
async def change_visibility(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyDetailResponseScheme:
    updated_company = await service.change_user_self_company_visibility(
        company_id=company_id, user=owner
    )
    return updated_company


@company_router.get("/{company_id}")
async def get_company(
    company_id: UUID,
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyDetailResponseScheme:
    company = await service.get_company_by_id(company_id=company_id)
    return company


@company_router.patch("/{company_id}")
async def update_company(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    body: CompanyUpdateRequestScheme,
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyDetailResponseScheme:
    updated_company = await service.update_user_self_company(
        company_id=company_id, user=owner, scheme=body
    )
    return updated_company


@company_router.delete("/{company_id}")
async def delete_company(
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    company_id: UUID,
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyDetailResponseScheme:
    company = await service.delete_self_company(
        company_id=company_id, user=owner
    )
    return company
