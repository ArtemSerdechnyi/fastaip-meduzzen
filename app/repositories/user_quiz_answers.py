from select import select
from uuid import UUID

from sqlalchemy import insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserQuizAnswers


class UserQuizAnswersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user_quiz_answer(
        self, user_quiz_id: UUID, question_id: UUID, answer_id: UUID
    ) -> UserQuizAnswers:
        query = (
            insert(UserQuizAnswers)
            .values(
                user_quiz_id=user_quiz_id,
                question_id=question_id,
                answer_id=answer_id,
            )
            .returning(UserQuizAnswers)
        )
        result = await self.session.execute(query)
        user_quiz_answer = result.scalar()
        return user_quiz_answer
