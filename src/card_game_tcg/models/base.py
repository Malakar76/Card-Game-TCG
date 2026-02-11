"""Base SQLAlchemy model for all database tables."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class BaseModel(Base):
    """Abstract base class providing common columns for all models.

    Provides created_at, updated_at, deleted_at (soft delete).
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, session: Session) -> None:
        self.deleted_at = datetime.now(UTC)
        session.add(self)
        session.flush()

    def restore(self, session: Session) -> None:
        self.deleted_at = None
        session.add(self)
        session.flush()
