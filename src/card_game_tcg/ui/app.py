"""QML application setup."""

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from card_game_tcg.config import settings
from card_game_tcg.ui.controllers import CardController

QML_DIR = Path(__file__).parent / "qml"


class Controllers:
    def __init__(self, **controllers):
        self.__dict__.update(controllers)


def create_app(runtime) -> tuple[QGuiApplication, QQmlApplicationEngine]:
    """Create and configure the Qt/QML application."""
    app = QGuiApplication(sys.argv)
    app.setApplicationName(settings.app_name)

    engine = QQmlApplicationEngine()

    card_controller = CardController(runtime=runtime)
    engine.rootContext().setContextProperty("cardController", card_controller)
    app.controllers = Controllers(
        card=card_controller,
    )

    engine.load(QML_DIR / "main.qml")

    if not engine.rootObjects():
        sys.exit(1)

    return app, engine
