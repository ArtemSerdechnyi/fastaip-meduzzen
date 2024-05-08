from pydantic import BaseModel


class UserQuizAverageScoreScheme(BaseModel):
    average_score: float
