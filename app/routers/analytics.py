from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.db.models import User
from app.schemas.analytics import (
    AverageScoreScheme,
    ListCompanyMemberUserQuizAverageScoreScheme,
    ListUserQuizAverageScoreScheme,
    ListUserQuizLastPassingScheme,
)
from app.services.auth import GenericAuthService
from app.services.user_quiz import UserQuizService
from app.utils.generics import FromDate, ToDate
from app.utils.services import get_user_quiz_service

quiz_analytics_router = APIRouter()


@quiz_analytics_router.get("/global_average_score")
async def get_average_for_all_companies_all_quizzes(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
) -> AverageScoreScheme:
    score = await service.get_average_score_for_all_quizzes()
    return score


@quiz_analytics_router.get("/average_score_for_each_quiz")
async def get_average_score_for_each_quiz(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    from_date: FromDate,
    to_date: ToDate,
) -> ListUserQuizAverageScoreScheme:
    quizzes = await service.get_average_score_for_each_quiz(
        from_date=from_date, to_date=to_date
    )
    return quizzes


@quiz_analytics_router.get("/last_passing_time_for_each_quiz")
async def get_last_passing_time_for_each_quiz(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
) -> ListUserQuizLastPassingScheme:
    quizzes = await service.get_last_passing_time_for_each_quiz()
    return quizzes


@quiz_analytics_router.get(
    "/average_score_for_each_company_member/{company_id}"
)
async def get_company_average_score_for_each_member(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    company_id: UUID,
    from_date: FromDate,
    to_date: ToDate,
) -> ListCompanyMemberUserQuizAverageScoreScheme:
    quizzes = await service.get_company_average_score_for_each_member(
        company_id=company_id, from_date=from_date, to_date=to_date, user=user
    )
    return quizzes


@quiz_analytics_router.get("/average_score_for_each_member_quiz/{member_id}")
async def get_average_score_for_each_quiz_by_company_member(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    member_id: UUID,
    from_date: FromDate,
    to_date: ToDate,
) -> ListUserQuizAverageScoreScheme:
    quizzes = await service.get_average_score_for_each_quiz_by_company_member(
        member_id=member_id, from_date=from_date, to_date=to_date, user=user
    )
    return quizzes


@quiz_analytics_router.get(
    "/company_members_with_last_pass_quiz_time/{company_id}"
)
async def get_company_members_with_last_pass_quiz_time(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    company_id: UUID,
):
    members = await service.get_company_members_with_last_pass_quiz_time(
        company_id=company_id, user=user
    )
    return members
