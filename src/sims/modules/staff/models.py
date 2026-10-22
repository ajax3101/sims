import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sims.core.db import Base
from sims.core.types import Timestamps, UUIDPk


class Staff(UUIDPk, Timestamps, Base):
    __tablename__ = "staff"

    last_name: Mapped[str]
    first_name: Mapped[str]
    patronymic: Mapped[str | None]
    position: Mapped[str | None]
    academic_degree: Mapped[str | None]
    org_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("org_unit.id"), index=True)
    email: Mapped[str | None]
    phone: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)

    curatorships: Mapped[list["Curatorship"]] = relationship(back_populates="staff")


class Curatorship(UUIDPk, Timestamps, Base):
    __tablename__ = "curatorship"
    __table_args__ = (
        # One curator per group at any moment; '[)' lets a handover happen on the same day.
        ExcludeConstraint(
            ("group_id", "="),
            (text("daterange(starts_on, ends_on, '[)')"), "&&"),
            using="gist",
            name="ex_curatorship_no_overlap",
        ),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("study_group.id"), index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff.id"), index=True)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)

    group: Mapped["StudyGroup"] = relationship(back_populates="curatorships")  # noqa: F821
    staff: Mapped[Staff] = relationship(back_populates="curatorships")
