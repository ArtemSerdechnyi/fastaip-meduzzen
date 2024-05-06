from uuid import UUID

from app.db.models import User, Quiz
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.question import QuestionRepository
from app.repositories.quiz import QuizRepository

from app.repositories.user_quiz import UserQuizRepository
from app.repositories.user_quiz_answers import UserQuizAnswersRepository
from app.schemas.quiz import QuizDetailScheme, QuestionDetailScheme

from app.schemas.user_quiz import UserQuizCreateScheme, UserQuizDetailScheme
from app.services.base import Service
from app.utils.validators.quiz import QuizAnswerValidator


class UserQuizService(Service):
    validator = QuizAnswerValidator()

    def __init__(self, session):
        self.company_member_repo = CompanyMemberRepository(session)
        self.quiz_repo = QuizRepository(session)
        self.user_quiz_repo = UserQuizRepository(session)
        self.user_quiz_answers_repo = UserQuizAnswersRepository(session)
        super().__init__(session)

    @staticmethod
    async def get_quiz_question_count(quiz: QuizDetailScheme) -> int:
        return len(quiz.questions)

    @staticmethod
    async def get_quiz_correct_answers_count(
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
        question_count = await self.get_quiz_question_count(quiz=nested_quiz)
        correct_answer_count = await self.get_quiz_correct_answers_count(
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
        return correct_answers_sum / question_count_sum

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
        return correct_answers_sum / question_count_sum
