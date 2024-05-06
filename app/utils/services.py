from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_async_session
from app.services.company import CompanyService
from app.services.company_action import CompanyActionService
from app.services.quiz import QuizService
from app.services.user import UserService
from app.services.user_action import UserActionService
from app.services.user_quiz import UserQuizService


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


async def get_quiz_service(db: AsyncSession = Depends(get_async_session)):
    async with QuizService(session=db) as service:
        yield service


async def get_user_quiz_service(db: AsyncSession = Depends(get_async_session)):
    async with UserQuizService(session=db) as service:
        yield service
