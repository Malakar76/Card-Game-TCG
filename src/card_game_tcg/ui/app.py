"""Kivy application setup."""

from pathlib import Path

from kivy.app import App
from kivy.lang import Builder

from card_game_tcg.config import settings
from card_game_tcg.ui.screens import CardsScreen, SearchScreen  # noqa: F401

KV_DIR = Path(__file__).parent / "kv"


class CardGameApp(App):
    """Main Kivy application."""

    title = settings.app_name

    def build(self):
        return Builder.load_file(str(KV_DIR / "main.kv"))
