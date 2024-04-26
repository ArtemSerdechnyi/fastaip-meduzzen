from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.postgres import get_async_session
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyListResponseScheme,
    CompanyUpdateRequestScheme,
    UserCompanyDetailResponseScheme,
)
from app.services.company import CompanyService
from app.services.user import GenericAuthService
from app.utils.company import get_companies_page_limit

company_router = APIRouter()


@company_router.post("/", status_code=201)
async def create_company(
    body: CompanyCreateRequestScheme,
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    db: AsyncSession = Depends(get_async_session),
):
    async with CompanyService(db) as service:
        new_company_id = await service.create_company(
            owner=owner,
            scheme=body,
        )
    return {
        "status_code": 201,
        "company_id": new_company_id,
    }


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
    company_id: UUID,
    body: CompanyUpdateRequestScheme,
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
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
    company_id: UUID,
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    db: AsyncSession = Depends(get_async_session),
):
    async with CompanyService(db) as service:
        await service.delete_self_company(company_id, owner)
    return {"status_code": 204, "detail": "Company deleted"}


@company_router.get("/all/{page}", response_model=CompanyListResponseScheme)
async def list_companies(
    page: int,
    db: AsyncSession = Depends(get_async_session),
    limit: int = Depends(get_companies_page_limit),
) -> CompanyListResponseScheme:
    async with CompanyService(db) as service:
        companies = await service.get_all_companies(page, limit)
    return companies


@company_router.get("/my/{page}", response_model=CompanyListResponseScheme)
async def my_companies(
    page: int,
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    db: AsyncSession = Depends(get_async_session),
    limit: int = Depends(get_companies_page_limit),
) -> CompanyListResponseScheme:
    async with CompanyService(db) as service:
        companies = await service.get_user_self_companies(
            page=page,
            limit=limit,
            user=owner,
        )
    return companies


@company_router.patch(
    "/visibility/{company_id}", response_model=UserCompanyDetailResponseScheme
)
async def my_companies(
    company_id: UUID,
    owner: Annotated[
        User, Depends(GenericAuthService.get_user_from_any_token)
    ],
    db: AsyncSession = Depends(get_async_session),
) -> UserCompanyDetailResponseScheme:
    async with CompanyService(db) as service:
        updated_company = await service.change_user_self_company_visibility(
            company_id=company_id,
            user=owner,
        )
    return updated_company
