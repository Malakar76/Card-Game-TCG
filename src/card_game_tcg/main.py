"""Application entry point."""

import ssl
from pathlib import Path

import certifi

from card_game_tcg.db.session import init_db
from card_game_tcg.ui.app import CardGameApp

# urllib.request.urlopen uses this factory for HTTPS connections.
# On Android, the default context has no CA certs; point it at certifi's bundle.
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

DB_FILENAME = "card_game_tcg.db"


def main() -> None:
    """Launch the application."""
    app = CardGameApp()
    db_path = Path(app.user_data_dir) / DB_FILENAME
    init_db(db_path)
    app.run()


if __name__ == "__main__":
    main()
