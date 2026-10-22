import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import CHAR, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sims.core.db import Base
from sims.core.types import Timestamps, UUIDPk, str_enum


class ContractStatus(enum.StrEnum):
    ACTIVE = "active"
    TERMINATED = "terminated"
    COMPLETED = "completed"


class Contract(UUIDPk, Timestamps, Base):
    __tablename__ = "contract"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student.id"), index=True)
    number: Mapped[str] = mapped_column(String(64), unique=True)
    signed_on: Mapped[date | None] = mapped_column(Date)
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(CHAR(3), default="UAH")
    payer: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[ContractStatus] = mapped_column(str_enum(ContractStatus), default=ContractStatus.ACTIVE)

    schedule: Mapped[list["PaymentScheduleItem"]] = relationship(back_populates="contract")
    payments: Mapped[list["Payment"]] = relationship(back_populates="contract")


class PaymentScheduleItem(UUIDPk, Base):
    __tablename__ = "payment_schedule_item"
    __table_args__ = (UniqueConstraint("contract_id", "due_date"),)

    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contract.id"))  # leads the unique index
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("academic_year.id"), index=True)
    due_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    contract: Mapped[Contract] = relationship(back_populates="schedule")


class Payment(UUIDPk, Timestamps, Base):
    __tablename__ = "payment"

    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contract.id"), index=True)
    paid_on: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    method: Mapped[str | None] = mapped_column(String(32))
    external_ref: Mapped[str | None] = mapped_column(String(64), unique=True)

    contract: Mapped[Contract] = relationship(back_populates="payments")
