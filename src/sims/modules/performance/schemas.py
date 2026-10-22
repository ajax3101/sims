import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from sims.modules.performance.models import ControlForm, DebtStatus, EctsGrade, GradeKind, NationalGrade


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SemesterIn(BaseModel):
    academic_year_id: uuid.UUID
    number: int = Field(ge=1, le=2)
    starts_on: date | None = None
    ends_on: date | None = None


class SemesterOut(SemesterIn, ORM):
    id: uuid.UUID


class DisciplineIn(BaseModel):
    name: str = Field(min_length=2)
    code: str | None = None
    department_id: uuid.UUID | None = None


class DisciplineOut(DisciplineIn, ORM):
    id: uuid.UUID


class GroupDisciplineIn(BaseModel):
    group_id: uuid.UUID
    discipline_id: uuid.UUID
    semester_id: uuid.UUID
    control_form: ControlForm
    credits_ects: Decimal | None = Field(None, ge=0, le=60)
    teacher_id: uuid.UUID | None = None


class GroupDisciplineOut(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    discipline_id: uuid.UUID
    discipline: str
    semester_id: uuid.UUID
    academic_year: str
    semester: int
    control_form: str
    credits_ects: Decimal | None
    teacher_id: uuid.UUID | None


class GradeIn(BaseModel):
    student_id: uuid.UUID
    group_discipline_id: uuid.UUID
    kind: GradeKind
    score: int | None = Field(None, ge=0, le=100)
    ects: EctsGrade | None = None
    national: NationalGrade | None = None
    graded_on: date
    recorded_by: uuid.UUID | None = None


class GradeOut(ORM):
    id: uuid.UUID
    student_id: uuid.UUID
    group_discipline_id: uuid.UUID
    kind: str
    attempt_no: int
    score: int | None
    ects: str | None
    national: str | None
    graded_on: date


class DebtPatch(BaseModel):
    status: DebtStatus | None = None
    retake_deadline: date | None = None
    closed_on: date | None = None
    note: str | None = None


class Named(BaseModel):
    id: uuid.UUID
    name: str


class GroupRef(BaseModel):
    id: uuid.UUID
    code: str


class StudentRef(BaseModel):
    id: uuid.UUID
    full_name: str


class DebtListItem(BaseModel):
    id: uuid.UUID
    student: StudentRef
    group: GroupRef
    discipline: str
    control_form: str
    academic_year: str
    semester: int
    status: str
    opened_on: date
    retake_deadline: date | None
    closed_on: date | None
    note: str | None
