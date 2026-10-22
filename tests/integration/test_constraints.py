"""Invariants the database must enforce on its own, whatever the service layer does."""
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from sims.models import AcademicDebt, Curatorship, DebtStatus, Grade, GradeKind, OrgUnit, OrgUnitKind, Semester
from tests import factories as f


async def _rejected(session, *objs):
    """Flush inside a savepoint; return True if the DB refused it."""
    try:
        async with session.begin_nested():
            session.add_all(objs)
            await session.flush()
    except (IntegrityError, DBAPIError):
        return True
    return False


async def test_org_unit_head_must_be_existing_staff(session):
    import uuid
    unit = OrgUnit(kind=OrgUnitKind.DEPARTMENT, name="Кафедра", head_staff_id=uuid.uuid7())
    assert await _rejected(session, unit)


async def test_curatorship_periods_of_one_group_cannot_overlap(session):
    g, a, b = await f.group(session), await f.staff(session), await f.staff(session)
    session.add(Curatorship(group_id=g.id, staff_id=a.id, starts_on=date(2025, 9, 1), ends_on=None))
    await session.flush()
    assert await _rejected(session, Curatorship(group_id=g.id, staff_id=b.id, starts_on=date(2026, 9, 1)))


async def test_curatorship_handover_on_same_day_is_allowed(session):
    g, a, b = await f.group(session), await f.staff(session), await f.staff(session)
    session.add(Curatorship(group_id=g.id, staff_id=a.id, starts_on=date(2025, 9, 1), ends_on=date(2026, 9, 1)))
    await session.flush()
    assert not await _rejected(session, Curatorship(group_id=g.id, staff_id=b.id, starts_on=date(2026, 9, 1)))


async def test_student_has_at_most_one_open_membership(session):
    st, g1, g2 = await f.student(session), await f.group(session), await f.group(session)
    await f.membership(session, st, g1, date(2025, 9, 1))
    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await f.membership(session, st, g2, date(2026, 2, 1))


async def test_closed_membership_does_not_block_new_open_one(session):
    st, g1, g2 = await f.student(session), await f.group(session), await f.group(session)
    await f.membership(session, st, g1, date(2025, 9, 1), ends_on=date(2026, 2, 1))
    await f.membership(session, st, g2, date(2026, 2, 1))  # must not raise


async def test_only_one_academic_year_is_current(session):
    await f.academic_year(session, 2061, is_current=True)
    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await f.academic_year(session, 2062, is_current=True)


async def test_one_unclosed_debt_per_student_and_discipline(session):
    st, gd = await f.student(session), await f.group_discipline(session)
    session.add(AcademicDebt(student_id=st.id, group_discipline_id=gd.id, opened_on=date(2026, 1, 20)))
    await session.flush()
    again = AcademicDebt(
        student_id=st.id, group_discipline_id=gd.id, opened_on=date(2026, 2, 1), status=DebtStatus.RETAKE_SCHEDULED
    )
    assert await _rejected(session, again)


async def test_closed_debt_does_not_block_a_new_one(session):
    st, gd = await f.student(session), await f.group_discipline(session)
    session.add(AcademicDebt(
        student_id=st.id, group_discipline_id=gd.id, opened_on=date(2025, 1, 20),
        status=DebtStatus.CLOSED, closed_on=date(2025, 2, 10),
    ))
    await session.flush()
    assert not await _rejected(
        session, AcademicDebt(student_id=st.id, group_discipline_id=gd.id, opened_on=date(2026, 1, 20))
    )


@pytest.mark.parametrize("entry_course, rejected", [(0, True), (1, False), (6, False), (7, True)])
async def test_group_entry_course_within_1_to_6(session, entry_course, rejected):
    try:
        async with session.begin_nested():
            await f.group(session, entry_course=entry_course)
        outcome = False
    except IntegrityError:
        outcome = True
    assert outcome is rejected


@pytest.mark.parametrize("score, rejected", [(-1, True), (0, False), (100, False), (101, True)])
async def test_grade_score_within_0_to_100(session, score, rejected):
    st, gd = await f.student(session), await f.group_discipline(session)
    grade = Grade(
        student_id=st.id, group_discipline_id=gd.id, kind=GradeKind.FINAL, score=score, graded_on=date(2026, 1, 20)
    )
    assert await _rejected(session, grade) is rejected


async def test_semester_number_is_1_or_2(session):
    year = await f.academic_year(session, 2070)
    assert await _rejected(session, Semester(academic_year_id=year.id, number=3))


async def test_enum_columns_reject_unknown_values_written_bypassing_orm(session):
    st = await f.student(session)
    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await session.execute(text("UPDATE student SET status = 'on_vacation' WHERE id = :id"), {"id": st.id})
