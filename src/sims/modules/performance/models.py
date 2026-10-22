import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, SmallInteger, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sims.core.db import Base
from sims.core.types import Timestamps, UUIDPk, str_enum


class ControlForm(enum.StrEnum):
    EXAM = "exam"
    CREDIT = "credit"
    DIFF_CREDIT = "diff_credit"
    COURSEWORK = "coursework"


class GradeKind(enum.StrEnum):
    CURRENT = "current"
    FINAL = "final"
    RETAKE = "retake"
    COMMISSION = "commission"


class EctsGrade(enum.StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    FX = "FX"
    F = "F"


class NationalGrade(enum.StrEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    UNSATISFACTORY = "unsatisfactory"
    PASSED = "passed"
    FAILED = "failed"


class DebtStatus(enum.StrEnum):
    OPEN = "open"
    RETAKE_SCHEDULED = "retake_scheduled"
    CLOSED = "closed"
    WRITTEN_OFF = "written_off"


class Semester(UUIDPk, Base):
    __tablename__ = "semester"
    __table_args__ = (
        UniqueConstraint("academic_year_id", "number"),
        CheckConstraint("number IN (1, 2)", name="number_range"),
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_year.id"))
    number: Mapped[int] = mapped_column(SmallInteger)
    starts_on: Mapped[date | None] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)


class Discipline(UUIDPk, Timestamps, Base):
    __tablename__ = "discipline"

    code: Mapped[str | None] = mapped_column(String(32), unique=True)
    name: Mapped[str]
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("org_unit.id"), index=True)


class GroupDiscipline(UUIDPk, Timestamps, Base):
    __tablename__ = "group_discipline"
    __table_args__ = (UniqueConstraint("group_id", "discipline_id", "semester_id"),)

    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_group.id"))  # leads the unique index
    discipline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("discipline.id"), index=True)
    semester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("semester.id"), index=True)
    control_form: Mapped[ControlForm] = mapped_column(str_enum(ControlForm))
    credits_ects: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff.id"), index=True)

    discipline: Mapped[Discipline] = relationship()
    semester: Mapped[Semester] = relationship()


class Grade(UUIDPk, Timestamps, Base):
    __tablename__ = "grade"
    __table_args__ = (
        UniqueConstraint("student_id", "group_discipline_id", "kind", "attempt_no"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student.id"))  # leads the unique index
    group_discipline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("group_discipline.id"), index=True)
    kind: Mapped[GradeKind] = mapped_column(str_enum(GradeKind))
    attempt_no: Mapped[int] = mapped_column(SmallInteger, default=1)
    score: Mapped[int | None] = mapped_column(SmallInteger)
    ects: Mapped[EctsGrade | None] = mapped_column(str_enum(EctsGrade))
    national: Mapped[NationalGrade | None] = mapped_column(str_enum(NationalGrade))
    graded_on: Mapped[date] = mapped_column(Date)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff.id"), index=True)

    group_discipline: Mapped[GroupDiscipline] = relationship()


class AcademicDebt(UUIDPk, Timestamps, Base):
    __tablename__ = "academic_debt"
    __table_args__ = (
        # Unresolved = open or retake scheduled; closed/written-off ones are history.
        Index(
            "uq_academic_debt_unresolved",
            "student_id",
            "group_discipline_id",
            unique=True,
            postgresql_where=text("status IN ('open', 'retake_scheduled')"),
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student.id"), index=True)
    group_discipline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("group_discipline.id"), index=True)
    status: Mapped[DebtStatus] = mapped_column(str_enum(DebtStatus), default=DebtStatus.OPEN)
    opened_on: Mapped[date] = mapped_column(Date)
    retake_deadline: Mapped[date | None] = mapped_column(Date)
    closed_on: Mapped[date | None] = mapped_column(Date)
    closing_grade_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("grade.id"), index=True)
    note: Mapped[str | None]

    group_discipline: Mapped[GroupDiscipline] = relationship()
