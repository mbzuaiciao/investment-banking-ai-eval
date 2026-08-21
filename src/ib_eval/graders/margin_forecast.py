"""Grader 3 — Margin Forecast.

Validates EBITDA margin, EBITDA, D&A, and EBIT for each forecast year.

Hard failure codes:
  MARGIN_EBITDA_INCONSISTENCY   : EBITDA ≠ revenue × margin
  MARGIN_DA_INCONSISTENCY       : D&A ≠ 4% of revenue
  MARGIN_EBIT_INCONSISTENCY     : EBIT ≠ EBITDA − D&A
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

GRADER_NAME = "margin_forecast"

_GOLD_MARGINS = {
    2026: 0.170,
    2027: 0.175,
    2028: 0.180,
    2029: 0.1825,
    2030: 0.185,
}
_DA_PCT = 0.040
_ABS_TOL = 0.01


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    tol = config.tolerances.get("margin_abs", _ABS_TOL)
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    forecast_by_year = {fy.year: fy for fy in submission.forecast}

    for year, gold_margin in _GOLD_MARGINS.items():
        fy = forecast_by_year.get(year)
        if fy is None:
            continue  # revenue grader already flagged missing year

        # 1. EBITDA = revenue × margin
        expected_ebitda = fy.revenue * fy.ebitda_margin
        if abs(expected_ebitda - fy.ebitda) > tol:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ARITHMETIC,
                    severity=Severity.CRITICAL,
                    metric=f"ebitda/{year}E",
                    expected=expected_ebitda,
                    observed=fy.ebitda,
                    message=(
                        f"EBITDA arithmetic: {fy.revenue} × {fy.ebitda_margin} "
                        f"= {expected_ebitda:.4f} ≠ {fy.ebitda}"
                    ),
                    diagnostic_code="MARGIN_EBITDA_INCONSISTENCY",
                )
            )

        # 2. D&A = 4.0% of revenue
        expected_da = fy.revenue * _DA_PCT
        if abs(expected_da - fy.da) > tol:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.FORMULA,
                    severity=Severity.CRITICAL,
                    metric=f"da/{year}E",
                    expected=expected_da,
                    observed=fy.da,
                    message=(
                        f"D&A should be {_DA_PCT:.1%} of revenue: "
                        f"{fy.revenue} × {_DA_PCT} = {expected_da:.4f} ≠ {fy.da}"
                    ),
                    diagnostic_code="MARGIN_DA_INCONSISTENCY",
                )
            )

        # 3. EBIT = EBITDA − D&A
        expected_ebit = fy.ebitda - fy.da
        if abs(expected_ebit - fy.ebit) > tol:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ACCOUNTING,
                    severity=Severity.CRITICAL,
                    metric=f"ebit/{year}E",
                    expected=expected_ebit,
                    observed=fy.ebit,
                    message=(
                        f"EBIT = EBITDA − D&A: {fy.ebitda} − {fy.da} = {expected_ebit:.4f} "
                        f"≠ {fy.ebit}"
                    ),
                    diagnostic_code="MARGIN_EBIT_INCONSISTENCY",
                )
            )

        # 4. Check gold margin (info only — candidate may choose different margin)
        if abs(fy.ebitda_margin - gold_margin) > 0.005:
            info.append(
                f"margin/{year}E: submitted {fy.ebitda_margin:.4%}, gold={gold_margin:.4%}. "
                "Within ±0.5pp is acceptable."
            )

    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    deduction = n_critical * (max_points / (len(_GOLD_MARGINS) * 3))
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
