"""Word rosters: each group is a run of header paragraphs followed by a table (№ | ПІБ | Б/К)."""
import re
from datetime import date, datetime
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from sims.modules.imports.normalize import clean_text
from sims.modules.imports.parsers.base import RawRow, RosterSection, SectionHeader

_LEVELS = {"БАКАЛАВР": "bachelor", "МАГІСТР": "master", "ДОКТОР": "phd"}
_FORMS = {"ДЕННОЇ": "full_time", "ЗАОЧНОЇ": "part_time", "ДУАЛЬНОЇ": "dual"}
_DATE = r"\d{2}\.\d{2}\.\d{4}"

_RE_COURSE = re.compile(r"СТУДЕНТІВ\s+(\d)\s+КУРСУ", re.I)
_RE_LEVEL = re.compile(r"«\s*(\w+)\s*»")
_RE_FORM = re.compile(r"(\w+)\s+ФОРМИ", re.I)
_RE_SPECIALTY = re.compile(r"СПЕЦІАЛЬНІСТЬ:\s*([A-Z]\d{1,2}|\d{3})\s+(.+)", re.I)
_RE_PROGRAM = re.compile(r"ОСВІТНЯ ПРОГРАМА:\s*(.*)", re.I)
_RE_GROUP = re.compile(r"ГРУПА:?\s*(\S+)", re.I)
_RE_FORM_PREFIX = re.compile(r"^.*ФОРМИ\s+ЗДОБУТТЯ\s+ОСВІТИ\s*", re.I)
_RE_TERM = re.compile(rf"Термін навчання:?\s*({_DATE})\s*-\s*({_DATE})", re.I)


def _date(s: str) -> date:
    return datetime.strptime(s, "%d.%m.%Y").date()


def parse_header(lines: list[str]) -> SectionHeader:
    h = SectionHeader(lines=lines)
    for line in lines:
        upper = line.upper()
        if m := _RE_COURSE.search(line):
            h.header_course = int(m.group(1))
        if (m := _RE_LEVEL.search(line)) and m.group(1).upper() in _LEVELS:
            h.level = _LEVELS[m.group(1).upper()]
        if (m := _RE_FORM.search(line)) and m.group(1).upper() in _FORMS:
            h.form = _FORMS[m.group(1).upper()]
        if "ІНСТИТУТ" in upper or "ФАКУЛЬТЕТ" in upper:
            if not upper.startswith("В.О.") and "ДИРЕКТОР" not in upper and "ДЕКАН" not in upper:
                h.institute = _RE_FORM_PREFIX.sub("", line)  # form line glued on without a break
        if m := _RE_SPECIALTY.search(line):
            h.specialty_code, h.specialty_name = m.group(1).upper(), m.group(2).strip()
        if m := _RE_PROGRAM.search(line):
            h.program_name = m.group(1).strip() or None
        if m := _RE_GROUP.search(line):
            h.group_code = m.group(1)
        if m := _RE_TERM.search(line):
            h.study_start, h.study_end = _date(m.group(1)), _date(m.group(2))
    return h


def parse_docx_roster(path: Path) -> list[RosterSection]:
    document = docx.Document(str(path))
    sections: list[RosterSection] = []
    lines: list[str] = []
    for el in document.element.body.iterchildren():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "p":
            if text := clean_text(Paragraph(el, document).text):
                lines.append(text)
        elif tag == "tbl":
            table_no = len(sections)
            header = parse_header(lines)
            section = RosterSection(location={"table": table_no}, header=header)
            if not header.group_code:
                section.errors.append("header_missing_group")
            for row_no, row in enumerate(Table(el, document).rows):
                cells = [c.text for c in row.cells]
                if not any(c.strip() for c in cells):
                    continue
                name, funding = (cells[1], cells[2]) if len(cells) >= 3 else (cells[-1], "")
                section.rows.append(RawRow(location={"table": table_no, "row": row_no}, name=name, funding=funding))
            sections.append(section)
            lines = []
    return sections
