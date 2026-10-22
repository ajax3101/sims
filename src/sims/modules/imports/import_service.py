"""Roster import: parse → normalise → validate → resolve dictionaries → upsert students.

One file is one transaction and one ImportBatch. Row-level problems become
ImportIssue rows and never abort the file; an unexpected failure rolls the
file back and records a failed batch instead.
"""
import hashlib
import uuid
from datetime import date
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sims.core.types import utcnow
from sims.models import (
    EducationalProgram, EducationLevel, ImportBatch, ImportIssue, ImportKind, ImportStatus, MembershipReason,
    OrgUnit, OrgUnitKind, Specialty, SpecialtyClassifier, Student, StudentGroupMembership, StudyForm, StudyGroup,
)
from sims.modules.imports.group_code import GroupCode, GroupCodeError, parse_group_code
from sims.modules.imports.normalize import NameError_, clean_text, fuzzy_equal, normalize_full_name, parse_funding, sentence_case
from sims.modules.imports.parsers.base import RawRow, RosterSection
from sims.modules.imports.parsers.docx_roster import parse_docx_roster
from sims.modules.imports.parsers.xlsx_roster import parse_xlsx_roster
from sims.modules.imports.schemas import ImportReport, IssueOut, StudentRowIn

_NQF_LEVEL = {6: "bachelor", 7: "master", 8: "phd"}
_PARSERS = {
    ".docx": (ImportKind.ROSTER_DOCX, parse_docx_roster),
    ".xlsx": (ImportKind.ROSTER_XLSX, parse_xlsx_roster),
}
SUPPORTED_SUFFIXES = frozenset(_PARSERS)
# Fields a re-import may change on an existing student when the file has a value.
_UPDATABLE = ("funding", "funding_raw", "enrolled_on", "tax_id", "birth_date", "record_book_no")


class UnsupportedFile(ValueError):
    pass


class _SectionError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class _Importer:
    def __init__(self, session: AsyncSession, report: ImportReport, batch_id: uuid.UUID, source: str):
        self.s = session
        self.report = report
        self.batch_id = batch_id
        self.source = source
        self.levels: dict[str, EducationLevel] = {}
        self.forms: dict[str, StudyForm] = {}
        self.specialties: dict[tuple[str, str], Specialty] = {}
        self.institutes: list[OrgUnit] = []
        self.programs: dict[uuid.UUID, list[EducationalProgram]] = {}

    def issue(self, severity: str, code: str, message: str, location: dict) -> None:
        self.report.issues.append(IssueOut(severity=severity, code=code, message=message, location=location))

    async def load_dictionaries(self) -> None:
        self.levels = {x.code: x for x in (await self.s.scalars(select(EducationLevel))).all()}
        self.forms = {x.code: x for x in (await self.s.scalars(select(StudyForm))).all()}
        self.specialties = {(x.classifier, x.code): x for x in (await self.s.scalars(select(Specialty))).all()}
        self.institutes = list(
            (await self.s.scalars(select(OrgUnit).where(OrgUnit.kind == OrgUnitKind.INSTITUTE))).all()
        )

    # --- dictionaries -------------------------------------------------------------

    def institute(self, name: str) -> OrgUnit:
        for unit in self.institutes:
            if fuzzy_equal(unit.name, name):
                return unit
        unit = OrgUnit(kind=OrgUnitKind.INSTITUTE, name=name)
        self.s.add(unit)
        self.institutes.append(unit)
        self.report.dictionaries_created["org_unit"] += 1
        return unit

    def specialty(self, code: str, name: str | None, loc: dict) -> Specialty:
        classifier = SpecialtyClassifier.V2015 if code.isdigit() else SpecialtyClassifier.V2024
        if spec := self.specialties.get((classifier, code)):
            return spec
        spec = Specialty(
            classifier=classifier, code=code, name=sentence_case(name or code),
            field_code=code[:2] if code.isdigit() else code[0],
        )
        self.s.add(spec)
        self.specialties[(classifier, code)] = spec
        self.report.dictionaries_created["specialty"] += 1
        self.issue("warning", "specialty_created", f"new specialty {code} {spec.name!r} added to the dictionary", loc)
        return spec

    async def program(self, spec: Specialty, level: EducationLevel, raw_name: str | None,
                      short_code: str | None, loc: dict) -> EducationalProgram | None:
        if not raw_name:
            self.issue("warning", "program_missing", "educational program is empty in the header", loc)
            return None
        name = sentence_case(raw_name)
        if spec.id not in self.programs:
            self.programs[spec.id] = (
                list((await self.s.scalars(select(EducationalProgram).where(EducationalProgram.specialty_id == spec.id))).all())
                if spec.id else []
            )
        candidates = self.programs[spec.id]
        same_level = [p for p in candidates if p.level is level]
        for p in same_level:
            if p.name.casefold() == name.casefold():
                return p
        for p in same_level:
            if fuzzy_equal(p.name, name):
                self.issue("warning", "program_fuzzy_matched", f"{name!r} matched existing program {p.name!r}", loc)
                return p
        for p in candidates:
            if p.level is not level and fuzzy_equal(p.name, name) and p.name != name:
                self.issue("warning", "program_name_corrected",
                           f"{name!r} spelled as {p.name!r}, taken from the same program at another level", loc)
                name = p.name
                break
        program = EducationalProgram(specialty=spec, level=level, name=name, short_code=short_code)
        self.s.add(program)
        candidates.append(program)
        self.report.dictionaries_created["program"] += 1
        return program

    # --- sections -----------------------------------------------------------------

    async def group(self, section: RosterSection) -> StudyGroup:
        h, loc = section.header, section.location
        default_nqf = {v: k for k, v in _NQF_LEVEL.items()}.get(h.level)
        try:
            code: GroupCode = parse_group_code(h.group_code or "", default_nqf=default_nqf)
        except GroupCodeError as e:
            raise _SectionError("invalid_group_code", str(e)) from e

        existing = await self.s.scalar(select(StudyGroup).where(StudyGroup.code_norm == code.code_norm))
        if existing:
            self.report.groups_matched += 1
            return existing

        if code.repairs:
            self.issue("warning", "group_code_repaired",
                       f"{h.group_code!r} read as {code.code_norm!r} ({', '.join(code.repairs)})", loc)
        level_code = _NQF_LEVEL[code.nqf_level]
        if h.level and h.level != level_code:
            self.issue("warning", "level_mismatch", f"header says {h.level}, group code says {level_code}", loc)
        form_code = h.form or ("part_time" if code.part_time else "full_time")
        if not h.institute and not h.specialty_code:
            raise _SectionError("unknown_group", f"group {code.code_norm!r} not found; spreadsheet rows join existing groups only")
        if not h.institute:
            raise _SectionError("header_missing_institute", "no institute/faculty line in the header")

        level = self.levels[level_code]
        spec = self.specialty(h.specialty_code or code.specialty_code, h.specialty_name, loc)
        group = StudyGroup(
            code=clean_text(h.group_code), code_norm=code.code_norm,
            specialty=spec, program=await self.program(spec, level, h.program_name, code.program_code, loc),
            level=level, form=self.forms[form_code], org_unit=self.institute(h.institute),
            admission_year=code.admission_year, entry_course=code.entry_course, is_shortened=code.entry_course > 1,
            cohort_tag=code.cohort_tag, study_start=h.study_start, study_end=h.study_end,
            meta={"source_file": self.source, "header_course": h.header_course, "header": h.lines},
        )
        self.s.add(group)
        await self.s.flush()
        self.report.groups_created += 1
        return group

    async def open_members(self, group: StudyGroup) -> dict[str, Student]:
        """Current students of the group, keyed by normalised name and by tax id."""
        rows = (await self.s.scalars(
            select(Student).join(StudentGroupMembership)
            .where(StudentGroupMembership.group_id == group.id, StudentGroupMembership.ends_on.is_(None))
        )).all()
        return {st.full_name_norm: st for st in rows} | {f"tax:{st.tax_id}": st for st in rows if st.tax_id}

    def validate_row(self, row: RawRow) -> StudentRowIn | None:
        try:
            name = normalize_full_name(row.name)
        except NameError_ as e:
            self.issue("error", "invalid_name", str(e), row.location)
            return None
        funding, funding_warning = parse_funding(row.funding)
        try:
            data = StudentRowIn(
                last_name=name.last_name, first_name=name.first_name, patronymic=name.patronymic,
                full_name_norm=name.norm, funding=funding, funding_raw=row.funding.strip() or None,
                enrolled_on=name.enrolled_on, **row.extra,
            )
        except ValidationError as e:
            fields = ", ".join(".".join(map(str, err["loc"])) for err in e.errors())
            self.issue("error", "invalid_row", f"{row.name!r}: invalid {fields}", row.location)
            return None
        if funding_warning:
            self.issue("warning", funding_warning, f"{row.name!r}: funding code {row.funding.strip()!r}", row.location)
        for w in name.warnings:
            self.issue("warning", w, f"{row.name!r}", row.location)
        return data

    async def section(self, section: RosterSection) -> None:
        for code in section.errors:
            self.issue("error", code, f"section skipped: {code}", section.location)
        if section.errors:
            return
        try:
            group = await self.group(section)
        except _SectionError as e:
            self.issue("error", e.code, str(e), section.location)
            return

        members = await self.open_members(group)
        seen: set[str] = set()
        for row in section.rows:
            data = self.validate_row(row)
            if data is None:
                continue
            keys = {data.full_name_norm} | ({f"tax:{data.tax_id}"} if data.tax_id else set())
            if keys & seen:
                self.report.duplicates += 1
                self.issue("warning", "duplicate_in_file", f"{row.name!r} repeats in this group", row.location)
                continue
            seen |= keys
            existing = members.get(f"tax:{data.tax_id}") if data.tax_id else None
            if existing := existing or members.get(data.full_name_norm):
                self._update(existing, data)
            else:
                self._create(group, data)
        await self.s.flush()

    def _update(self, st: Student, data: StudentRowIn) -> None:
        changed = False
        for field in _UPDATABLE:
            value = getattr(data, field)
            if value is not None and getattr(st, field) != value:
                setattr(st, field, value)
                changed = True
        if changed:
            self.report.students_updated += 1
        else:
            self.report.duplicates += 1

    def _create(self, group: StudyGroup, data: StudentRowIn) -> None:
        contacts = {k: v for k, v in (("phone", data.phone), ("email", data.email)) if v}
        st = Student(
            last_name=data.last_name, first_name=data.first_name, patronymic=data.patronymic,
            full_name_norm=data.full_name_norm, funding=data.funding, funding_raw=data.funding_raw,
            enrolled_on=data.enrolled_on, tax_id=data.tax_id, birth_date=data.birth_date,
            record_book_no=data.record_book_no, contacts=contacts,
            current_group=group, source_batch_id=self.batch_id,
        )
        st.memberships.append(StudentGroupMembership(
            group=group, starts_on=data.enrolled_on or group.study_start or date.today(),
            reason=MembershipReason.ENROLLMENT,
        ))
        self.s.add(st)
        self.report.students_created += 1


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def import_file(session: AsyncSession, path: Path, *, source_name: str | None = None) -> ImportReport:
    path = Path(path)
    source = source_name or path.name
    if path.suffix.lower() not in _PARSERS:
        raise UnsupportedFile(f"unsupported file type {path.suffix!r}: {source}")
    kind, parse = _PARSERS[path.suffix.lower()]
    sha = _sha256(path)
    report = ImportReport(source_filename=source)

    try:
        batch = ImportBatch(source_filename=source, file_sha256=sha, kind=kind)
        session.add(batch)
        await session.flush()
        report.batch_id = batch.id
        importer = _Importer(session, report, batch.id, source)
        await importer.load_dictionaries()
        for section in parse(path):
            await importer.section(section)
        _finish(session, batch, report, ImportStatus.DONE)
        await session.commit()
    except Exception as exc:  # noqa: BLE001 — the failure is recorded, then re-raised for unexpected types
        message = f"{type(exc).__name__}: {exc}"  # read before rollback expires anything
        await session.rollback()
        report = ImportReport(source_filename=source)
        report.issues.append(IssueOut(severity="error", code="import_failed", message=message))
        batch = ImportBatch(source_filename=source, file_sha256=sha, kind=kind)
        session.add(batch)
        await session.flush()
        report.batch_id = batch.id
        _finish(session, batch, report, ImportStatus.FAILED)
        await session.commit()
    return report


def _finish(session: AsyncSession, batch: ImportBatch, report: ImportReport, status: ImportStatus) -> None:
    report.status = status.value
    batch.status = status
    batch.finished_at = utcnow()
    batch.stats = report.stats()
    session.add_all(
        ImportIssue(batch_id=batch.id, severity=i.severity, code=i.code, message=i.message, location=i.location)
        for i in report.issues
    )
