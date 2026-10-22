import pytest

from sims.cli import collect_files, format_report
from sims.modules.imports.schemas import ImportReport, IssueOut


def test_collect_files_expands_directories_and_skips_office_lock_files(tmp_path):
    for name in ["b.xlsx", "a.docx", "~$a.docx", "notes.txt"]:
        (tmp_path / name).write_bytes(b"")
    single = tmp_path / "sub" / "c.docx"
    single.parent.mkdir()
    single.write_bytes(b"")
    assert collect_files([tmp_path, single]) == [tmp_path / "a.docx", tmp_path / "b.xlsx", single]


def test_collect_files_rejects_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        collect_files([tmp_path / "nope.docx"])


def test_format_report_lists_counts_and_each_issue_with_location():
    report = ImportReport(
        source_filename="r.docx", status="done", students_created=3, duplicates=1, groups_created=1,
        issues=[IssueOut(severity="error", code="invalid_name", message="bad", location={"table": 0, "row": 2})],
    )
    text = format_report(report)
    assert "r.docx" in text and "done" in text
    assert "створено 3" in text and "дублікатів 1" in text and "груп нових 1" in text and "помилок 1" in text
    assert "ERROR invalid_name [table=0 row=2] bad" in text
