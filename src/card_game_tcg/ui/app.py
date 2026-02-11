"""QML application setup."""

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from card_game_tcg.config import settings

QML_DIR = Path(__file__).parent / "qml"


def create_app() -> tuple[QGuiApplication, QQmlApplicationEngine]:
    """Create and configure the Qt/QML application."""
    app = QGuiApplication(sys.argv)
    app.setApplicationName(settings.app_name)

    engine = QQmlApplicationEngine()
    engine.load(QML_DIR / "main.qml")

    if not engine.rootObjects():
        sys.exit(1)

    return app, engine
