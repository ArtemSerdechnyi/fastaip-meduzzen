from fastapi import FastAPI

from app.routers import health_check
from app.core.settings import settings

_app = None


def get_app() -> FastAPI:
    global _app
    if _app:
        return _app

    _app = FastAPI(
        debug=settings.DEBUG,
        title="Meduzzen internship",
    )
    _app.include_router(health_check.router)
    return _app
