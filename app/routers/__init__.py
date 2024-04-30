from fastapi import APIRouter

from app.routers import company, health_check, user

__all__ = [
    "main_router",
]

main_router = APIRouter()

main_router.include_router(health_check.router)

# user routers
user.user_router.include_router(user.user_action_router, prefix="/action")
main_router.include_router(user.user_router, prefix="/user", tags=["user"])

# company routers
company.company_router.include_router(
    company.company_action_router, prefix="/action"
)
main_router.include_router(
    company.company_router, prefix="/company", tags=["company"]
)
