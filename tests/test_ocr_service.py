"""Tests for the OCR service Pokemon name extraction."""

from pathlib import Path

import pytest

from card_game_tcg.services.ocr_service import extract_pokemon_name, is_available

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Pikachu", "Pikachu"),
        ("Dracaufeu", "Dracaufeu"),
        ("Mewtwo", "Mewtwo"),
    ],
)
def test_simple_names(text: str, expected: str) -> None:
    assert extract_pokemon_name(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Pikachu EX", "Pikachu"),
        ("Dracaufeu VMAX", "Dracaufeu"),
        ("Mewtwo GX", "Mewtwo"),
        ("Rayquaza VSTAR", "Rayquaza"),
        ("Gardevoir ex", "Gardevoir"),
        ("Mew V", "Mew"),
    ],
)
def test_suffix_stripping(text: str, expected: str) -> None:
    assert extract_pokemon_name(text) == expected


def test_skips_numeric_lines() -> None:
    text = "120\n30+\nPikachu\n50"
    assert extract_pokemon_name(text) == "Pikachu"


def test_multiline_takes_first_valid() -> None:
    text = "100\nDracaufeu VMAX\nAttaque Feu\n200"
    assert extract_pokemon_name(text) == "Dracaufeu"


def test_empty_text_returns_none() -> None:
    assert extract_pokemon_name("") is None


def test_whitespace_only_returns_none() -> None:
    assert extract_pokemon_name("   \n  \n  ") is None


def test_only_numbers_returns_none() -> None:
    assert extract_pokemon_name("120\n30\n50") is None


def test_leading_blank_lines_skipped() -> None:
    text = "\n\n\nFlorizarre\nSolar Beam"
    assert extract_pokemon_name(text) == "Florizarre"


def test_suffix_with_dash() -> None:
    text = "Pikachu - EX"
    assert extract_pokemon_name(text) == "Pikachu"


def test_none_returns_none() -> None:
    assert extract_pokemon_name(None) is None  # type: ignore[arg-type]


def test_is_available_returns_bool() -> None:
    result = is_available()
    assert isinstance(result, bool)


# --- Integration tests (require easyocr, slow) ---


@pytest.mark.slow
def test_recognize_card_image() -> None:
    """Full pipeline: OCR on a real card image extracts the Pokemon name."""
    from card_game_tcg.services.ocr_service import recognize_text_from_file

    image_path = FIXTURES_DIR / "nucleos_card.png"
    if not image_path.exists():
        pytest.skip("Test fixture nucleos_card.png not found")

    if not is_available():
        pytest.skip("No OCR backend available")

    raw_text = recognize_text_from_file(image_path)
    assert raw_text, "OCR returned empty text"

    name = extract_pokemon_name(raw_text)
    assert name is not None, f"Could not extract name from OCR text: {raw_text!r}"
    assert name.lower() == "nucleos", f"Expected 'Nucleos', got {name!r}"


@pytest.mark.slow
def test_recognize_card_image_raw_text_contains_collision() -> None:
    """OCR should also detect the attack name 'Collision' on the card."""
    from card_game_tcg.services.ocr_service import recognize_text_from_file

    image_path = FIXTURES_DIR / "nucleos_card.png"
    if not image_path.exists():
        pytest.skip("Test fixture nucleos_card.png not found")

    if not is_available():
        pytest.skip("No OCR backend available")

    raw_text = recognize_text_from_file(image_path)
    # EasyOCR may return "Collislon" or "Collision" depending on confidence
    assert any(word in raw_text.lower() for word in ("collision", "collislon")), (
        f"Expected 'Collision' in OCR text: {raw_text!r}"
    )
