import pytest

from sims.modules.imports.group_code import GroupCodeError, parse_group_code

# raw, default_nqf -> nqf, classifier, specialty, admission_year, entry_course,
#                     program_code, part_time, cohort_tag, code_norm, repairs
CASES = [
    ("6.G3.26", 6, (6, "2024", "G3", 2026, 1, None, False, None, "6.G3.26", [])),
    ("6.G3.26-с2", 6, (6, "2024", "G3", 2026, 2, None, False, None, "6.G3.26-с2", [])),
    ("6.G4.26-т-с2", 6, (6, "2024", "G4", 2026, 2, "т", False, None, "6.G4.26-т-с2", [])),
    ("6.G19.26-з-пцб-с2", 6, (6, "2024", "G19", 2026, 2, "пцб", True, None, "6.G19.26-пцб-з-с2", [])),
    ("6.G19.25-пцб-з-с2", 6, (6, "2024", "G19", 2025, 2, "пцб", True, None, "6.G19.25-пцб-з-с2", [])),
    ("6.G3.26-з-c2", 6, (6, "2024", "G3", 2026, 2, None, True, None, "6.G3.26-з-с2", ["latin_letters"])),
    ("G5.26-с2", 6, (6, "2024", "G5", 2026, 2, None, False, None, "6.G5.26-с2", ["level_prefix_added"])),
    ("6.1364-мчм-з", 6, (6, "2015", "136", 2024, 1, "мчм", True, None, "6.1364-мчм-з", [])),
    ("6.1743-з", 6, (6, "2015", "174", 2023, 1, None, True, None, "6.1743-з", [])),
    ("6.1364-м-з-с2", 6, (6, "2015", "136", 2024, 2, "м", True, None, "6.1364-м-з-с2", [])),
    ("7.G19.25-з-дн-мбг", 7, (7, "2024", "G19", 2025, 1, "мбг", True, "дн", "7.G19.25-мбг-з-дн", [])),
    (" 7.G2.25-з ", 7, (7, "2024", "G2", 2025, 1, None, True, None, "7.G2.25-з", [])),
]


@pytest.mark.parametrize("raw, default_nqf, want", CASES, ids=[c[0].strip() for c in CASES])
def test_parse_group_code(raw, default_nqf, want):
    g = parse_group_code(raw, default_nqf=default_nqf)
    got = (g.nqf_level, g.classifier, g.specialty_code, g.admission_year, g.entry_course,
           g.program_code, g.part_time, g.cohort_tag, g.code_norm, g.repairs)
    assert got == want


@pytest.mark.parametrize("raw", ["", "ГРУПА", "6.XYZ", "5.G3.26"])
def test_unparseable_group_code_raises(raw):
    with pytest.raises(GroupCodeError):
        parse_group_code(raw, default_nqf=6)


def test_missing_level_prefix_without_default_raises():
    with pytest.raises(GroupCodeError):
        parse_group_code("G5.26-с2", default_nqf=None)


def test_two_program_tokens_are_rejected():
    with pytest.raises(GroupCodeError):
        parse_group_code("6.G19.26-пцб-мбг", default_nqf=6)
