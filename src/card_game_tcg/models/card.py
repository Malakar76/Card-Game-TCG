"""Card database model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from card_game_tcg.models.base import BaseModel


class Card(BaseModel):
    """Represents a trading card from TCGdex stored in the user's collection."""

    __tablename__ = "cards"

    tcgdex_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
