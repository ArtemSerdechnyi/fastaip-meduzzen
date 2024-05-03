from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_async_session
from app.services.company import CompanyService
from app.services.user import UserService
from app.services.user_action import UserActionService
from app.services.company_action import CompanyActionService


async def get_user_service(db: AsyncSession = Depends(get_async_session)):
    async with UserService(session=db) as service:
        yield service


async def get_company_service(db: AsyncSession = Depends(get_async_session)):
    async with CompanyService(session=db) as service:
        yield service


async def get_user_action_service(
    db: AsyncSession = Depends(get_async_session),
):
    async with UserActionService(session=db) as service:
        yield service


async def get_company_action_service(
    db: AsyncSession = Depends(get_async_session),
):
    async with CompanyActionService(session=db) as service:
        yield service
