"""Format-neutral roster shapes produced by every parser and consumed by the import service."""
from dataclasses import dataclass, field
from datetime import date


@dataclass
class SectionHeader:
    level: str | None = None          # education_level.code
    form: str | None = None           # study_form.code
    institute: str | None = None
    specialty_code: str | None = None
    specialty_name: str | None = None
    program_name: str | None = None
    group_code: str | None = None
    study_start: date | None = None
    study_end: date | None = None
    header_course: int | None = None
    lines: list[str] = field(default_factory=list)


@dataclass
class RawRow:
    location: dict[str, int]
    name: str
    funding: str = ""
    extra: dict[str, str] = field(default_factory=dict)  # tax_id, birth_date, phone, email, record_book_no


@dataclass
class RosterSection:
    location: dict[str, int]
    header: SectionHeader
    rows: list[RawRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
