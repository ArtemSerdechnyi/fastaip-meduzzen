from datetime import datetime, timedelta
from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import CompanyMember, Quiz, UserQuiz


class UserQuizRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_quiz(self, **kwargs) -> UserQuiz:
        query = insert(UserQuiz).values(kwargs).returning(UserQuiz)
        result = await self.session.execute(query)
        user_quiz = result.scalar()
        return user_quiz

    async def get_nested_user_quiz(self, user_quiz_id: UUID) -> UserQuiz:
        query = (
            select(UserQuiz)
            .options(joinedload(UserQuiz.answers))
            .where(UserQuiz.user_quiz_id == user_quiz_id)
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def get_nested_user_quizzes_by_user_id(
        self, user_id: UUID
    ) -> Sequence[UserQuiz]:
        query = (
            select(UserQuiz)
            .options(joinedload(UserQuiz.answers))
            .where(
                and_(
                    UserQuiz.user_id == user_id,
                    UserQuiz.quiz_id == Quiz.quiz_id,
                    Quiz.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_nested_user_quizzes_by_member_id(
        self, member_id: UUID
    ) -> Sequence[UserQuiz]:
        query = (
            select(UserQuiz)
            .options(joinedload(UserQuiz.answers))
            .where(
                and_(
                    CompanyMember.member_id == member_id,
                    CompanyMember.user_id == UserQuiz.user_id,
                    UserQuiz.quiz_id == Quiz.quiz_id,
                    Quiz.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_nested_quizzes_by_company_id(
        self, company_id: UUID
    ) -> Sequence[UserQuiz]:
        query = (
            select(UserQuiz)
            .options(joinedload(UserQuiz.answers))
            .where(
                and_(
                    UserQuiz.quiz_id == Quiz.quiz_id,
                    Quiz.company_id == company_id,
                    Quiz.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_nested_quizzes_by_quiz_id(
        self, quiz_id: UUID
    ) -> Sequence[UserQuiz]:
        query = (
            select(UserQuiz)
            .options(joinedload(UserQuiz.answers))
            .where(
                and_(
                    UserQuiz.quiz_id == Quiz.quiz_id,
                    Quiz.quiz_id == quiz_id,
                    Quiz.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_sum_correct_answers_count_by_user(
        self, user_id: UUID, company_id: UUID = None
    ) -> int:
        query = select(func.sum(UserQuiz.correct_answers_count)).where(
            and_(
                UserQuiz.user_id == user_id,
                Quiz.quiz_id == UserQuiz.quiz_id,
                Quiz.is_active == True,
            )
        )
        if company_id is not None:
            query = query.where(
                Quiz.company_id == company_id,
            )
        result = await self.session.execute(query)
        result = result.scalar()
        return result

    async def get_sum_correct_answers_count_for_all(self) -> int:
        query = select(func.sum(UserQuiz.correct_answers_count))
        result = await self.session.execute(query)
        result = result.scalar()
        return result

    async def get_sum_total_questions_by_user(
        self, user_id: UUID, company_id: UUID = None
    ) -> int:
        query = select(func.sum(UserQuiz.total_questions)).where(
            and_(
                UserQuiz.user_id == user_id,
                Quiz.quiz_id == UserQuiz.quiz_id,
                Quiz.is_active == True,
            )
        )
        if company_id is not None:
            query = query.where(
                Quiz.company_id == company_id,
            )
        result = await self.session.execute(query)
        result = result.scalar()
        return result

    async def get_sum_total_questions_for_all(self) -> int:
        query = select(func.sum(UserQuiz.total_questions))
        result = await self.session.execute(query)
        result = result.scalar()
        return result

    async def get_statistic_for_each_quiz(
        self, from_date: datetime, to_date: datetime
    ) -> Sequence:
        to_date += timedelta(days=1)
        query = (
            select(
                UserQuiz.quiz_id,
                func.sum(UserQuiz.total_questions),
                func.sum(UserQuiz.correct_answers_count),
            )
            .where(
                and_(
                    UserQuiz.attempt_time >= from_date,
                    UserQuiz.attempt_time < to_date,
                )
            )
            .group_by(UserQuiz.quiz_id)
        )
        result = await self.session.execute(query)
        average_scores = result.fetchall()
        return average_scores

    async def get_last_passing_for_each_quiz(self) -> Sequence:
        query = select(
            UserQuiz.quiz_id,
            func.max(UserQuiz.attempt_time),
        ).group_by(UserQuiz.quiz_id)
        result = await self.session.execute(query)
        last_passing = result.fetchall()
        return last_passing

    async def get_statistic_for_each_member_quiz_by_company_id(
        self, company_id: UUID, from_date: datetime, to_date: datetime
    ) -> Sequence:
        to_date += timedelta(days=1)
        query = (
            select(
                CompanyMember.member_id,
                func.sum(UserQuiz.total_questions),
                func.sum(UserQuiz.correct_answers_count),
            )
            .where(
                and_(
                    CompanyMember.company_id == company_id,
                    CompanyMember.user_id == UserQuiz.user_id,
                    Quiz.company_id == company_id,
                    Quiz.quiz_id == UserQuiz.quiz_id,
                    UserQuiz.attempt_time >= from_date,
                    UserQuiz.attempt_time < to_date,
                )
            )
            .group_by(CompanyMember.member_id)
        )
        result = await self.session.execute(query)
        average_scores = result.fetchall()
        return average_scores

    async def get_statistic_for_each_quiz_for_company_member(
        self, member_id: UUID, from_date: datetime, to_date: datetime
    ) -> Sequence:
        to_date += timedelta(days=1)
        query = (
            select(
                UserQuiz.quiz_id,
                func.sum(UserQuiz.total_questions),
                func.sum(UserQuiz.correct_answers_count),
            )
            .where(
                and_(
                    CompanyMember.member_id == member_id,
                    CompanyMember.user_id == UserQuiz.user_id,
                    Quiz.company_id == CompanyMember.company_id,
                    Quiz.quiz_id == UserQuiz.quiz_id,
                    UserQuiz.attempt_time >= from_date,
                    UserQuiz.attempt_time < to_date,
                )
            )
            .group_by(UserQuiz.quiz_id)
        )
        result = await self.session.execute(query)
        average_scores = result.fetchall()
        return average_scores

    async def get_last_passing_for_each_member_quiz_by_company_id(
        self, company_id: UUID
    ) -> Sequence:
        query = (
            select(
                CompanyMember.member_id,
                func.max(UserQuiz.attempt_time),
            )
            .where(
                and_(
                    CompanyMember.company_id == company_id,
                    CompanyMember.user_id == UserQuiz.user_id,
                    Quiz.company_id == company_id,
                    Quiz.quiz_id == UserQuiz.quiz_id,
                )
            )
            .group_by(CompanyMember.member_id)
        )
        result = await self.session.execute(query)
        last_passing = result.fetchall()
        return last_passing
