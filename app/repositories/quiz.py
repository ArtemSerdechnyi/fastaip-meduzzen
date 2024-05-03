from uuid import UUID

from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Answer, Question, Quiz


class QuizRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_nested_quiz(self, quiz_id: UUID) -> Quiz:
        query = (
            select(Quiz)
            .options(joinedload(Quiz.questions).joinedload(Question.answers))
            .where(and_(Quiz.quiz_id == quiz_id, Quiz.is_active == True))
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def get_all_company_nested_quizzes(
        self, company_id: UUID, page: int, limit: int
    ):
        query = (
            select(Quiz, Question, Answer)
            .options(joinedload(Quiz.questions).joinedload(Question.answers))
            .where(and_(Quiz.company_id == company_id, Quiz.is_active == True))
        )
        query = query.limit(limit).offset(
            page - 1 if page == 1 else (page - 1) * limit
        )
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def create_quiz(
        self, company_id: UUID, name: str, description: str
    ) -> Quiz:
        query = (
            insert(Quiz)
            .values(company_id=company_id, name=name, description=description)
            .returning(Quiz)
        )

        result = await self.session.execute(query)
        quiz = result.scalar()
        return quiz

    async def update_quiz(self, quiz_id: UUID, **kwargs) -> Quiz:
        query = (
            update(Quiz)
            .where(and_(Quiz.quiz_id == quiz_id, Quiz.is_active == True))
            .values(kwargs)
            .returning(Quiz)
        )
        result = await self.session.execute(query)
        return result.scalar()
