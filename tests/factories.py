"""Minimal valid object graphs on top of the seeded reference data."""
import itertools
import uuid
from datetime import date

from sqlalchemy import select

from sims.models import (
    AcademicYear, Discipline, EducationLevel, GroupDiscipline, MembershipReason, OrgUnit,
    OrgUnitKind, Semester, Specialty, Staff, Student, StudentGroupMembership, StudyForm, StudyGroup,
    ControlForm,
)


_scratch_years = itertools.count(1800)  # far from any year a test asserts on


def _uniq() -> str:
    return uuid.uuid4().hex[:8]


async def ref(session, model, code):
    return (await session.execute(select(model).where(model.code == code))).scalar_one()


async def institute(session) -> OrgUnit:
    unit = OrgUnit(kind=OrgUnitKind.INSTITUTE, name=f"Інститут {_uniq()}")
    session.add(unit)
    await session.flush()
    return unit


async def group(session, **kw) -> StudyGroup:
    code = kw.pop("code", f"6.G3.25-{_uniq()}")
    g = StudyGroup(
        code=code, code_norm=code,
        specialty=await ref(session, Specialty, "G3"),
        level=await ref(session, EducationLevel, "bachelor"),
        form=await ref(session, StudyForm, "part_time"),
        org_unit=await institute(session),
        admission_year=kw.pop("admission_year", 2025),
        **kw,
    )
    session.add(g)
    await session.flush()
    return g


async def staff(session) -> Staff:
    s = Staff(last_name=f"Куратор{_uniq()}", first_name="Ім'я")
    session.add(s)
    await session.flush()
    return s


async def student(session, **kw) -> Student:
    fields = {"last_name": "Іванов", "first_name": "Іван", "full_name_norm": f"іванов іван {_uniq()}"} | kw
    st = Student(**fields)
    session.add(st)
    await session.flush()
    return st


async def membership(session, st, g, starts_on, ends_on=None) -> StudentGroupMembership:
    m = StudentGroupMembership(
        student=st, group=g, starts_on=starts_on, ends_on=ends_on, reason=MembershipReason.ENROLLMENT
    )
    session.add(m)
    await session.flush()
    return m


async def academic_year(session, start_year: int, is_current=False) -> AcademicYear:
    y = AcademicYear(
        label=f"{start_year}/{start_year + 1}", start_year=start_year,
        starts_on=date(start_year, 9, 1), ends_on=date(start_year + 1, 6, 30), is_current=is_current,
    )
    session.add(y)
    await session.flush()
    return y


async def group_discipline(session, g=None) -> GroupDiscipline:
    year = await academic_year(session, next(_scratch_years))
    sem = Semester(academic_year_id=year.id, number=1)
    disc = Discipline(name=f"Дисципліна {_uniq()}")
    session.add_all([sem, disc])
    await session.flush()
    gd = GroupDiscipline(
        group_id=(g or await group(session)).id, discipline=disc, semester=sem, control_form=ControlForm.EXAM
    )
    session.add(gd)
    await session.flush()
    return gd
