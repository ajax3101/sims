import re
from dataclasses import dataclass, field
from datetime import date, datetime
from difflib import SequenceMatcher


class NameError_(ValueError):
    pass


@dataclass(frozen=True)
class FullName:
    last_name: str
    first_name: str
    patronymic: str | None
    norm: str
    enrolled_on: date | None
    warnings: list[str] = field(default_factory=list)


APOSTROPHE = "’"  # U+2019, the Ukrainian orthographic apostrophe
_APOSTROPHES = re.compile(r"[`'ʼ‘´]")
_ENROLLED = re.compile(r"\(\s*з\s+(\d{2}\.\d{2}\.\d{4})\s*\)")
_NAME_PART = re.compile(r"^[^\W\d_](?:[^\W\d_]|[’-])*$")
_FUZZY_RATIO = 0.92

FUNDING_CODES = {"Б": "budget", "К": "contract"}


def clean_text(raw: str) -> str:
    return re.sub(r"\s+", " ", _APOSTROPHES.sub(APOSTROPHE, raw or "")).strip()


def name_norm(*parts: str | None) -> str:
    """Search/dedup key: cleaned, casefolded 'last first patronymic'."""
    return clean_text(" ".join(p for p in parts if p)).casefold()


def normalize_full_name(raw: str) -> FullName:
    text = clean_text(raw)
    enrolled_on = None
    if m := _ENROLLED.search(text):
        enrolled_on = datetime.strptime(m.group(1), "%d.%m.%Y").date()
        text = clean_text(_ENROLLED.sub("", text))

    parts = text.split(" ") if text else []
    if len(parts) < 2:
        raise NameError_(f"expected at least last and first name: {raw!r}")
    if bad := [p for p in parts if not _NAME_PART.match(p)]:
        raise NameError_(f"invalid characters in name part(s) {bad}: {raw!r}")

    warnings = ["name_extra_parts"] if len(parts) > 3 else []
    patronymic = " ".join(parts[2:]) or None
    return FullName(
        last_name=parts[0],
        first_name=parts[1],
        patronymic=patronymic,
        norm=name_norm(*parts),
        enrolled_on=enrolled_on,
        warnings=warnings,
    )


def parse_funding(raw: str) -> tuple[str | None, str | None]:
    """Roster code -> (Funding value, warning code)."""
    code = (raw or "").strip().upper()
    if not code:
        return None, "funding_missing"
    if code in FUNDING_CODES:
        return FUNDING_CODES[code], None
    return "other", "funding_unknown_code"


def sentence_case(raw: str) -> str:
    text = clean_text(raw)
    if text != text.upper():
        return text  # already deliberately cased
    return text[:1].upper() + text[1:].lower()


def _fuzzy_key(text: str) -> str:
    return re.sub(r"[\W_]", "", clean_text(text).casefold())


def fuzzy_equal(a: str, b: str) -> bool:
    """Same name modulo case, spacing, punctuation and a typo or two."""
    ka, kb = _fuzzy_key(a), _fuzzy_key(b)
    return ka == kb or SequenceMatcher(None, ka, kb).ratio() >= _FUZZY_RATIO
