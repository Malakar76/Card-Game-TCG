"""Application entry point."""

import sys

from card_game_tcg.db.connection import AsyncRuntime, init_db
from card_game_tcg.ui.app import create_app


def main() -> None:
    """Launch the application."""
    runtime = AsyncRuntime()
    runtime.start()
    fut = runtime.submit(init_db())
    fut.result()

    app, _engine = create_app(runtime=runtime)
    app.aboutToQuit.connect(runtime.stop)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
