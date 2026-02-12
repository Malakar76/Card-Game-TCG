"""Tests for scan screen language fallback and translation logic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, call

from tcgdexsdk import Language

from card_game_tcg.ui.screens.scan_screen import (
    _strip_card_suffix,
    _validate_and_translate,
)


def _make_card_resume(card_id: str, name: str) -> SimpleNamespace:
    """Create a minimal card-resume-like object."""
    return SimpleNamespace(id=card_id, name=name)


def _make_card(name: str) -> SimpleNamespace:
    """Create a minimal card-like object."""
    return SimpleNamespace(name=name)


class TestStripCardSuffix:
    """Tests for _strip_card_suffix."""

    def test_no_suffix(self) -> None:
        assert _strip_card_suffix("Dracaufeu") == "Dracaufeu"

    def test_strip_ex(self) -> None:
        assert _strip_card_suffix("Dracaufeu-EX") == "Dracaufeu"

    def test_strip_ex_lowercase(self) -> None:
        assert _strip_card_suffix("Dracaufeu ex") == "Dracaufeu"

    def test_strip_vmax(self) -> None:
        assert _strip_card_suffix("Dracaufeu VMAX") == "Dracaufeu"

    def test_strip_gx(self) -> None:
        assert _strip_card_suffix("Dracaufeu-GX") == "Dracaufeu"

    def test_strip_vstar(self) -> None:
        assert _strip_card_suffix("Dracaufeu VSTAR") == "Dracaufeu"


class TestValidateAndTranslate:
    """Tests for _validate_and_translate."""

    def test_found_in_target_language(self) -> None:
        """Candidate found in FR directly returns the OCR name."""
        client = MagicMock()
        client.search_cards_by_name.return_value = [_make_card_resume("swsh3-136", "Dracaufeu")]

        result = _validate_and_translate(client, "Dracaufeu", Language.FR)

        assert result == "Dracaufeu"
        client.search_cards_by_name.assert_called_once_with("Dracaufeu", Language.FR, page_size=1)
        client.get_card_in_language.assert_not_called()

    def test_fallback_translates_to_french(self) -> None:
        """Candidate not found in FR, found in EN, translates to FR."""
        client = MagicMock()
        client.search_cards_by_name.side_effect = [
            [],  # FR: not found
            [_make_card_resume("swsh3-136", "Charizard")],  # EN: found
        ]
        client.get_card_in_language.return_value = _make_card("Dracaufeu")

        result = _validate_and_translate(client, "Charizard", Language.FR)

        assert result == "Dracaufeu"
        assert client.search_cards_by_name.call_count == 2
        client.get_card_in_language.assert_called_once_with("swsh3-136", Language.FR)

    def test_not_found_in_any_language(self) -> None:
        """Candidate not found in any language returns None."""
        client = MagicMock()
        client.search_cards_by_name.return_value = []

        result = _validate_and_translate(client, "NotAPokemon", Language.FR)

        assert result is None
        assert client.search_cards_by_name.call_count == 5  # FR, EN, DE, ES, IT

    def test_suffix_stripped_on_translation(self) -> None:
        """Translated name has its TCG suffix stripped."""
        client = MagicMock()
        client.search_cards_by_name.side_effect = [
            [],  # FR
            [_make_card_resume("swsh3-136", "Charizard EX")],  # EN
        ]
        client.get_card_in_language.return_value = _make_card("Dracaufeu-EX")

        result = _validate_and_translate(client, "Charizard EX", Language.FR)

        assert result == "Dracaufeu"

    def test_get_card_in_language_calls_set_language(self) -> None:
        """get_card_in_language properly delegates to the SDK."""
        from card_game_tcg.clients.tcgdex import TCGDEX

        client = TCGDEX()
        client.sdk = MagicMock()
        client.sdk.card.getSync.return_value = _make_card("Dracaufeu")

        result = client.get_card_in_language("swsh3-136", Language.FR)

        client.sdk.setLanguage.assert_called_once_with(Language.FR)
        client.sdk.card.getSync.assert_called_once_with("swsh3-136")
        assert result.name == "Dracaufeu"

    def test_search_exception_skipped(self) -> None:
        """If search raises an exception for one language, try the next."""
        client = MagicMock()
        client.search_cards_by_name.side_effect = [
            Exception("network error"),  # FR
            [_make_card_resume("swsh3-136", "Charizard")],  # EN
        ]
        client.get_card_in_language.return_value = _make_card("Dracaufeu")

        result = _validate_and_translate(client, "Charizard", Language.FR)

        assert result == "Dracaufeu"

    def test_translation_failure_returns_none(self) -> None:
        """If translation card has no name, continue to next language."""
        client = MagicMock()
        client.search_cards_by_name.side_effect = [
            [],  # FR
            [_make_card_resume("swsh3-136", "Charizard")],  # EN
            [],  # DE
            [],  # ES
            [],  # IT
        ]
        client.get_card_in_language.return_value = _make_card("")

        result = _validate_and_translate(client, "Charizard", Language.FR)

        assert result is None

    def test_fallback_order(self) -> None:
        """Languages are tried in order: FR, EN, DE, ES, IT."""
        client = MagicMock()
        client.search_cards_by_name.return_value = []

        _validate_and_translate(client, "Test", Language.FR)

        expected_calls = [
            call("Test", Language.FR, page_size=1),
            call("Test", Language.EN, page_size=1),
            call("Test", Language.DE, page_size=1),
            call("Test", Language.ES, page_size=1),
            call("Test", Language.IT, page_size=1),
        ]
        assert client.search_cards_by_name.call_args_list == expected_calls
