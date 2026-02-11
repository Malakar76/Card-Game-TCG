"""Shared test fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from card_game_tcg.models.base import Base


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine for tests."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture
def session(engine) -> Session:
    """Yield a transactional session that rolls back after each test."""
    factory = sessionmaker(bind=engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.rollback()
        sess.close()
