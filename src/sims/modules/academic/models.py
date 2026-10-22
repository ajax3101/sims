import enum
import uuid
from datetime import date
from typing import Any

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, SmallInteger, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sims.core.db import Base
from sims.core.types import Timestamps, UUIDPk, str_enum


class SpecialtyClassifier(enum.StrEnum):
    V2015 = "2015"
    V2024 = "2024"


class OrgUnitKind(enum.StrEnum):
    UNIVERSITY = "university"
    INSTITUTE = "institute"
    FACULTY = "faculty"
    DEPARTMENT = "department"


class GroupStatus(enum.StrEnum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    ARCHIVED = "archived"


class EducationLevel(UUIDPk, Base):
    __tablename__ = "education_level"

    code: Mapped[str] = mapped_column(String(16), unique=True)
    nqf_level: Mapped[int] = mapped_column(SmallInteger, unique=True)
    name: Mapped[str]


class StudyForm(UUIDPk, Base):
    __tablename__ = "study_form"

    code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str]
    group_marker: Mapped[str | None] = mapped_column(String(8))


class OrgUnit(UUIDPk, Timestamps, Base):
    __tablename__ = "org_unit"

    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("org_unit.id"), index=True)
    kind: Mapped[OrgUnitKind] = mapped_column(str_enum(OrgUnitKind))
    name: Mapped[str]
    short_name: Mapped[str | None]
    # staff.org_unit_id points back here: break the cycle with ALTER.
    head_staff_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("staff.id", use_alter=True), index=True
    )

    parent: Mapped["OrgUnit | None"] = relationship(remote_side="OrgUnit.id", back_populates="children")
    children: Mapped[list["OrgUnit"]] = relationship(back_populates="parent")


class Specialty(UUIDPk, Base):
    __tablename__ = "specialty"
    __table_args__ = (UniqueConstraint("classifier", "code"),)

    classifier: Mapped[SpecialtyClassifier] = mapped_column(str_enum(SpecialtyClassifier))
    code: Mapped[str] = mapped_column(String(16))
    name: Mapped[str]
    field_code: Mapped[str | None] = mapped_column(String(8))
    successor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("specialty.id"), index=True)

    successor: Mapped["Specialty | None"] = relationship(remote_side="Specialty.id")


class EducationalProgram(UUIDPk, Timestamps, Base):
    __tablename__ = "educational_program"
    __table_args__ = (UniqueConstraint("specialty_id", "level_id", "name"),)

    specialty_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("specialty.id"), index=True)
    level_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("education_level.id"), index=True)
    name: Mapped[str]
    short_code: Mapped[str | None] = mapped_column(String(16))
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("org_unit.id"), index=True)

    specialty: Mapped[Specialty] = relationship()
    level: Mapped[EducationLevel] = relationship()


class AcademicYear(UUIDPk, Base):
    __tablename__ = "academic_year"
    __table_args__ = (
        Index("uq_academic_year_current", "is_current", unique=True, postgresql_where=text("is_current")),
    )

    label: Mapped[str] = mapped_column(String(9), unique=True)
    start_year: Mapped[int] = mapped_column(SmallInteger, unique=True)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(default=False)


class StudyGroup(UUIDPk, Timestamps, Base):
    __tablename__ = "study_group"
    __table_args__ = (CheckConstraint("entry_course BETWEEN 1 AND 6", name="entry_course_range"),)

    code: Mapped[str] = mapped_column(String(64), unique=True)
    code_norm: Mapped[str] = mapped_column(String(64), unique=True)
    specialty_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("specialty.id"), index=True)
    program_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("educational_program.id"), index=True)
    level_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("education_level.id"), index=True)
    form_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_form.id"), index=True)
    org_unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("org_unit.id"), index=True)
    admission_year: Mapped[int] = mapped_column(SmallInteger)
    entry_course: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_shortened: Mapped[bool] = mapped_column(default=False)
    cohort_tag: Mapped[str | None] = mapped_column(String(16))
    study_start: Mapped[date | None] = mapped_column(Date)
    study_end: Mapped[date | None] = mapped_column(Date)
    status: Mapped[GroupStatus] = mapped_column(str_enum(GroupStatus), default=GroupStatus.ACTIVE)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    specialty: Mapped[Specialty] = relationship()
    program: Mapped[EducationalProgram | None] = relationship()
    level: Mapped[EducationLevel] = relationship()
    form: Mapped[StudyForm] = relationship()
    org_unit: Mapped[OrgUnit] = relationship()
    memberships: Mapped[list["StudentGroupMembership"]] = relationship(back_populates="group")  # noqa: F821
    curatorships: Mapped[list["Curatorship"]] = relationship(back_populates="group")  # noqa: F821
