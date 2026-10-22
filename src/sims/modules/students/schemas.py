import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sims.modules.academic.schemas import GroupOut
from sims.modules.students.models import Funding, MembershipReason, StudentStatus

TAX_ID = r"^\d{10}$"


class GroupRef(BaseModel):
    id: uuid.UUID
    code: str


class SpecialtyRef(BaseModel):
    code: str
    name: str


class StudentListItem(BaseModel):
    id: uuid.UUID
    full_name: str
    last_name: str
    first_name: str
    patronymic: str | None
    status: str
    funding: str | None
    record_book_no: str | None
    group: GroupRef | None
    specialty: SpecialtyRef | None
    course: int | None
    has_academic_debt: bool
    financial_debt: Decimal


class StudentIn(BaseModel):
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    patronymic: str | None = Field(None, max_length=100)
    group_id: uuid.UUID | None = None
    funding: Funding | None = None
    enrolled_on: date | None = None
    tax_id: str | None = Field(None, pattern=TAX_ID)
    birth_date: date | None = None
    gender: str | None = None
    contacts: dict[str, Any] = {}
    record_book_no: str | None = None
    student_card_no: str | None = None


class StudentPatch(BaseModel):
    last_name: str | None = Field(None, min_length=1, max_length=100)
    first_name: str | None = Field(None, min_length=1, max_length=100)
    patronymic: str | None = None
    funding: Funding | None = None
    enrolled_on: date | None = None
    tax_id: str | None = Field(None, pattern=TAX_ID)
    birth_date: date | None = None
    gender: str | None = None
    contacts: dict[str, Any] | None = None
    record_book_no: str | None = None
    student_card_no: str | None = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    last_name: str
    first_name: str
    patronymic: str | None
    status: str
    funding: str | None
    funding_raw: str | None
    enrolled_on: date | None
    tax_id: str | None
    birth_date: date | None
    gender: str | None
    contacts: dict[str, Any]
    record_book_no: str | None
    student_card_no: str | None
    group: GroupOut | None = None


class StatusChangeIn(BaseModel):
    status: StudentStatus
    changed_on: date
    order_no: str | None = None
    note: str | None = None


class TransferIn(BaseModel):
    group_id: uuid.UUID
    on: date
    order_ref: str | None = None


# --- tabs -------------------------------------------------------------------------

class GradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    attempt_no: int
    score: int | None
    ects: str | None
    national: str | None
    graded_on: date


class DisciplineResult(BaseModel):
    group_discipline_id: uuid.UUID
    discipline: str
    control_form: str
    credits_ects: Decimal | None
    grades: list[GradeOut]
    final: GradeOut | None
    has_debt: bool


class SemesterResults(BaseModel):
    academic_year: str
    semester: int
    disciplines: list[DisciplineResult]


class DebtOut(BaseModel):
    id: uuid.UUID
    discipline: str
    academic_year: str
    semester: int
    status: str
    opened_on: date
    retake_deadline: date | None
    closed_on: date | None
    note: str | None


class PerformanceOut(BaseModel):
    semesters: list[SemesterResults]
    debts: list[DebtOut]


class ScheduleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    due_date: date
    amount: Decimal


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    paid_on: date
    amount: Decimal
    method: str | None
    external_ref: str | None


class ContractOut(BaseModel):
    id: uuid.UUID
    number: str
    signed_on: date | None
    starts_on: date
    ends_on: date | None
    total_amount: Decimal
    currency: str
    status: str
    schedule: list[ScheduleItemOut]
    payments: list[PaymentOut]
    due_total: Decimal
    paid_total: Decimal
    debt: Decimal


class FinanceOut(BaseModel):
    funding: str | None
    contracts: list[ContractOut]
    total_debt: Decimal


class MembershipOut(BaseModel):
    group: GroupRef
    starts_on: date
    ends_on: date | None
    reason: MembershipReason
    order_ref: str | None


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    changed_on: date
    order_no: str | None
    note: str | None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    title: str
    file_path: str | None
    issued_on: date | None


class HistoryOut(BaseModel):
    memberships: list[MembershipOut]
    status_history: list[StatusHistoryOut]
    documents: list[DocumentOut]
