from datetime import date
from pathlib import Path

from sqlalchemy import func, select, text

from sims.models import (
    EducationalProgram, ImportBatch, ImportIssue, OrgUnit, Specialty, Student, StudentGroupMembership, StudyGroup,
)
from sims.modules.imports.import_service import import_file
from tests import docx_builder as b
from tests import factories as f

INPUT = Path(__file__).resolve().parents[2] / "input_data"


def _codes(report, severity=None):
    return sorted(i.code for i in report.issues if severity is None or i.severity == severity)


async def _count(session, stmt):
    return (await session.execute(stmt)).scalar_one()


async def _group(session, code_norm):
    return (await session.execute(select(StudyGroup).where(StudyGroup.code_norm == code_norm))).scalar_one()


async def test_import_creates_group_dictionaries_and_students(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(
        group="6.G3.25-з", rows=[("1", "Бадя Віталій Олегович", "Б"), ("2", "Бренер Віталій Дмитрович", "К")],
    ))
    report = await import_file(session, path)

    assert (report.students_created, report.groups_created, report.errors) == (2, 1, 0)
    assert report.dictionaries_created == {"org_unit": 1, "program": 1, "specialty": 0}

    g = await _group(session, "6.G3.25-з")
    assert (g.admission_year, g.entry_course, g.is_shortened, g.study_start, g.study_end) == (
        2025, 1, False, date(2025, 9, 1), date(2029, 6, 30))
    spec = await session.get(Specialty, g.specialty_id)
    assert (spec.classifier, spec.code) == ("2024", "G3")  # the seeded row, not a new one
    program = await session.get(EducationalProgram, g.program_id)
    assert program.name == "Електроенергетика, електротехніка та електромеханіка"

    students = (await session.execute(
        select(Student.last_name, Student.funding, Student.current_group_id).order_by(Student.last_name)
        .join(StudentGroupMembership).where(StudentGroupMembership.group_id == g.id,
                                            StudentGroupMembership.ends_on.is_(None))
    )).all()
    assert [tuple(s) for s in students] == [("Бадя", "budget", g.id), ("Бренер", "contract", g.id)]


async def test_reimport_of_same_file_creates_nothing_and_counts_duplicates(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(group="6.G3.25-з", rows=[
        ("1", "Бадя Віталій Олегович", "Б"), ("2", "Бренер Віталій Дмитрович", "К")]))
    await import_file(session, path)
    again = await import_file(session, path)

    assert (again.students_created, again.students_updated, again.duplicates, again.groups_created) == (0, 0, 2, 0)
    g = await _group(session, "6.G3.25-з")
    assert await _count(session, select(func.count()).select_from(StudentGroupMembership)
                        .where(StudentGroupMembership.group_id == g.id)) == 2


async def test_changed_funding_on_reimport_updates_the_student(session, tmp_path):
    await import_file(session, b.build(tmp_path / "a.docx", b.section(rows=[("1", "Бадя Віталій Олегович", "Б")])))
    report = await import_file(session, b.build(tmp_path / "b.docx", b.section(rows=[("1", "Бадя Віталій Олегович", "К")])))

    assert (report.students_created, report.students_updated, report.duplicates) == (0, 1, 0)
    funding = await _count(session, select(Student.funding).where(Student.last_name == "Бадя"))
    assert funding == "contract"


async def test_same_name_twice_in_one_group_is_a_duplicate_in_file(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(rows=[
        ("1", "Бадя Віталій Олегович", "Б"), ("2", "Бадя  Віталій Олегович", "Б")]))
    report = await import_file(session, path)
    assert (report.students_created, report.duplicates) == (1, 1)
    assert _codes(report) == ["duplicate_in_file"]


async def test_unknown_specialty_is_created_and_flagged(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(group="6.G99.25-з", specialty="G99 ТЕСТОВА СПЕЦІАЛЬНІСТЬ", program=""))
    report = await import_file(session, path)

    assert report.dictionaries_created["specialty"] == 1
    assert _codes(report, "warning") == ["program_missing", "specialty_created"]
    spec = (await session.execute(select(Specialty).where(Specialty.code == "G99"))).scalar_one()
    assert (spec.classifier, spec.name, spec.field_code) == ("2024", "Тестова спеціальність", "G")


async def test_program_typo_reuses_existing_program_of_same_level(session, tmp_path):
    path = b.build(tmp_path / "r.docx",
                   b.section(group="6.G10.25-мчм-з", specialty="G10 МЕТАЛУРГІЯ", program="МЕТАЛУРГІЯ ЧОРНИХ МЕТАЛІВ"),
                   b.section(group="6.G10.25-мчм-з-с2", specialty="G10 МЕТАЛУРГІЯ", program="МЕТАЛУРГВЯ ЧОРНИХ МЕТАЛІВ",
                             rows=[("1", "Овдієнко Артем Анатолійович", "Б")]))
    report = await import_file(session, path)

    assert report.dictionaries_created["program"] == 1
    assert "program_fuzzy_matched" in _codes(report, "warning")
    g1, g2 = await _group(session, "6.G10.25-мчм-з"), await _group(session, "6.G10.25-мчм-з-с2")
    assert g1.program_id == g2.program_id


async def test_program_typo_takes_spelling_from_other_level(session, tmp_path):
    path = b.build(tmp_path / "r.docx",
                   b.section(group="6.G10.25-мчм-з", specialty="G10 МЕТАЛУРГІЯ", program="МЕТАЛУРГІЯ ЧОРНИХ МЕТАЛІВ"),
                   b.section(group="7.G10.25-з-мчм", level="МАГІСТР", specialty="G10 МЕТАЛУРГІЯ",
                             program="МЕТАЛУРГВЯ ЧОРНИХ МЕТАЛІВ", rows=[("1", "Овдієнко Артем Анатолійович", "Б")]))
    report = await import_file(session, path)

    master = await _group(session, "7.G10.25-мчм-з")
    program = await session.get(EducationalProgram, master.program_id)
    assert program.name == "Металургія чорних металів"
    assert "program_name_corrected" in _codes(report, "warning")


async def test_invalid_row_is_reported_with_location_and_others_still_imported(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(rows=[("1", "123 Іван Петрович", "Б"), ("2", "Бадя Віталій Олегович", "Б")]))
    report = await import_file(session, path)

    assert (report.students_created, report.errors) == (1, 1)
    [err] = [i for i in report.issues if i.severity == "error"]
    assert (err.code, err.location) == ("invalid_name", {"table": 0, "row": 0})


async def test_enrollment_note_and_unknown_funding_code(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(rows=[("", "Кучер Олег Васильович   (з 25.09.2026)", "В")]))
    report = await import_file(session, path)

    st = (await session.execute(select(Student).where(Student.last_name == "Кучер"))).scalar_one()
    assert (st.funding, st.funding_raw, st.enrolled_on) == ("other", "В", date(2026, 9, 25))
    starts_on = await _count(session, select(StudentGroupMembership.starts_on).where(StudentGroupMembership.student_id == st.id))
    assert starts_on == date(2026, 9, 25)
    assert _codes(report, "warning") == ["funding_unknown_code"]


async def test_repaired_group_code_is_flagged(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(group="G5.26-с2", specialty="G5 ЕЛЕКТРОНІКА", program="Мікро- та наносистемна техніка"))
    report = await import_file(session, path)
    assert await _group(session, "6.G5.26-с2")
    assert _codes(report, "warning") == ["group_code_repaired"]


async def test_section_without_group_is_an_error_and_its_rows_are_skipped(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(header=["СПИСОК", "СПЕЦІАЛЬНІСТЬ: G3 ЕЛЕКТРИЧНА ІНЖЕНЕРІЯ"]),
                   b.section(group="6.G3.25-з"))
    report = await import_file(session, path)
    assert (report.students_created, report.errors) == (1, 1)
    assert _codes(report, "error") == ["header_missing_group"]


async def test_unparseable_group_code_is_an_error(session, tmp_path):
    report = await import_file(session, b.build(tmp_path / "r.docx", b.section(group="Х-25")))
    assert (report.students_created, _codes(report, "error")) == (0, ["invalid_group_code"])


async def test_batch_and_issues_are_persisted(session, tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(rows=[("1", "123", "Б"), ("2", "Бадя Віталій Олегович", "")]))
    report = await import_file(session, path)

    batch = await session.get(ImportBatch, report.batch_id)
    assert (batch.status, batch.kind, batch.source_filename, len(batch.file_sha256)) == ("done", "roster_docx", "r.docx", 64)
    assert batch.stats["students_created"] == 1 and batch.stats["errors"] == 1 and batch.stats["warnings"] == 1
    assert await _count(session, select(func.count()).select_from(ImportIssue)
                        .where(ImportIssue.batch_id == batch.id)) == 2


# Course the filename names, for every group in it (с2 groups of the 1st-year intake enter the 2nd course).
FILE_COURSES = {
    "+1 курс таблица список з 25.09.docx": {1, 2},
    "1- курс бак заочне .docx": {1},
    "2- курс бак заочне .docx": {2},
    "3- курс бак заочне.docx": {3},
    "4- курс бак заочне.docx": {4},
    "Магістри 1 - курс заочне .docx": {1},
    "Магістри 2-  курс ДН заочне .docx": {2},
    "Магістри 2-  курс заочне.docx": {2},
}


async def test_real_input_files_import_cleanly_with_courses_matching_filenames(session):
    year = await f.academic_year(session, 2026)
    reports = [await import_file(session, p) for p in sorted(INPUT.glob("*.docx"))]

    assert sum(r.students_created for r in reports) == 252
    assert sum(r.groups_created for r in reports) == 53
    assert sum(r.errors for r in reports) == 0
    assert await _count(session, select(func.count()).select_from(OrgUnit)) == 1

    for r in reports:
        courses = set((await session.execute(text(
            "SELECT DISTINCT v.course FROM v_group_course v JOIN study_group g ON g.id = v.group_id "
            "WHERE v.academic_year_id = :y AND g.meta->>'source_file' = :f"
        ), {"y": year.id, "f": r.source_filename})).scalars())
        assert courses == FILE_COURSES[r.source_filename], r.source_filename


async def _seed_group(session, tmp_path, rows=(("1", "Бадя Віталій Олегович", "Б"),)):
    await import_file(session, b.build(tmp_path / "seed.docx", b.section(group="6.G3.25-з", rows=list(rows))))


async def test_xlsx_rows_enrich_existing_students_of_existing_group(session, tmp_path):
    from tests import xlsx_builder as x
    await _seed_group(session, tmp_path)
    path = x.build(tmp_path / "r.xlsx", ["ПІБ", "Група", "Фінансування", "ІПН", "Дата народження"], [
        ["Бадя Віталій Олегович", "6.G3.25-з", "Б", "3456789012", "01.03.2005"],
        ["Бренер Віталій Дмитрович", "6.G3.25-з", "К", None, None],
    ])
    report = await import_file(session, path)

    assert (report.students_created, report.students_updated, report.groups_created, report.errors) == (1, 1, 0, 0)
    st = (await session.execute(select(Student).where(Student.last_name == "Бадя"))).scalar_one()
    assert (st.tax_id, st.birth_date) == ("3456789012", date(2005, 3, 1))
    assert (await session.get(ImportBatch, report.batch_id)).kind == "roster_xlsx"


async def test_xlsx_matches_by_tax_id_before_name(session, tmp_path):
    from tests import xlsx_builder as x
    await _seed_group(session, tmp_path)
    await import_file(session, x.build(tmp_path / "a.xlsx", ["ПІБ", "Група", "ІПН"],
                                       [["Бадя Віталій Олегович", "6.G3.25-з", "3456789012"]]))
    report = await import_file(session, x.build(tmp_path / "b.xlsx", ["ПІБ", "Група", "ІПН", "Фінансування"],
                                                [["Бадя Віталій Олегович", "6.G3.25-з", "3456789012", "К"],
                                                 ["Бадя Віталiй Олегович", "6.G3.25-з", "3456789012", "К"]]))
    assert report.students_created == 0  # the Latin-'i' spelling is the same person by tax id


async def test_xlsx_row_for_unknown_group_is_an_error(session, tmp_path):
    from tests import xlsx_builder as x
    report = await import_file(session, x.build(tmp_path / "r.xlsx", ["ПІБ", "Група"], [["Бадя Віталій Олегович", "6.G3.24-з"]]))
    assert (report.students_created, _codes(report, "error")) == (0, ["unknown_group"])


async def test_xlsx_invalid_tax_id_is_a_row_error(session, tmp_path):
    from tests import xlsx_builder as x
    await _seed_group(session, tmp_path)
    report = await import_file(session, x.build(tmp_path / "r.xlsx", ["ПІБ", "Група", "ІПН"],
                                                [["Бренер Віталій Дмитрович", "6.G3.25-з", "12345"]]))
    assert (report.students_created, _codes(report, "error")) == (0, ["invalid_row"])
