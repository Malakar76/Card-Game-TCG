"""Tests for card service."""

from card_game_tcg.models.card import Card
from card_game_tcg.schemas.card import CardCreate
from card_game_tcg.services import card_service


class TestCreateCard:
    def test_creates_card(self, session):
        data = CardCreate(
            tcgdex_id="swsh3-136",
            name="Pikachu",
            image_url="https://example.com/pikachu.png",
        )
        card = card_service.create_card(session, data)

        assert card.id is not None
        assert card.tcgdex_id == "swsh3-136"
        assert card.name == "Pikachu"
        assert card.image_url == "https://example.com/pikachu.png"

    def test_creates_card_with_defaults(self, session):
        data = CardCreate(tcgdex_id="swsh3-136", name="Pikachu")
        card = card_service.create_card(session, data)

        assert card.image_url is None


class TestGetAllCards:
    def test_returns_all_non_deleted(self, session):
        card_service.create_card(session, CardCreate(tcgdex_id="alpha-1", name="Alpha"))
        card_service.create_card(session, CardCreate(tcgdex_id="beta-1", name="Beta"))

        cards = card_service.get_all_cards(session)
        assert len(cards) == 2

    def test_excludes_deleted(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="del-1", name="Deleted"))
        card_service.delete_card(session, card)

        cards = card_service.get_all_cards(session)
        assert len(cards) == 0

    def test_ordered_by_name(self, session):
        card_service.create_card(session, CardCreate(tcgdex_id="zeta-1", name="Zeta"))
        card_service.create_card(session, CardCreate(tcgdex_id="alpha-1", name="Alpha"))

        cards = card_service.get_all_cards(session)
        assert cards[0].name == "Alpha"
        assert cards[1].name == "Zeta"


class TestGetCard:
    def test_find_by_id(self, session):
        created = card_service.create_card(session, CardCreate(tcgdex_id="target-1", name="Target"))
        found = card_service.get_card(session, created.id)

        assert found is not None
        assert found.name == "Target"

    def test_returns_none_for_deleted(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="target-1", name="Target"))
        card_service.delete_card(session, card)

        found = card_service.get_card(session, card.id)
        assert found is None

    def test_returns_none_for_missing(self, session):
        found = card_service.get_card(session, 9999)
        assert found is None


class TestGetCardByTcgdexId:
    def test_find_by_tcgdex_id(self, session):
        card_service.create_card(session, CardCreate(tcgdex_id="swsh3-136", name="Pikachu"))
        found = card_service.get_card_by_tcgdex_id(session, "swsh3-136")

        assert found is not None
        assert found.name == "Pikachu"

    def test_returns_none_for_missing(self, session):
        found = card_service.get_card_by_tcgdex_id(session, "nonexistent")
        assert found is None

    def test_excludes_deleted(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="swsh3-136", name="Pikachu"))
        card_service.delete_card(session, card)

        found = card_service.get_card_by_tcgdex_id(session, "swsh3-136")
        assert found is None


class TestGetDeletedCardByTcgdexId:
    def test_finds_deleted_card(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="swsh3-136", name="Pikachu"))
        card_service.delete_card(session, card)

        found = card_service.get_deleted_card_by_tcgdex_id(session, "swsh3-136")
        assert found is not None
        assert found.name == "Pikachu"

    def test_returns_none_for_non_deleted(self, session):
        card_service.create_card(session, CardCreate(tcgdex_id="swsh3-136", name="Pikachu"))

        found = card_service.get_deleted_card_by_tcgdex_id(session, "swsh3-136")
        assert found is None

    def test_returns_none_for_missing(self, session):
        found = card_service.get_deleted_card_by_tcgdex_id(session, "nonexistent")
        assert found is None


class TestDeleteCard:
    def test_soft_deletes(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="target-1", name="Target"))
        card_service.delete_card(session, card)

        assert card.is_deleted is True
        assert card.deleted_at is not None


class TestGetDeletedCards:
    def test_returns_only_deleted(self, session):
        card_service.create_card(session, CardCreate(tcgdex_id="alive-1", name="Alive"))
        deleted = card_service.create_card(session, CardCreate(tcgdex_id="del-1", name="Deleted"))
        card_service.delete_card(session, deleted)

        cards = card_service.get_deleted_cards(session)
        assert len(cards) == 1
        assert cards[0].tcgdex_id == "del-1"

    def test_returns_empty_when_none_deleted(self, session):
        card_service.create_card(session, CardCreate(tcgdex_id="alive-1", name="Alive"))

        cards = card_service.get_deleted_cards(session)
        assert len(cards) == 0

    def test_ordered_by_name(self, session):
        zeta = card_service.create_card(session, CardCreate(tcgdex_id="z-1", name="Zeta"))
        alpha = card_service.create_card(session, CardCreate(tcgdex_id="a-1", name="Alpha"))
        card_service.delete_card(session, zeta)
        card_service.delete_card(session, alpha)

        cards = card_service.get_deleted_cards(session)
        assert cards[0].name == "Alpha"
        assert cards[1].name == "Zeta"


class TestRestoreCard:
    def test_restores_deleted_card(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="target-1", name="Target"))
        card_service.delete_card(session, card)
        assert card.is_deleted is True

        card_service.restore_card(session, card)

        assert card.is_deleted is False
        assert card.deleted_at is None

    def test_restored_card_appears_in_all_cards(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="target-1", name="Target"))
        card_service.delete_card(session, card)
        card_service.restore_card(session, card)

        cards = card_service.get_all_cards(session)
        assert len(cards) == 1
        assert cards[0].tcgdex_id == "target-1"


class TestHardDeleteCard:
    def test_permanently_removes_card(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="target-1", name="Target"))
        card_id = card.id
        card_service.hard_delete_card(session, card)

        assert session.get(Card, card_id) is None

    def test_hard_deleted_not_in_deleted_cards(self, session):
        card = card_service.create_card(session, CardCreate(tcgdex_id="target-1", name="Target"))
        card_service.delete_card(session, card)
        card_service.hard_delete_card(session, card)

        cards = card_service.get_deleted_cards(session)
        assert len(cards) == 0
