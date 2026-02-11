"""Buildozer entry point.

Buildozer expects a main.py at the project root.
This module adds ``src/`` to the path so that the src-layout package
is importable, then delegates to the real entry point.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from card_game_tcg.main import main  # noqa: E402

if __name__ == "__main__":
    main()
