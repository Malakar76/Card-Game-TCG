"""Tests for screen logic (no GUI rendering)."""

from card_game_tcg.schemas.card import CardCreate
from card_game_tcg.services import card_service


class TestCreateCardScreenLogic:
    """Test the create card business logic that screens rely on."""

    def test_create_card_via_service(self, session):
        data = CardCreate(name="Dragon", attack=5, defense=3, cost=4)
        card = card_service.create_card(session, data)

        assert card.name == "Dragon"
        assert card.id is not None

    def test_empty_name_rejected_by_schema(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CardCreate(name="")

    def test_whitespace_name_rejected_after_strip(self):
        """The screen strips whitespace before validation, resulting in empty name."""
        import pytest
        from pydantic import ValidationError

        name = "   ".strip()
        with pytest.raises(ValidationError):
            CardCreate(name=name)


class TestCardsScreenLogic:
    """Test the cards listing logic that screens rely on."""

    def test_load_cards_returns_list(self, session):
        card_service.create_card(session, CardCreate(name="Alpha"))
        card_service.create_card(session, CardCreate(name="Beta"))

        cards = card_service.get_all_cards(session)
        assert len(cards) == 2

    def test_cards_as_dict_for_recycleview(self, session):
        card_service.create_card(session, CardCreate(name="Dragon", attack=5, defense=3, cost=4))
        cards = card_service.get_all_cards(session)

        data = [
            {
                "card_name": c.name,
                "description": c.description,
                "attack": c.attack,
                "defense": c.defense,
                "cost": c.cost,
            }
            for c in cards
        ]

        assert len(data) == 1
        assert data[0]["card_name"] == "Dragon"
        assert data[0]["attack"] == 5
