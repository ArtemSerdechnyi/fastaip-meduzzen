from datetime import datetime, timedelta
from typing import Annotated, Optional
from uuid import UUID
from dateutil import relativedelta

from fastapi import APIRouter, Depends, Query

from app.schemas.analytics import UserQuizAverageScoreScheme
from app.services.user_quiz import UserQuizService
from app.utils.services import get_user_quiz_service
from app.utils.generics import FromDate, ToDate

quiz_analytics_router = APIRouter()


@quiz_analytics_router.get("/global_average_score")
async def get_average_for_all_companies_all_quizzes(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
) -> UserQuizAverageScoreScheme:
    score = await service.get_average_score_for_all_quizzes()
    return score


@quiz_analytics_router.get("/average_score_for_each_quiz")
async def get_average_score_for_each_quiz(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    from_date: FromDate,
    to_date: ToDate,
):
    # score = await service.get_average_score_for_each_quiz()
    return from_date, to_date
