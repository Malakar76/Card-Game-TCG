"""Alembic environment configuration."""

from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

from card_game_tcg.models.base import Base

target_metadata = Base.metadata

DB_FILENAME = "card_game_tcg.db"


def _get_url() -> str:
    """Return the database URL.

    Resolution order:
    1. CLI override: ``alembic -x db_path=/path/to/file.db``
    2. Kivy ``user_data_dir`` (auto-detected)
    3. ``sqlalchemy.url`` from alembic.ini (if set)
    """
    explicit = context.get_x_argument(as_dictionary=True).get("db_path")
    if explicit:
        return f"sqlite:///{explicit}"

    from card_game_tcg.ui.app import CardGameApp

    app = CardGameApp()
    db_path = Path(app.user_data_dir) / DB_FILENAME
    return f"sqlite:///{db_path}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
