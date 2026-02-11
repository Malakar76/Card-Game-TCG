"""Screen for creating a new card."""

from pathlib import Path

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen

from card_game_tcg.db.session import SessionLocal
from card_game_tcg.schemas.card import CardCreate
from card_game_tcg.services import card_service

Builder.load_file(str(Path(__file__).parent.parent / "kv" / "createcardscreen.kv"))


class CreateCardScreen(Screen):
    """Screen with a form to create a new card."""

    status_text = StringProperty("")

    def create_card(
        self,
        name: str,
        description: str,
        attack: str,
        defense: str,
        cost: str,
    ) -> None:
        """Validate input and create a card in the database."""
        name = name.strip()
        if not name:
            self.status_text = "Le nom de la carte est obligatoire."
            return

        try:
            data = CardCreate(
                name=name,
                description=description,
                attack=int(attack) if attack else 0,
                defense=int(defense) if defense else 0,
                cost=int(cost) if cost else 0,
            )
        except (ValueError, Exception) as exc:
            self.status_text = str(exc)
            return

        session = SessionLocal()
        try:
            card_service.create_card(session, data)
            self.status_text = f"Carte \u00ab {name} \u00bb cr\u00e9\u00e9e avec succ\u00e8s !"
            self._clear_form()
        except Exception as exc:
            self.status_text = f"Erreur : {exc}"
        finally:
            session.close()

    def _clear_form(self) -> None:
        """Reset form fields after successful creation."""
        self.ids.name_input.text = ""
        self.ids.description_input.text = ""
        self.ids.attack_input.text = "0"
        self.ids.defense_input.text = "0"
        self.ids.cost_input.text = "0"
