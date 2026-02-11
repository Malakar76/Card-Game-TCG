"""Tests for SQLAlchemy models."""

import pytest
from sqlalchemy.exc import IntegrityError

from card_game_tcg.models.card import Card


class TestCardColumns:
    def test_card_has_base_columns(self, session):
        card = Card(name="Test")
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.id is not None
        assert card.created_at is not None
        assert card.updated_at is not None
        assert card.deleted_at is None

    def test_card_has_own_columns(self, session):
        card = Card(name="Dragon", description="Fire", attack=5, defense=3, cost=4)
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.name == "Dragon"
        assert card.description == "Fire"
        assert card.attack == 5
        assert card.defense == 3
        assert card.cost == 4

    def test_card_defaults(self, session):
        card = Card(name="Simple")
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.description == ""
        assert card.attack == 0
        assert card.defense == 0
        assert card.cost == 0


class TestCheckConstraints:
    def test_negative_attack_raises(self, session):
        card = Card(name="Bad", attack=-1)
        session.add(card)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_negative_defense_raises(self, session):
        card = Card(name="Bad", defense=-1)
        session.add(card)
        with pytest.raises(IntegrityError):
            session.commit()

    def test_negative_cost_raises(self, session):
        card = Card(name="Bad", cost=-1)
        session.add(card)
        with pytest.raises(IntegrityError):
            session.commit()


class TestSoftDelete:
    def test_soft_delete_sets_deleted_at(self, session):
        card = Card(name="Target")
        session.add(card)
        session.commit()

        card.soft_delete(session)
        session.commit()
        session.refresh(card)

        assert card.deleted_at is not None
        assert card.is_deleted is True

    def test_restore_clears_deleted_at(self, session):
        card = Card(name="Target")
        session.add(card)
        session.commit()

        card.soft_delete(session)
        session.commit()
        card.restore(session)
        session.commit()
        session.refresh(card)

        assert card.deleted_at is None
        assert card.is_deleted is False

    def test_is_deleted_false_by_default(self, session):
        card = Card(name="Active")
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.is_deleted is False
