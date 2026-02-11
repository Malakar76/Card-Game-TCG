"""Card document model."""

from pydantic import Field

from card_game_tcg.models.base import BaseDocument


class Card(BaseDocument):
    """Represents a single trading card."""

    name: str
    description: str = ""
    attack: int = Field(default=0, ge=0)
    defense: int = Field(default=0, ge=0)
    cost: int = Field(default=0, ge=0)

    class Settings:
        name = "cards"
