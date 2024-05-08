import json
from io import StringIO
from uuid import UUID

import pandas as pd

from app.core.constants import USER_QUIZ_ANSWERS_EXPIRE_TIME
from app.db.models import User
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.quiz import QuizRepository
from app.repositories.user_quiz import UserQuizRepository
from app.repositories.user_quiz_answers import UserQuizAnswersRepository
from app.schemas.quiz import QuizDetailScheme
from app.schemas.user_quiz import (
    ListUserQuizDetailScheme,
    UserQuizAverageScoreScheme,
    UserQuizCreateScheme,
    UserQuizDetailScheme,
)
from app.services.base import Service
from app.services.redis import RedisService
from app.utils.generics import ResponseFileType
from app.utils.validators.quiz import QuizAnswerValidator


class UserQuizService(Service):
    validator = QuizAnswerValidator()

    def __init__(self, session):
        self.company_member_repo = CompanyMemberRepository(session)
        self.quiz_repo = QuizRepository(session)
        self.user_quiz_repo = UserQuizRepository(session)
        self.user_quiz_answers_repo = UserQuizAnswersRepository(session)
        self.redis = RedisService()
        super().__init__(session)

    @staticmethod
    async def _get_quiz_question_count(quiz: QuizDetailScheme) -> int:
        return len(quiz.questions)

    @staticmethod
    async def _get_quiz_correct_answers_count(
        quiz: QuizDetailScheme, user_quiz: UserQuizCreateScheme
    ) -> int:
        quiz_sorted_questions = sorted(
            quiz.questions, key=lambda q: q.question_id
        )
        user_quiz_sorted_questions = sorted(
            user_quiz.questions, key=lambda q: q.question_id
        )

        count = 0
        for question, user_question in zip(
            quiz_sorted_questions, user_quiz_sorted_questions
        ):
            correct_answers_ids = {
                a.answer_id for a in question.answers if a.is_correct
            }
            user_answers_ids = {a.answer_id for a in user_question.answers}
            if correct_answers_ids == user_answers_ids:
                count += 1

        return count

    @staticmethod
    def _export_user_quizzes_to_json(scheme: ListUserQuizDetailScheme) -> str:
        json_dump = scheme.model_dump_json(exclude_unset=True)
        return json_dump

    @staticmethod
    def _export_user_quizzes_to_csv(scheme: ListUserQuizDetailScheme) -> str:
        json_dump = scheme.model_dump_json(exclude_unset=True)
        json_data = json.loads(json_dump)
        normalize_data = pd.json_normalize(
            json_data["user_quizzes"],
            record_path=["answers"],
            meta=[
                "user_id",
                "quiz_id",
                "correct_answers_count",
                "total_questions",
                "attempt_time",
            ],
        )
        string = StringIO()
        normalize_data.to_csv(string, index=False)
        return string.getvalue()

    @staticmethod
    def get_media_type(file_type: ResponseFileType) -> str:
        match file_type:
            case "json":
                return "application/json"
            case "csv":
                return "text/csv"
            case _:
                raise ValueError(f"Invalid file type: {file_type}")

    def export_user_quizzes(
        self, scheme: ListUserQuizDetailScheme, file_type: ResponseFileType
    ) -> str:
        match file_type:
            case "json":
                return self._export_user_quizzes_to_json(scheme=scheme)
            case "csv":
                return self._export_user_quizzes_to_csv(scheme=scheme)
            case _:
                raise ValueError(f"Invalid file type: {file_type}")

    @validator.validate_quiz_exist_and_active_by_quiz_id
    @validator.validate_user_is_company_member_or_owner_by_quiz_id
    @validator.validate_question_count_matches
    @validator.validate_all_questions_matches_to_quiz
    @validator.validate_all_answers_matches_to_question
    async def record_user_quiz(
        self, scheme: UserQuizCreateScheme, quiz_id: UUID, user: User
    ) -> UserQuizDetailScheme:
        raw_nested_quiz = await self.quiz_repo.get_nested_quiz(quiz_id=quiz_id)
        nested_quiz = QuizDetailScheme.from_orm(raw_nested_quiz)
        question_count = await self._get_quiz_question_count(quiz=nested_quiz)
        correct_answer_count = await self._get_quiz_correct_answers_count(
            quiz=nested_quiz, user_quiz=scheme
        )

        raw_user_quiz = await self.user_quiz_repo.create_user_quiz(
            quiz_id=quiz_id,
            user_id=user.user_id,
            correct_answers_count=correct_answer_count,
            total_questions=question_count,
        )
        user_quiz_id = raw_user_quiz.user_quiz_id
        for question in scheme.questions:
            question_id = question.question_id
            for answer in question.answers:
                answer_id = answer.answer_id
                await self.user_quiz_answers_repo.create_user_quiz_answer(
                    user_quiz_id=user_quiz_id,
                    question_id=question_id,
                    answer_id=answer_id,
                )

        raw_nested_user_quiz = await self.user_quiz_repo.get_nested_user_quiz(
            user_quiz_id=user_quiz_id
        )
        user_quiz = UserQuizDetailScheme.from_orm(raw_nested_user_quiz)

        # add to redis
        await self.redis.set_value(
            key=user_quiz.user_quiz_id,
            value=user_quiz.model_dump_json(exclude_unset=True),
            expire=USER_QUIZ_ANSWERS_EXPIRE_TIME,
        )
        return user_quiz

    @validator.validate_user_quiz_is_exist_by_user_quiz_id
    async def get_user_quiz(self, user_quiz_id: UUID):
        if cache := await self.redis.get_value(user_quiz_id):
            return UserQuizDetailScheme.parse_raw(cache)

        raw_nested_user_quiz = await self.user_quiz_repo.get_nested_user_quiz(
            user_quiz_id=user_quiz_id
        )
        return UserQuizDetailScheme.from_orm(raw_nested_user_quiz)

    @validator.validate_company_member_user_quiz_exist
    async def average_company_member_score(self, company_member_id: UUID):
        member = await self.company_member_repo.get_member_by_attributes(
            member_id=company_member_id
        )
        correct_answers_sum = (
            await self.user_quiz_repo.get_sum_correct_answers_count_by_user(
                user_id=member.user_id, company_id=member.company_id
            )
        )

        question_count_sum = (
            await self.user_quiz_repo.get_sum_total_questions_by_user(
                user_id=member.user_id, company_id=member.company_id
            )
        )
        score = correct_answers_sum / question_count_sum
        return UserQuizAverageScoreScheme(average_score=score)

    @validator.validate_user_has_user_quiz
    async def average_user_score(self, user_id: UUID):
        correct_answers_sum = (
            await self.user_quiz_repo.get_sum_correct_answers_count_by_user(
                user_id=user_id,
            )
        )

        question_count_sum = (
            await self.user_quiz_repo.get_sum_total_questions_by_user(
                user_id=user_id,
            )
        )
        score = correct_answers_sum / question_count_sum
        return UserQuizAverageScoreScheme(average_score=score)

    async def get_all_user_quizzes(
        self, user: User
    ) -> ListUserQuizDetailScheme:
        if cache := await self.redis.get_value(f"user_answers:{user.user_id}"):
            return ListUserQuizDetailScheme.parse_raw(cache)

        raw_nested_user_quizzes = (
            await self.user_quiz_repo.get_nested_user_quizzes_by_user_id(
                user_id=user.user_id
            )
        )
        list_user_quizzes = [
            UserQuizDetailScheme.from_orm(uq) for uq in raw_nested_user_quizzes
        ]
        user_quizzes = ListUserQuizDetailScheme(user_quizzes=list_user_quizzes)

        # add to redis
        await self.redis.set_value(
            key=f"user_answers:{user.user_id}",
            value=user_quizzes.model_dump_json(exclude_unset=True),
            expire=USER_QUIZ_ANSWERS_EXPIRE_TIME,
        )

        return user_quizzes

    @validator.validate_user_is_owner_or_admin_by_company_member_id
    async def get_company_member_quizzes(
        self, member_id: UUID, user: User
    ) -> ListUserQuizDetailScheme:
        if cache := await self.redis.get_value(f"member_answers:{member_id}"):
            return ListUserQuizDetailScheme.parse_raw(cache)

        raw_nested_user_quizzes = (
            await self.user_quiz_repo.get_nested_user_quizzes_by_member_id(
                member_id=member_id,
            )
        )
        list_user_quizzes = [
            UserQuizDetailScheme.from_orm(uq) for uq in raw_nested_user_quizzes
        ]
        user_quizzes = ListUserQuizDetailScheme(user_quizzes=list_user_quizzes)

        # add to redis
        await self.redis.set_value(
            key=f"member_answers:{member_id}",
            value=user_quizzes.model_dump_json(exclude_unset=True),
            expire=USER_QUIZ_ANSWERS_EXPIRE_TIME,
        )
        return user_quizzes

    @validator.validate_exist_company_is_active
    @validator.validate_user_is_owner_or_admin_by_company_id
    async def get_all_company_members_quizzes(
        self, company_id: UUID, user: User
    ) -> ListUserQuizDetailScheme:
        if cache := await self.redis.get_value(
            f"members_answers:{company_id}"
        ):
            return ListUserQuizDetailScheme.parse_raw(cache)

        raw_nested_user_quizzes = (
            await self.user_quiz_repo.get_nested_quizzes_by_company_id(
                company_id=company_id
            )
        )
        list_user_quizzes = [
            UserQuizDetailScheme.from_orm(uq) for uq in raw_nested_user_quizzes
        ]
        user_quizzes = ListUserQuizDetailScheme(user_quizzes=list_user_quizzes)

        # add to redis
        await self.redis.set_value(
            key=f"members_answers:{company_id}",
            value=user_quizzes.model_dump_json(exclude_unset=True),
            expire=USER_QUIZ_ANSWERS_EXPIRE_TIME,
        )
        return user_quizzes

    @validator.validate_quiz_exist_and_active_by_quiz_id
    @validator.validate_user_is_company_member_or_owner_by_quiz_id
    async def get_all_quiz_answers(
        self, quiz_id: UUID, user: User
    ) -> ListUserQuizDetailScheme:
        if cache := await self.redis.get_value(f"quiz_answers:{quiz_id}"):
            return ListUserQuizDetailScheme.parse_raw(cache)

        raw_nested_user_quizzes = (
            await self.user_quiz_repo.get_nested_quizzes_by_quiz_id(
                quiz_id=quiz_id,
            )
        )
        list_user_quizzes = [
            UserQuizDetailScheme.from_orm(uq) for uq in raw_nested_user_quizzes
        ]
        user_quizzes = ListUserQuizDetailScheme(user_quizzes=list_user_quizzes)

        # add to redis
        await self.redis.set_value(
            key=f"quiz_answers:{quiz_id}",
            value=user_quizzes.model_dump_json(exclude_unset=True),
            expire=USER_QUIZ_ANSWERS_EXPIRE_TIME,
        )
        return user_quizzes
