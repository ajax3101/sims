import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sims.core.db import commit, get_session
from sims.core.pagination import Page, Paging, count
from sims.models import AcademicDebt, AcademicYear, Discipline, GroupDiscipline, Semester
from sims.modules.performance import repository as repo
from sims.modules.performance import service
from sims.modules.performance.models import DebtStatus
from sims.modules.performance.schemas import (
    DebtListItem, DebtPatch, DisciplineIn, DisciplineOut, GradeIn, GradeOut, GroupDisciplineIn, GroupDisciplineOut,
    SemesterIn, SemesterOut,
)

router = APIRouter(prefix="/api", tags=["performance"])
Session = Depends(get_session)


@router.get("/semesters", response_model=list[SemesterOut])
async def list_semesters(academic_year_id: uuid.UUID | None = None, session: AsyncSession = Session):
    stmt = select(Semester).join(AcademicYear).order_by(AcademicYear.start_year.desc(), Semester.number)
    if academic_year_id:
        stmt = stmt.where(Semester.academic_year_id == academic_year_id)
    return (await session.scalars(stmt)).all()


@router.post("/semesters", response_model=SemesterOut, status_code=status.HTTP_201_CREATED)
async def create_semester(data: SemesterIn, session: AsyncSession = Session):
    sem = Semester(**data.model_dump())
    session.add(sem)
    await commit(session)
    return sem


@router.get("/disciplines", response_model=Page[DisciplineOut])
async def list_disciplines(paging: Paging, q: str | None = None, department_id: uuid.UUID | None = None,
                           session: AsyncSession = Session):
    stmt = select(Discipline)
    if q:
        stmt = stmt.where(Discipline.name.ilike(f"%{q}%"))
    if department_id:
        stmt = stmt.where(Discipline.department_id == department_id)
    total = await count(session, stmt)
    rows = (await session.scalars(stmt.order_by(Discipline.name, Discipline.id).offset(paging.offset).limit(paging.size))).all()
    return Page(items=rows, total=total, page=paging.page, size=paging.size)


@router.post("/disciplines", response_model=DisciplineOut, status_code=status.HTTP_201_CREATED)
async def create_discipline(data: DisciplineIn, session: AsyncSession = Session):
    d = Discipline(**data.model_dump())
    session.add(d)
    await commit(session)
    return d


def _curriculum_select():
    return (
        select(GroupDiscipline, Discipline.name, AcademicYear.label, Semester.number)
        .join(Discipline, Discipline.id == GroupDiscipline.discipline_id)
        .join(Semester, Semester.id == GroupDiscipline.semester_id)
        .join(AcademicYear, AcademicYear.id == Semester.academic_year_id)
    )


def _gd_out(gd: GroupDiscipline, name: str, label: str, number: int) -> GroupDisciplineOut:
    return GroupDisciplineOut(
        id=gd.id, group_id=gd.group_id, discipline_id=gd.discipline_id, discipline=name, semester_id=gd.semester_id,
        academic_year=label, semester=number, control_form=gd.control_form, credits_ects=gd.credits_ects,
        teacher_id=gd.teacher_id,
    )


@router.post("/group-disciplines", response_model=GroupDisciplineOut, status_code=status.HTTP_201_CREATED,
             summary="Put a discipline into a group's curriculum for a semester")
async def create_group_discipline(data: GroupDisciplineIn, session: AsyncSession = Session):
    gd = GroupDiscipline(**data.model_dump())
    session.add(gd)
    await commit(session)
    return _gd_out(*(await session.execute(_curriculum_select().where(GroupDiscipline.id == gd.id))).one())


@router.get("/groups/{group_id}/disciplines", response_model=list[GroupDisciplineOut], summary="Group curriculum")
async def group_curriculum(group_id: uuid.UUID, session: AsyncSession = Session):
    rows = (await session.execute(_curriculum_select().where(GroupDiscipline.group_id == group_id)
                                  .order_by(AcademicYear.start_year, Semester.number, Discipline.name))).all()
    return [_gd_out(*r) for r in rows]


@router.post("/grades", response_model=GradeOut, status_code=status.HTTP_201_CREATED,
             summary="Record a grade; failing finals open a debt, passing retakes close it")
async def add_grade(data: GradeIn, session: AsyncSession = Session):
    return await service.add_grade(session, data)


@router.get("/academic-debts", response_model=Page[DebtListItem])
async def list_debts(paging: Paging, group_id: uuid.UUID | None = None, student_id: uuid.UUID | None = None,
                     status: DebtStatus | None = None, org_unit_id: uuid.UUID | None = None,
                     department_id: uuid.UUID | None = None, session: AsyncSession = Session):
    stmt = repo.filter_debts(repo.debts_select(), group_id=group_id, student_id=student_id, status=status,
                             org_unit_id=org_unit_id, department_id=department_id)
    total = await count(session, stmt)
    rows = (await session.execute(repo.order_debts(stmt).offset(paging.offset).limit(paging.size))).all()
    return Page(items=[service.debt_item(r) for r in rows], total=total, page=paging.page, size=paging.size)


@router.patch("/academic-debts/{debt_id}", response_model=DebtListItem, summary="Schedule a retake, close, write off")
async def patch_debt(debt_id: uuid.UUID, data: DebtPatch, session: AsyncSession = Session):
    debt = await service.patch_debt(session, debt_id, data)
    row = (await session.execute(repo.debts_select().where(AcademicDebt.id == debt.id))).one()
    return service.debt_item(row)
