from fastapi import APIRouter

from . import health_check, user

__all__ = [
    "main_router",
]

main_router = APIRouter()

main_router.include_router(health_check.router)

# user routers
user.user_router.include_router(user.gwt_router, prefix="/gwt")
user.user_router.include_router(user.auth0_router, prefix="/auth0")
main_router.include_router(user.user_router, prefix="/user", tags=["user"])
