"""Screen for searching cards via the TCGdex API."""

from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen
from tcgdexsdk import Language

from card_game_tcg.clients import TCGDEX
from card_game_tcg.db.session import SessionLocal
from card_game_tcg.schemas.card import CardCreate
from card_game_tcg.services import card_service

Builder.load_file(str(Path(__file__).parent.parent / "kv" / "searchscreen.kv"))

LANGUAGES: list[tuple[str, Language]] = [
    ("Français", Language.FR),
    ("English", Language.EN),
    ("Deutsch", Language.DE),
    ("Español", Language.ES),
    ("Italiano", Language.IT),
    ("日本語", Language.JA),
]

PAGE_SIZE = 20

_client = TCGDEX()


class SearchResultRow(RecycleDataViewBehavior, BoxLayout):
    """A single row in the search results RecycleView."""

    card_id = StringProperty("")
    card_name = StringProperty("")
    card_image = StringProperty("")
    in_collection = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        self.card_id = data.get("card_id", "")
        self.card_name = data.get("card_name", "")
        self.card_image = data.get("card_image", "")
        self.in_collection = data.get("in_collection", False)
        return super().refresh_view_attrs(rv, index, data)

    def show_details(self) -> None:
        """Fetch full card details in a background thread, then show popup."""
        card_id = self.card_id

        def _fetch() -> None:
            card = _client.get_card(card_id)
            if card is None:
                return
            Clock.schedule_once(lambda _dt: _show_popup(card))

        def _show_popup(card) -> None:  # type: ignore[no-untyped-def]
            lines = [
                f"[b]{card.name}[/b]",
                "",
            ]
            if card.category:
                lines.append(f"Catégorie : {card.category}")
            if card.rarity:
                lines.append(f"Rareté : {card.rarity}")
            if card.hp is not None:
                lines.append(f"HP : {card.hp}")
            if card.types:
                lines.append(f"Types : {', '.join(card.types)}")
            if card.stage:
                lines.append(f"Stage : {card.stage}")
            if card.evolveFrom:
                lines.append(f"Évolue de : {card.evolveFrom}")
            if card.description:
                lines.append(f"\n{card.description}")
            if card.attacks:
                lines.append("")
                for atk in card.attacks:
                    cost = ", ".join(atk.cost) if atk.cost else "—"
                    dmg = atk.damage if atk.damage else ""
                    lines.append(f"[b]{atk.name}[/b]  ({cost})  {dmg}")
                    if atk.effect:
                        lines.append(f"  {atk.effect}")
            if card.weaknesses:
                parts = [f"{w.type} {w.value}" for w in card.weaknesses]
                lines.append(f"\nFaiblesse : {', '.join(parts)}")
            if card.resistances:
                parts = [f"{r.type} {r.value}" for r in card.resistances]
                lines.append(f"Résistance : {', '.join(parts)}")
            if card.retreat is not None:
                lines.append(f"Retraite : {card.retreat}")
            if card.set:
                lines.append(f"\nSet : {card.set.name}")

            image_url = f"{card.image}/high.png" if card.image else ""
            popup = CardDetailPopup(
                title=card.name, detail_text="\n".join(lines), detail_image=image_url
            )
            popup.open()

        Thread(target=_fetch, daemon=True).start()

    def add_to_collection(self) -> None:
        """Add this card to the local SQLite collection."""
        if self.in_collection:
            return

        screen = self.parent
        while screen is not None and not isinstance(screen, SearchScreen):
            screen = screen.parent

        session = SessionLocal()
        try:
            existing = card_service.get_card_by_tcgdex_id(session, self.card_id)
            if existing:
                self.in_collection = True
                if screen:
                    screen._mark_in_collection(self.card_id)
                return

            deleted = card_service.get_deleted_card_by_tcgdex_id(session, self.card_id)
            if deleted:
                card_service.restore_card(session, deleted)
            else:
                data = CardCreate(
                    tcgdex_id=self.card_id,
                    name=self.card_name,
                    image_url=self.card_image if self.card_image else None,
                )
                card_service.create_card(session, data)
            self.in_collection = True
            if screen:
                screen._mark_in_collection(self.card_id)
                screen.status_text = f"« {self.card_name} » ajoutée à la collection !"
        except Exception as exc:
            if screen:
                screen.status_text = f"Erreur : {exc}"
        finally:
            session.close()


class CardDetailPopup(Popup):
    """Popup displaying full card details."""

    detail_text = StringProperty("")
    detail_image = StringProperty("")


class SearchScreen(Screen):
    """Screen for searching Pokémon cards on TCGdex."""

    status_text = StringProperty("")

    _current_query: str = ""
    _current_lang: Language = Language.FR
    _current_page: int = 1

    def search(self, name: str, language_label: str) -> None:
        """Search cards by name via the TCGdex API."""
        name = name.strip()
        if not name:
            self.status_text = "Entrez un nom de carte."
            self.ids.rv.data = []
            return

        lang = Language.FR
        for label, lang_enum in LANGUAGES:
            if label == language_label:
                lang = lang_enum
                break

        self._current_query = name
        self._current_lang = lang
        self._current_page = 1
        self._do_search()

    def _get_collection_ids(self) -> set[str]:
        """Return the set of tcgdex_ids currently in the collection."""
        session = SessionLocal()
        try:
            cards = card_service.get_all_cards(session)
            return {c.tcgdex_id for c in cards}
        finally:
            session.close()

    def _mark_in_collection(self, tcgdex_id: str) -> None:
        """Update the RecycleView data to flag a card as in_collection."""
        for item in self.ids.rv.data:
            if item["card_id"] == tcgdex_id:
                item["in_collection"] = True
        self.ids.rv.refresh_from_data()

    def _do_search(self) -> None:
        """Execute the search with current query, language, and page."""
        try:
            results = _client.search_cards_by_name(
                self._current_query,
                self._current_lang,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )
        except Exception as exc:
            self.status_text = f"Erreur : {exc}"
            self.ids.rv.data = []
            return

        if not results:
            if self._current_page == 1:
                self.status_text = "Aucun résultat."
            else:
                self._current_page -= 1
                self.status_text = f"Page {self._current_page} (dernière page)"
            self.ids.rv.data = []
            return

        owned = self._get_collection_ids()
        self.status_text = f"Page {self._current_page} — {len(results)} résultat(s)"
        self.ids.rv.data = [
            {
                "card_id": card.id,
                "card_name": card.name,
                "card_image": f"{card.image}/low.png" if card.image else "",
                "in_collection": card.id in owned,
            }
            for card in results
        ]

    def prev_page(self) -> None:
        """Go to the previous page of results."""
        if self._current_page > 1 and self._current_query:
            self._current_page -= 1
            self._do_search()

    def next_page(self) -> None:
        """Go to the next page of results."""
        if self._current_query:
            self._current_page += 1
            self._do_search()
