import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from sims.modules.finance.models import ContractStatus

Money = Decimal


class ScheduleIn(BaseModel):
    due_date: date
    amount: Money = Field(gt=0, max_digits=12, decimal_places=2)
    academic_year_id: uuid.UUID | None = None


class ContractIn(BaseModel):
    student_id: uuid.UUID
    number: str = Field(min_length=1, max_length=64)
    signed_on: date | None = None
    starts_on: date
    ends_on: date | None = None
    total_amount: Money = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field("UAH", min_length=3, max_length=3)
    payer: dict[str, Any] | None = None
    schedule: list[ScheduleIn] = []

    @model_validator(mode="after")
    def _schedule_within_total(self):
        if sum((s.amount for s in self.schedule), Decimal(0)) > self.total_amount:
            raise ValueError("payment schedule exceeds the contract total")
        return self


class ContractPatch(BaseModel):
    status: ContractStatus | None = None
    ends_on: date | None = None
    signed_on: date | None = None
    payer: dict[str, Any] | None = None


class PaymentIn(BaseModel):
    paid_on: date
    amount: Money = Field(gt=0, max_digits=12, decimal_places=2)
    method: str | None = Field(None, max_length=32)
    external_ref: str | None = Field(None, max_length=64)
