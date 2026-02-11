"""SQLite database engine and session management."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from card_game_tcg.models.base import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_db(db_path: Path) -> None:
    """Create the engine, session factory, and all tables.

    Must be called once at startup with the database file path
    (typically from Kivy's ``App.user_data_dir``).
    """
    global _engine, _SessionLocal  # noqa: PLW0603

    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"

    _engine = create_engine(url)
    _SessionLocal = sessionmaker(bind=_engine)
    Base.metadata.create_all(bind=_engine)


def SessionLocal() -> Session:  # noqa: N802
    """Return a new database session. Raises if ``init_db`` was not called."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialised – call init_db() first")
    return _SessionLocal()
