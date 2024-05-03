from fastapi import APIRouter

import app.routers.company_action
import app.routers.user_action
from app.routers import (
    company,
    company_action,
    health_check,
    quiz,
    user,
    user_action,
)

__all__ = [
    "main_router",
]

main_router = APIRouter()

main_router.include_router(health_check.router)

# user routers
user.user_router.include_router(
    user_action.user_action_router, prefix="/action"
)
main_router.include_router(user.user_router, prefix="/user", tags=["user"])

# company routers
company.company_router.include_router(
    company_action.company_action_router, prefix="/action"
)
main_router.include_router(
    company.company_router, prefix="/company", tags=["company"]
)

# quiz routers
main_router.include_router(quiz.quiz_router, prefix="/quiz", tags=["quiz"])
