"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from card_game_tcg.schemas.card import CardCreate, CardRead


class TestCardCreate:
    def test_valid_card(self):
        card = CardCreate(name="Dragon", description="Fire", attack=5, defense=3, cost=4)
        assert card.name == "Dragon"
        assert card.description == "Fire"
        assert card.attack == 5

    def test_defaults(self):
        card = CardCreate(name="Simple")
        assert card.description == ""
        assert card.attack == 0
        assert card.defense == 0
        assert card.cost == 0

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            CardCreate(name="")

    def test_negative_attack_raises(self):
        with pytest.raises(ValidationError):
            CardCreate(name="Bad", attack=-1)

    def test_negative_defense_raises(self):
        with pytest.raises(ValidationError):
            CardCreate(name="Bad", defense=-1)

    def test_negative_cost_raises(self):
        with pytest.raises(ValidationError):
            CardCreate(name="Bad", cost=-1)


class TestCardRead:
    def test_from_attributes(self):
        """CardRead can be built from an ORM object."""

        class FakeCard:
            id = 1
            name = "Dragon"
            description = "Fire"
            attack = 5
            defense = 3
            cost = 4
            created_at = "2024-01-01T00:00:00Z"
            updated_at = "2024-01-01T00:00:00Z"
            deleted_at = None

        card = CardRead.model_validate(FakeCard())
        assert card.id == 1
        assert card.name == "Dragon"
        assert card.deleted_at is None
