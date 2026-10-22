import pytest

from sims.modules.performance.grading import grade_scale

# Ukrainian 100-point scale -> ECTS / national (exam-type vs pass/fail credit).
@pytest.mark.parametrize("score, form, want", [
    (100, "exam", ("A", "excellent")), (90, "exam", ("A", "excellent")),
    (89, "exam", ("B", "good")), (82, "exam", ("B", "good")),
    (81, "exam", ("C", "good")), (74, "exam", ("C", "good")),
    (73, "exam", ("D", "satisfactory")), (64, "exam", ("D", "satisfactory")),
    (63, "exam", ("E", "satisfactory")), (60, "exam", ("E", "satisfactory")),
    (59, "exam", ("FX", "unsatisfactory")), (35, "exam", ("FX", "unsatisfactory")),
    (34, "exam", ("F", "unsatisfactory")), (0, "exam", ("F", "unsatisfactory")),
    (60, "credit", ("E", "passed")), (59, "credit", ("FX", "failed")),
    (95, "diff_credit", ("A", "excellent")), (75, "coursework", ("C", "good")),
])
def test_grade_scale(score, form, want):
    assert grade_scale(score, form) == want
