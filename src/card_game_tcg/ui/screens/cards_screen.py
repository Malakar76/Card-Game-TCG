"""Screen for listing all cards."""

from pathlib import Path

from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen

from card_game_tcg.db.session import SessionLocal
from card_game_tcg.models.card import Card
from card_game_tcg.services import card_service

Builder.load_file(str(Path(__file__).parent.parent / "kv" / "cardsscreen.kv"))


def _find_cards_screen(widget) -> "CardsScreen | None":
    """Walk up the widget tree to find the CardsScreen ancestor."""
    parent = widget.parent
    while parent is not None and not isinstance(parent, CardsScreen):
        parent = parent.parent
    return parent


class CardRow(RecycleDataViewBehavior, BoxLayout):
    """A single row in the cards RecycleView."""

    card_db_id = NumericProperty(0)
    tcgdex_id = StringProperty("")
    card_name = StringProperty("")
    card_image = StringProperty("")

    def refresh_view_attrs(self, rv, index, data):
        self.card_db_id = data.get("card_db_id", 0)
        self.tcgdex_id = data.get("tcgdex_id", "")
        self.card_name = data.get("card_name", "")
        self.card_image = data.get("card_image", "")
        return super().refresh_view_attrs(rv, index, data)

    def delete_from_collection(self) -> None:
        """Soft-delete this card from the collection and reload the list."""
        session = SessionLocal()
        try:
            card = card_service.get_card(session, self.card_db_id)
            if card:
                card_service.delete_card(session, card)
        finally:
            session.close()

        screen = _find_cards_screen(self)
        if screen:
            screen.load_cards()


class TrashRow(RecycleDataViewBehavior, BoxLayout):
    """A single row in the trash RecycleView."""

    card_db_id = NumericProperty(0)
    tcgdex_id = StringProperty("")
    card_name = StringProperty("")
    card_image = StringProperty("")

    def refresh_view_attrs(self, rv, index, data):
        self.card_db_id = data.get("card_db_id", 0)
        self.tcgdex_id = data.get("tcgdex_id", "")
        self.card_name = data.get("card_name", "")
        self.card_image = data.get("card_image", "")
        return super().refresh_view_attrs(rv, index, data)

    def restore_card(self) -> None:
        """Restore a soft-deleted card and reload both lists."""
        session = SessionLocal()
        try:
            card = session.get(Card, self.card_db_id)
            if card:
                card_service.restore_card(session, card)
        finally:
            session.close()

        screen = _find_cards_screen(self)
        if screen:
            screen.load_cards()
            screen.load_trash()

    def hard_delete_card(self) -> None:
        """Permanently delete a card and reload the trash."""
        session = SessionLocal()
        try:
            card = session.get(Card, self.card_db_id)
            if card:
                card_service.hard_delete_card(session, card)
        finally:
            session.close()

        screen = _find_cards_screen(self)
        if screen:
            screen.load_trash()


class CardsScreen(Screen):
    """Screen displaying a list of all cards."""

    show_trash = BooleanProperty(False)

    def on_enter(self, *args) -> None:
        """Reload cards every time the screen is shown."""
        self.load_cards()
        if self.show_trash:
            self.load_trash()

    def load_cards(self) -> None:
        """Fetch cards from the database and populate the RecycleView."""
        session = SessionLocal()
        try:
            cards = card_service.get_all_cards(session)
            self.ids.rv.data = [
                {
                    "card_db_id": card.id,
                    "tcgdex_id": card.tcgdex_id,
                    "card_name": card.name,
                    "card_image": card.image_url or "",
                }
                for card in cards
            ]
        finally:
            session.close()

    def toggle_trash(self) -> None:
        """Toggle trash visibility and load trash data if opening."""
        self.show_trash = not self.show_trash
        if self.show_trash:
            self.load_trash()

    def load_trash(self) -> None:
        """Fetch deleted cards from the database and populate the trash RecycleView."""
        session = SessionLocal()
        try:
            cards = card_service.get_deleted_cards(session)
            self.ids.rv_trash.data = [
                {
                    "card_db_id": card.id,
                    "tcgdex_id": card.tcgdex_id,
                    "card_name": card.name,
                    "card_image": card.image_url or "",
                }
                for card in cards
            ]
        finally:
            session.close()
