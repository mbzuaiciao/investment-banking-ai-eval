"""Tests for scoring and graders using the gold submission."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission

_GOLD_PATH = Path(__file__).parent.parent / "examples" / "gold_submission" / "submission.json"
_CASES_DIR = Path(__file__).parent.parent / "cases"


def load_submission(path: Path) -> Submission:
    raw = json.loads(path.read_text())
    return Submission.model_validate(raw)


@pytest.fixture(scope="module")
def gold_submission() -> Submission:
    return load_submission(_GOLD_PATH)


# ---------------------------------------------------------------------------
# Gold submission
# ---------------------------------------------------------------------------


def test_gold_submission_total_score(gold_submission: Submission) -> None:
    """Gold submission must score 100/100."""
    from ib_eval.case import load_case

    case = load_case(_CASES_DIR / "northstar-v1")
    report = grade_submission(gold_submission, case)
    assert report.total_score == pytest.approx(100.0, abs=0.01)
    assert report.max_score == 100.0


def test_gold_submission_no_hard_failures(gold_submission: Submission) -> None:
    """Gold submission must have zero hard failures."""
    from ib_eval.case import load_case

    case = load_case(_CASES_DIR / "northstar-v1")
    report = grade_submission(gold_submission, case)
    assert report.hard_failures == []


def test_gold_submission_all_graders_pass(gold_submission: Submission) -> None:
    """All 10 graders must pass for the gold submission."""
    from ib_eval.case import load_case

    case = load_case(_CASES_DIR / "northstar-v1")
    report = grade_submission(gold_submission, case)
    failed = [r for r in report.grader_results if not r.passed]
    assert failed == [], f"Graders failed: {[r.grader for r in failed]}"


def test_gold_submission_wacc() -> None:
    """Verify gold WACC is 9.2832%."""
    sub = load_submission(_GOLD_PATH)
    assert abs(sub.wacc_outputs.wacc - 0.092832) < 1e-5


def test_gold_submission_ev() -> None:
    """Verify gold DCF EV is approximately $1,713mm."""
    sub = load_submission(_GOLD_PATH)
    assert abs(sub.dcf_outputs.enterprise_value - 1712.97) < 1.0


def test_gold_submission_equity() -> None:
    """Verify gold DCF equity value is approximately $1,388mm."""
    sub = load_submission(_GOLD_PATH)
    assert abs(sub.equity_bridge.equity_value - 1387.97) < 1.0


def test_gold_submission_share_price() -> None:
    """Verify gold DCF share price is approximately $23.13."""
    sub = load_submission(_GOLD_PATH)
    assert abs(sub.equity_bridge.implied_share_price - 23.13) < 0.01


def test_gold_submission_comps_median() -> None:
    """Verify gold comps NTM median is 8.20x."""
    sub = load_submission(_GOLD_PATH)
    assert sub.comps_outputs.ntm_median is not None
    assert abs(sub.comps_outputs.ntm_median - 8.2) < 0.01


def test_gold_submission_comps_share_price() -> None:
    """Verify gold comps share price is approximately $19.68."""
    sub = load_submission(_GOLD_PATH)
    assert abs(sub.comps_outputs.implied_share_price - 19.68) < 0.01


# ---------------------------------------------------------------------------
# Scoring report structure
# ---------------------------------------------------------------------------


def test_scoring_report_grade_letter(gold_submission: Submission) -> None:
    """Gold should earn A+ grade."""
    from ib_eval.case import load_case

    case = load_case(_CASES_DIR / "northstar-v1")
    report = grade_submission(gold_submission, case)
    assert report.grade == "A+"


def test_scoring_report_has_all_graders(gold_submission: Submission) -> None:
    """Report should include results from all 10 graders."""
    from ib_eval.case import load_case

    case = load_case(_CASES_DIR / "northstar-v1")
    report = grade_submission(gold_submission, case)
    grader_names = {r.grader for r in report.grader_results}
    expected = {
        "source_fidelity",
        "revenue_forecast",
        "margin_forecast",
        "free_cash_flow",
        "wacc",
        "terminal_value",
        "enterprise_value",
        "equity_bridge",
        "comps",
        "consistency",
    }
    assert grader_names == expected
