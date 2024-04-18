from pydantic_settings import BaseSettings


class _AppSettings(BaseSettings):
    DEBUG: bool = False
    HOST: str = "localhost"
    PORT: int = 8000
    RELOAD: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


app_settings = _AppSettings()


class _PostgresConfig(BaseSettings):
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    class Config:
        env_file = ".env.docker"
        env_file_encoding = "utf-8"
        extra = "ignore"


postgres_config = _PostgresConfig()


class _RedisConfig(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env.docker"
        env_file_encoding = "utf-8"
        extra = "ignore"


redis_conf = _RedisConfig()
