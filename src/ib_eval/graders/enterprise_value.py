"""Grader 7 — Enterprise Value.

Validates that DCF enterprise value = Σ PV(UFCF) + PV(TV).

Hard failure codes:
  EV_SUM_ERROR             : EV ≠ Σ PV(UFCF) + PV(TV)
  EV_MATERIALLY_WRONG      : EV is materially different from expected
"""

from __future__ import annotations

from ib_eval.case import GraderConfig
from ib_eval.schemas import (
    ErrorType,
    GraderFailure,
    GraderResult,
    Severity,
    Submission,
)

GRADER_NAME = "enterprise_value"

_ABS_TOL = 1.0  # $1mm — tight for an EV check
_REL_TOL = 0.02  # 2% for "materially wrong" threshold
_GOLD_EV_APPROX = 1713.0


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    tol = config.tolerances.get("ev_abs", _ABS_TOL)
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    do = submission.dcf_outputs
    tvo = submission.terminal_value_outputs

    # 1. Σ PV(UFCF) from forecast
    computed_sum_pv_ufcf = sum(fy.pv_ufcf for fy in submission.forecast)
    if abs(computed_sum_pv_ufcf - do.sum_pv_ufcf) > tol:
        failures.append(
            GraderFailure(
                error_type=ErrorType.ARITHMETIC,
                severity=Severity.CRITICAL,
                metric="sum_pv_ufcf",
                expected=computed_sum_pv_ufcf,
                observed=do.sum_pv_ufcf,
                message=(
                    f"Σ PV(UFCF) from forecast years = {computed_sum_pv_ufcf:.4f}, "
                    f"but dcf_outputs.sum_pv_ufcf = {do.sum_pv_ufcf:.4f}"
                ),
                diagnostic_code="EV_SUM_PVUFCF_MISMATCH",
            )
        )

    # 2. EV = Σ PV(UFCF) + PV(TV)
    expected_ev = computed_sum_pv_ufcf + tvo.pv_terminal_value
    if abs(expected_ev - do.enterprise_value) > tol:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="enterprise_value",
                expected=expected_ev,
                observed=do.enterprise_value,
                message=(
                    f"EV = Σ PV(UFCF) + PV(TV): {computed_sum_pv_ufcf:.4f} + "
                    f"{tvo.pv_terminal_value:.4f} = {expected_ev:.4f} "
                    f"≠ {do.enterprise_value:.4f}"
                ),
                diagnostic_code="EV_SUM_ERROR",
            )
        )

    # 3. Relative sanity vs. approximate gold if configured
    gold_ev_approx = config.params.get(
        "gold_ev_approx", _GOLD_EV_APPROX if submission.case_id == "northstar-v1" else None
    )
    if gold_ev_approx is not None:
        gold_ev_val = float(gold_ev_approx)
        rel_diff = abs(do.enterprise_value - gold_ev_val) / gold_ev_val
        if rel_diff > _REL_TOL:
            warnings.append(
                f"DCF EV = {do.enterprise_value:.1f} differs from approximate gold "
                f"({gold_ev_val:.1f}) by {rel_diff:.1%}. "
                "Verify WACC, TV, and forecast assumptions are consistent."
            )
            info.append(
                f"Note: gold EV ({gold_ev_val:.1f}) is approximate; "
                "use internally consistent precise values as canonical."
            )

    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    deduction = n_critical * (max_points / 3)
    points = max(0.0, max_points - deduction)
    score = points / max_points if max_points > 0 else 0.0

    return GraderResult(
        grader=GRADER_NAME,
        score=score,
        max_points=max_points,
        points_earned=points,
        passed=not any(f.severity == Severity.CRITICAL for f in failures),
        failures=failures,
        warnings=warnings,
        info=info,
    )
