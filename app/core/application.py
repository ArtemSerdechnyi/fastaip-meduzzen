from fastapi import FastAPI

from app.core.settings import app_settings
from app.routers import health_check
from app.services.redis import lifespan_redis

_app = None


def _create_app() -> FastAPI:
    app = FastAPI(
        debug=app_settings.DEBUG,
        title="Meduzzen internship",
        lifespan=lifespan_redis,
    )

    app.include_router(health_check.router)

    return app


def get_app() -> FastAPI:
    global _app
    if _app:
        return _app
    _app = _create_app()
    return _app
