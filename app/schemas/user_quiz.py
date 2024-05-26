import datetime
import enum
from typing import List, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class UserQuizAnswerCreateScheme(BaseModel):
    answer_id: UUID


class UserQuizQuestionCreateScheme(BaseModel):
    question_id: UUID
    answers: List[UserQuizAnswerCreateScheme]

    @model_validator(mode="after")
    def check_answers_unique(self) -> Self:
        answer_ids = [answer.answer_id for answer in self.answers]
        if len(answer_ids) != len(set(answer_ids)):
            raise ValueError("Duplicate answers found in a single question.")
        return self


class UserQuizCreateScheme(BaseModel):
    # quiz_id: UUID
    questions: List[UserQuizQuestionCreateScheme]

    @model_validator(mode="after")
    def check_questions_unique(self) -> Self:
        question_ids = [question.question_id for question in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Duplicate questions found in a single quiz.")
        return self


class UserQuizAnswerDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_answer_id: UUID
    user_quiz_id: UUID
    question_id: UUID
    answer_id: UUID


class UserQuizDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_quiz_id: UUID
    user_id: UUID
    quiz_id: UUID
    correct_answers_count: int
    total_questions: int
    attempt_time: datetime.datetime
    answers: List[UserQuizAnswerDetailScheme]


class ListUserQuizDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_quizzes: List[UserQuizDetailScheme]


class ResponseFileTypeEnum(str, enum.Enum):
    JSON = "json"
    CSV = "csv"
