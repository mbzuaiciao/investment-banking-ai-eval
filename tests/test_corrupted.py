"""Tests for corrupted submission fixtures.

Each test verifies that:
1. The submission scores below 100
2. The expected diagnostic code is emitted
3. The expected grader catches the error
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ib_eval.case import NorthstarCase, load_case
from ib_eval.schemas import GraderResult, ScoringReport, Submission
from ib_eval.scoring import grade_submission

_CORRUPTED_DIR = Path(__file__).parent.parent / "examples" / "corrupted"
_CASES_DIR = Path(__file__).parent.parent / "cases"


def load_corrupted(name: str) -> Submission:
    path = _CORRUPTED_DIR / name / "submission.json"
    raw = json.loads(path.read_text())
    return Submission.model_validate(raw)


def _has_code(report: ScoringReport, code: str) -> bool:
    return any(
        f.diagnostic_code == code
        for r in report.grader_results
        for f in r.failures
    )


def _grader_result(report: ScoringReport, grader: str) -> GraderResult | None:
    for r in report.grader_results:
        if r.grader == grader:
            return r
    return None


@pytest.fixture(scope="module")
def case() -> NorthstarCase:
    return load_case(_CASES_DIR / "northstar-v1")


# ---------------------------------------------------------------------------
# C01: Quarterly revenue confused with annual
# ---------------------------------------------------------------------------


def test_c01_quarterly_revenue_score(case: NorthstarCase) -> None:
    """C01 submission should score below 100."""
    sub = load_corrupted("c01_quarterly_revenue")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c01_quarterly_revenue_diagnostic(case: NorthstarCase) -> None:
    """C01 must emit REV_QUARTERLY_CONFUSION."""
    sub = load_corrupted("c01_quarterly_revenue")
    report = grade_submission(sub, case)
    assert _has_code(report, "REV_QUARTERLY_CONFUSION"), (
        f"Expected REV_QUARTERLY_CONFUSION. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c01_caught_by_revenue_grader(case: NorthstarCase) -> None:
    """C01 must fail the revenue_forecast grader."""
    sub = load_corrupted("c01_quarterly_revenue")
    report = grade_submission(sub, case)
    rev_result = _grader_result(report, "revenue_forecast")
    assert rev_result is not None
    assert not rev_result.passed


# ---------------------------------------------------------------------------
# C02: Terminal value not discounted
# ---------------------------------------------------------------------------


def test_c02_tv_not_discounted_score(case: NorthstarCase) -> None:
    """C02 submission should score below 100."""
    sub = load_corrupted("c02_tv_not_discounted")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c02_tv_not_discounted_diagnostic(case: NorthstarCase) -> None:
    """C02 must emit TV_NOT_DISCOUNTED."""
    sub = load_corrupted("c02_tv_not_discounted")
    report = grade_submission(sub, case)
    assert _has_code(report, "TV_NOT_DISCOUNTED"), (
        f"Expected TV_NOT_DISCOUNTED. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c02_caught_by_tv_grader(case: NorthstarCase) -> None:
    """C02 must fail the terminal_value grader."""
    sub = load_corrupted("c02_tv_not_discounted")
    report = grade_submission(sub, case)
    tv_result = _grader_result(report, "terminal_value")
    assert tv_result is not None
    assert not tv_result.passed


# ---------------------------------------------------------------------------
# C03: Cash subtracted instead of added in equity bridge
# ---------------------------------------------------------------------------


def test_c03_cash_subtracted_score(case: NorthstarCase) -> None:
    """C03 submission should score below 100."""
    sub = load_corrupted("c03_cash_subtracted")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c03_cash_subtracted_diagnostic(case: NorthstarCase) -> None:
    """C03 must emit EQ_BRIDGE_CASH_REVERSED."""
    sub = load_corrupted("c03_cash_subtracted")
    report = grade_submission(sub, case)
    assert _has_code(report, "EQ_BRIDGE_CASH_REVERSED"), (
        f"Expected EQ_BRIDGE_CASH_REVERSED. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c03_caught_by_equity_bridge_grader(case: NorthstarCase) -> None:
    """C03 must fail the equity_bridge grader."""
    sub = load_corrupted("c03_cash_subtracted")
    report = grade_submission(sub, case)
    eb_result = _grader_result(report, "equity_bridge")
    assert eb_result is not None
    assert not eb_result.passed


# ---------------------------------------------------------------------------
# C04: Debt omitted from equity bridge
# ---------------------------------------------------------------------------


def test_c04_debt_omitted_score(case: NorthstarCase) -> None:
    """C04 submission should score below 100."""
    sub = load_corrupted("c04_debt_omitted")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c04_debt_omitted_diagnostic(case: NorthstarCase) -> None:
    """C04 must emit EQ_BRIDGE_DEBT_OMITTED."""
    sub = load_corrupted("c04_debt_omitted")
    report = grade_submission(sub, case)
    assert _has_code(report, "EQ_BRIDGE_DEBT_OMITTED"), (
        f"Expected EQ_BRIDGE_DEBT_OMITTED. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


# ---------------------------------------------------------------------------
# C05: N/M peer treated as zero
# ---------------------------------------------------------------------------


def test_c05_nm_peer_zero_score(case: NorthstarCase) -> None:
    """C05 submission should score below 100."""
    sub = load_corrupted("c05_nm_peer_zero")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c05_nm_peer_zero_diagnostic(case: NorthstarCase) -> None:
    """C05 must emit COMPS_NM_COERCED_ZERO."""
    sub = load_corrupted("c05_nm_peer_zero")
    report = grade_submission(sub, case)
    assert _has_code(report, "COMPS_NM_COERCED_ZERO"), (
        f"Expected COMPS_NM_COERCED_ZERO. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c05_caught_by_comps_grader(case: NorthstarCase) -> None:
    """C05 must fail the comps grader."""
    sub = load_corrupted("c05_nm_peer_zero")
    report = grade_submission(sub, case)
    comps_result = _grader_result(report, "comps")
    assert comps_result is not None
    assert not comps_result.passed


# ---------------------------------------------------------------------------
# C06: Fabricated guidance
# ---------------------------------------------------------------------------


def test_c06_fabricated_guidance_score(case: NorthstarCase) -> None:
    """C06 submission should score below 100."""
    sub = load_corrupted("c06_fabricated_guidance")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c06_fabricated_guidance_diagnostic(case: NorthstarCase) -> None:
    """C06 must emit SF_GUIDANCE_FABRICATED."""
    sub = load_corrupted("c06_fabricated_guidance")
    report = grade_submission(sub, case)
    assert _has_code(report, "SF_GUIDANCE_FABRICATED"), (
        f"Expected SF_GUIDANCE_FABRICATED. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c06_caught_by_source_fidelity_grader(case: NorthstarCase) -> None:
    """C06 must fail the source_fidelity grader."""
    sub = load_corrupted("c06_fabricated_guidance")
    report = grade_submission(sub, case)
    sf_result = _grader_result(report, "source_fidelity")
    assert sf_result is not None
    assert not sf_result.passed


# ---------------------------------------------------------------------------
# C07: EBITDA/D&A/EBIT inconsistency
# ---------------------------------------------------------------------------


def test_c07_ebitda_inconsistency_score(case: NorthstarCase) -> None:
    """C07 submission should score below 100."""
    sub = load_corrupted("c07_ebitda_inconsistency")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c07_ebitda_inconsistency_diagnostic(case: NorthstarCase) -> None:
    """C07 must emit MARGIN_EBIT_INCONSISTENCY."""
    sub = load_corrupted("c07_ebitda_inconsistency")
    report = grade_submission(sub, case)
    assert _has_code(report, "MARGIN_EBIT_INCONSISTENCY"), (
        f"Expected MARGIN_EBIT_INCONSISTENCY. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c07_caught_by_margin_grader(case: NorthstarCase) -> None:
    """C07 must fail the margin_forecast grader."""
    sub = load_corrupted("c07_ebitda_inconsistency")
    report = grade_submission(sub, case)
    margin_result = _grader_result(report, "margin_forecast")
    assert margin_result is not None
    assert not margin_result.passed


# ---------------------------------------------------------------------------
# C08: Capex double counted
# ---------------------------------------------------------------------------


def test_c08_capex_double_counted_score(case: NorthstarCase) -> None:
    """C08 submission should score below 100."""
    sub = load_corrupted("c08_capex_double_counted")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c08_capex_double_counted_diagnostic(case: NorthstarCase) -> None:
    """C08 must emit FCF_CAPEX_DOUBLE_COUNTED."""
    sub = load_corrupted("c08_capex_double_counted")
    report = grade_submission(sub, case)
    assert _has_code(report, "FCF_CAPEX_DOUBLE_COUNTED"), (
        f"Expected FCF_CAPEX_DOUBLE_COUNTED. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c08_caught_by_fcf_grader(case: NorthstarCase) -> None:
    """C08 must fail the free_cash_flow grader."""
    sub = load_corrupted("c08_capex_double_counted")
    report = grade_submission(sub, case)
    fcf_result = _grader_result(report, "free_cash_flow")
    assert fcf_result is not None
    assert not fcf_result.passed


# ---------------------------------------------------------------------------
# C09: Headline/model mismatch
# ---------------------------------------------------------------------------


def test_c09_headline_mismatch_score(case: NorthstarCase) -> None:
    """C09 submission should score below 100."""
    sub = load_corrupted("c09_headline_mismatch")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c09_headline_mismatch_diagnostic(case: NorthstarCase) -> None:
    """C09 must emit CONSISTENCY_HEADLINE_DCF."""
    sub = load_corrupted("c09_headline_mismatch")
    report = grade_submission(sub, case)
    assert _has_code(report, "CONSISTENCY_HEADLINE_DCF"), (
        f"Expected CONSISTENCY_HEADLINE_DCF. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c09_caught_by_consistency_grader(case: NorthstarCase) -> None:
    """C09 must fail the consistency grader."""
    sub = load_corrupted("c09_headline_mismatch")
    report = grade_submission(sub, case)
    cons_result = _grader_result(report, "consistency")
    assert cons_result is not None
    assert not cons_result.passed


# ---------------------------------------------------------------------------
# C10: WACC without tax shield
# ---------------------------------------------------------------------------


def test_c10_pretax_wacc_score(case: NorthstarCase) -> None:
    """C10 submission should score below 100."""
    sub = load_corrupted("c10_pretax_wacc")
    report = grade_submission(sub, case)
    assert report.total_score < 100.0


def test_c10_pretax_wacc_diagnostic(case: NorthstarCase) -> None:
    """C10 must emit WACC_PRETAX_DEBT."""
    sub = load_corrupted("c10_pretax_wacc")
    report = grade_submission(sub, case)
    assert _has_code(report, "WACC_PRETAX_DEBT"), (
        f"Expected WACC_PRETAX_DEBT. Got: "
        f"{[f.diagnostic_code for r in report.grader_results for f in r.failures]}"
    )


def test_c10_caught_by_wacc_grader(case: NorthstarCase) -> None:
    """C10 must fail the wacc grader."""
    sub = load_corrupted("c10_pretax_wacc")
    report = grade_submission(sub, case)
    wacc_result = _grader_result(report, "wacc")
    assert wacc_result is not None
    assert not wacc_result.passed
