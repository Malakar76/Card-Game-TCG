"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TCG_"}

    app_name: str = "Card Game TCG"
    debug: bool = False


settings = Settings()
