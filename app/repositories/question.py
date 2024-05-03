from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Question
from app.schemas.quiz import QuestionCreateScheme


class QuestionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def creat_question(
        self, question: QuestionCreateScheme, quiz_id: UUID
    ) -> Question:
        question_data = question.model_dump(exclude_unset=True)
        query = (
            insert(Question)
            .values(quiz_id=quiz_id, **question_data)
            .returning(Question)
        )
        result = await self.session.execute(query)
        question = result.scalar()
        return question

    async def create_questions(
        self, questions: list[QuestionCreateScheme], quiz_id: UUID
    ) -> list[Question]:
        question_list = []
        for question in questions:
            question_data = question.model_dump(exclude_unset=True)
            query = (
                insert(Question)
                .values(quiz_id=quiz_id, **question_data)
                .returning(Question)
            )
            result = await self.session.execute(query)

            question = result.scalar()
            question_list.append(question)
        return question_list

    async def get_nested_question(self, question_id: UUID) -> Question:
        query = (
            select(Question)
            .options(joinedload(Question.answers))
            .where(Question.question_id == question_id)
        )
        result = await self.session.execute(query)
        question = result.scalar()
        return question

    async def delete_question(self, question_id: UUID) -> None:
        query = (
            delete(Question)
            .where(Question.question_id == question_id)
            .returning(Question)
        )
        result = await self.session.execute(query)
        question = result.scalar()
        return question
