from datetime import date

import pytest

from sims.modules.imports.normalize import (
    NameError_, fuzzy_equal, normalize_full_name, parse_funding, sentence_case,
)


@pytest.mark.parametrize("raw, want", [
    ("Булигін Давід Олексійович", ("Булигін", "Давід", "Олексійович", None)),
    ("Дригваль Іван Іванович           (з 25.09.2026)", ("Дригваль", "Іван", "Іванович", date(2026, 9, 25))),
    ("Зінов`єв Роман Олександрович", ("Зінов’єв", "Роман", "Олександрович", None)),
    ("Лисенко Дар'я Властимирівна", ("Лисенко", "Дар’я", "Властимирівна", None)),
    ("Твердохліб  Кирило Артемович", ("Твердохліб", "Кирило", "Артемович", None)),
    ("Волохіна-Черняк Анна Миколаївна", ("Волохіна-Черняк", "Анна", "Миколаївна", None)),
    ("Іванов Іван", ("Іванов", "Іван", None, None)),
])
def test_normalize_full_name_parts(raw, want):
    n = normalize_full_name(raw)
    assert (n.last_name, n.first_name, n.patronymic, n.enrolled_on) == want


def test_full_name_norm_is_casefolded_with_unified_apostrophe():
    assert normalize_full_name("Зінов`єв  Роман Олександрович").norm == "зінов’єв роман олександрович"


def test_four_part_name_keeps_tail_in_patronymic_and_flags_it():
    n = normalize_full_name("Алієв Артур Тимур огли")
    assert (n.patronymic, n.warnings) == ("Тимур огли", ["name_extra_parts"])


@pytest.mark.parametrize("raw", ["", "   ", "Іванов", "123 Іван Петрович", "(з 25.09.2026)"])
def test_invalid_names_raise(raw):
    with pytest.raises(NameError_):
        normalize_full_name(raw)


@pytest.mark.parametrize("raw, want", [
    ("Б", ("budget", None)), ("К", ("contract", None)), (" к ", ("contract", None)),
    ("В", ("other", "funding_unknown_code")), ("", (None, "funding_missing")),
])
def test_parse_funding(raw, want):
    assert parse_funding(raw) == want


@pytest.mark.parametrize("raw, want", [
    ("ЕЛЕКТРИЧНА ІНЖЕНЕРІЯ", "Електрична інженерія"),
    ("  МЕТАЛУРГІЯ  ЧОРНИХ МЕТАЛІВ", "Металургія чорних металів"),
    ("АВТОМАТИЗАЦІЯ ТА КОМП'ЮТЕРНО-ІНТЕГРОВАНІ ТЕХНОЛОГІЇ", "Автоматизація та комп’ютерно-інтегровані технології"),
    ("Міське будівництво та господарство", "Міське будівництво та господарство"),
])
def test_sentence_case(raw, want):
    assert sentence_case(raw) == want


@pytest.mark.parametrize("a, b, want", [
    ("МЕТАЛУРГВЯ ЧОРНИХ МЕТАЛІВ", "Металургія чорних металів", True),
    ("НЖЕНЕРНОГО НАВЧАЛЬНО-НАУКОВОГО ІНСТИТУТУ ім. Ю.М.Потебні",
     "ІНЖЕНЕРНОГО НАВЧАЛЬНО-НАУКОВОГО ІНСТИТУТУ ім. Ю.М. Потебні", True),
    ("Металургія чорних металів", "Металургія кольорових металів", False),
    ("Теплоенергетика", "Гідроенергетика", False),
])
def test_fuzzy_equal(a, b, want):
    assert fuzzy_equal(a, b) is want
