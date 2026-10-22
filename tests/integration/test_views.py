from datetime import date
from decimal import Decimal

from sqlalchemy import text

from sims.models import Contract, Payment, PaymentScheduleItem
from tests import factories as f

COURSE_SQL = text(
    "SELECT y.start_year, v.course FROM v_group_course v JOIN academic_year y ON y.id = v.academic_year_id "
    "WHERE v.group_id = :g ORDER BY y.start_year"
)


async def _years(session, *start_years):
    for y in start_years:
        await f.academic_year(session, y)


async def _courses(session, g) -> list[tuple[int, int]]:
    return [tuple(r) for r in (await session.execute(COURSE_SQL, {"g": g.id})).all()]


async def test_course_counts_from_admission_year(session):
    await _years(session, 2023, 2024, 2025, 2026)
    g = await f.group(session, admission_year=2025, study_end=date(2029, 6, 30))
    assert await _courses(session, g) == [(2025, 1), (2026, 2)]


async def test_shortened_group_starts_at_its_entry_course(session):
    await _years(session, 2026)
    g = await f.group(session, admission_year=2026, entry_course=2, is_shortened=True, study_end=date(2029, 6, 30))
    assert await _courses(session, g) == [(2026, 2)]


async def test_no_course_after_study_end(session):
    await _years(session, 2023, 2024, 2025, 2026, 2027)
    g = await f.group(session, admission_year=2023, study_end=date(2027, 6, 30))
    assert await _courses(session, g) == [(2023, 1), (2024, 2), (2025, 3), (2026, 4)]


async def test_course_never_exceeds_6_without_study_end(session):
    await _years(session, 2030, 2031, 2032, 2033, 2034, 2035, 2036)
    g = await f.group(session, admission_year=2030)
    assert [c for _, c in await _courses(session, g)] == [1, 2, 3, 4, 5, 6]


BALANCE_SQL = text("SELECT due_total, paid_total, debt FROM v_contract_balance WHERE contract_id = :c")


async def _contract(session, schedule=(), payments=()):
    st = await f.student(session)
    c = Contract(student_id=st.id, number=f"К-{st.id.hex[:8]}", starts_on=date(2025, 9, 1), total_amount=Decimal("20000"))
    c.schedule = [PaymentScheduleItem(due_date=d, amount=Decimal(a)) for d, a in schedule]
    c.payments = [Payment(paid_on=d, amount=Decimal(a)) for d, a in payments]
    session.add(c)
    await session.flush()
    return c


async def _balance(session, c):
    return tuple((await session.execute(BALANCE_SQL, {"c": c.id})).one())


async def test_debt_counts_only_installments_already_due(session):
    c = await _contract(
        session,
        schedule=[(date(2000, 9, 1), "10000"), (date(2999, 2, 1), "10000")],
        payments=[(date(2000, 9, 5), "4000")],
    )
    assert await _balance(session, c) == (Decimal("10000.00"), Decimal("4000.00"), Decimal("6000.00"))


async def test_overpayment_is_not_negative_debt(session):
    c = await _contract(session, schedule=[(date(2000, 9, 1), "5000")], payments=[(date(2000, 9, 1), "7000")])
    assert await _balance(session, c) == (Decimal("5000.00"), Decimal("7000.00"), Decimal("0.00"))


async def test_contract_without_schedule_or_payments_has_zero_debt(session):
    c = await _contract(session)
    assert await _balance(session, c) == (Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
