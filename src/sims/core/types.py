import enum
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


def str_enum(enum_cls: type[enum.StrEnum]) -> Enum:
    """VARCHAR-backed enum storing member values (no native PG type to migrate)."""
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=True,
        name=re.sub(r"(?<!^)(?=[A-Z])", "_", enum_cls.__name__).lower(),
        length=32,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


class UUIDPk:
    # uuid7: time-ordered, keeps B-tree inserts append-only.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid7)


class Timestamps:
    # Python-side values: never expired by a flush, readable after commit in async code.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
