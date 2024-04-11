from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool = False
    HOST: str = "localhost"
    PORT: int = 8000
    RELOAD: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
