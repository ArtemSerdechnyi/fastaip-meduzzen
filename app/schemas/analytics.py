from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class AverageScoreScheme(BaseModel):
    average_score: float


class UserQuizAverageScoreScheme(BaseModel):
    quiz_id: Optional[UUID]
    average_score: float


class ListUserQuizAverageScoreScheme(BaseModel):
    quizzes: List[UserQuizAverageScoreScheme]


class UserQuizLastPassingScheme(BaseModel):
    quiz_id: Optional[UUID]
    last_passing: datetime

    @field_validator("last_passing", mode="after")
    def last_passing_validator(cls, v: datetime):
        return v.strftime("%Y-%m-%dT%H:%M:%S")


class ListUserQuizLastPassingScheme(BaseModel):
    quizzes: List[UserQuizLastPassingScheme]


class CompanyMemberUserQuizAverageScoreScheme(BaseModel):
    member_id: Optional[UUID]
    average_score: float


class ListCompanyMemberUserQuizAverageScoreScheme(BaseModel):
    members: List[CompanyMemberUserQuizAverageScoreScheme]


class CompanyMemberLastPassingQuizScheme(BaseModel):
    member_id: Optional[UUID]
    last_passing: datetime

    @field_validator("last_passing", mode="after")
    def last_passing_validator(cls, v: datetime):
        return v.strftime("%Y-%m-%dT%H:%M:%S")


class ListCompanyMemberLastPassingQuizScheme(BaseModel):
    members: List[CompanyMemberLastPassingQuizScheme]
