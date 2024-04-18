from fastapi import APIRouter

from . import health_check
from . import user

__all__ = [
    "main_router",
]

main_router = APIRouter()

main_router.include_router(health_check.router)
main_router.include_router(user.router, prefix="/user", tags=["user"])
