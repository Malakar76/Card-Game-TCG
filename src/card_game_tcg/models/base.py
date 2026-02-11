"""Base document model for all MongoDB collections."""

from datetime import UTC, datetime
from typing import Any

from beanie import Document
from pydantic import Field

_NOT_DELETED_FILTER: dict[str, None] = {"deleted_at": None}


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

    @classmethod
    async def find_many(
        cls, *args: Any, include_deleted: bool = False, **kwargs: Any
    ) -> list[Any]:
        if not include_deleted:
            args = (_NOT_DELETED_FILTER, *args)
        return await super().find_many(*args, **kwargs).to_list()

    find = find_many

    @classmethod
    async def find_one(
        cls, *args: Any, include_deleted: bool = False, **kwargs: Any
    ) -> Any:
        if not include_deleted:
            args = (_NOT_DELETED_FILTER, *args)
        return await super().find_one(*args, **kwargs)

    @classmethod
    async def find_all(
        cls, *, include_deleted: bool = False, **kwargs: Any
    ) -> list[Any]:
        return await cls.find_many(include_deleted=include_deleted, **kwargs)

    @classmethod
    async def get(
        cls,
        document_id: Any,
        *,
        include_deleted: bool = False,
        **kwargs: Any,
    ) -> Any:
        doc = await super().get(document_id, **kwargs)
        if doc is not None and not include_deleted and doc.deleted_at is not None:
            return None
        return doc

    class Settings:
        use_state_management = True
