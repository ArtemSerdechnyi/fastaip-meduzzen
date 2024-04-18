from fastapi import FastAPI

from app.core.settings import app_settings
from app.db.redis import lifespan_redis
from app.routers import main_router

_app = None


def _create_app() -> FastAPI:
    app = FastAPI(
        debug=app_settings.DEBUG,
        title="Meduzzen internship",
        lifespan=lifespan_redis,
    )

    app.include_router(main_router)

    return app


def get_app() -> FastAPI:
    global _app
    if _app:
        return _app
    _app = _create_app()
    return _app
