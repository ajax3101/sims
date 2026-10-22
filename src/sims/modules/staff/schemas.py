import uuid
from datetime import date

from pydantic import BaseModel, Field

from sims.models import Staff


def staff_full_name(s: Staff) -> str:
    return " ".join(x for x in (s.last_name, s.first_name, s.patronymic) if x)


class StaffIn(BaseModel):
    last_name: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    patronymic: str | None = None
    position: str | None = None
    academic_degree: str | None = None
    org_unit_id: uuid.UUID | None = None
    email: str | None = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = None


class StaffPatch(BaseModel):
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    position: str | None = None
    academic_degree: str | None = None
    org_unit_id: uuid.UUID | None = None
    email: str | None = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = None
    is_active: bool | None = None


class GroupCode(BaseModel):
    id: uuid.UUID
    code: str


class StaffOut(StaffIn):
    id: uuid.UUID
    full_name: str
    is_active: bool
    curated_groups: list[GroupCode] = []

    @classmethod
    def of(cls, s: Staff, curated: list[GroupCode] | None = None) -> "StaffOut":
        return cls(curated_groups=curated or [],
            id=s.id, full_name=staff_full_name(s), is_active=s.is_active, last_name=s.last_name, first_name=s.first_name,
            patronymic=s.patronymic, position=s.position, academic_degree=s.academic_degree,
            org_unit_id=s.org_unit_id, email=s.email, phone=s.phone,
        )


class CuratorshipOut(BaseModel):
    id: uuid.UUID
    starts_on: date
    ends_on: date | None
    staff: StaffOut
