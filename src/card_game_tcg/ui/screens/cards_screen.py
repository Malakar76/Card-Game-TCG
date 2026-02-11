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

    card_name = StringProperty("")
    description = StringProperty("")
    attack = NumericProperty(0)
    defense = NumericProperty(0)
    cost = NumericProperty(0)

    def refresh_view_attrs(self, rv, index, data):
        self.card_name = data.get("card_name", "")
        self.description = data.get("description", "")
        self.attack = data.get("attack", 0)
        self.defense = data.get("defense", 0)
        self.cost = data.get("cost", 0)
        return super().refresh_view_attrs(rv, index, data)


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
                    "card_name": card.name,
                    "description": card.description,
                    "attack": card.attack,
                    "defense": card.defense,
                    "cost": card.cost,
                }
                for card in cards
            ]
        finally:
            session.close()
