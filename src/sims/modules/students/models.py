import enum
import uuid
from datetime import date
from typing import Any

from sqlalchemy import Date, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sims.core.db import Base
from sims.core.types import Timestamps, UUIDPk, str_enum


class StudentStatus(enum.StrEnum):
    ACTIVE = "active"
    ACADEMIC_LEAVE = "academic_leave"
    EXPELLED = "expelled"
    GRADUATED = "graduated"


class Funding(enum.StrEnum):
    BUDGET = "budget"
    CONTRACT = "contract"
    OTHER = "other"


class MembershipReason(enum.StrEnum):
    ENROLLMENT = "enrollment"
    TRANSFER = "transfer"
    REINSTATEMENT = "reinstatement"
    PROMOTION = "promotion"


class DocumentKind(enum.StrEnum):
    ORDER = "order"
    CONTRACT = "contract"
    CERTIFICATE = "certificate"
    OTHER = "other"


class Student(UUIDPk, Timestamps, Base):
    __tablename__ = "student"
    __table_args__ = (
        Index(
            "ix_student_full_name_norm_trgm",
            "full_name_norm",
            postgresql_using="gin",
            postgresql_ops={"full_name_norm": "gin_trgm_ops"},
        ),
    )

    last_name: Mapped[str]
    first_name: Mapped[str]
    patronymic: Mapped[str | None]
    full_name_norm: Mapped[str]
    tax_id: Mapped[str | None] = mapped_column(String(10), unique=True)
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(16))
    contacts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    record_book_no: Mapped[str | None] = mapped_column(String(32), unique=True)
    student_card_no: Mapped[str | None] = mapped_column(String(32), unique=True)
    status: Mapped[StudentStatus] = mapped_column(
        str_enum(StudentStatus), default=StudentStatus.ACTIVE, index=True
    )
    funding: Mapped[Funding | None] = mapped_column(str_enum(Funding))
    funding_raw: Mapped[str | None] = mapped_column(String(8))
    current_group_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("study_group.id"), index=True)
    enrolled_on: Mapped[date | None] = mapped_column(Date)
    source_batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("import_batch.id"), index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    current_group: Mapped["StudyGroup | None"] = relationship()  # noqa: F821
    memberships: Mapped[list["StudentGroupMembership"]] = relationship(back_populates="student")
    status_history: Mapped[list["StudentStatusHistory"]] = relationship(back_populates="student")
    documents: Mapped[list["StudentDocument"]] = relationship(back_populates="student")


class StudentGroupMembership(UUIDPk, Timestamps, Base):
    __tablename__ = "student_group_membership"
    __table_args__ = (
        Index("uq_student_group_membership_open", "student_id", unique=True, postgresql_where=text("ends_on IS NULL")),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student.id"), index=True)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_group.id"), index=True)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    reason: Mapped[MembershipReason] = mapped_column(str_enum(MembershipReason))
    order_ref: Mapped[str | None]

    student: Mapped[Student] = relationship(back_populates="memberships")
    group: Mapped["StudyGroup"] = relationship(back_populates="memberships")  # noqa: F821


class StudentStatusHistory(UUIDPk, Timestamps, Base):
    __tablename__ = "student_status_history"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student.id"), index=True)
    status: Mapped[StudentStatus] = mapped_column(str_enum(StudentStatus))
    changed_on: Mapped[date] = mapped_column(Date)
    order_no: Mapped[str | None]
    note: Mapped[str | None]

    student: Mapped[Student] = relationship(back_populates="status_history")


class StudentDocument(UUIDPk, Timestamps, Base):
    __tablename__ = "student_document"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student.id"), index=True)
    kind: Mapped[DocumentKind] = mapped_column(str_enum(DocumentKind))
    title: Mapped[str]
    file_path: Mapped[str | None]
    issued_on: Mapped[date | None] = mapped_column(Date)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    student: Mapped[Student] = relationship(back_populates="documents")
