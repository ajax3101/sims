import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sims.core.db import commit
from sims.core.errors import NotFound
from sims.models import AcademicDebt, DebtStatus, Grade, GradeKind, GroupDiscipline, Student
from sims.modules.performance.grading import FAILING, PASS_SCORE, grade_scale
from sims.modules.performance.schemas import DebtListItem, DebtPatch, GradeIn, GroupRef, StudentRef
from sims.modules.students.repository import UNRESOLVED_DEBT

_RETAKES = (GradeKind.RETAKE, GradeKind.COMMISSION)


async def add_grade(session: AsyncSession, data: GradeIn) -> Grade:
    gd = await session.get(GroupDiscipline, data.group_discipline_id)
    if gd is None:
        raise NotFound("group discipline")
    if await session.get(Student, data.student_id) is None:
        raise NotFound("student")

    ects, national = data.ects, data.national
    if data.score is not None and (ects is None or national is None):
        derived_ects, derived_national = grade_scale(data.score, gd.control_form)
        ects, national = ects or derived_ects, national or derived_national
    attempt = (await session.scalar(select(func.coalesce(func.max(Grade.attempt_no), 0)).where(
        Grade.student_id == data.student_id, Grade.group_discipline_id == gd.id, Grade.kind == data.kind))) + 1
    grade = Grade(**data.model_dump(exclude={"ects", "national"}), ects=ects, national=national, attempt_no=attempt)
    session.add(grade)
    await session.flush()

    if data.kind != GradeKind.CURRENT:
        await _sync_debt(session, grade)
    await commit(session)
    return grade


async def _sync_debt(session: AsyncSession, grade: Grade) -> None:
    """A failing final/retake opens a debt (if none is unresolved); a passing retake closes it."""
    failed = grade.national in FAILING or (grade.score is not None and grade.score < PASS_SCORE)
    debt = await session.scalar(select(AcademicDebt).where(
        AcademicDebt.student_id == grade.student_id, AcademicDebt.group_discipline_id == grade.group_discipline_id,
        AcademicDebt.status.in_(UNRESOLVED_DEBT)))
    if failed and debt is None:
        session.add(AcademicDebt(student_id=grade.student_id, group_discipline_id=grade.group_discipline_id,
                                 opened_on=grade.graded_on))
    elif not failed and debt is not None and grade.kind in _RETAKES:
        debt.status = DebtStatus.CLOSED
        debt.closed_on = grade.graded_on
        debt.closing_grade_id = grade.id


async def patch_debt(session: AsyncSession, debt_id: uuid.UUID, data: DebtPatch) -> AcademicDebt:
    debt = await session.get(AcademicDebt, debt_id)
    if debt is None:
        raise NotFound("academic debt")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(debt, field, value)
    await commit(session)
    return debt


def debt_item(row) -> DebtListItem:
    d = row.AcademicDebt
    return DebtListItem(
        id=d.id, student=StudentRef(id=d.student_id, full_name=row.full_name),
        group=GroupRef(id=row.group_id, code=row.group_code), discipline=row.discipline,
        control_form=row.control_form, academic_year=row.academic_year, semester=row.semester, status=d.status,
        opened_on=d.opened_on, retake_deadline=d.retake_deadline, closed_on=d.closed_on, note=d.note,
    )
