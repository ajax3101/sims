from datetime import datetime

from sims.modules.imports.parsers.xlsx_roster import parse_xlsx_roster
from tests import xlsx_builder as x


def test_rows_are_grouped_into_sections_by_group_code(tmp_path):
    path = x.build(tmp_path / "r.xlsx", ["№", "ПІБ", "Група", "Фінансування", "ІПН", "Дата народження", "Телефон", "E-mail"], [
        [1, "Бадя Віталій Олегович", "6.G3.25-з", "Б", 3456789012, datetime(2005, 3, 1), "+380501112233", "badia@example.com"],
        [2, "Кучер Олег Васильович", "7.G3.25-з", "К", None, "01.03.2001", None, None],
        [3, "Бренер Віталій Дмитрович", "6.G3.25-з", "К", None, None, None, None],
    ])
    first, second = parse_xlsx_roster(path)
    assert (first.header.group_code, second.header.group_code) == ("6.G3.25-з", "7.G3.25-з")
    assert [(r.location, r.name, r.funding) for r in first.rows] == [
        ({"row": 2}, "Бадя Віталій Олегович", "Б"), ({"row": 4}, "Бренер Віталій Дмитрович", "К"),
    ]
    assert first.rows[0].extra == {
        "tax_id": "3456789012", "birth_date": "2005-03-01", "phone": "+380501112233", "email": "badia@example.com",
    }
    assert second.rows[0].extra == {"birth_date": "2001-03-01"}


def test_header_aliases_are_case_and_space_insensitive(tmp_path):
    path = x.build(tmp_path / "r.xlsx", ["  прізвище, ім'я, по батькові ", "ШИФР ГРУПИ", "Форма фінансування", "№ залікової книжки"],
                   [["Бадя Віталій Олегович", "6.G3.25-з", "К", "ЗК-0012"]])
    [s] = parse_xlsx_roster(path)
    assert (s.header.group_code, s.rows[0].funding, s.rows[0].extra) == ("6.G3.25-з", "К", {"record_book_no": "ЗК-0012"})


def test_missing_required_columns_is_a_file_error(tmp_path):
    [s] = parse_xlsx_roster(x.build(tmp_path / "r.xlsx", ["ПІБ", "Фінансування"], [["Бадя Віталій Олегович", "Б"]]))
    assert (s.errors, s.rows) == (["missing_columns"], [])


def test_row_without_group_is_its_own_error_section(tmp_path):
    [s] = parse_xlsx_roster(x.build(tmp_path / "r.xlsx", ["ПІБ", "Група"], [["Бадя Віталій Олегович", None]]))
    assert (s.errors, [r.location for r in s.rows]) == (["row_missing_group"], [{"row": 2}])
