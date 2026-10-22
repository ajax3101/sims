import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import aliased

from sims.models import AcademicDebt, AcademicYear, Discipline, GroupDiscipline, OrgUnit, Semester, Student, StudyGroup


def debts_select() -> Select:
    """Debts with everything a list row or a report line shows, in one query."""
    full_name = func.concat_ws(" ", Student.last_name, Student.first_name, Student.patronymic)
    return (
        select(AcademicDebt, full_name.label("full_name"), StudyGroup.id.label("group_id"),
               StudyGroup.code.label("group_code"), Discipline.name.label("discipline"),
               GroupDiscipline.control_form, AcademicYear.label.label("academic_year"),
               Semester.number.label("semester"))
        .join(Student, Student.id == AcademicDebt.student_id)
        .join(GroupDiscipline, GroupDiscipline.id == AcademicDebt.group_discipline_id)
        .join(StudyGroup, StudyGroup.id == GroupDiscipline.group_id)
        .join(Discipline, Discipline.id == GroupDiscipline.discipline_id)
        .join(Semester, Semester.id == GroupDiscipline.semester_id)
        .join(AcademicYear, AcademicYear.id == Semester.academic_year_id)
    )


def org_subtree(root_id: uuid.UUID):
    """ids of an org unit and all units below it (faculty → departments)."""
    tree = select(OrgUnit.id).where(OrgUnit.id == root_id).cte("org_tree", recursive=True)
    child = aliased(OrgUnit)
    return tree.union_all(select(child.id).where(child.parent_id == tree.c.id))


def filter_debts(stmt: Select, *, group_id=None, student_id=None, status=None, statuses=None,
                 org_unit_id=None, department_id=None) -> Select:
    if group_id:
        stmt = stmt.where(StudyGroup.id == group_id)
    if student_id:
        stmt = stmt.where(AcademicDebt.student_id == student_id)
    if status:
        stmt = stmt.where(AcademicDebt.status == status)
    if statuses:
        stmt = stmt.where(AcademicDebt.status.in_(statuses))
    if org_unit_id:
        stmt = stmt.where(StudyGroup.org_unit_id.in_(select(org_subtree(org_unit_id).c.id)))
    if department_id:
        stmt = stmt.where(Discipline.department_id == department_id)
    return stmt


def order_debts(stmt: Select) -> Select:
    return stmt.order_by(StudyGroup.code_norm, Student.last_name, Student.first_name, AcademicYear.start_year,
                         Semester.number, Discipline.name, AcademicDebt.id)
