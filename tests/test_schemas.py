"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from card_game_tcg.schemas.card import CardCreate, CardRead


class TestCardCreate:
    def test_valid_card(self):
        card = CardCreate(
            tcgdex_id="swsh3-136",
            name="Pikachu",
            image_url="https://example.com/pikachu.png",
        )
        assert card.tcgdex_id == "swsh3-136"
        assert card.name == "Pikachu"
        assert card.image_url == "https://example.com/pikachu.png"

    def test_defaults(self):
        card = CardCreate(tcgdex_id="swsh3-136", name="Pikachu")
        assert card.image_url is None

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            CardCreate(tcgdex_id="swsh3-136", name="")

    def test_empty_tcgdex_id_raises(self):
        with pytest.raises(ValidationError):
            CardCreate(tcgdex_id="", name="Pikachu")


class TestCardRead:
    def test_from_attributes(self):
        """CardRead can be built from an ORM object."""

        class FakeCard:
            id = 1
            tcgdex_id = "swsh3-136"
            name = "Pikachu"
            image_url = "https://example.com/pikachu.png"
            created_at = "2024-01-01T00:00:00Z"
            updated_at = "2024-01-01T00:00:00Z"
            deleted_at = None

        card = CardRead.model_validate(FakeCard())
        assert card.id == 1
        assert card.tcgdex_id == "swsh3-136"
        assert card.name == "Pikachu"
        assert card.deleted_at is None
