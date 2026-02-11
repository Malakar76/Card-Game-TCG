"""Tests for SQLAlchemy models."""

from sqlalchemy.exc import IntegrityError

from card_game_tcg.models.card import Card


class TestCardColumns:
    def test_card_has_base_columns(self, session):
        card = Card(tcgdex_id="swsh3-136", name="Test")
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.id is not None
        assert card.created_at is not None
        assert card.updated_at is not None
        assert card.deleted_at is None

    def test_card_has_own_columns(self, session):
        card = Card(
            tcgdex_id="swsh3-136",
            name="Pikachu",
            image_url="https://example.com/pikachu.png",
        )
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.tcgdex_id == "swsh3-136"
        assert card.name == "Pikachu"
        assert card.image_url == "https://example.com/pikachu.png"

    def test_card_image_url_nullable(self, session):
        card = Card(tcgdex_id="swsh3-136", name="Pikachu")
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.image_url is None

    def test_tcgdex_id_unique(self, session):
        card1 = Card(tcgdex_id="swsh3-136", name="Pikachu")
        card2 = Card(tcgdex_id="swsh3-136", name="Pikachu V")
        session.add(card1)
        session.commit()
        session.add(card2)
        try:
            session.commit()
            assert False, "Expected IntegrityError"
        except IntegrityError:
            session.rollback()


class TestSoftDelete:
    def test_soft_delete_sets_deleted_at(self, session):
        card = Card(tcgdex_id="swsh3-136", name="Target")
        session.add(card)
        session.commit()

        card.soft_delete(session)
        session.commit()
        session.refresh(card)

        assert card.deleted_at is not None
        assert card.is_deleted is True

    def test_restore_clears_deleted_at(self, session):
        card = Card(tcgdex_id="swsh3-136", name="Target")
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
        card = Card(tcgdex_id="swsh3-136", name="Active")
        session.add(card)
        session.commit()
        session.refresh(card)

        assert card.is_deleted is False
