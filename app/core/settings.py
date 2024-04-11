import pathlib

from pydantic_settings import BaseSettings

BASE_DIR = pathlib.Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    debug: bool = False
    host: str = "localhost"
    port: int = 8000
    reload: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
