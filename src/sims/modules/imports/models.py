import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CHAR, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sims.core.db import Base
from sims.core.types import UUIDPk, str_enum, utcnow


class ImportKind(enum.StrEnum):
    ROSTER_DOCX = "roster_docx"
    ROSTER_XLSX = "roster_xlsx"
    DEBTS_XLSX = "debts_xlsx"
    CONTRACTS_XLSX = "contracts_xlsx"


class ImportStatus(enum.StrEnum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class IssueSeverity(enum.StrEnum):
    ERROR = "error"
    WARNING = "warning"


class ImportBatch(UUIDPk, Base):
    __tablename__ = "import_batch"

    source_filename: Mapped[str]
    file_sha256: Mapped[str] = mapped_column(CHAR(64), index=True)
    kind: Mapped[ImportKind] = mapped_column(str_enum(ImportKind))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[ImportStatus] = mapped_column(str_enum(ImportStatus), default=ImportStatus.RUNNING)
    stats: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_by: Mapped[str | None]

    issues: Mapped[list["ImportIssue"]] = relationship(back_populates="batch")


class ImportIssue(UUIDPk, Base):
    __tablename__ = "import_issue"

    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_batch.id"), index=True)
    severity: Mapped[IssueSeverity] = mapped_column(str_enum(IssueSeverity))
    code: Mapped[str] = mapped_column(String(64))
    location: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    message: Mapped[str]
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    batch: Mapped[ImportBatch] = relationship(back_populates="issues")
