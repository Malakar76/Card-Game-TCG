"""Application entry point."""

import os
from pathlib import Path

import certifi

from card_game_tcg.db.session import init_db
from card_game_tcg.ui.app import CardGameApp

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

DB_FILENAME = "card_game_tcg.db"


def main() -> None:
    """Launch the application."""
    app = CardGameApp()
    db_path = Path(app.user_data_dir) / DB_FILENAME
    init_db(db_path)
    app.run()


if __name__ == "__main__":
    main()
