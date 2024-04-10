import pathlib
import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = pathlib.Path(__file__).parent.parent.parent
ENV = os.environ


class Settings(BaseSettings):
    debug: bool = ENV.get("DEBUG", False)
    host: str = ENV.get("HOST", "localhost")
    port: int = ENV.get("PORT", 8000)
    reload: bool = ENV.get("RELOAD", False)


settings = Settings()
