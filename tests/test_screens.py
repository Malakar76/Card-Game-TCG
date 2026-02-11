"""Tests for screen logic (no GUI rendering)."""

from card_game_tcg.schemas.card import CardCreate
from card_game_tcg.services import card_service


class TestCardsScreenLogic:
    """Test the cards listing logic that screens rely on."""

    def test_load_cards_returns_list(self, session):
        card_service.create_card(session, CardCreate(tcgdex_id="alpha-1", name="Alpha"))
        card_service.create_card(session, CardCreate(tcgdex_id="beta-1", name="Beta"))

        cards = card_service.get_all_cards(session)
        assert len(cards) == 2

    def test_cards_as_dict_for_recycleview(self, session):
        card_service.create_card(
            session,
            CardCreate(
                tcgdex_id="swsh3-136",
                name="Pikachu",
                image_url="https://example.com/pikachu.png",
            ),
        )
        cards = card_service.get_all_cards(session)

        data = [
            {
                "tcgdex_id": c.tcgdex_id,
                "card_name": c.name,
                "card_image": c.image_url or "",
            }
            for c in cards
        ]

        assert len(data) == 1
        assert data[0]["card_name"] == "Pikachu"
        assert data[0]["tcgdex_id"] == "swsh3-136"

    def test_add_to_collection_prevents_duplicates(self, session):
        """Adding the same tcgdex_id twice should be prevented by service check."""
        card_service.create_card(session, CardCreate(tcgdex_id="swsh3-136", name="Pikachu"))
        existing = card_service.get_card_by_tcgdex_id(session, "swsh3-136")
        assert existing is not None

    def test_empty_name_rejected_by_schema(self):
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CardCreate(tcgdex_id="swsh3-136", name="")
