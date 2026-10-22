import uuid
from datetime import date

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from sims.models import AcademicYear, Curatorship, EducationLevel, Staff, StudyForm, StudyGroup
from sims.modules.academic.views import v_group_course


async def current_year(session: AsyncSession, today: date | None = None) -> AcademicYear | None:
    """The flagged current year, else the one whose dates contain today."""
    if flagged := await session.scalar(select(AcademicYear).where(AcademicYear.is_current)):
        return flagged
    today = today or date.today()
    return await session.scalar(
        select(AcademicYear).where(AcademicYear.starts_on <= today, AcademicYear.ends_on >= today)
    )


def groups_select(year_id: uuid.UUID | None) -> Select:
    """Groups with their course in `year_id` and the open curatorship's staff member, in one query."""
    return (
        select(StudyGroup, v_group_course.c.course, Staff)
        .outerjoin(v_group_course, and_(v_group_course.c.group_id == StudyGroup.id,
                                        v_group_course.c.academic_year_id == year_id))
        .outerjoin(Curatorship, and_(Curatorship.group_id == StudyGroup.id, Curatorship.ends_on.is_(None)))
        .outerjoin(Staff, Staff.id == Curatorship.staff_id)
        .options(
            joinedload(StudyGroup.specialty), joinedload(StudyGroup.program), joinedload(StudyGroup.level),
            joinedload(StudyGroup.form), joinedload(StudyGroup.org_unit),
        )
    )


def filter_groups(stmt: Select, *, specialty_id=None, program_id=None, level=None, form=None,
                  org_unit_id=None, course=None, status=None, q=None) -> Select:
    if specialty_id:
        stmt = stmt.where(StudyGroup.specialty_id == specialty_id)
    if program_id:
        stmt = stmt.where(StudyGroup.program_id == program_id)
    if level:
        stmt = stmt.where(StudyGroup.level_id == select(EducationLevel.id).where(EducationLevel.code == level).scalar_subquery())
    if form:
        stmt = stmt.where(StudyGroup.form_id == select(StudyForm.id).where(StudyForm.code == form).scalar_subquery())
    if org_unit_id:
        stmt = stmt.where(StudyGroup.org_unit_id == org_unit_id)
    if course:
        stmt = stmt.where(v_group_course.c.course == course)
    if status:
        stmt = stmt.where(StudyGroup.status == status)
    if q:
        stmt = stmt.where(or_(StudyGroup.code.ilike(f"%{q}%"), StudyGroup.code_norm.ilike(f"%{q}%")))
    return stmt
