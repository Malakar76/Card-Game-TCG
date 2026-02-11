"""Pydantic schemas for Card validation and serialization."""

from datetime import datetime

from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    """Schema for creating a new card."""

    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    attack: int = Field(default=0, ge=0)
    defense: int = Field(default=0, ge=0)
    cost: int = Field(default=0, ge=0)


class CardRead(BaseModel):
    """Schema for reading a card from the database."""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str
    attack: int
    defense: int
    cost: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
