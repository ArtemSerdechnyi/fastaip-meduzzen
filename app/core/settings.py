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


# GWT


class _GWTConfig(BaseSettings):
    GWT_ALGORITHMS: str
    GWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    GWT_SECRET_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


gwt_config = _GWTConfig()


# AUTH0


class _Auth0Config(BaseSettings):
    AUTH0_CLIENT_ID: str
    AUTH0_DOMAIN: str
    AUTH0_API_AUDIENCE: str
    AUTH0_API_SECRET: str
    AUTH0_ALGORITHMS: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


auth0_config = _Auth0Config()
