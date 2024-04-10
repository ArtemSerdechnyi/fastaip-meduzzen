import uvicorn

from app.core.application import get_app
from app.core.settings import settings

app = get_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
