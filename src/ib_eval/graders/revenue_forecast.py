"""Grader 2 — Revenue Forecast.

Validates the revenue forecast for each projection year.

Hard failure codes:
  REV_QUARTERLY_CONFUSION  : 2026E revenue looks like it was taken from Q2 revenue
  REV_GROWTH_OUT_OF_RANGE  : growth rate is implausible
  REV_ARITHMETIC           : revenue arithmetic is inconsistent
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

GRADER_NAME = "revenue_forecast"

# Gold values from the Northstar v1 case
_GOLD_REVENUES = {
    2026: 1080.0,
    2027: 1155.6,
    2028: 1224.936,
    2029: 1286.1828,
    2030: 1337.630112,
}
_GOLD_GROWTH_RATES = {
    2026: 0.08,
    2027: 0.07,
    2028: 0.06,
    2029: 0.05,
    2030: 0.04,
}

# Q2 standalone revenue — a candidate using this as annual 2026E commits a source error
_Q2_REVENUE = 281.0
_H1_REVENUE = 535.0
_BASE_REVENUE_2025 = 1000.0

# Tolerance: defensible range for 2026E revenue given "high single digits" guidance
_REVENUE_2026_LOW = _BASE_REVENUE_2025 * 1.07  # 7%
_REVENUE_2026_HIGH = _BASE_REVENUE_2025 * 1.09  # 9%

# Absolute tolerance for numerical precision
_ABS_TOL = 0.01  # $0.01mm


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    tol = config.tolerances.get("revenue_abs", _ABS_TOL)
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    forecast_by_year = {fy.year: fy for fy in submission.forecast}

    for year, gold_rev in _GOLD_REVENUES.items():
        fy = forecast_by_year.get(year)
        if fy is None:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.FORMULA,
                    severity=Severity.CRITICAL,
                    metric=f"revenue/{year}E",
                    expected=gold_rev,
                    observed=None,
                    message=f"Forecast year {year} is missing from submission.",
                    diagnostic_code=f"REV_MISSING_{year}",
                )
            )
            continue

        # 1. Check for Q2 confusion only on 2026E
        if year == 2026:
            if abs(fy.revenue - _Q2_REVENUE) < 5.0:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.PROVENANCE,
                        severity=Severity.CRITICAL,
                        metric="revenue/2026E",
                        expected=f"~{gold_rev}",
                        observed=fy.revenue,
                        message=(
                            f"2026E revenue ({fy.revenue}) is close to Q2 standalone "
                            f"revenue ({_Q2_REVENUE}). Possible quarterly/annual confusion."
                        ),
                        diagnostic_code="REV_QUARTERLY_CONFUSION",
                    )
                )
            elif abs(fy.revenue - _H1_REVENUE) < 5.0:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.PROVENANCE,
                        severity=Severity.CRITICAL,
                        metric="revenue/2026E",
                        expected=f"~{gold_rev}",
                        observed=fy.revenue,
                        message=(
                            f"2026E revenue ({fy.revenue}) is close to H1 YTD revenue "
                            f"({_H1_REVENUE}). Possible quarterly/annual confusion."
                        ),
                        diagnostic_code="REV_QUARTERLY_CONFUSION",
                    )
                )

            # Check defensible range for 2026E (analyst-chosen growth rate)
            if fy.revenue < _REVENUE_2026_LOW - tol or fy.revenue > _REVENUE_2026_HIGH + tol:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.UNSUPPORTED,
                        severity=Severity.WARNING,
                        metric="revenue/2026E",
                        expected=f"{_REVENUE_2026_LOW}–{_REVENUE_2026_HIGH}",
                        observed=fy.revenue,
                        message=(
                            f"2026E revenue {fy.revenue} is outside the defensible "
                            f"7–9% growth range ({_REVENUE_2026_LOW}–{_REVENUE_2026_HIGH}). "
                            "Verify that the growth assumption is supportable."
                        ),
                        diagnostic_code="REV_GROWTH_OUT_OF_RANGE",
                    )
                )
        else:
            # Subsequent years: check arithmetic from prior year
            prev_fy = forecast_by_year.get(year - 1)
            if prev_fy is not None:
                expected_rev = prev_fy.revenue * (1.0 + fy.revenue_growth)
                if abs(expected_rev - fy.revenue) > tol:
                    failures.append(
                        GraderFailure(
                            error_type=ErrorType.ARITHMETIC,
                            severity=Severity.CRITICAL,
                            metric=f"revenue/{year}E",
                            expected=expected_rev,
                            observed=fy.revenue,
                            message=(
                                f"Revenue arithmetic error: {prev_fy.revenue} × "
                                f"(1 + {fy.revenue_growth}) = {expected_rev:.4f} "
                                f"≠ {fy.revenue}"
                            ),
                            diagnostic_code="REV_ARITHMETIC",
                        )
                    )

        # 2. Check internal consistency: revenue_growth stated vs actual
        if year > 2026 or (year == 2026):
            prev_year_rev = (
                _BASE_REVENUE_2025
                if year == 2026
                else (forecast_by_year[year - 1].revenue if year - 1 in forecast_by_year else None)
            )
            if prev_year_rev is not None:
                implied_growth = (fy.revenue / prev_year_rev) - 1.0
                if abs(implied_growth - fy.revenue_growth) > 0.0001:
                    warnings.append(
                        f"revenue/{year}E: stated growth {fy.revenue_growth:.4%} "
                        f"≠ implied {implied_growth:.4%}."
                    )

    # Score: count critical failures
    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    n_warnings_list = [f for f in failures if f.severity == Severity.WARNING]
    deduction = n_critical * (max_points / len(_GOLD_REVENUES)) + len(n_warnings_list) * (
        max_points * 0.05
    )
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
