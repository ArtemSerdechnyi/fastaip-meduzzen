from fastapi import APIRouter

from . import company, health_check, user

__all__ = [
    "main_router",
]

main_router = APIRouter()

main_router.include_router(health_check.router)

# user routers
main_router.include_router(user.user_router, prefix="/user", tags=["user"])
# company routers
main_router.include_router(
    company.company_router, prefix="/company", tags=["company"]
)
