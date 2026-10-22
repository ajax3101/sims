"""Group cipher parser: '6.G19.26-з-пцб-с2', '6.1364-мчм-з', 'G5.26-с2' (repaired).

Layout: <nqf>.<specialty>.<yy>[-token...] (2024 classifier) or
<nqf>.<ddd><y>[-token...] (2015 classifier: specialty 136 + last digit of year).
Tokens in any order: 'з' part-time, 'с2' shortened (enters 2nd course),
'дн' cohort tag, anything else Cyrillic is the educational program code.
"""
import re
from dataclasses import dataclass, field


class GroupCodeError(ValueError):
    pass


@dataclass(frozen=True)
class GroupCode:
    nqf_level: int
    classifier: str
    specialty_code: str
    admission_year: int
    entry_course: int
    program_code: str | None
    part_time: bool
    cohort_tag: str | None
    code_norm: str
    repairs: list[str] = field(default_factory=list)


# Latin look-alikes typed into Cyrillic tokens ('c2' -> 'с2').
_LATIN_TO_CYR = str.maketrans("aceiopxyACEIOPXTMHBK", "асеіорхуАСЕІОРХТМНВК")
_PREFIX = re.compile(r"^(\d)\.(.+)$")
_NEW_BODY = re.compile(r"^([A-Z]\d{1,2})\.(\d{2})$")
_OLD_BODY = re.compile(r"^(\d{3})(\d)$")
_PROGRAM = re.compile(r"^[а-яіїєґ’]+$")
_COHORT_TAGS = {"дн"}


def parse_group_code(raw: str, *, default_nqf: int | None) -> GroupCode:
    code = re.sub(r"\s+", "", raw or "")
    repairs: list[str] = []

    if m := _PREFIX.match(code):
        nqf, rest = int(m.group(1)), m.group(2)
    elif default_nqf is not None and code:
        nqf, rest = default_nqf, code
        repairs.append("level_prefix_added")
    else:
        raise GroupCodeError(f"no level prefix in group code {raw!r}")
    if nqf not in (6, 7, 8):
        raise GroupCodeError(f"unknown level {nqf} in group code {raw!r}")

    body, *tokens = rest.split("-")
    if m := _NEW_BODY.match(body):
        classifier, specialty, year = "2024", m.group(1), 2000 + int(m.group(2))
        body_norm = f"{specialty}.{m.group(2)}"
    elif m := _OLD_BODY.match(body):
        classifier, specialty, year = "2015", m.group(1), 2020 + int(m.group(2))
        body_norm = body
    else:
        raise GroupCodeError(f"unrecognised specialty/year part {body!r} in {raw!r}")

    fixed = [t.translate(_LATIN_TO_CYR).lower() for t in tokens if t]
    if fixed != [t.lower() for t in tokens if t]:
        repairs.append("latin_letters")

    part_time, shortened, cohort, program = False, False, None, None
    for t in fixed:
        if t == "з":
            part_time = True
        elif t == "с2":
            shortened = True
        elif t in _COHORT_TAGS:
            cohort = t
        elif _PROGRAM.match(t) and program is None:
            program = t
        else:
            raise GroupCodeError(f"unexpected token {t!r} in group code {raw!r}")

    canonical = [x for x in (program, "з" if part_time else None, cohort, "с2" if shortened else None) if x]
    return GroupCode(
        nqf_level=nqf,
        classifier=classifier,
        specialty_code=specialty,
        admission_year=year,
        entry_course=2 if shortened else 1,
        program_code=program,
        part_time=part_time,
        cohort_tag=cohort,
        code_norm="-".join([f"{nqf}.{body_norm}", *canonical]),
        repairs=repairs,
    )
