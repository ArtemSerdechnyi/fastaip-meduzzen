from fastapi import FastAPI

import app.routers as r
from app.core.settings import settings

_app = None


def get_app() -> FastAPI:
    global _app
    if _app:
        return _app

    _app = FastAPI(
        debug=settings.debug,
        title="Meduzzen internship",
    )
    _app.include_router(r.health_check.router)
    return _app
