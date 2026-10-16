from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: str = "local"
    database_url: str = (
        "postgresql+psycopg://wowlance:wowlance@127.0.0.1:5433/wowlance"
    )


settings = Settings()
