"""Screen for listing all cards."""

from pathlib import Path

from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen

from card_game_tcg.db.session import SessionLocal
from card_game_tcg.services import card_service

Builder.load_file(str(Path(__file__).parent.parent / "kv" / "cardsscreen.kv"))


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

        screen = self.parent
        while screen is not None and not isinstance(screen, CardsScreen):
            screen = screen.parent
        if screen:
            screen.load_cards()


class CardsScreen(Screen):
    """Screen displaying a list of all cards."""

    def on_enter(self, *args) -> None:
        """Reload cards every time the screen is shown."""
        self.load_cards()

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
