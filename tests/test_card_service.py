"""Tests for card service."""

from card_game_tcg.schemas.card import CardCreate
from card_game_tcg.services import card_service


class TestCreateCard:
    def test_creates_card(self, session):
        data = CardCreate(name="Dragon", description="Fire", attack=5, defense=3, cost=4)
        card = card_service.create_card(session, data)

        assert card.id is not None
        assert card.name == "Dragon"
        assert card.description == "Fire"
        assert card.attack == 5
        assert card.defense == 3
        assert card.cost == 4

    def test_creates_card_with_defaults(self, session):
        data = CardCreate(name="Simple")
        card = card_service.create_card(session, data)

        assert card.description == ""
        assert card.attack == 0
        assert card.defense == 0
        assert card.cost == 0


class TestGetAllCards:
    def test_returns_all_non_deleted(self, session):
        card_service.create_card(session, CardCreate(name="Alpha"))
        card_service.create_card(session, CardCreate(name="Beta"))

        cards = card_service.get_all_cards(session)
        assert len(cards) == 2

    def test_excludes_deleted(self, session):
        card = card_service.create_card(session, CardCreate(name="Deleted"))
        card_service.delete_card(session, card)

        cards = card_service.get_all_cards(session)
        assert len(cards) == 0

    def test_ordered_by_name(self, session):
        card_service.create_card(session, CardCreate(name="Zeta"))
        card_service.create_card(session, CardCreate(name="Alpha"))

        cards = card_service.get_all_cards(session)
        assert cards[0].name == "Alpha"
        assert cards[1].name == "Zeta"


class TestGetCard:
    def test_find_by_id(self, session):
        created = card_service.create_card(session, CardCreate(name="Target"))
        found = card_service.get_card(session, created.id)

        assert found is not None
        assert found.name == "Target"

    def test_returns_none_for_deleted(self, session):
        card = card_service.create_card(session, CardCreate(name="Target"))
        card_service.delete_card(session, card)

        found = card_service.get_card(session, card.id)
        assert found is None

    def test_returns_none_for_missing(self, session):
        found = card_service.get_card(session, 9999)
        assert found is None


class TestGetCardByName:
    def test_find_by_name(self, session):
        card_service.create_card(session, CardCreate(name="Dragon"))
        found = card_service.get_card_by_name(session, "Dragon")

        assert found is not None
        assert found.name == "Dragon"

    def test_returns_none_for_missing(self, session):
        found = card_service.get_card_by_name(session, "Nonexistent")
        assert found is None


class TestDeleteCard:
    def test_soft_deletes(self, session):
        card = card_service.create_card(session, CardCreate(name="Target"))
        card_service.delete_card(session, card)

        assert card.is_deleted is True
        assert card.deleted_at is not None
