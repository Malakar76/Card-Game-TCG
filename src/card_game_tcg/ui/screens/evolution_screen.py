"""Screen displaying the evolution family of a scanned Pokémon."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen
from tcgdexsdk import Language

from card_game_tcg.clients import TCGDEX
from card_game_tcg.ui.constants import LANGUAGES

logger = logging.getLogger(__name__)

Builder.load_file(str(Path(__file__).parent.parent / "kv" / "evolutionscreen.kv"))

_client = TCGDEX()


class EvolutionRow(RecycleDataViewBehavior, BoxLayout):
    """A single row in the evolution chain RecycleView."""

    evo_name = StringProperty("")
    evo_image = StringProperty("")
    evo_stage = StringProperty("")

    def refresh_view_attrs(self, rv, index, data):  # type: ignore[no-untyped-def]
        self.evo_name = data.get("evo_name", "")
        self.evo_image = data.get("evo_image", "")
        self.evo_stage = data.get("evo_stage", "")
        return super().refresh_view_attrs(rv, index, data)


class EvolutionScreen(Screen):
    """Screen that displays the full evolution family of a Pokémon."""

    pokemon_name = StringProperty("")
    selected_language = StringProperty("Français")
    status_text = StringProperty("")
    is_loading = BooleanProperty(False)
    chain_data = ListProperty([])

    _request_id: int = 0

    def on_enter(self) -> None:
        """Start resolving the evolution chain when entering the screen."""
        if not self.pokemon_name:
            self.status_text = "Aucun Pokémon sélectionné"
            return

        self._request_id += 1
        request_id = self._request_id

        self.is_loading = True
        self.status_text = "Recherche de la famille d'évolution..."
        self.chain_data = []

        language = self._get_language()
        Thread(
            target=self._resolve_chain,
            args=(self.pokemon_name, language, request_id),
            daemon=True,
        ).start()

    def _get_language(self) -> Language:
        """Resolve the selected language label to a ``Language`` enum."""
        for label, lang in LANGUAGES:
            if label == self.selected_language:
                return lang
        return Language.FR

    def go_back(self) -> None:
        """Navigate back to the scan screen."""
        self.manager.current = "scan"

    def _resolve_chain(self, name: str, language: Language, request_id: int) -> None:
        """Resolve the full evolution chain in a background thread."""
        try:
            chain = resolve_evolution_chain(_client, name, language)
            Clock.schedule_once(lambda _dt: self._on_chain_resolved(chain, request_id))
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda _dt: self._on_chain_error(msg, request_id))

    def _on_chain_resolved(self, chain: list[tuple[str, str, str]], request_id: int) -> None:
        """Handle resolved chain on the main thread."""
        if request_id != self._request_id:
            return
        self.is_loading = False
        if not chain:
            self.status_text = "Aucune famille d'évolution trouvée"
            return

        self.status_text = f"{len(chain)} membre(s) trouvé(s)"
        self.chain_data = [
            {"evo_name": name, "evo_image": image, "evo_stage": stage}
            for name, image, stage in chain
        ]

    def _on_chain_error(self, error: str, request_id: int) -> None:
        """Handle chain resolution error on the main thread."""
        if request_id != self._request_id:
            return
        self.is_loading = False
        self.status_text = f"Erreur : {error}"


def resolve_evolution_chain(
    client: TCGDEX, name: str, language: Language
) -> list[tuple[str, str, str]]:
    """Resolve the full evolution chain for a Pokémon.

    Returns a list of ``(name, image_url, stage_label)`` tuples ordered
    from base form to final evolution.  Handles branching evolutions
    (e.g. Eevee -> multiple stage-1 forms).

    Uses per-resolution caches to minimise API calls.
    """
    card_cache: dict[str, object | None] = {}
    exact_cache: dict[str, list[object]] = {}

    # 1. Get a card for the detected name
    results = client.search_cards_by_name(name, language, page_size=1)
    if not results:
        return []

    card = _cached_get_card(client, results[0].id, card_cache)
    if card is None:
        return []

    # 2. Climb to the base form using the initial evolveFrom directly
    base_name = card.name
    base_image = f"{card.image}/high.png" if card.image else ""

    visited: set[str] = {base_name}
    evolve_from = card.evolveFrom
    while evolve_from and evolve_from not in visited:
        parent = _resolve_parent(client, evolve_from, base_name, language, exact_cache, card_cache)
        if parent is None:
            break
        visited.add(parent.name)
        base_name = parent.name
        base_image = f"{parent.image}/high.png" if parent.image else ""
        evolve_from = parent.evolveFrom

    # 3. Descend from the base form to collect the full tree
    chain: list[tuple[str, str, str]] = []
    desc_visited: set[str] = set()
    _collect_descendants(
        client, base_name, base_image, language, chain, depth=0, visited=desc_visited
    )

    return chain


def _cached_get_card(
    client: TCGDEX, card_id: str, cache: dict[str, object | None]
) -> object | None:
    """Fetch a card by ID, using a local cache to avoid duplicate API calls."""
    if card_id in cache:
        return cache[card_id]
    try:
        card = client.get_card(card_id)
    except Exception:
        card = None
    cache[card_id] = card
    return card


def _cached_exact_search(
    client: TCGDEX, name: str, language: Language, cache: dict[str, list[object]]
) -> list[object]:
    """Search cards by exact name, using a local cache."""
    if name in cache:
        return cache[name]
    results = client.search_cards_by_exact_name(name, language)
    cache[name] = results
    return results


def _resolve_parent(
    client: TCGDEX,
    evolve_from: str,
    current_name: str,
    language: Language,
    exact_cache: dict[str, list[object]],
    card_cache: dict[str, object | None],
) -> object | None:
    """Resolve the parent card for a given ``evolveFrom`` value.

    First tries the direct ``evolve_from`` name.  If that name cannot be
    found in TCGdex, falls back to checking other printings of
    ``current_name`` for an alternative ``evolveFrom`` value.
    """
    # Direct lookup: search for the evolveFrom name
    parent_results = _cached_exact_search(client, evolve_from, language, exact_cache)
    if parent_results:
        parent = _cached_get_card(client, parent_results[0].id, card_cache)
        if parent is not None:
            return parent

    # Fallback: try other printings of current_name for a different evolveFrom
    printings = _cached_exact_search(client, current_name, language, exact_cache)
    seen_names: set[str] = {evolve_from}
    for printing in printings:
        full = _cached_get_card(client, printing.id, card_cache)
        if full is None or not full.evolveFrom or full.evolveFrom in seen_names:
            continue
        seen_names.add(full.evolveFrom)
        alt_results = _cached_exact_search(client, full.evolveFrom, language, exact_cache)
        if alt_results:
            parent = _cached_get_card(client, alt_results[0].id, card_cache)
            if parent is not None:
                return parent

    return None


_VARIANT_SUFFIX = re.compile(
    r"[\s\-]+"
    r"(?:EX|GX|ex|V|VMAX|VSTAR|BREAK|TURBO|V-UNION"
    r"|δ|SP|GL|FB|LV\.X"
    r"|Niv\.\s*\d+"
    r"|lumineux|lumineuse|obscur|obscure"
    r"|d['\u2019]Alola|de Galar|de Hisui|de Paldea)$"
)

_VARIANT_PREFIX = re.compile(r"^M[\s\-]+")


def _species_name(card_name: str) -> str:
    """Extract the base species name by stripping TCG variant suffixes/prefixes."""
    name = card_name.strip()
    while True:
        stripped = _VARIANT_SUFFIX.sub("", name).strip()
        if stripped == name:
            break
        name = stripped
    name = _VARIANT_PREFIX.sub("", name).strip()
    return name


def _collect_descendants(
    client: TCGDEX,
    name: str,
    image: str,
    language: Language,
    chain: list[tuple[str, str, str]],
    depth: int,
    visited: set[str],
) -> None:
    """Recursively collect a Pokémon and all its evolutions."""
    species = _species_name(name)
    if species in visited:
        return
    visited.add(species)

    stage_labels = ["Base", "Stage 1", "Stage 2"]
    stage = stage_labels[depth] if depth < len(stage_labels) else f"Stage {depth}"
    chain.append((name, image, stage))

    # Find all cards that evolve from this Pokémon
    try:
        evo_results = client.search_by_evolve_from(name, language)
    except Exception:
        return

    if not evo_results:
        return

    for evo_card in evo_results:
        evo_species = _species_name(evo_card.name)
        if evo_species in visited:
            continue
        evo_image = f"{evo_card.image}/high.png" if evo_card.image else ""
        _collect_descendants(client, evo_species, evo_image, language, chain, depth + 1, visited)
