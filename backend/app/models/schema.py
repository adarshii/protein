"""SQLAlchemy table mixins and schema helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """
    Adds ``created_at`` and ``updated_at`` columns to any ORM model.

    Usage::

        class MyModel(TimestampMixin, Base):
            __tablename__ = "my_table"
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )


class UUIDMixin:
    """
    Adds a UUID primary key ``id`` column to any ORM model.

    Usage::

        class MyModel(UUIDMixin, TimestampMixin, Base):
            __tablename__ = "my_table"
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )


def table_args(**kw: Any) -> dict:
    """
    Build a ``__table_args__`` dict with optional schema / constraints.

    Example::

        __table_args__ = table_args(schema="biochem")
    """
    return kw
