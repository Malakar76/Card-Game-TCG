"""Application entry point."""

import asyncio
import sys

from card_game_tcg.db.connection import init_db
from card_game_tcg.ui.app import create_app


async def _init_backend() -> None:
    """Initialize database connection."""
    await init_db()


def main() -> None:
    """Launch the application."""
    asyncio.run(_init_backend())

    app, _engine = create_app()
    sys.exit(app.exec())
