"""100-point institutional scale → ECTS letter and national grade."""
from sims.modules.performance.models import ControlForm, EctsGrade, NationalGrade

# (lowest score, ECTS, national grade for graded control forms)
_SCALE = [
    (90, EctsGrade.A, NationalGrade.EXCELLENT),
    (82, EctsGrade.B, NationalGrade.GOOD),
    (74, EctsGrade.C, NationalGrade.GOOD),
    (64, EctsGrade.D, NationalGrade.SATISFACTORY),
    (60, EctsGrade.E, NationalGrade.SATISFACTORY),
    (35, EctsGrade.FX, NationalGrade.UNSATISFACTORY),
    (0, EctsGrade.F, NationalGrade.UNSATISFACTORY),
]
PASS_SCORE = 60
FAILING = (NationalGrade.UNSATISFACTORY, NationalGrade.FAILED)


def grade_scale(score: int, control_form: str) -> tuple[str, str]:
    ects, national = next((e, n) for low, e, n in _SCALE if score >= low)
    if control_form == ControlForm.CREDIT:  # pass/fail credit: ECTS letter kept, national is passed/failed
        national = NationalGrade.PASSED if score >= PASS_SCORE else NationalGrade.FAILED
    return ects.value, national.value
