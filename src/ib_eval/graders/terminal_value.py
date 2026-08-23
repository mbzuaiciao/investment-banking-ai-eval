"""Grader 6 — Terminal Value.

Validates the terminal value computation.

Hard failure codes:
  TV_NOT_DISCOUNTED        : TV used at face value without discounting
  TV_FORMULA_ERROR         : perpetuity formula incorrect
  TV_GROWTH_GT_WACC        : terminal growth >= WACC (conceptual error)
"""

from __future__ import annotations

import math

from ib_eval.case import GraderConfig
from ib_eval.dcf import (
    compute_pv_terminal_value,
    compute_terminal_fcf,
    compute_terminal_value_at_horizon,
)
from ib_eval.schemas import (
    ErrorType,
    GraderFailure,
    GraderResult,
    Severity,
    Submission,
)

GRADER_NAME = "terminal_value"

_TOL_PCT = 0.005  # 0.5% relative tolerance
_ABS_TOL = 1.0  # $1mm absolute tolerance for large values


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    tol_pct = config.tolerances.get("tv_rel", _TOL_PCT)
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    tvi = submission.terminal_value_inputs
    tvo = submission.terminal_value_outputs
    wo = submission.wacc_outputs
    wacc = wo.wacc
    g = tvi.terminal_growth_rate

    # 1. Growth rate < WACC
    if g >= wacc:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="terminal_growth_rate",
                expected=f"< {wacc:.4%}",
                observed=g,
                message=(
                    f"Terminal growth rate ({g:.4%}) ≥ WACC ({wacc:.4%}). "
                    "The Gordon Growth Model requires g < WACC."
                ),
                diagnostic_code="TV_GROWTH_GT_WACC",
            )
        )
        # Cannot proceed with further checks
        return GraderResult(
            grader=GRADER_NAME,
            score=0.0,
            max_points=max_points,
            points_earned=0.0,
            passed=False,
            failures=failures,
            warnings=warnings,
            info=info,
        )

    # 2. Terminal FCF = final UFCF × (1 + g)
    if not submission.forecast:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="terminal_fcf",
                expected=None,
                observed=None,
                message="No forecast years to derive terminal FCF from.",
                diagnostic_code="TV_NO_FORECAST",
            )
        )
        return GraderResult(
            grader=GRADER_NAME,
            score=0.0,
            max_points=max_points,
            points_earned=0.0,
            passed=False,
            failures=failures,
            warnings=warnings,
            info=info,
        )

    sorted_years = sorted(submission.forecast, key=lambda x: x.year)
    final_ufcf = sorted_years[-1].ufcf
    n = len(sorted_years)

    expected_terminal_fcf = compute_terminal_fcf(final_ufcf, g)
    if abs(tvo.terminal_fcf - expected_terminal_fcf) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="terminal_fcf",
                expected=expected_terminal_fcf,
                observed=tvo.terminal_fcf,
                message=(
                    f"Terminal FCF = final UFCF × (1 + g): "
                    f"{final_ufcf:.4f} × {1 + g} = {expected_terminal_fcf:.4f} "
                    f"≠ {tvo.terminal_fcf}"
                ),
                diagnostic_code="TV_FORMULA_ERROR",
            )
        )

    # 3. TV at horizon = terminal_fcf / (WACC − g)
    expected_tv_horizon = compute_terminal_value_at_horizon(expected_terminal_fcf, wacc, g)
    if abs(tvo.terminal_value_at_horizon - expected_tv_horizon) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="terminal_value_at_horizon",
                expected=expected_tv_horizon,
                observed=tvo.terminal_value_at_horizon,
                message=(
                    f"TV = FCF_T+1 / (WACC − g) = {expected_terminal_fcf:.4f} / "
                    f"({wacc:.6f} − {g}) = {expected_tv_horizon:.4f} "
                    f"≠ {tvo.terminal_value_at_horizon}"
                ),
                diagnostic_code="TV_FORMULA_ERROR",
            )
        )

    # 4. PV(TV) — check that TV was discounted
    term_exp = float(config.params.get("terminal_discount_exponent", n))
    expected_pv_tv = compute_pv_terminal_value(expected_tv_horizon, wacc, term_exp)
    expected_df = 1.0 / ((1.0 + wacc) ** term_exp)

    if abs(tvo.pv_terminal_value - expected_pv_tv) > _ABS_TOL:
        # Check the specific pattern where TV is not discounted at all
        if abs(tvo.pv_terminal_value - expected_tv_horizon) < _ABS_TOL * 5:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.FORMULA,
                    severity=Severity.CRITICAL,
                    metric="pv_terminal_value",
                    expected=expected_pv_tv,
                    observed=tvo.pv_terminal_value,
                    message=(
                        "Terminal value appears NOT discounted to valuation date. "
                        f"PV(TV) = TV / (1 + WACC)^{term_exp:.1f} = "
                        f"{expected_tv_horizon:.4f} × {expected_df:.6f} "
                        f"= {expected_pv_tv:.4f}, not {tvo.pv_terminal_value:.4f}."
                    ),
                    diagnostic_code="TV_NOT_DISCOUNTED",
                )
            )
        # Check if 4.5 was used when 5.0 was specified (or vice-versa)
        elif abs(tvo.pv_terminal_value - expected_tv_horizon / ((1.0 + wacc) ** 4.5)) < _ABS_TOL:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.VALUATION,
                    severity=Severity.CRITICAL,
                    metric="pv_terminal_value",
                    expected=expected_pv_tv,
                    observed=tvo.pv_terminal_value,
                    message=(
                        "Terminal Value discounted using t=4.5 rather than full forecast "
                        f"horizon t=5.0. Expected PV(TV) = {expected_tv_horizon:.4f} / "
                        f"(1+{wacc:.4f})^5.0 = {expected_pv_tv:.4f}, "
                        f"got {tvo.pv_terminal_value:.4f}."
                    ),
                    diagnostic_code="DCF_MIDYEAR_CONVENTION_ERROR",
                )
            )
        else:
            rel_err = abs(tvo.pv_terminal_value - expected_pv_tv) / max(abs(expected_pv_tv), 1.0)
            if rel_err > tol_pct:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.ARITHMETIC,
                        severity=Severity.CRITICAL,
                        metric="pv_terminal_value",
                        expected=expected_pv_tv,
                        observed=tvo.pv_terminal_value,
                        message=(
                            f"PV(TV) discounting error: expected {expected_pv_tv:.4f}, "
                            f"got {tvo.pv_terminal_value:.4f} "
                            f"(rel error {rel_err:.2%})"
                        ),
                        diagnostic_code="TV_PV_ERROR",
                    )
                )
            else:
                info.append(
                    f"PV(TV) within {rel_err:.2%} of expected — acceptable numerical precision."
                )

    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    deduction = n_critical * (max_points / 4)
    points = max(0.0, max_points - deduction)
    score = points / max_points if max_points > 0 else 0.0

    _ = math.inf  # suppress unused import warning

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
