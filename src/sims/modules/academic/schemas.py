import re
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sims.modules.academic.models import GroupStatus, OrgUnitKind, SpecialtyClassifier


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LevelOut(ORM):
    id: uuid.UUID
    code: str
    nqf_level: int
    name: str


class FormOut(ORM):
    id: uuid.UUID
    code: str
    name: str


class SpecialtyOut(ORM):
    id: uuid.UUID
    classifier: str
    code: str
    name: str
    successor_id: uuid.UUID | None = None


_CODE_PATTERN = {SpecialtyClassifier.V2024: r"^[A-Z]\d{1,2}$", SpecialtyClassifier.V2015: r"^\d{3}$"}


class SpecialtyIn(BaseModel):
    classifier: SpecialtyClassifier
    code: str = Field(min_length=2, max_length=16)
    name: str = Field(min_length=2, max_length=200)
    successor_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _code_matches_classifier(self):
        self.code = self.code.strip().upper()
        if not re.match(_CODE_PATTERN[self.classifier], self.code):
            raise ValueError(f"code {self.code!r} does not fit the {self.classifier.value} classifier")
        return self


class SpecialtyPatch(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    successor_id: uuid.UUID | None = None


class SpecialtyRow(SpecialtyOut):
    field_code: str | None
    successor_code: str | None
    groups_count: int
    students_count: int


class ProgramOut(ORM):
    id: uuid.UUID
    specialty_id: uuid.UUID
    level_id: uuid.UUID
    name: str
    short_code: str | None


class OrgUnitOut(ORM):
    id: uuid.UUID
    kind: str
    name: str
    short_name: str | None
    parent_id: uuid.UUID | None


class OrgUnitIn(BaseModel):
    kind: OrgUnitKind
    name: str = Field(min_length=2)
    short_name: str | None = None
    parent_id: uuid.UUID | None = None


class DictionariesOut(BaseModel):
    levels: list[LevelOut]
    forms: list[FormOut]
    specialties: list[SpecialtyOut]
    programs: list[ProgramOut]
    org_units: list[OrgUnitOut]


class AcademicYearIn(BaseModel):
    start_year: int = Field(ge=2000, le=2100)
    starts_on: date | None = None
    ends_on: date | None = None
    is_current: bool = False


class AcademicYearPatch(BaseModel):
    starts_on: date | None = None
    ends_on: date | None = None
    is_current: bool | None = None


class AcademicYearOut(ORM):
    id: uuid.UUID
    label: str
    start_year: int
    starts_on: date
    ends_on: date
    is_current: bool


class Ref(BaseModel):
    id: uuid.UUID
    name: str


class CuratorRef(BaseModel):
    id: uuid.UUID
    full_name: str


class GroupIn(BaseModel):
    code: str = Field(min_length=3, max_length=64)
    specialty_id: uuid.UUID
    program_id: uuid.UUID | None = None
    level: str
    form: str
    org_unit_id: uuid.UUID
    study_start: date | None = None
    study_end: date | None = None
    cohort_tag: str | None = None


class GroupPatch(BaseModel):
    program_id: uuid.UUID | None = None
    org_unit_id: uuid.UUID | None = None
    study_start: date | None = None
    study_end: date | None = None
    status: GroupStatus | None = None


class GroupOut(BaseModel):
    id: uuid.UUID
    code: str
    code_norm: str
    specialty: SpecialtyOut
    program: Ref | None
    level: str
    form: str
    org_unit: Ref
    admission_year: int
    entry_course: int
    is_shortened: bool
    cohort_tag: str | None
    study_start: date | None
    study_end: date | None
    status: str
    course: int | None
    curator: CuratorRef | None
