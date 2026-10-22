import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from sims.modules.students.models import Funding


class StudentRowIn(BaseModel):
    """One roster row after normalisation; validated before anything is written."""

    model_config = ConfigDict(str_strip_whitespace=True)

    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    patronymic: str | None = Field(None, max_length=100)
    full_name_norm: str = Field(min_length=3)
    funding: Funding | None = None
    funding_raw: str | None = Field(None, max_length=8)
    enrolled_on: date | None = None
    tax_id: str | None = Field(None, pattern=r"^\d{10}$")
    birth_date: date | None = None
    phone: str | None = Field(None, max_length=32)
    email: str | None = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    record_book_no: str | None = Field(None, max_length=32)


class IssueOut(BaseModel):
    severity: str
    code: str
    message: str
    location: dict[str, int | str] = {}


class ImportReport(BaseModel):
    batch_id: uuid.UUID | None = None
    source_filename: str
    status: str = "running"
    students_created: int = 0
    students_updated: int = 0
    duplicates: int = 0
    groups_created: int = 0
    groups_matched: int = 0
    dictionaries_created: dict[str, int] = Field(
        default_factory=lambda: {"org_unit": 0, "program": 0, "specialty": 0}
    )
    issues: list[IssueOut] = []

    @computed_field
    @property
    def errors(self) -> int:
        return sum(i.severity == "error" for i in self.issues)

    @computed_field
    @property
    def warnings(self) -> int:
        return sum(i.severity == "warning" for i in self.issues)

    def stats(self) -> dict[str, int | dict[str, int]]:
        return {
            "students_created": self.students_created,
            "students_updated": self.students_updated,
            "duplicates": self.duplicates,
            "groups_created": self.groups_created,
            "groups_matched": self.groups_matched,
            "dictionaries_created": self.dictionaries_created,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ImportBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_filename: str
    kind: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    stats: dict
    issues: list[IssueOut]
