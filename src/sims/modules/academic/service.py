import uuid
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from sims.core.db import commit
from sims.core.errors import Conflict, InvalidInput, NotFound
from sims.models import AcademicYear, Curatorship, EducationLevel, Staff, StudyForm, StudyGroup
from sims.modules.academic import repository as repo
from sims.modules.academic.schemas import (
    AcademicYearIn, AcademicYearPatch, CuratorRef, GroupIn, GroupOut, GroupPatch, Ref, SpecialtyOut,
)
from sims.modules.staff.schemas import staff_full_name
from sims.modules.imports.group_code import GroupCodeError, parse_group_code

_NQF = {"bachelor": 6, "master": 7, "phd": 8}


# --- academic years ---------------------------------------------------------------

async def create_year(session: AsyncSession, data: AcademicYearIn) -> AcademicYear:
    if data.is_current:
        await session.execute(update(AcademicYear).where(AcademicYear.is_current).values(is_current=False))
    year = AcademicYear(
        label=f"{data.start_year}/{data.start_year + 1}", start_year=data.start_year,
        starts_on=data.starts_on or date(data.start_year, 9, 1),
        ends_on=data.ends_on or date(data.start_year + 1, 6, 30),
        is_current=data.is_current,
    )
    session.add(year)
    await commit(session)
    return year


async def patch_year(session: AsyncSession, year_id: uuid.UUID, data: AcademicYearPatch) -> AcademicYear:
    year = await session.get(AcademicYear, year_id) or _raise(NotFound("academic year"))
    if data.is_current:
        await session.execute(
            update(AcademicYear).where(AcademicYear.is_current, AcademicYear.id != year_id).values(is_current=False))
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(year, field, value)
    await commit(session)
    return year


# --- groups -----------------------------------------------------------------------

def group_out(group: StudyGroup, course: int | None, curator: Staff | None) -> GroupOut:
    return GroupOut(
        id=group.id, code=group.code, code_norm=group.code_norm,
        specialty=SpecialtyOut.model_validate(group.specialty),
        program=Ref(id=group.program.id, name=group.program.name) if group.program else None,
        level=group.level.code, form=group.form.code,
        org_unit=Ref(id=group.org_unit.id, name=group.org_unit.name),
        admission_year=group.admission_year, entry_course=group.entry_course, is_shortened=group.is_shortened,
        cohort_tag=group.cohort_tag, study_start=group.study_start, study_end=group.study_end,
        status=group.status, course=course,
        curator=CuratorRef(id=curator.id, full_name=staff_full_name(curator)) if curator else None,
    )


async def get_group_out(session: AsyncSession, group_id: uuid.UUID) -> GroupOut:
    year = await repo.current_year(session)
    row = (await session.execute(
        repo.groups_select(year.id if year else None).where(StudyGroup.id == group_id)
    )).unique().first()
    if row is None:
        raise NotFound("group")
    return group_out(*row)


async def create_group(session: AsyncSession, data: GroupIn) -> uuid.UUID:
    if data.level not in _NQF:
        raise InvalidInput(f"unknown level {data.level!r}")
    try:
        code = parse_group_code(data.code, default_nqf=_NQF[data.level])
    except GroupCodeError as e:
        raise InvalidInput(str(e)) from e
    level = await session.scalar(select(EducationLevel).where(EducationLevel.code == data.level))
    form = await session.scalar(select(StudyForm).where(StudyForm.code == data.form)) or _raise(
        InvalidInput(f"unknown form {data.form!r}"))
    group = StudyGroup(
        code=data.code.strip(), code_norm=code.code_norm, specialty_id=data.specialty_id, program_id=data.program_id,
        level_id=level.id, form_id=form.id, org_unit_id=data.org_unit_id,
        admission_year=code.admission_year, entry_course=code.entry_course, is_shortened=code.entry_course > 1,
        cohort_tag=data.cohort_tag or code.cohort_tag, study_start=data.study_start, study_end=data.study_end,
    )
    session.add(group)
    await commit(session)
    return group.id


async def patch_group(session: AsyncSession, group_id: uuid.UUID, data: GroupPatch) -> None:
    group = await session.get(StudyGroup, group_id) or _raise(NotFound("group"))
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await commit(session)


# --- curatorship ------------------------------------------------------------------

async def assign_curator(session: AsyncSession, group_id: uuid.UUID, staff_id: uuid.UUID, starts_on: date) -> Curatorship:
    await session.get(StudyGroup, group_id) or _raise(NotFound("group"))
    await session.get(Staff, staff_id) or _raise(NotFound("staff member"))
    current = await session.scalar(
        select(Curatorship).where(Curatorship.group_id == group_id, Curatorship.ends_on.is_(None)))
    if current:
        if starts_on <= current.starts_on:
            raise Conflict(f"new curatorship must start after the current one ({current.starts_on})")
        current.ends_on = starts_on
    new = Curatorship(group_id=group_id, staff_id=staff_id, starts_on=starts_on)
    session.add(new)
    await commit(session)
    return new


def _raise(exc: Exception):
    raise exc
