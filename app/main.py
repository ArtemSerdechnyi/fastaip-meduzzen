import uvicorn

from app.core.application import get_app
from app.core.settings import app_settings

app = get_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=app_settings.RELOAD,
    )
