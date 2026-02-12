"""Tests for evolution chain resolution logic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from tcgdexsdk import Language

from card_game_tcg.ui.screens.evolution_screen import (
    _cached_exact_search,
    _cached_get_card,
    _resolve_parent,
    _species_name,
    resolve_evolution_chain,
)


def _make_card_resume(card_id: str, name: str, image: str = "") -> SimpleNamespace:
    """Create a minimal card-resume-like object."""
    return SimpleNamespace(id=card_id, name=name, image=image)


def _make_card(name: str, image: str = "", evolve_from: str = "") -> SimpleNamespace:
    """Create a minimal card-like object with evolveFrom."""
    return SimpleNamespace(name=name, image=image, evolveFrom=evolve_from)


def _setup_client(
    *,
    name_results: dict[str, list] | None = None,
    exact_name_results: dict[str, list] | None = None,
    card_details: dict[str, SimpleNamespace] | None = None,
    evolve_from_results: dict[str, list] | None = None,
) -> MagicMock:
    """Build a mock TCGDEX client with lookup tables."""
    client = MagicMock()

    _name = name_results or {}
    _exact = exact_name_results or {}
    _cards = card_details or {}
    _evo = evolve_from_results or {}

    client.search_cards_by_name.side_effect = lambda n, lang, page_size=20: _name.get(n, [])
    client.search_cards_by_exact_name.side_effect = lambda n, lang: _exact.get(n, [])
    client.get_card.side_effect = lambda cid: _cards.get(cid)
    client.search_by_evolve_from.side_effect = lambda n, lang: _evo.get(n, [])
    return client


class TestResolveEvolutionChain:
    """Test the resolve_evolution_chain function with mocked API."""

    def test_base_pokemon_alone(self) -> None:
        """A Pokémon with no pre-evolution and no evolution returns only itself."""
        client = _setup_client(
            name_results={
                "Kangaskhan": [
                    _make_card_resume("swsh1-100", "Kangaskhan", "https://img/kangaskhan")
                ],
            },
            exact_name_results={
                "Kangaskhan": [
                    _make_card_resume("swsh1-100", "Kangaskhan", "https://img/kangaskhan")
                ],
            },
            card_details={
                "swsh1-100": _make_card("Kangaskhan", "https://img/kangaskhan"),
            },
        )

        chain = resolve_evolution_chain(client, "Kangaskhan", Language.FR)

        assert len(chain) == 1
        assert chain[0][0] == "Kangaskhan"
        assert chain[0][2] == "Base"

    def test_linear_chain_three_stages(self) -> None:
        """Charmander -> Charmeleon -> Charizard should produce a 3-member chain."""
        client = _setup_client(
            name_results={
                "Charmeleon": [_make_card_resume("xy1-12", "Charmeleon", "https://img/charmeleon")],
            },
            exact_name_results={
                "Charmeleon": [_make_card_resume("xy1-12", "Charmeleon", "https://img/charmeleon")],
                "Charmander": [_make_card_resume("xy1-11", "Charmander", "https://img/charmander")],
            },
            card_details={
                "xy1-12": _make_card(
                    "Charmeleon", "https://img/charmeleon", evolve_from="Charmander"
                ),
                "xy1-11": _make_card("Charmander", "https://img/charmander"),
            },
            evolve_from_results={
                "Charmander": [_make_card_resume("xy1-12", "Charmeleon", "https://img/charmeleon")],
                "Charmeleon": [_make_card_resume("xy1-13", "Charizard", "https://img/charizard")],
            },
        )

        chain = resolve_evolution_chain(client, "Charmeleon", Language.FR)

        assert len(chain) == 3
        assert chain[0] == ("Charmander", "https://img/charmander/high.png", "Base")
        assert chain[1] == ("Charmeleon", "https://img/charmeleon/high.png", "Stage 1")
        assert chain[2] == ("Charizard", "https://img/charizard/high.png", "Stage 2")

    def test_branching_evolutions(self) -> None:
        """Eevee -> Vaporeon, Jolteon, Flareon should produce 4 members."""
        client = _setup_client(
            name_results={
                "Eevee": [_make_card_resume("xy1-20", "Eevee", "https://img/eevee")],
            },
            exact_name_results={
                "Eevee": [_make_card_resume("xy1-20", "Eevee", "https://img/eevee")],
            },
            card_details={
                "xy1-20": _make_card("Eevee", "https://img/eevee"),
            },
            evolve_from_results={
                "Eevee": [
                    _make_card_resume("xy1-21", "Vaporeon", "https://img/vaporeon"),
                    _make_card_resume("xy1-22", "Jolteon", "https://img/jolteon"),
                    _make_card_resume("xy1-23", "Flareon", "https://img/flareon"),
                ],
            },
        )

        chain = resolve_evolution_chain(client, "Eevee", Language.FR)

        assert len(chain) == 4
        assert chain[0][0] == "Eevee"
        assert chain[0][2] == "Base"
        evo_names = {chain[1][0], chain[2][0], chain[3][0]}
        assert evo_names == {"Vaporeon", "Jolteon", "Flareon"}
        assert all(c[2] == "Stage 1" for c in chain[1:])

    def test_no_results_returns_empty(self) -> None:
        """If the API returns no results for the name, return an empty chain."""
        client = _setup_client()

        chain = resolve_evolution_chain(client, "UnknownMon", Language.FR)

        assert chain == []

    def test_variant_cards_deduplicated(self) -> None:
        """Variants (GX, EX, δ, etc.) should be grouped into one species entry."""
        client = _setup_client(
            name_results={
                "Charmander": [_make_card_resume("xy1-11", "Charmander", "https://img/charmander")],
            },
            exact_name_results={
                "Charmander": [_make_card_resume("xy1-11", "Charmander", "https://img/charmander")],
            },
            card_details={
                "xy1-11": _make_card("Charmander", "https://img/charmander"),
            },
            evolve_from_results={
                "Charmander": [
                    _make_card_resume("xy1-12a", "Charmeleon", "https://img/charmeleon"),
                    _make_card_resume("xy1-12b", "Charmeleon GX", "https://img/charmeleon-gx"),
                    _make_card_resume("xy1-12c", "Charmeleon δ", "https://img/charmeleon-d"),
                    _make_card_resume("xy1-12d", "Charmeleon", "https://img/charmeleon2"),
                ],
            },
        )

        chain = resolve_evolution_chain(client, "Charmander", Language.FR)

        assert len(chain) == 2
        assert chain[0][0] == "Charmander"
        assert chain[1][0] == "Charmeleon"

    def test_inconsistent_evolve_from_resolved(self) -> None:
        """When first card has an unfindable evolveFrom, try other printings.

        Simulates the Dracolosse case: first card says evolveFrom="Dragonir"
        (not found), but another printing says evolveFrom="Draco" (found).
        """
        client = _setup_client(
            name_results={
                "Dracolosse": [_make_card_resume("dp6-2", "Dracolosse", "https://img/dracolosse")],
            },
            exact_name_results={
                "Dracolosse": [
                    _make_card_resume("dp6-2", "Dracolosse", "https://img/dracolosse"),
                    _make_card_resume("dv1-5", "Dracolosse", "https://img/dracolosse2"),
                ],
                "Draco": [
                    _make_card_resume("dv1-3", "Draco", "https://img/draco"),
                ],
                "Minidraco": [
                    _make_card_resume("dv1-1", "Minidraco", "https://img/minidraco"),
                ],
            },
            card_details={
                # First Dracolosse has unfindable "Dragonir"
                "dp6-2": _make_card("Dracolosse", "https://img/dracolosse", evolve_from="Dragonir"),
                # Second Dracolosse has correct "Draco"
                "dv1-5": _make_card("Dracolosse", "https://img/dracolosse2", evolve_from="Draco"),
                "dv1-3": _make_card("Draco", "https://img/draco", evolve_from="Minidraco"),
                "dv1-1": _make_card("Minidraco", "https://img/minidraco"),
            },
            evolve_from_results={
                "Minidraco": [
                    _make_card_resume("dv1-3", "Draco", "https://img/draco"),
                ],
                "Draco": [
                    _make_card_resume("dp6-2", "Dracolosse", "https://img/dracolosse"),
                ],
            },
        )

        chain = resolve_evolution_chain(client, "Dracolosse", Language.FR)

        assert len(chain) == 3
        assert chain[0][0] == "Minidraco"
        assert chain[0][2] == "Base"
        assert chain[1][0] == "Draco"
        assert chain[1][2] == "Stage 1"
        assert chain[2][0] == "Dracolosse"
        assert chain[2][2] == "Stage 2"


class TestCachedGetCard:
    """Test the _cached_get_card helper."""

    def test_returns_card_and_caches(self) -> None:
        """First call fetches from client, second uses cache."""
        card = _make_card("Pikachu", "https://img/pikachu")
        client = MagicMock()
        client.get_card.return_value = card

        cache: dict[str, object | None] = {}
        result = _cached_get_card(client, "xy1-50", cache)

        assert result is card
        assert "xy1-50" in cache
        client.get_card.assert_called_once_with("xy1-50")

        # Second call should use cache, not the client
        result2 = _cached_get_card(client, "xy1-50", cache)
        assert result2 is card
        client.get_card.assert_called_once()  # still only one call

    def test_caches_none_on_exception(self) -> None:
        """If get_card raises, cache None to avoid retrying."""
        client = MagicMock()
        client.get_card.side_effect = Exception("API error")

        cache: dict[str, object | None] = {}
        result = _cached_get_card(client, "bad-id", cache)

        assert result is None
        assert cache["bad-id"] is None


class TestCachedExactSearch:
    """Test the _cached_exact_search helper."""

    def test_returns_results_and_caches(self) -> None:
        resumes = [_make_card_resume("xy1-50", "Pikachu")]
        client = MagicMock()
        client.search_cards_by_exact_name.return_value = resumes

        cache: dict[str, list] = {}
        result = _cached_exact_search(client, "Pikachu", Language.FR, cache)

        assert result == resumes
        assert "Pikachu" in cache

        # Second call uses cache
        _cached_exact_search(client, "Pikachu", Language.FR, cache)
        client.search_cards_by_exact_name.assert_called_once()


class TestResolveParent:
    """Test the _resolve_parent helper."""

    def test_direct_lookup_succeeds(self) -> None:
        """Parent found directly via evolveFrom name."""
        parent_card = _make_card("Charmander", "https://img/charmander")
        client = _setup_client(
            exact_name_results={
                "Charmander": [_make_card_resume("xy1-11", "Charmander")],
            },
            card_details={
                "xy1-11": parent_card,
            },
        )

        exact_cache: dict[str, list] = {}
        card_cache: dict[str, object | None] = {}
        result = _resolve_parent(
            client, "Charmander", "Charmeleon", Language.FR, exact_cache, card_cache
        )

        assert result is parent_card

    def test_fallback_to_alternative_printing(self) -> None:
        """When direct evolveFrom is not found, try other printings."""
        parent_card = _make_card("Draco", "https://img/draco", evolve_from="Minidraco")
        client = _setup_client(
            exact_name_results={
                # "Dragonir" not found
                "Dracolosse": [
                    _make_card_resume("dp6-2", "Dracolosse"),
                    _make_card_resume("dv1-5", "Dracolosse"),
                ],
                "Draco": [_make_card_resume("dv1-3", "Draco")],
            },
            card_details={
                "dp6-2": _make_card("Dracolosse", "https://img/d1", evolve_from="Dragonir"),
                "dv1-5": _make_card("Dracolosse", "https://img/d2", evolve_from="Draco"),
                "dv1-3": parent_card,
            },
        )

        exact_cache: dict[str, list] = {}
        card_cache: dict[str, object | None] = {}
        result = _resolve_parent(
            client, "Dragonir", "Dracolosse", Language.FR, exact_cache, card_cache
        )

        assert result is parent_card

    def test_returns_none_when_nothing_found(self) -> None:
        """Return None when neither direct nor fallback finds a parent."""
        client = _setup_client(
            exact_name_results={
                "UnknownMon": [_make_card_resume("x-1", "UnknownMon")],
            },
            card_details={
                "x-1": _make_card("UnknownMon", ""),
            },
        )

        result = _resolve_parent(client, "NoParent", "UnknownMon", Language.FR, {}, {})

        assert result is None


class TestSpeciesName:
    """Test the _species_name normalization helper."""

    def test_plain_name_unchanged(self) -> None:
        assert _species_name("Pikachu") == "Pikachu"

    def test_strips_gx(self) -> None:
        assert _species_name("Dracolosse GX") == "Dracolosse"

    def test_strips_ex_lowercase(self) -> None:
        assert _species_name("Dracolosse ex") == "Dracolosse"

    def test_strips_hyphen_ex(self) -> None:
        assert _species_name("Dracolosse-ex") == "Dracolosse"

    def test_strips_delta(self) -> None:
        assert _species_name("Draco δ") == "Draco"

    def test_strips_vmax(self) -> None:
        assert _species_name("Pikachu VMAX") == "Pikachu"

    def test_strips_multiple_suffixes(self) -> None:
        assert _species_name("Dracolosse ex δ") == "Dracolosse"

    def test_strips_lumineux(self) -> None:
        assert _species_name("Draco lumineux") == "Draco"

    def test_strips_mega_prefix(self) -> None:
        assert _species_name("M Dracolosse-EX") == "Dracolosse"

    def test_strips_turbo(self) -> None:
        assert _species_name("Raichu TURBO") == "Raichu"

    def test_strips_level(self) -> None:
        assert _species_name("Pyroli Niv. 38") == "Pyroli"
        assert _species_name("Voltali Niv. 43") == "Voltali"

    def test_strips_alola_curly_apostrophe(self) -> None:
        assert _species_name("Raichu d\u2019Alola") == "Raichu"

    def test_no_false_positive_on_similar_name(self) -> None:
        """'Dracolosse' must not be truncated when 'Draco' is a substring."""
        assert _species_name("Dracolosse") == "Dracolosse"
        assert _species_name("Minidraco") == "Minidraco"
