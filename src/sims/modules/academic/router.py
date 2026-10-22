import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from sims.core.db import commit, get_session
from sims.core.errors import NotFound
from sims.core.pagination import Page, Paging, count
from sims.models import (
    AcademicYear, Curatorship, EducationalProgram, EducationLevel, OrgUnit, Specialty, Student, StudyForm, StudyGroup,
)
from sims.modules.academic import repository as repo
from sims.modules.academic import service
from sims.modules.academic.schemas import (
    AcademicYearIn, AcademicYearOut, AcademicYearPatch, DictionariesOut, GroupIn, GroupOut, GroupPatch, OrgUnitIn,
    OrgUnitOut, SpecialtyIn, SpecialtyPatch, SpecialtyRow,
)
from sims.modules.staff.schemas import CuratorshipOut, StaffOut

router = APIRouter(prefix="/api", tags=["academic"])
Session = Depends(get_session)


@router.get("/dictionaries", response_model=DictionariesOut, summary="Reference data for forms and filters")
async def dictionaries(session: AsyncSession = Session):
    all_of = lambda model, *order: session.scalars(select(model).order_by(*order))  # noqa: E731
    return DictionariesOut(
        levels=(await all_of(EducationLevel, EducationLevel.nqf_level)).all(),
        forms=(await all_of(StudyForm, StudyForm.code)).all(),
        specialties=(await all_of(Specialty, Specialty.classifier.desc(), Specialty.code)).all(),
        programs=(await all_of(EducationalProgram, EducationalProgram.name)).all(),
        org_units=(await all_of(OrgUnit, OrgUnit.kind, OrgUnit.name)).all(),
    )


@router.post("/org-units", response_model=OrgUnitOut, status_code=status.HTTP_201_CREATED)
async def create_org_unit(data: OrgUnitIn, session: AsyncSession = Session):
    unit = OrgUnit(**data.model_dump())
    session.add(unit)
    await commit(session)
    return unit


# --- specialties ------------------------------------------------------------------

async def _specialty_rows(session: AsyncSession, specialty_id: uuid.UUID | None = None) -> list[SpecialtyRow]:
    successor = aliased(Specialty)
    groups = select(func.count()).where(StudyGroup.specialty_id == Specialty.id).correlate(Specialty).scalar_subquery()
    students = (select(func.count()).select_from(Student).join(StudyGroup, StudyGroup.id == Student.current_group_id)
                .where(StudyGroup.specialty_id == Specialty.id).correlate(Specialty).scalar_subquery())
    stmt = (select(Specialty, successor.code, groups, students)
            .outerjoin(successor, successor.id == Specialty.successor_id)
            .order_by(Specialty.classifier.desc(), func.length(Specialty.code), Specialty.code))
    if specialty_id:
        stmt = stmt.where(Specialty.id == specialty_id)
    return [
        SpecialtyRow(id=s.id, classifier=s.classifier, code=s.code, name=s.name, successor_id=s.successor_id,
                     field_code=s.field_code, successor_code=succ, groups_count=g, students_count=n)
        for s, succ, g, n in (await session.execute(stmt)).all()
    ]


@router.get("/specialties", response_model=list[SpecialtyRow], summary="Specialty dictionary with usage counts")
async def list_specialties(session: AsyncSession = Session):
    return await _specialty_rows(session)


@router.post("/specialties", response_model=SpecialtyRow, status_code=status.HTTP_201_CREATED)
async def create_specialty(data: SpecialtyIn, session: AsyncSession = Session):
    field = data.code[:2] if data.classifier.value == "2015" else data.code[0]
    spec = Specialty(classifier=data.classifier, code=data.code, name=data.name.strip(), field_code=field,
                     successor_id=data.successor_id)
    session.add(spec)
    await commit(session)
    return (await _specialty_rows(session, spec.id))[0]


@router.patch("/specialties/{specialty_id}", response_model=SpecialtyRow)
async def patch_specialty(specialty_id: uuid.UUID, data: SpecialtyPatch, session: AsyncSession = Session):
    spec = await session.get(Specialty, specialty_id)
    if spec is None:
        raise NotFound("specialty")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(spec, field, value.strip() if isinstance(value, str) else value)
    await commit(session)
    return (await _specialty_rows(session, specialty_id))[0]


# --- academic years ---------------------------------------------------------------

@router.get("/academic-years", response_model=list[AcademicYearOut])
async def list_years(session: AsyncSession = Session):
    return (await session.scalars(select(AcademicYear).order_by(AcademicYear.start_year.desc()))).all()


@router.get("/academic-years/current", response_model=AcademicYearOut)
async def get_current_year(session: AsyncSession = Session):
    if (year := await repo.current_year(session)) is None:
        raise NotFound("current academic year")
    return year


@router.post("/academic-years", response_model=AcademicYearOut, status_code=status.HTTP_201_CREATED)
async def create_year(data: AcademicYearIn, session: AsyncSession = Session):
    return await service.create_year(session, data)


@router.patch("/academic-years/{year_id}", response_model=AcademicYearOut)
async def patch_year(year_id: uuid.UUID, data: AcademicYearPatch, session: AsyncSession = Session):
    return await service.patch_year(session, year_id, data)


# --- groups -----------------------------------------------------------------------

@router.get("/groups", response_model=Page[GroupOut], summary="Groups with current course and curator")
async def list_groups(
    paging: Paging,
    specialty_id: uuid.UUID | None = None, program_id: uuid.UUID | None = None,
    level: str | None = None, form: str | None = None, org_unit_id: uuid.UUID | None = None,
    course: int | None = Query(None, ge=1, le=6), status: str | None = None, q: str | None = None,
    session: AsyncSession = Session,
):
    year = await repo.current_year(session)
    stmt = repo.filter_groups(
        repo.groups_select(year.id if year else None), specialty_id=specialty_id, program_id=program_id,
        level=level, form=form, org_unit_id=org_unit_id, course=course, status=status, q=q,
    )
    total = await count(session, stmt)
    rows = (await session.execute(
        stmt.order_by(StudyGroup.code_norm).offset(paging.offset).limit(paging.size))).unique().all()
    return Page(items=[service.group_out(*r) for r in rows], total=total, page=paging.page, size=paging.size)


@router.get("/groups/{group_id}", response_model=GroupOut)
async def get_group(group_id: uuid.UUID, session: AsyncSession = Session):
    return await service.get_group_out(session, group_id)


@router.post("/groups", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(data: GroupIn, session: AsyncSession = Session):
    return await service.get_group_out(session, await service.create_group(session, data))


@router.patch("/groups/{group_id}", response_model=GroupOut)
async def patch_group(group_id: uuid.UUID, data: GroupPatch, session: AsyncSession = Session):
    await service.patch_group(session, group_id, data)
    return await service.get_group_out(session, group_id)


# --- curatorship ------------------------------------------------------------------

class CuratorIn(BaseModel):
    staff_id: uuid.UUID
    starts_on: date


@router.post("/groups/{group_id}/curator", response_model=CuratorshipOut, status_code=status.HTTP_201_CREATED,
             summary="Assign a curator; the open curatorship ends the day the new one starts")
async def assign_curator(group_id: uuid.UUID, data: CuratorIn, session: AsyncSession = Session):
    c = await service.assign_curator(session, group_id, data.staff_id, data.starts_on)
    return await _curatorship_out(session, c.id)


@router.get("/groups/{group_id}/curators", response_model=list[CuratorshipOut], summary="Curatorship history")
async def curator_history(group_id: uuid.UUID, session: AsyncSession = Session):
    rows = (await session.scalars(
        select(Curatorship).where(Curatorship.group_id == group_id).order_by(Curatorship.starts_on.desc())
        .options(joinedload(Curatorship.staff)))).all()
    return [CuratorshipOut(id=c.id, starts_on=c.starts_on, ends_on=c.ends_on, staff=StaffOut.of(c.staff)) for c in rows]


async def _curatorship_out(session: AsyncSession, cid: uuid.UUID) -> CuratorshipOut:
    c = await session.scalar(select(Curatorship).where(Curatorship.id == cid).options(joinedload(Curatorship.staff)))
    return CuratorshipOut(id=c.id, starts_on=c.starts_on, ends_on=c.ends_on, staff=StaffOut.of(c.staff))
