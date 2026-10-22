import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from sims.core.db import get_session
from sims.core.pagination import Page, Paging, count
from sims.modules.academic.repository import current_year
from sims.modules.students import repository as repo
from sims.modules.students import service
from sims.modules.students.models import Funding, StudentStatus
from sims.modules.students.schemas import (
    FinanceOut, HistoryOut, PerformanceOut, StatusChangeIn, StudentIn, StudentListItem, StudentOut, StudentPatch,
    TransferIn,
)

router = APIRouter(prefix="/api/students", tags=["students"])
Session = Depends(get_session)
SORT_PATTERN = "^-?(" + "|".join(repo.SORTS) + ")$"


@router.get("", response_model=Page[StudentListItem], summary="Students: paging, sorting, multi-level filters, search")
async def list_students(
    paging: Paging,
    sort: str = Query("name", pattern=SORT_PATTERN, description="field or -field"),
    q: str | None = Query(None, description="name fragment, record book, student card or tax id"),
    group_id: uuid.UUID | None = None, specialty_id: uuid.UUID | None = None, program_id: uuid.UUID | None = None,
    level: str | None = None, form: str | None = None, org_unit_id: uuid.UUID | None = None,
    course: int | None = Query(None, ge=1, le=6), curator_id: uuid.UUID | None = None,
    status: StudentStatus | None = None, funding: Funding | None = None,
    has_academic_debt: bool | None = None, has_financial_debt: bool | None = None,
    session: AsyncSession = Session,
):
    year = await current_year(session)
    stmt = repo.filter_students(
        repo.students_select(year.id if year else None), q=q, group_id=group_id, specialty_id=specialty_id,
        program_id=program_id, level=level, form=form, org_unit_id=org_unit_id, course_no=course,
        curator_id=curator_id, status=status, funding=funding,
        academic_debt=has_academic_debt, financial=has_financial_debt,
    )
    total = await count(session, stmt)
    rows = await repo.page(session, repo.order_students(stmt, sort), paging.offset, paging.size)
    return Page(items=[service.list_item(r) for r in rows], total=total, page=paging.page, size=paging.size)


@router.get("/{student_id}", response_model=StudentOut, summary="Student card: general data")
async def get_student(student_id: uuid.UUID, session: AsyncSession = Session):
    return await service.card(session, student_id)


@router.get("/{student_id}/performance", response_model=PerformanceOut, summary="Grades by semester and debts")
async def get_performance(student_id: uuid.UUID, session: AsyncSession = Session):
    return await service.performance(session, student_id)


@router.get("/{student_id}/finance", response_model=FinanceOut, summary="Contracts, payments and balance")
async def get_finance(student_id: uuid.UUID, session: AsyncSession = Session):
    return await service.finance(session, student_id)


@router.get("/{student_id}/history", response_model=HistoryOut, summary="Group memberships, statuses, documents")
async def get_history(student_id: uuid.UUID, session: AsyncSession = Session):
    return await service.history(session, student_id)


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(data: StudentIn, session: AsyncSession = Session):
    return await service.card(session, await service.create(session, data))


@router.patch("/{student_id}", response_model=StudentOut)
async def patch_student(student_id: uuid.UUID, data: StudentPatch, session: AsyncSession = Session):
    await service.patch(session, student_id, data)
    return await service.card(session, student_id)


@router.post("/{student_id}/status", response_model=StudentOut, summary="Change status (recorded in history)")
async def change_status(student_id: uuid.UUID, data: StatusChangeIn, session: AsyncSession = Session):
    await service.change_status(session, student_id, data)
    return await service.card(session, student_id)


@router.post("/{student_id}/transfer", response_model=StudentOut, summary="Move to another group")
async def transfer(student_id: uuid.UUID, data: TransferIn, session: AsyncSession = Session):
    await service.transfer(session, student_id, data)
    return await service.card(session, student_id)
