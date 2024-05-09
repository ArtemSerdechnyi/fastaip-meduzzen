from datetime import datetime, date
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, field_validator


class UserQuizAverageScoreScheme(BaseModel):
    quiz_id: Optional[UUID]
    average_score: float


class ListUserQuizAverageScoreScheme(BaseModel):
    quizzes: list[UserQuizAverageScoreScheme]


class UserQuizLastPassingScheme(BaseModel):
    quiz_id: Optional[UUID]
    last_passing: datetime

    @field_validator("last_passing", mode="after")
    def last_passing_validator(cls, v: datetime):
        return v.strftime("%Y-%m-%dT%H:%M:%S")


class ListUserQuizLastPassingScheme(BaseModel):
    quizzes: list[UserQuizLastPassingScheme]


class CompanyMemberUserQuizAverageScoreScheme(BaseModel):
    member_id: Optional[UUID]
    average_score: float


class ListCompanyMemberUserQuizAverageScoreScheme(BaseModel):
    members: list[CompanyMemberUserQuizAverageScoreScheme]


class CompanyMemberLastPassingQuizScheme(BaseModel):
    member_id: Optional[UUID]
    last_passing: datetime

    @field_validator("last_passing", mode="after")
    def last_passing_validator(cls, v: datetime):
        return v.strftime("%Y-%m-%dT%H:%M:%S")


class ListCompanyMemberLastPassingQuizScheme(BaseModel):
    members: list[CompanyMemberLastPassingQuizScheme]
