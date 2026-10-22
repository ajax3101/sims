"""Student list query: one SELECT with flags computed by correlated subqueries (no per-row queries)."""
import uuid

from sqlalchemy import Numeric, Select, and_, asc, cast, desc, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from sims.models import AcademicDebt, Curatorship, DebtStatus, EducationLevel, Specialty, Student, StudyForm, StudyGroup
from sims.modules.academic.views import v_contract_balance, v_group_course
from sims.modules.imports.normalize import clean_text

UNRESOLVED_DEBT = (DebtStatus.OPEN, DebtStatus.RETAKE_SCHEDULED)

has_academic_debt = exists().where(
    AcademicDebt.student_id == Student.id, AcademicDebt.status.in_(UNRESOLVED_DEBT)
).correlate(Student)
financial_debt = (
    select(cast(func.coalesce(func.sum(v_contract_balance.c.debt), 0), Numeric(12, 2)))
    .where(v_contract_balance.c.student_id == Student.id)
    .correlate(Student)
    .scalar_subquery()
)
course = v_group_course.c.course

SORTS = {
    "name": (Student.last_name, Student.first_name, Student.patronymic),
    "group": (StudyGroup.code_norm,),
    "course": (course,),
    "status": (Student.status,),
    "funding": (Student.funding,),
    "created_at": (Student.created_at,),
    "financial_debt": (financial_debt,),
}


def students_select(year_id: uuid.UUID | None) -> Select:
    return (
        select(Student, StudyGroup.code, course, has_academic_debt.label("has_academic_debt"),
               financial_debt.label("financial_debt"), Specialty.code.label("specialty_code"),
               Specialty.name.label("specialty_name"))
        .outerjoin(StudyGroup, StudyGroup.id == Student.current_group_id)
        .outerjoin(Specialty, Specialty.id == StudyGroup.specialty_id)
        .outerjoin(v_group_course, and_(v_group_course.c.group_id == Student.current_group_id,
                                        v_group_course.c.academic_year_id == year_id))
    )


def filter_students(stmt: Select, *, q=None, group_id=None, specialty_id=None, program_id=None, level=None,
                    form=None, org_unit_id=None, course_no=None, curator_id=None, status=None, funding=None,
                    academic_debt=None, financial=None) -> Select:
    if q:
        text = clean_text(q)
        stmt = stmt.where(or_(
            Student.full_name_norm.contains(text.casefold(), autoescape=True),  # pg_trgm GIN index
            Student.record_book_no == text, Student.student_card_no == text, Student.tax_id == text,
        ))
    for column, value in ((Student.current_group_id, group_id), (StudyGroup.specialty_id, specialty_id),
                          (StudyGroup.program_id, program_id), (StudyGroup.org_unit_id, org_unit_id),
                          (course, course_no), (Student.status, status), (Student.funding, funding)):
        if value is not None:
            stmt = stmt.where(column == value)
    if level:
        stmt = stmt.where(StudyGroup.level_id == select(EducationLevel.id).where(EducationLevel.code == level).scalar_subquery())
    if form:
        stmt = stmt.where(StudyGroup.form_id == select(StudyForm.id).where(StudyForm.code == form).scalar_subquery())
    if curator_id:
        stmt = stmt.where(Student.current_group_id.in_(
            select(Curatorship.group_id).where(Curatorship.staff_id == curator_id, Curatorship.ends_on.is_(None))))
    if academic_debt is not None:
        stmt = stmt.where(has_academic_debt if academic_debt else ~has_academic_debt)
    if financial is not None:
        stmt = stmt.where(financial_debt > 0 if financial else financial_debt == 0)
    return stmt


def order_students(stmt: Select, sort: str) -> Select:
    direction = desc if sort.startswith("-") else asc
    columns = SORTS[sort.lstrip("-")]
    return stmt.order_by(*(direction(c).nulls_last() for c in columns), Student.id)


async def page(session: AsyncSession, stmt: Select, offset: int, limit: int):
    return (await session.execute(stmt.offset(offset).limit(limit))).all()
