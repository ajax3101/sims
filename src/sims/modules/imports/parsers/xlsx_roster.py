"""Excel rosters: first row is the header, one student per row, group cipher in a column.

Columns are recognised by alias, so the same importer takes registry exports
with differently worded headers. Rows are grouped into one section per group.
"""
import re
from datetime import date, datetime
from pathlib import Path

import openpyxl

from sims.modules.imports.normalize import clean_text
from sims.modules.imports.parsers.base import RawRow, RosterSection, SectionHeader

_ALIASES = {
    "name": {"піб", "прізвище, ім’я, по батькові", "прізвище ім’я по батькові", "студент"},
    "group": {"група", "шифр групи", "академічна група"},
    "funding": {"фінансування", "форма фінансування", "б/к"},
    "tax_id": {"іпн", "рнокпп", "ідентифікаційний код"},
    "birth_date": {"дата народження"},
    "phone": {"телефон", "тел."},
    "email": {"email", "e-mail", "пошта", "електронна пошта"},
    "record_book_no": {"№ залікової книжки", "залікова книжка", "номер залікової книжки"},
}
_EXTRA = ("tax_id", "birth_date", "phone", "email", "record_book_no")


def _column_map(header_row) -> dict[str, int]:
    found = {}
    for idx, cell in enumerate(header_row):
        key = clean_text(str(cell or "")).casefold()
        for field, aliases in _ALIASES.items():
            if key in aliases and field not in found:
                found[field] = idx
    return found


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = clean_text(str(value))
    if m := re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", text):
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return text


def parse_xlsx_roster(path: Path) -> list[RosterSection]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = list(wb.active.iter_rows(values_only=True))
    finally:
        wb.close()
    if not rows:
        return []
    cols = _column_map(rows[0])
    if "name" not in cols or "group" not in cols:
        return [RosterSection(location={"row": 1}, header=SectionHeader(), errors=["missing_columns"])]

    sections: dict[str, RosterSection] = {}
    for excel_row, values in enumerate(rows[1:], start=2):
        get = lambda field: _cell(values[cols[field]]) if field in cols and cols[field] < len(values) else ""  # noqa: E731
        name = get("name")
        if not name:
            continue
        group = get("group")
        row = RawRow(
            location={"row": excel_row}, name=name, funding=get("funding"),
            extra={f: v for f in _EXTRA if (v := get(f))},
        )
        if not group:
            sections[f"#{excel_row}"] = RosterSection(
                location={"row": excel_row}, header=SectionHeader(), rows=[row], errors=["row_missing_group"])
            continue
        section = sections.setdefault(
            group, RosterSection(location={"row": excel_row}, header=SectionHeader(group_code=group)))
        section.rows.append(row)
    return list(sections.values())
