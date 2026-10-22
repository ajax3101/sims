from datetime import date
from pathlib import Path

from sims.modules.imports.parsers.docx_roster import parse_docx_roster
from tests import docx_builder as b

INPUT = Path(__file__).resolve().parents[2] / "input_data"


def test_header_fields_are_extracted(tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(
        group="6.G19.26-з-пцб-с2", specialty="G19 Будівництво та цивільна інженерія",
        program="Промислове і цивільне будівництво", course=1, term="01.09.2026-30.06.2029",
    ))
    [s] = parse_docx_roster(path)
    h = s.header
    assert (h.level, h.form, h.header_course, h.group_code) == ("bachelor", "part_time", 1, "6.G19.26-з-пцб-с2")
    assert (h.specialty_code, h.specialty_name) == ("G19", "Будівництво та цивільна інженерія")
    assert h.program_name == "Промислове і цивільне будівництво"
    assert (h.study_start, h.study_end) == (date(2026, 9, 1), date(2029, 6, 30))
    assert h.institute == "ІНЖЕНЕРНОГО НАВЧАЛЬНО-НАУКОВОГО ІНСТИТУТУ ім. Ю.М.Потебні"
    assert s.errors == []


def test_rows_keep_raw_cells_and_location(tmp_path):
    path = b.build(tmp_path / "r.docx",
                   b.section(rows=[("1", "Бадя Віталій Олегович", "Б")]),
                   b.section(rows=[("", "Кучер Олег Васильович", "В"), ("", "", "")]))
    first, second = parse_docx_roster(path)
    assert [(r.location, r.name, r.funding) for r in first.rows] == [
        ({"table": 0, "row": 0}, "Бадя Віталій Олегович", "Б"),
    ]
    assert [(r.location, r.name, r.funding) for r in second.rows] == [
        ({"table": 1, "row": 0}, "Кучер Олег Васильович", "В"),  # blank row dropped
    ]


def test_master_full_time_and_empty_program(tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(level="МАГІСТР", form="ДЕННОЇ", program="", group="7.G3.25"))
    [s] = parse_docx_roster(path)
    assert (s.header.level, s.header.form, s.header.program_name) == ("master", "full_time", None)


def test_term_with_spaces_around_dash(tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(term="15.09.2025 - 31.12.2026"))
    [s] = parse_docx_roster(path)
    assert (s.header.study_start, s.header.study_end) == (date(2025, 9, 15), date(2026, 12, 31))


def test_table_without_group_line_is_a_section_error(tmp_path):
    path = b.build(tmp_path / "r.docx", b.section(header=["СПИСОК", "СПЕЦІАЛЬНІСТЬ: G3 ЕЛЕКТРИЧНА ІНЖЕНЕРІЯ"]))
    [s] = parse_docx_roster(path)
    assert s.errors == ["header_missing_group"]


def test_real_input_files_yield_all_groups_and_rows():
    sections = [s for p in sorted(INPUT.glob("*.docx")) for s in parse_docx_roster(p)]
    assert len(sections) == 53  # 10+4+8+7+11+4+3+6 tables per file
    assert sum(len(s.rows) for s in sections) == 252
    assert [s for s in sections if s.errors] == []


def test_form_and_institute_glued_in_one_paragraph(tmp_path):
    # Real case (4- курс бак заочне.docx): no break or space between the two header lines.
    lines = [
        "СТУДЕНТІВ 3 КУРСУ ОСВІТНЬОГО РІВНЯ «БАКАЛАВР»",
        "ЗАОЧНОЇ ФОРМИ ЗДОБУТТЯ ОСВІТИІНЖЕНЕРНОГО НАВЧАЛЬНО-НАУКОВОГО ІНСТИТУТУ ім. Ю.М.Потебні",
        "СПЕЦІАЛЬНІСТЬ: 141 ЕЛЕКТРОЕНЕРГЕТИКА, ЕЛЕКТРОТЕХНІКА ТА ЕЛЕКТРОМЕХАНІКА",
        "ГРУПА 6.1414-з-с2",
    ]
    [s] = parse_docx_roster(b.build(tmp_path / "r.docx", b.section(header=lines)))
    assert (s.header.form, s.header.institute) == (
        "part_time", "ІНЖЕНЕРНОГО НАВЧАЛЬНО-НАУКОВОГО ІНСТИТУТУ ім. Ю.М.Потебні")
