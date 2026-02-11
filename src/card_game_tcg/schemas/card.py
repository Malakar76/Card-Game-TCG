"""Pydantic schemas for Card validation and serialization."""

from datetime import datetime

from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    """Schema for creating a new card from TCGdex data."""

    tcgdex_id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    image_url: str | None = None


class CardRead(BaseModel):
    """Schema for reading a card from the database."""

    model_config = {"from_attributes": True}

    id: int
    tcgdex_id: str
    name: str
    image_url: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
