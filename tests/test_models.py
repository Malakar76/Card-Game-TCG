"""Tests for document models."""

from unittest.mock import AsyncMock, MagicMock, patch

from card_game_tcg.models import BaseDocument, Card

_NOT_DELETED = {"deleted_at": None}


def test_card_has_base_fields():
    fields = Card.model_fields
    assert "created_at" in fields
    assert "updated_at" in fields
    assert "deleted_at" in fields


def test_card_has_own_fields():
    fields = Card.model_fields
    assert "name" in fields
    assert "description" in fields
    assert "attack" in fields
    assert "defense" in fields
    assert "cost" in fields


# --- Soft-delete filtering tests ---

_PARENT_CLS = BaseDocument.__mro__[1]


def _mock_query(result: list | None = None) -> MagicMock:
    """Create a mock query builder that supports .to_list()."""
    query = MagicMock()
    query.to_list = AsyncMock(return_value=result if result is not None else [])
    return query


class TestSoftDeleteFiltering:
    """Tests that BaseDocument overrides inject deleted_at filter."""

    def test_find_many_exists_on_base(self):
        assert hasattr(BaseDocument, "find_many")

    def test_find_one_exists_on_base(self):
        assert hasattr(BaseDocument, "find_one")

    def test_find_all_exists_on_base(self):
        assert hasattr(BaseDocument, "find_all")

    def test_get_exists_on_base(self):
        assert hasattr(BaseDocument, "get")

    def test_find_is_find_many(self):
        assert BaseDocument.find == BaseDocument.find_many

    @patch.object(_PARENT_CLS, "find_many")
    async def test_find_many_injects_filter(self, mock_super: MagicMock):
        mock_super.return_value = _mock_query()
        await Card.find_many({"name": "test"})
        args = mock_super.call_args[0]
        assert _NOT_DELETED in args

    @patch.object(_PARENT_CLS, "find_many")
    async def test_find_many_include_deleted_skips_filter(self, mock_super: MagicMock):
        mock_super.return_value = _mock_query()
        await Card.find_many({"name": "test"}, include_deleted=True)
        args = mock_super.call_args[0]
        assert _NOT_DELETED not in args

    @patch.object(_PARENT_CLS, "find_one", new_callable=AsyncMock)
    async def test_find_one_injects_filter(self, mock_super: AsyncMock):
        mock_super.return_value = None
        await Card.find_one({"name": "test"})
        args = mock_super.call_args[0]
        assert _NOT_DELETED in args

    @patch.object(_PARENT_CLS, "find_one", new_callable=AsyncMock)
    async def test_find_one_include_deleted_skips_filter(self, mock_super: AsyncMock):
        mock_super.return_value = None
        await Card.find_one({"name": "test"}, include_deleted=True)
        args = mock_super.call_args[0]
        assert _NOT_DELETED not in args

    @patch.object(_PARENT_CLS, "find_many")
    async def test_find_all_injects_filter(self, mock_super: MagicMock):
        mock_super.return_value = _mock_query()
        await Card.find_all()
        args = mock_super.call_args[0]
        assert _NOT_DELETED in args

    @patch.object(_PARENT_CLS, "find_many")
    async def test_find_all_include_deleted_skips_filter(self, mock_super: MagicMock):
        mock_super.return_value = _mock_query()
        await Card.find_all(include_deleted=True)
        args = mock_super.call_args[0]
        assert _NOT_DELETED not in args

    async def test_get_filters_deleted_document(self):
        deleted_card = MagicMock(spec=Card)
        deleted_card.deleted_at = "2024-01-01"

        with patch.object(_PARENT_CLS, "get", new_callable=AsyncMock, return_value=deleted_card):
            result = await Card.get("some-id")
            assert result is None

    async def test_get_returns_non_deleted_document(self):
        active_card = MagicMock(spec=Card)
        active_card.deleted_at = None

        with patch.object(_PARENT_CLS, "get", new_callable=AsyncMock, return_value=active_card):
            result = await Card.get("some-id")
            assert result is active_card

    async def test_get_include_deleted_returns_deleted_document(self):
        deleted_card = MagicMock(spec=Card)
        deleted_card.deleted_at = "2024-01-01"

        with patch.object(_PARENT_CLS, "get", new_callable=AsyncMock, return_value=deleted_card):
            result = await Card.get("some-id", include_deleted=True)
            assert result is deleted_card
