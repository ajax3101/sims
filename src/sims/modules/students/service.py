import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select, union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sims.core.db import commit
from sims.core.errors import InvalidInput, NotFound
from sims.models import (
    AcademicDebt, AcademicYear, Contract, Discipline, GradeKind, Grade, GroupDiscipline, MembershipReason, Semester,
    Student, StudentDocument, StudentGroupMembership, StudentStatusHistory, StudyGroup,
)
from sims.modules.academic.service import get_group_out
from sims.modules.academic.views import v_contract_balance
from sims.modules.imports.normalize import name_norm
from sims.modules.students.repository import UNRESOLVED_DEBT
from sims.modules.students.schemas import (
    ContractOut, DebtOut, DisciplineResult, DocumentOut, FinanceOut, GradeOut, GroupRef, HistoryOut, MembershipOut,
    PaymentOut, PerformanceOut, ScheduleItemOut, SemesterResults, SpecialtyRef, StatusChangeIn, StatusHistoryOut, StudentIn,
    StudentListItem, StudentOut, StudentPatch, TransferIn,
)

_FINAL_KINDS = (GradeKind.FINAL, GradeKind.RETAKE, GradeKind.COMMISSION)


def full_name(st: Student) -> str:
    return " ".join(x for x in (st.last_name, st.first_name, st.patronymic) if x)


def list_item(row) -> StudentListItem:
    st, group_code, course, academic_debt, fin_debt, spec_code, spec_name = row
    return StudentListItem(
        id=st.id, full_name=full_name(st), last_name=st.last_name, first_name=st.first_name,
        patronymic=st.patronymic, status=st.status, funding=st.funding, record_book_no=st.record_book_no,
        group=GroupRef(id=st.current_group_id, code=group_code) if st.current_group_id else None,
        specialty=SpecialtyRef(code=spec_code, name=spec_name) if spec_code else None,
        course=course, has_academic_debt=academic_debt, financial_debt=fin_debt,
    )


async def _student(session: AsyncSession, student_id: uuid.UUID) -> Student:
    st = await session.get(Student, student_id)
    if st is None:
        raise NotFound("student")
    return st


async def card(session: AsyncSession, student_id: uuid.UUID) -> StudentOut:
    st = await _student(session, student_id)
    fields = {f: getattr(st, f) for f in StudentOut.model_fields if f not in ("full_name", "group")}
    out = StudentOut(**fields, full_name=full_name(st))
    if st.current_group_id:
        out.group = await get_group_out(session, st.current_group_id)
    return out


# --- tabs -------------------------------------------------------------------------

async def performance(session: AsyncSession, student_id: uuid.UUID) -> PerformanceOut:
    await _student(session, student_id)
    group_ids = select(StudentGroupMembership.group_id).where(StudentGroupMembership.student_id == student_id)
    gd_ids = union(
        select(GroupDiscipline.id).where(GroupDiscipline.group_id.in_(group_ids)),
        select(Grade.group_discipline_id).where(Grade.student_id == student_id),
        select(AcademicDebt.group_discipline_id).where(AcademicDebt.student_id == student_id),
    )
    rows = (await session.execute(
        select(GroupDiscipline, Discipline.name, AcademicYear.label, Semester.number)
        .join(Discipline, Discipline.id == GroupDiscipline.discipline_id)
        .join(Semester, Semester.id == GroupDiscipline.semester_id)
        .join(AcademicYear, AcademicYear.id == Semester.academic_year_id)
        .where(GroupDiscipline.id.in_(gd_ids))
        .order_by(AcademicYear.start_year, Semester.number, Discipline.name)
    )).all()
    grades = (await session.scalars(
        select(Grade).where(Grade.student_id == student_id).order_by(Grade.graded_on, Grade.attempt_no))).all()
    debts = (await session.scalars(
        select(AcademicDebt).where(AcademicDebt.student_id == student_id).order_by(AcademicDebt.opened_on))).all()
    unresolved = {d.group_discipline_id for d in debts if d.status in UNRESOLVED_DEBT}
    meta = {gd.id: (name, label, number) for gd, name, label, number in rows}

    semesters: dict[tuple[str, int], SemesterResults] = {}
    for gd, name, label, number in rows:
        own = [GradeOut.model_validate(g) for g in grades if g.group_discipline_id == gd.id]
        finals = [g for g in own if g.kind in _FINAL_KINDS]
        semesters.setdefault((label, number), SemesterResults(academic_year=label, semester=number, disciplines=[]))
        semesters[(label, number)].disciplines.append(DisciplineResult(
            group_discipline_id=gd.id, discipline=name, control_form=gd.control_form, credits_ects=gd.credits_ects,
            grades=own, final=finals[-1] if finals else None, has_debt=gd.id in unresolved,
        ))
    return PerformanceOut(
        semesters=list(semesters.values()),
        debts=[DebtOut(
            id=d.id, discipline=meta[d.group_discipline_id][0], academic_year=meta[d.group_discipline_id][1],
            semester=meta[d.group_discipline_id][2], status=d.status, opened_on=d.opened_on,
            retake_deadline=d.retake_deadline, closed_on=d.closed_on, note=d.note,
        ) for d in debts],
    )


async def finance(session: AsyncSession, student_id: uuid.UUID) -> FinanceOut:
    st = await _student(session, student_id)
    contracts = (await session.scalars(
        select(Contract).where(Contract.student_id == student_id).order_by(Contract.starts_on)
        .options(selectinload(Contract.schedule), selectinload(Contract.payments)))).all()
    balances = {r.contract_id: r for r in (await session.execute(
        select(v_contract_balance).where(v_contract_balance.c.student_id == student_id))).all()}
    out = [contract_out(c, balances[c.id]) for c in contracts]
    return FinanceOut(funding=st.funding, contracts=out, total_debt=sum((c.debt for c in out), start=_zero()))


def contract_out(c: Contract, balance) -> ContractOut:
    return ContractOut(
        id=c.id, number=c.number, signed_on=c.signed_on, starts_on=c.starts_on, ends_on=c.ends_on,
        total_amount=c.total_amount, currency=c.currency, status=c.status,
        schedule=[ScheduleItemOut.model_validate(s) for s in sorted(c.schedule, key=lambda s: s.due_date)],
        payments=[PaymentOut.model_validate(p) for p in sorted(c.payments, key=lambda p: p.paid_on)],
        due_total=balance.due_total, paid_total=balance.paid_total, debt=balance.debt,
    )


def _zero() -> Decimal:
    return Decimal("0.00")


async def history(session: AsyncSession, student_id: uuid.UUID) -> HistoryOut:
    await _student(session, student_id)
    memberships = (await session.execute(
        select(StudentGroupMembership, StudyGroup.code).join(StudyGroup)
        .where(StudentGroupMembership.student_id == student_id)
        .order_by(StudentGroupMembership.starts_on.desc(), StudentGroupMembership.created_at.desc()))).all()
    statuses = (await session.scalars(
        select(StudentStatusHistory).where(StudentStatusHistory.student_id == student_id)
        .order_by(StudentStatusHistory.changed_on.desc()))).all()
    documents = (await session.scalars(
        select(StudentDocument).where(StudentDocument.student_id == student_id)
        .order_by(StudentDocument.issued_on.desc().nulls_last()))).all()
    return HistoryOut(
        memberships=[MembershipOut(group=GroupRef(id=m.group_id, code=code), starts_on=m.starts_on, ends_on=m.ends_on,
                                   reason=m.reason, order_ref=m.order_ref) for m, code in memberships],
        status_history=[StatusHistoryOut.model_validate(h) for h in statuses],
        documents=[DocumentOut.model_validate(d) for d in documents],
    )


# --- changes ----------------------------------------------------------------------

async def create(session: AsyncSession, data: StudentIn) -> uuid.UUID:
    fields = data.model_dump(exclude={"group_id"})
    st = Student(**fields, full_name_norm=name_norm(data.last_name, data.first_name, data.patronymic))
    if data.group_id:
        if await session.get(StudyGroup, data.group_id) is None:
            raise NotFound("group")
        st.current_group_id = data.group_id
        st.memberships.append(StudentGroupMembership(
            group_id=data.group_id, starts_on=data.enrolled_on or date.today(), reason=MembershipReason.ENROLLMENT))
    session.add(st)
    await commit(session)
    return st.id


async def patch(session: AsyncSession, student_id: uuid.UUID, data: StudentPatch) -> None:
    st = await _student(session, student_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(st, field, value)
    st.full_name_norm = name_norm(st.last_name, st.first_name, st.patronymic)
    await commit(session)


async def change_status(session: AsyncSession, student_id: uuid.UUID, data: StatusChangeIn) -> None:
    st = await _student(session, student_id)
    if st.status == data.status:
        raise InvalidInput(f"student is already {data.status.value}")
    st.status = data.status
    session.add(StudentStatusHistory(student_id=st.id, status=data.status, changed_on=data.changed_on,
                                     order_no=data.order_no, note=data.note))
    await commit(session)


async def transfer(session: AsyncSession, student_id: uuid.UUID, data: TransferIn) -> None:
    st = await _student(session, student_id)
    if st.current_group_id == data.group_id:
        raise InvalidInput("student is already in this group")
    if await session.get(StudyGroup, data.group_id) is None:
        raise NotFound("group")
    current = await session.scalar(select(StudentGroupMembership).where(
        StudentGroupMembership.student_id == student_id, StudentGroupMembership.ends_on.is_(None)))
    if current:
        if data.on <= current.starts_on:
            raise InvalidInput(f"transfer date must be after {current.starts_on}")
        current.ends_on = data.on
        await session.flush()  # free the one-open-membership slot before inserting the new one
    session.add(StudentGroupMembership(student_id=st.id, group_id=data.group_id, starts_on=data.on,
                                       reason=MembershipReason.TRANSFER, order_ref=data.order_ref))
    st.current_group_id = data.group_id
    await commit(session)
