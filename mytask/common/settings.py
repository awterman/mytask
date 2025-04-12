from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class MyTaskSettings(BaseSettings):
    postgres_dsn: str
    redis_host: str
    redis_port: int
    redis_password: str

    datura_api_key: str
    chutes_api_key: str

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache(maxsize=1)
def get_settings() -> MyTaskSettings:
    return MyTaskSettings()  # type: ignore