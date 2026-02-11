"""Tests for document models."""

from card_game_tcg.models.base import BaseDocument
from card_game_tcg.models.card import Card


def test_card_inherits_base_document():
    assert issubclass(Card, BaseDocument)


def test_card_has_base_fields():
    fields = Card.model_fields
    assert "created_at" in fields
    assert "updated_at" in fields
    assert "deleted_at" in fields


def test_card_has_own_fields():
    fields = Card.model_fields
    assert "name" in fields
    assert "description" in fields
    assert "attack" in fields
    assert "defense" in fields
    assert "cost" in fields
