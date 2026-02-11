"""Base document model for all MongoDB collections."""

from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


class BaseDocument(Document):
    """Base class for all Beanie document models.

    Provides common fields shared across all collections.
    """

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    async def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)
        await self.save()

    async def restore(self) -> None:
        self.deleted_at = None
        await self.save()

    class Settings:
        use_state_management = True
