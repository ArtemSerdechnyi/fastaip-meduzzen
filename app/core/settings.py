from pydantic_settings import BaseSettings


class _AppSettings(BaseSettings):
    DEBUG: bool = False
    HOST: str = "localhost"
    PORT: int = 8000
    RELOAD: bool = False
    SECRET_KEY: str = "secret_key"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


app_settings = _AppSettings()


# postgres settings


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


class _PostgresConfigTest(BaseSettings):
    POSTGRES_SERVER_TEST: str = "localhost"
    POSTGRES_PORT_TEST: str = "5433"
    POSTGRES_DB_TEST: str = "postgres"
    POSTGRES_USER_TEST: str = "postgres"
    POSTGRES_PASSWORD_TEST: str = "postgres"

    class Config:
        env_file = ".env.docker"
        env_file_encoding = "utf-8"
        extra = "ignore"


postgres_config_test = _PostgresConfigTest()


# redis settings


class _RedisConfig(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env.docker"
        env_file_encoding = "utf-8"
        extra = "ignore"


redis_conf = _RedisConfig()


# AUTH0


class Auth0(BaseSettings):
    auth0_domain: str
    auth0_api_audience: str
    auth0_issuer: str
    auth0_algorithms: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


auth0_config = Auth0()
