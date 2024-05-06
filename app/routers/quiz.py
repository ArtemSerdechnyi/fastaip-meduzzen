from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.constants import QUIZ_PAGE_LIMIT
from app.db.models import User
from app.schemas.quiz import (
    AnswerCreateScheme,
    AnswerDetailScheme,
    ListQuizDetailScheme,
    QuestionCreateScheme,
    QuestionDetailScheme,
    QuizCreateRequestScheme,
    QuizDetailScheme,
)
from app.schemas.user_quiz import UserQuizCreateScheme, UserQuizDetailScheme
from app.services.auth import GenericAuthService
from app.services.quiz import QuizService
from app.services.user_quiz import UserQuizService
from app.utils.services import get_quiz_service, get_user_quiz_service

quiz_router = APIRouter()
user_quiz_router = APIRouter()


@quiz_router.post("/{company_id}")
async def create_quiz(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    body: QuizCreateRequestScheme,
    company_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> QuizDetailScheme:
    quiz = await service.create_quiz(
        scheme=body,
        company_id=company_id,
        user=user,
    )
    return quiz


@quiz_router.get("/all/{company_id}")
async def get_all_company_quizzes(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    company_id: UUID,
    page: int = 1,
    limit: int = QUIZ_PAGE_LIMIT,
) -> ListQuizDetailScheme:
    quiz = await service.get_all_company_quizzes(
        company_id=company_id, page=page, limit=limit
    )
    return quiz


@quiz_router.get("/{quiz_id}")
async def get_quiz(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    quiz_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> QuizDetailScheme:
    quiz = await service.get_quiz(quiz_id=quiz_id, user=user)
    return quiz


@quiz_router.delete("/{quiz_id}")
async def get_quiz(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    quiz_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> QuizDetailScheme:
    quiz = await service.delete_quiz(quiz_id=quiz_id, user=user)
    return quiz


@quiz_router.post("/add_question/{quiz_id}")
async def add_question(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    quiz_id: UUID,
    body: QuestionCreateScheme,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> QuestionDetailScheme:
    question = await service.add_question(
        scheme=body, quiz_id=quiz_id, user=user
    )
    return question


@quiz_router.delete("/delete_question/{question_id}")
async def delete_question(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    question_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> QuestionDetailScheme:
    question = await service.delete_question(
        question_id=question_id, user=user
    )
    return question


@quiz_router.post("/add_answer/{question_id}")
async def add_answer(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    question_id: UUID,
    body: AnswerCreateScheme,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> AnswerDetailScheme:
    answer = await service.add_answer(
        scheme=body, question_id=question_id, user=user
    )
    return answer


@quiz_router.delete("/delete_answer/{answer_id}")
async def delete_answer(
    service: Annotated[QuizService, Depends(get_quiz_service)],
    answer_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
) -> AnswerDetailScheme:
    answer = await service.delete_answer(answer_id=answer_id, user=user)
    return answer


# user quiz routers


@user_quiz_router.post("/take/{quiz_id}")
async def take_quiz(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    quiz_id: UUID,
    user: Annotated[User, Depends(GenericAuthService.get_user_from_any_token)],
    body: UserQuizCreateScheme,
) -> UserQuizDetailScheme:
    user_quiz = await service.record_user_quiz(
        scheme=body, quiz_id=quiz_id, user=user
    )
    return user_quiz


@user_quiz_router.get("/member/average/{company_member_id}")
async def average_member_score(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    company_member_id: UUID,
) -> float:
    average_score = await service.average_company_member_score(
        company_member_id=company_member_id
    )
    return average_score


@user_quiz_router.get("/average/{user_id}")
async def average_user_score(
    service: Annotated[UserQuizService, Depends(get_user_quiz_service)],
    user_id: UUID,
) -> float:
    average_score = await service.average_user_score(user_id=user_id)
    return average_score
