"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "TCG_"}

    app_name: str = "Card Game TCG"
    debug: bool = False

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "card_game_tcg"


settings = Settings()
