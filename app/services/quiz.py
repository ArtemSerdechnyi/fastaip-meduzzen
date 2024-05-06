from uuid import UUID

from app.db.models import User, Quiz, Question, Answer
from app.repositories.answer import AnswerRepository
from app.repositories.question import QuestionRepository
from app.repositories.quiz import QuizRepository
from app.repositories.user_quiz import UserQuizRepository
from app.repositories.user_quiz_answers import UserQuizAnswersRepository
from app.schemas.quiz import (
    AnswerCreateScheme,
    AnswerDetailScheme,
    ListQuizDetailScheme,
    QuestionCreateScheme,
    QuestionDetailScheme,
    QuizCreateRequestScheme,
    QuizDetailScheme,
)
from app.schemas.user_quiz import UserQuizCreateScheme
from app.services.base import Service
from app.utils.validators.quiz import QuizCreateValidator


class QuizService(Service):
    validator = QuizCreateValidator()

    def __init__(self, session):
        self.quiz_repository = QuizRepository(session)
        self.question_repository = QuestionRepository(session)
        self.answer_repository = AnswerRepository(session)
        super().__init__(session)

    # @validator.validate_quiz_company_and_name_unique
    @validator.validate_exist_company_is_active
    @validator.validate_user_is_owner_or_admin_by_company_id
    async def create_quiz(
        self, scheme: QuizCreateRequestScheme, company_id: UUID, user: User
    ) -> QuizDetailScheme:
        raw_quiz = await self.quiz_repository.create_quiz(
            company_id=company_id,
            name=scheme.name,
            description=scheme.description,
        )
        raw_questions = await self.question_repository.create_questions(
            questions=scheme.questions, quiz_id=raw_quiz.quiz_id
        )
        for input_question, raw_question in zip(
            scheme.questions, raw_questions
        ):
            question_id: UUID = raw_question.question_id
            answers: list[AnswerCreateScheme] = input_question.answers
            raw_answers = await self.answer_repository.create_answers(
                answers=answers, question_id=question_id
            )
        nested_quiz = await self.quiz_repository.get_nested_quiz(
            quiz_id=raw_quiz.quiz_id
        )
        return QuizDetailScheme.from_orm(nested_quiz)

    async def get_all_company_quizzes(
        self, company_id: UUID, page: int, limit: int
    ):
        raw_quizzes = (
            await self.quiz_repository.get_all_company_nested_quizzes(
                company_id=company_id, page=page, limit=limit
            )
        )
        quizzes = [QuizDetailScheme.from_orm(quiz) for quiz in raw_quizzes]
        return ListQuizDetailScheme(quizzes=quizzes)

    @validator.validate_quiz_exist_and_active_by_quiz_id
    @validator.validate_user_is_company_member_or_owner_by_quiz_id
    async def get_quiz(self, quiz_id: UUID, user: User) -> QuizDetailScheme:
        nested_quiz = await self.quiz_repository.get_nested_quiz(
            quiz_id=quiz_id
        )
        return QuizDetailScheme.from_orm(nested_quiz)

    @validator.validate_quiz_exist_and_active_by_quiz_id
    @validator.validate_user_is_company_member_or_owner_by_quiz_id
    async def delete_quiz(self, quiz_id: UUID, user: User):
        nested_quiz = await self.quiz_repository.get_nested_quiz(
            quiz_id=quiz_id
        )
        raw_quiz = await self.quiz_repository.update_quiz(
            quiz_id=quiz_id, is_active=False
        )
        return QuizDetailScheme.from_orm(nested_quiz)

    @validator.validate_quiz_exist_and_active_by_quiz_id
    @validator.validate_user_is_owner_or_admin_by_quiz_id
    async def add_question(
        self, scheme: QuestionCreateScheme, quiz_id: UUID, user: User
    ):
        raw_question = await self.question_repository.creat_question(
            question=scheme, quiz_id=quiz_id
        )
        raw_answers = await self.answer_repository.create_answers(
            answers=scheme.answers, question_id=raw_question.question_id
        )
        nested_question = await self.question_repository.get_nested_question(
            question_id=raw_question.question_id
        )
        return QuestionDetailScheme.from_orm(
            nested_question
        )  # todo why does it work when i use raw_question !!!

    @validator.validate_quiz_exist_and_active_by_question_id
    @validator.validate_user_is_owner_or_admin_by_question_id
    async def delete_question(self, question_id: UUID, user: User):
        nested_question = await self.question_repository.get_nested_question(
            question_id=question_id
        )
        raw_question = await self.question_repository.delete_question(
            question_id=question_id
        )
        return QuestionDetailScheme.from_orm(nested_question)

    @validator.validate_quiz_exist_and_active_by_question_id
    @validator.validate_user_is_owner_or_admin_by_question_id
    async def add_answer(
        self, scheme: AnswerCreateScheme, question_id: UUID, user: User
    ):
        raw_answer = await self.answer_repository.create_answer(
            answer=scheme, question_id=question_id
        )
        return AnswerDetailScheme.from_orm(raw_answer)

    @validator.validate_quiz_exist_and_active_by_answer_id
    @validator.validate_user_is_owner_or_admin_by_answer_id
    async def delete_answer(self, answer_id: UUID, user: User):
        raw_answer = await self.answer_repository.delete_answer(
            answer_id=answer_id
        )
        return AnswerDetailScheme.from_orm(raw_answer)
