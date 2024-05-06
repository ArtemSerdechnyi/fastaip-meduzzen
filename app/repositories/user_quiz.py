from uuid import UUID

from sqlalchemy import and_, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Quiz, UserQuiz


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
