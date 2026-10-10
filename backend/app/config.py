from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = (
        "postgresql+psycopg://wowlance:wowlance@127.0.0.1:5433/wowlance"
    )


settings = Settings()
