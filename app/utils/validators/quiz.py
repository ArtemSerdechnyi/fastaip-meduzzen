from abc import ABC
from functools import wraps
from uuid import UUID

from sqlalchemy import select, or_, and_, exists, func, all_, not_, any_

from app.db.models import (
    User,
    CompanyRole,
    CompanyMember,
    Company,
    Quiz,
    Question,
    Answer,
    UserQuiz,
)
from app.schemas.quiz import QuizCreateRequestScheme
from app.schemas.user_quiz import UserQuizCreateScheme
from app.utils.validators import BaseValidator


class AbstractQuizValidator(BaseValidator, ABC):
    def validate_quiz_exist_and_active_by_quiz_id(self, f):
        """
        Validate quiz is exist and active by quiz_id.

        Depends: quiz_id
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            question_id: UUID = kwargs["quiz_id"]

            query = self._build_where_exist_select_query(
                Quiz.quiz_id == question_id,
                Quiz.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error. Quiz dont exist.")
            return await f(self_service, **kwargs)

        return wrapper

    def validate_user_is_company_member_or_owner_by_quiz_id(self, f):
        """
        Validate that the user is a member of the company or owner company.


        Depends: company_id, scheme
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            quiz_id: UUID = kwargs["quiz_id"]
            user: User = kwargs["user"]

            query = self._build_where_exist_select_query(
                Quiz.quiz_id == quiz_id,
                Quiz.is_active == True,
                or_(
                    and_(
                        Quiz.company_id == CompanyMember.company_id,
                        CompanyMember.user_id == user.user_id,
                        CompanyMember.is_active == True,
                    ),
                    Company.owner_id == user.user_id,
                ),
                Company.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error.")
            return await f(self_service, **kwargs)

        return wrapper


class QuizCreateValidator(AbstractQuizValidator):
    def validate_user_is_owner_or_admin_by_company_id(self, f):
        """
        Validate that the user is admin or owner of the given company by company_id.

        Depends: company_id, user
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            user: User = kwargs["user"]

            admin_role = CompanyRole.admin.value

            admin_check_query = self._build_where_exist_select_query(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user.user_id,
                CompanyMember.role == admin_role,
                CompanyMember.is_active == True,
            )
            owner_check_query = self._build_where_exist_select_query(
                Company.company_id == company_id,
                Company.owner_id == user.user_id,
            )

            query = select(or_(owner_check_query, admin_check_query))

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User is not admin or owner."
                )
            return await f(self_service, **kwargs)

        return wrapper

    def validate_user_is_owner_or_admin_by_quiz_id(self, f):
        """
        Validate that the user is admin or owner of the given company by quiz_id.

        Depends: quiz_id, user
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            quiz_id: UUID = kwargs["quiz_id"]
            user: User = kwargs["user"]

            admin_role = CompanyRole.admin.value

            query = self._build_where_exist_select_query(
                Quiz.quiz_id == quiz_id,
                or_(
                    and_(
                        CompanyMember.company_id == Quiz.company_id,
                        CompanyMember.user_id == user.user_id,
                        CompanyMember.role == admin_role,
                        CompanyMember.is_active == True,
                    ),
                    Company.owner_id == user.user_id,
                ),
                Company.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User is not admin or owner."
                )
            return await f(self_service, **kwargs)

        return wrapper

    def validate_user_is_owner_or_admin_by_question_id(self, f):
        """
        Validate that the user is admin or owner of the given company by question_id.

        Depends: question_id, user
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            question_id: UUID = kwargs["question_id"]
            user: User = kwargs["user"]

            admin_role = CompanyRole.admin.value

            query = self._build_where_exist_select_query(
                Question.question_id == question_id,
                Quiz.quiz_id == Question.quiz_id,
                or_(
                    and_(
                        CompanyMember.company_id == Quiz.company_id,
                        CompanyMember.user_id == user.user_id,
                        CompanyMember.role == admin_role,
                        CompanyMember.is_active == True,
                    ),
                    Company.owner_id == user.user_id,
                ),
                Company.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User is not admin or owner."
                )
            return await f(self_service, **kwargs)

        return wrapper

    def validate_user_is_owner_or_admin_by_answer_id(self, f):
        """
        Validate that the user is admin or owner of the given company by answer_id.

        Depends: answer_id, user
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            answer_id: UUID = kwargs["answer_id"]
            user: User = kwargs["user"]

            admin_role = CompanyRole.admin.value

            query = self._build_where_exist_select_query(
                Answer.answer_id == answer_id,
                Question.question_id == Answer.question_id,
                Quiz.quiz_id == Question.quiz_id,
                Quiz.company_id == Company.company_id,
                or_(
                    and_(
                        CompanyMember.company_id == Quiz.company_id,
                        CompanyMember.user_id == user.user_id,
                        CompanyMember.role == admin_role,
                        CompanyMember.is_active == True,
                    ),
                    Company.owner_id == user.user_id,
                ),
                Company.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError(
                    "Validation error. User is not admin or owner."
                )
            return await f(self_service, **kwargs)

        return wrapper

    def validate_quiz_company_and_name_unique(self, f):
        """
        Validate that a quiz with the same name does not already exist in the company.

        Depends: company_id, scheme
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            company_id: UUID = kwargs["company_id"]
            quiz_scheme: QuizCreateRequestScheme = kwargs["scheme"]

            quiz_name = quiz_scheme.name

            query = self._build_where_not_exist_select_query(
                Quiz.company_id == company_id,
                Quiz.name == quiz_name,
                Quiz.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error. Quiz is exist.")
            return await f(self_service, **kwargs)

        return wrapper

    def validate_quiz_exist_and_active_by_question_id(self, f):
        """
        Validate quiz is exist and active by question_id.

        Depends: question_id
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            question_id: UUID = kwargs["question_id"]

            query = self._build_where_exist_select_query(
                Question.question_id == question_id,
                Quiz.quiz_id == Question.quiz_id,
                Quiz.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error. Quiz dont exist.")
            return await f(self_service, **kwargs)

        return wrapper

    def validate_quiz_exist_and_active_by_answer_id(self, f):
        """
        Validate that the quiz associated with the given answer_id exists and is active.

        Depends: answer_id
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            answer_id: UUID = kwargs["answer_id"]

            query = self._build_where_exist_select_query(
                Answer.answer_id == answer_id,
                Question.question_id == Answer.question_id,
                Quiz.quiz_id == Question.quiz_id,
                Quiz.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                raise PermissionError("Validation error. Quiz dont exist.")
            return await f(self_service, **kwargs)

        return wrapper


class QuizAnswerValidator(AbstractQuizValidator):
    def validate_question_count_matches(self, f):
        """
        Validate that the number of questions submitted matches the number of questions in the quiz.

        Depends: quiz_id, user_quiz_scheme
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            quiz_id: UUID = kwargs["quiz_id"]
            user_quiz_scheme: UserQuizCreateScheme = kwargs["scheme"]
            user_question_count = len(user_quiz_scheme.questions)

            query = (
                select(func.count())
                .select_from(Question)
                .where(Question.quiz_id == quiz_id)
            )
            result = await self_service.session.execute(query)
            quiz_question_count = result.scalar()

            if user_question_count != quiz_question_count:
                error_message = (
                    f"Validation error. The number of questions submitted {user_question_count} "
                    f"does not match the number of questions in the quiz {quiz_question_count}."
                )
                raise ValueError(error_message)

            return await f(self_service, **kwargs)

        return wrapper

    def validate_all_questions_matches_to_quiz(self, f):
        """
        Validate that the number of questions submitted matches the number of questions in the quiz.

        Depends: quiz_id, user_quiz_scheme
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            quiz_id: UUID = kwargs["quiz_id"]
            user_quiz_scheme: UserQuizCreateScheme = kwargs["scheme"]

            for question in user_quiz_scheme.questions:
                question_id = question.question_id
                query = select(
                    exists().where(
                        and_(
                            Question.question_id == question_id,
                            Question.quiz_id == quiz_id,
                        )
                    )
                )

                result = await self_service.session.execute(query)
                exist = result.scalar()

                if not exist:
                    error_message = (
                        f"Validation error: One or more question do not belong to quiz {quiz_id}\n"
                        f"Questions ids: {[q.question_id for q in user_quiz_scheme.questions]}"
                    )
                    raise PermissionError(error_message)
            return await f(self_service, **kwargs)

        return wrapper

    def validate_all_answers_matches_to_question(self, f):
        """
        Validate that answers associated with the question.

        Depends: user_quiz_scheme
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            user_quiz_scheme: UserQuizCreateScheme = kwargs["scheme"]

            for question in user_quiz_scheme.questions:
                question_id = question.question_id
                answer_ids = [answer.answer_id for answer in question.answers]

                query = select(
                    exists().where(
                        and_(
                            Answer.answer_id.in_(answer_ids),
                            Answer.question_id == question_id,
                        )
                    )
                )

                result = await self_service.session.execute(query)
                exist = result.scalar()

                if not exist:
                    error_message = (
                        f"Validation error: One or more answers do not belong to question {question_id}\n"
                        f"Answers ids: {answer_ids}"
                    )
                    raise PermissionError(error_message)

            return await f(self_service, **kwargs)

        return wrapper

    def validate_company_member_user_quiz_exist(self, f):
        """
        Validate that a company member has a user_quiz.

        Depends: company_member_id
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            company_member_id: UUID = kwargs["company_member_id"]

            query = self._build_where_exist_select_query(
                CompanyMember.member_id == company_member_id,
                CompanyMember.user_id == UserQuiz.user_id,
                CompanyMember.company_id == Quiz.company_id,
                CompanyMember.is_active == True,
                Quiz.is_active == True,
                UserQuiz.quiz_id == Quiz.quiz_id,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                error_message = (
                    f"Validation error. Member dont have any user_quiz."
                )
                raise PermissionError(error_message)

            return await f(self_service, **kwargs)

        return wrapper

    def validate_user_has_user_quiz(self, f):
        """
        Validate that a company member has a user_quiz.

        Depends: user_id
        """

        @wraps(f)
        async def wrapper(self_service, **kwargs):
            user_id: UUID = kwargs["user_id"]

            query = self._build_where_exist_select_query(
                UserQuiz.user_id == user_id,
                UserQuiz.quiz_id == Quiz.quiz_id,
                Quiz.is_active == True,
            )

            result = await self_service.session.execute(query)
            exist = result.scalar()

            if not exist:
                error_message = (
                    f"Validation error. User dont have any user_quiz."
                )
                raise PermissionError(error_message)

            return await f(self_service, **kwargs)

        return wrapper
