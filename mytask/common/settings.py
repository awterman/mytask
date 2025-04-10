from pydantic_settings import BaseSettings, SettingsConfigDict


class MyTaskSettings(BaseSettings):
    postgres_dsn: str
    redis_dsn: str

    datura_api_key: str
    chutes_api_key: str

    model_config = SettingsConfigDict(env_file=".env")


settings = MyTaskSettings()
