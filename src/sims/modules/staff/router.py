import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sims.core.db import commit, get_session
from sims.core.errors import NotFound
from sims.core.pagination import Page, Paging, count
from sims.models import Curatorship, Staff, StudyGroup
from sims.modules.staff.schemas import GroupCode, StaffIn, StaffOut, StaffPatch

router = APIRouter(prefix="/api/staff", tags=["staff"])
Session = Depends(get_session)


@router.get("", response_model=Page[StaffOut])
async def list_staff(paging: Paging, q: str | None = None, org_unit_id: uuid.UUID | None = None,
                     is_active: bool | None = None, session: AsyncSession = Session):
    stmt = select(Staff)
    if q:
        stmt = stmt.where(func.concat_ws(" ", Staff.last_name, Staff.first_name, Staff.patronymic).ilike(f"%{q}%"))
    if org_unit_id:
        stmt = stmt.where(Staff.org_unit_id == org_unit_id)
    if is_active is not None:
        stmt = stmt.where(Staff.is_active == is_active)
    total = await count(session, stmt)
    rows = (await session.scalars(
        stmt.order_by(Staff.last_name, Staff.first_name, Staff.id).offset(paging.offset).limit(paging.size))).all()
    curated = await _curated(session, [s.id for s in rows])
    return Page(items=[StaffOut.of(s, curated.get(s.id)) for s in rows], total=total, page=paging.page, size=paging.size)


async def _curated(session: AsyncSession, staff_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[GroupCode]]:
    """Open curatorships of a page of staff, in one query."""
    out: dict[uuid.UUID, list[GroupCode]] = {}
    if not staff_ids:
        return out
    rows = (await session.execute(
        select(Curatorship.staff_id, StudyGroup.id, StudyGroup.code).join(StudyGroup, StudyGroup.id == Curatorship.group_id)
        .where(Curatorship.staff_id.in_(staff_ids), Curatorship.ends_on.is_(None)).order_by(StudyGroup.code_norm))).all()
    for staff_id, gid, code in rows:
        out.setdefault(staff_id, []).append(GroupCode(id=gid, code=code))
    return out


@router.get("/{staff_id}", response_model=StaffOut)
async def get_staff(staff_id: uuid.UUID, session: AsyncSession = Session):
    s = await session.get(Staff, staff_id)
    if s is None:
        raise NotFound("staff member")
    return StaffOut.of(s)


@router.post("", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
async def create_staff(data: StaffIn, session: AsyncSession = Session):
    s = Staff(**data.model_dump())
    session.add(s)
    await commit(session)
    return StaffOut.of(s)


@router.patch("/{staff_id}", response_model=StaffOut)
async def patch_staff(staff_id: uuid.UUID, data: StaffPatch, session: AsyncSession = Session):
    s = await session.get(Staff, staff_id)
    if s is None:
        raise NotFound("staff member")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(s, field, value)
    await commit(session)
    return StaffOut.of(s)
