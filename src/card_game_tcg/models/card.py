"""Card database model."""

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from card_game_tcg.models.base import BaseModel


class Card(BaseModel):
    """Represents a single trading card."""

    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint("attack >= 0", name="ck_cards_attack_positive"),
        CheckConstraint("defense >= 0", name="ck_cards_defense_positive"),
        CheckConstraint("cost >= 0", name="ck_cards_cost_positive"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    attack: Mapped[int] = mapped_column(default=0, nullable=False)
    defense: Mapped[int] = mapped_column(default=0, nullable=False)
    cost: Mapped[int] = mapped_column(default=0, nullable=False)
