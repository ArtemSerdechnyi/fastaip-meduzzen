from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import List, Optional, Self
from uuid import UUID


class AnswerCreateScheme(BaseModel):
    text: str
    is_correct: bool = False


class QuestionCreateScheme(BaseModel):
    text: str
    answers: List[AnswerCreateScheme] = Field(exclude=True)

    @model_validator(mode="after")
    def check_answers_amount(self) -> Self:
        if len(self.answers) < 2:
            raise ValueError("Question must have at least two answers.")
        return self

    @model_validator(mode="after")
    def check_answers_correctness(self) -> Self:
        if not any(answer.is_correct for answer in self.answers):
            raise ValueError("Question must have at least one correct answer.")
        return self


class QuizCreateRequestScheme(BaseModel):
    name: str
    description: Optional[str]
    questions: list[QuestionCreateScheme]

    @model_validator(mode="after")
    def check_questions(self) -> Self:
        if len(self.questions) < 2:
            raise ValueError("Quiz must have at least two questions.")
        return self


class AnswerDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer_id: UUID
    question_id: UUID
    text: str
    is_correct: bool


class QuestionDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quiz_id: UUID
    question_id: UUID
    text: str
    answers: Optional[List[AnswerDetailScheme]]


class QuizDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quiz_id: UUID
    name: str
    description: Optional[str]
    questions: Optional[List[QuestionDetailScheme]]


class ListQuizDetailScheme(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quizzes: List[QuizDetailScheme]
