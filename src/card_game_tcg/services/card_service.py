"""Business logic for card operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from card_game_tcg.models.card import Card
from card_game_tcg.schemas.card import CardCreate


def get_all_cards(session: Session) -> list[Card]:
    """Return all non-deleted cards, ordered by name."""
    stmt = select(Card).where(Card.deleted_at.is_(None)).order_by(Card.name)
    return list(session.scalars(stmt).all())


def get_card(session: Session, card_id: int) -> Card | None:
    """Find a non-deleted card by primary key."""
    card = session.get(Card, card_id)
    if card is not None and card.is_deleted:
        return None
    return card


def get_card_by_tcgdex_id(session: Session, tcgdex_id: str) -> Card | None:
    """Find a non-deleted card by its TCGdex ID."""
    stmt = select(Card).where(Card.tcgdex_id == tcgdex_id, Card.deleted_at.is_(None))
    return session.scalars(stmt).first()


def create_card(session: Session, data: CardCreate) -> Card:
    """Create and persist a new card."""
    card = Card(**data.model_dump())
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def delete_card(session: Session, card: Card) -> None:
    """Soft-delete a card."""
    card.soft_delete(session)
    session.commit()


def get_deleted_card_by_tcgdex_id(session: Session, tcgdex_id: str) -> Card | None:
    """Find a soft-deleted card by its TCGdex ID."""
    stmt = select(Card).where(Card.tcgdex_id == tcgdex_id, Card.deleted_at.is_not(None))
    return session.scalars(stmt).first()


def get_deleted_cards(session: Session) -> list[Card]:
    """Return all soft-deleted cards, ordered by name."""
    stmt = select(Card).where(Card.deleted_at.is_not(None)).order_by(Card.name)
    return list(session.scalars(stmt).all())


def restore_card(session: Session, card: Card) -> None:
    """Restore a soft-deleted card."""
    card.restore(session)
    session.commit()


def hard_delete_card(session: Session, card: Card) -> None:
    """Permanently delete a card from the database."""
    session.delete(card)
    session.commit()
