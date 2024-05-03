from uuid import UUID

from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Answer
from app.schemas.quiz import AnswerCreateScheme


class AnswerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_answer(
        self, answer: AnswerCreateScheme, question_id: UUID
    ) -> Answer:
        answer_data = answer.model_dump(exclude_unset=True)
        query = (
            insert(Answer)
            .values(question_id=question_id, **answer_data)
            .returning(Answer)
        )
        result = await self.session.execute(query)
        answer = result.scalar()
        return answer

    async def create_answers(
        self, answers: list[AnswerCreateScheme], question_id: UUID
    ) -> list[Answer]:
        answer_list = []
        for answer in answers:
            answer_data = answer.model_dump(exclude_unset=True)
            query = (
                insert(Answer)
                .values(question_id=question_id, **answer_data)
                .returning(Answer)
            )
            result = await self.session.execute(query)
            answer = result.scalar()
            answer_list.append(answer)
        return answer_list

    async def delete_answer(self, answer_id: UUID):
        query = (
            delete(Answer)
            .where(Answer.answer_id == answer_id)
            .returning(Answer)
        )
        result = await self.session.execute(query)
        question = result.scalar()
        return question
