import uuid
from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sims.models import Contract, OrgUnit, Student, StudyGroup
from sims.modules.academic.repository import current_year
from sims.modules.academic.views import v_contract_balance, v_group_course
from sims.modules.performance import repository as debts_repo
from sims.modules.reports import labels as L
from sims.modules.reports.document import Column, Document, KeyValueBlock, TableBlock
from sims.modules.students import service as students
from sims.modules.students.repository import UNRESOLVED_DEBT


async def _scope_line(session: AsyncSession, *, org_unit_id=None, department_id=None, group_id=None) -> str:
    parts = [f"Сформовано {date.today():%d.%m.%Y}"]
    if org_unit_id and (u := await session.get(OrgUnit, org_unit_id)):
        parts.append(f"підрозділ: {u.name}")
    if department_id and (d := await session.get(OrgUnit, department_id)):
        parts.append(f"кафедра: {d.name}")
    if group_id and (g := await session.get(StudyGroup, group_id)):
        parts.append(f"група: {g.code}")
    return "; ".join(parts)


async def academic_debts(session: AsyncSession, *, org_unit_id: uuid.UUID | None = None,
                         department_id: uuid.UUID | None = None, group_id: uuid.UUID | None = None) -> Document:
    year = await current_year(session)
    stmt = debts_repo.filter_debts(
        debts_repo.debts_select().add_columns(v_group_course.c.course).outerjoin(
            v_group_course, and_(v_group_course.c.group_id == StudyGroup.id,
                                 v_group_course.c.academic_year_id == (year.id if year else None))),
        statuses=UNRESOLVED_DEBT, org_unit_id=org_unit_id, department_id=department_id, group_id=group_id,
    )
    rows = (await session.execute(debts_repo.order_debts(stmt))).all()
    table = TableBlock(
        columns=[Column("n", "№", "int"), Column("name", "ПІБ"), Column("group", "Група"), Column("course", "Курс", "int"),
                 Column("discipline", "Дисципліна"), Column("control", "Форма контролю"),
                 Column("year", "Навч. рік"), Column("semester", "Семестр", "int"), Column("status", "Статус"),
                 Column("opened", "Відкрито", "date"), Column("deadline", "Перескласти до", "date")],
        rows=[{"n": i, "name": r.full_name, "group": r.group_code, "course": r.course, "discipline": r.discipline,
               "control": L.CONTROL_FORM.get(r.control_form, r.control_form), "year": r.academic_year,
               "semester": r.semester, "status": L.DEBT_STATUS[r.AcademicDebt.status],
               "opened": r.AcademicDebt.opened_on, "deadline": r.AcademicDebt.retake_deadline}
              for i, r in enumerate(rows, start=1)],
    )
    meta = await _scope_line(session, org_unit_id=org_unit_id, department_id=department_id, group_id=group_id)
    return Document(title="Відомість академічних заборгованостей", meta=[meta], blocks=[table])


async def financial_debts(session: AsyncSession, *, org_unit_id: uuid.UUID | None = None,
                          group_id: uuid.UUID | None = None) -> Document:
    b = v_contract_balance.c
    stmt = (
        select(func.concat_ws(" ", Student.last_name, Student.first_name, Student.patronymic).label("name"),
               StudyGroup.code.label("group"), Contract.number, Contract.total_amount, b.due_total, b.paid_total, b.debt)
        .select_from(v_contract_balance)
        .join(Contract, Contract.id == b.contract_id)
        .join(Student, Student.id == b.student_id)
        .outerjoin(StudyGroup, StudyGroup.id == Student.current_group_id)
        .where(b.debt > 0)
        .order_by(StudyGroup.code_norm, Student.last_name, Student.first_name, Contract.number)
    )
    if group_id:
        stmt = stmt.where(StudyGroup.id == group_id)
    if org_unit_id:
        stmt = stmt.where(StudyGroup.org_unit_id.in_(select(debts_repo.org_subtree(org_unit_id).c.id)))
    rows = (await session.execute(stmt)).all()
    table = TableBlock(
        columns=[Column("n", "№", "int"), Column("name", "ПІБ"), Column("group", "Група"),
                 Column("number", "№ договору"), Column("total", "Сума договору, грн", "money"),
                 Column("due", "До сплати на сьогодні, грн", "money"), Column("paid", "Сплачено, грн", "money"),
                 Column("debt", "Борг, грн", "money")],
        rows=[{"n": i, "name": r.name, "group": r.group, "number": r.number, "total": r.total_amount,
               "due": r.due_total, "paid": r.paid_total, "debt": r.debt} for i, r in enumerate(rows, start=1)],
        totals=["due", "paid", "debt"],
    )
    meta = await _scope_line(session, org_unit_id=org_unit_id, group_id=group_id)
    return Document(title="Фінансовий звіт: заборгованість з оплати навчання", meta=[meta], blocks=[table])


async def student_card(session: AsyncSession, student_id: uuid.UUID) -> tuple[str, Document]:
    card = await students.card(session, student_id)
    perf = await students.performance(session, student_id)
    g = card.group
    profile = KeyValueBlock(title="Загальні дані", pairs=[
        ("ПІБ", card.full_name),
        ("Група", g.code if g else ""),
        ("Курс", g.course if g else ""),
        ("Спеціальність", f"{g.specialty.code} {g.specialty.name}" if g else ""),
        ("Освітня програма", g.program.name if g and g.program else ""),
        ("Рівень / форма", f"{g.level} / {L.FORM.get(g.form, g.form)}" if g else ""),
        ("Статус", L.STUDENT_STATUS.get(card.status, card.status)),
        ("Фінансування", L.FUNDING.get(card.funding or "", card.funding or "")),
        ("№ залікової книжки", card.record_book_no or ""),
        ("Дата народження", card.birth_date or ""),
    ])
    grades = TableBlock(
        title="Виписка оцінок",
        columns=[Column("year", "Навч. рік"), Column("semester", "Семестр", "int"), Column("discipline", "Дисципліна"),
                 Column("control", "Форма контролю"), Column("credits", "Кредити ЄКТС"),
                 Column("score", "Бал", "int"), Column("ects", "ECTS"), Column("national", "Оцінка")],
        rows=[{"year": s.academic_year, "semester": s.semester, "discipline": d.discipline,
               "control": L.CONTROL_FORM.get(d.control_form, d.control_form), "credits": d.credits_ects,
               "score": d.final.score if d.final else None, "ects": d.final.ects if d.final else None,
               "national": L.NATIONAL.get(d.final.national, "") if d.final and d.final.national else ""}
              for s in perf.semesters for d in s.disciplines],
    )
    blocks: list = [profile, grades]
    if open_debts := [d for d in perf.debts if d.status in UNRESOLVED_DEBT]:
        blocks.append(TableBlock(
            title="Академічні заборгованості",
            columns=[Column("discipline", "Дисципліна"), Column("year", "Навч. рік"), Column("semester", "Семестр", "int"),
                     Column("status", "Статус"), Column("deadline", "Перескласти до", "date")],
            rows=[{"discipline": d.discipline, "year": d.academic_year, "semester": d.semester,
                   "status": L.DEBT_STATUS[d.status], "deadline": d.retake_deadline} for d in open_debts],
        ))
    meta = [f"Сформовано {date.today():%d.%m.%Y}"]
    return card.full_name, Document(title="Індивідуальна картка студента", meta=meta, blocks=blocks)
