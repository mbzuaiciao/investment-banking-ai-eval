"""Scoring aggregator — runs all graders and produces a final ScoringReport."""

from __future__ import annotations

from pathlib import Path

from ib_eval import graders as _graders_pkg
from ib_eval.case import NorthstarCase, load_case
from ib_eval.graders import (
    comps as comps_grader,
)
from ib_eval.graders import (
    consistency as consistency_grader,
)
from ib_eval.graders import (
    enterprise_value as ev_grader,
)
from ib_eval.graders import (
    equity_bridge as eb_grader,
)
from ib_eval.graders import (
    free_cash_flow as fcf_grader,
)
from ib_eval.graders import (
    margin_forecast as margin_grader,
)
from ib_eval.graders import (
    revenue_forecast as rev_grader,
)
from ib_eval.graders import (
    source_fidelity as sf_grader,
)
from ib_eval.graders import (
    terminal_value as tv_grader,
)
from ib_eval.graders import (
    wacc as wacc_grader,
)
from ib_eval.schemas import GraderFailure, GraderResult, ScoringReport, Severity, Submission

_ = _graders_pkg  # suppress unused import

_GRADER_REGISTRY = {
    "source_fidelity": sf_grader.grade,
    "revenue_forecast": rev_grader.grade,
    "margin_forecast": margin_grader.grade,
    "free_cash_flow": fcf_grader.grade,
    "wacc": wacc_grader.grade,
    "terminal_value": tv_grader.grade,
    "enterprise_value": ev_grader.grade,
    "equity_bridge": eb_grader.grade,
    "comps": comps_grader.grade,
    "consistency": consistency_grader.grade,
}

_CASES_DIR = Path(__file__).parent.parent.parent / "cases"


def grade_letter(pct: float) -> str:
    if pct >= 0.95:
        return "A+"
    if pct >= 0.90:
        return "A"
    if pct >= 0.85:
        return "B+"
    if pct >= 0.80:
        return "B"
    if pct >= 0.70:
        return "C"
    if pct >= 0.60:
        return "D"
    return "F"


def grade_submission(
    submission: Submission,
    case: NorthstarCase | None = None,
) -> ScoringReport:
    """Run all graders and return a ScoringReport."""
    if case is None:
        case_dir = _CASES_DIR / submission.case_id
        case = load_case(case_dir)

    rubric = case.rubric
    results: list[GraderResult] = []

    for grader_cfg in rubric.graders:
        grade_fn = _GRADER_REGISTRY.get(grader_cfg.name)
        if grade_fn is None:
            continue
        result = grade_fn(submission, grader_cfg)
        results.append(result)

    total_points = sum(r.points_earned for r in results)
    max_points = rubric.max_score

    # Collect hard failures
    hard_failures: list[GraderFailure] = []
    for result in results:
        for failure in result.failures:
            if (
                failure.diagnostic_code in rubric.hard_failure_codes
                or failure.severity == Severity.CRITICAL
            ):
                hard_failures.append(failure)

    pct = total_points / max_points if max_points > 0 else 0.0

    n_hard = len(hard_failures)
    if n_hard == 0:
        summary = f"Score: {total_points:.1f}/{max_points:.0f}. No hard failures."
    else:
        codes = ", ".join(f.diagnostic_code for f in hard_failures[:5])
        summary = f"Score: {total_points:.1f}/{max_points:.0f}. {n_hard} hard failure(s): {codes}"

    return ScoringReport(
        case_id=submission.case_id,
        analyst=submission.analyst,
        total_score=round(total_points, 2),
        max_score=max_points,
        pct_score=round(pct, 4),
        grade=grade_letter(pct),
        hard_failures=hard_failures,
        grader_results=results,
        summary=summary,
    )
