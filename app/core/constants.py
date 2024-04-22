from app.core.settings import app_settings

USERS_PAGE_LIMIT: int = 10

SECRET_KEY = app_settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10
