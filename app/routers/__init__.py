from fastapi import APIRouter

from . import health_check, user

__all__ = [
    "main_router",
]

main_router = APIRouter()

main_router.include_router(health_check.router)
main_router.include_router(user.user_router, prefix="/user", tags=["user"])
