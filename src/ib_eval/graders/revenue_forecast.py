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
    gold_revenues_cfg = config.params.get("gold_revenues", _GOLD_REVENUES)
    gold_revenues = {int(k): float(v) for k, v in gold_revenues_cfg.items()}
    base_revenue = float(config.params.get("base_revenue", _BASE_REVENUE_2025))
    growth_low = float(config.params.get("growth_range_low", 0.07))
    growth_high = float(config.params.get("growth_range_high", 0.09))
    growth_label = str(config.params.get("growth_range_label", "7–9%"))
    rev_low = base_revenue * (1.0 + growth_low)
    rev_high = base_revenue * (1.0 + growth_high)

    arr_confusion = config.params.get("arr_confusion_value")
    first_forecast_year = min(gold_revenues.keys()) if gold_revenues else 2026

    for year, gold_rev in gold_revenues.items():
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

        # 1. Check for source confusion on the first forecast year
        if year == first_forecast_year:
            # Check ARR vs Revenue confusion if configured
            if arr_confusion is not None:
                arr_val = float(arr_confusion)
                arr_mismatch = abs(fy.revenue - arr_val * (1.0 + fy.revenue_growth)) < 5.0
                if arr_mismatch or abs(fy.revenue - arr_val) < 5.0:
                    failures.append(
                        GraderFailure(
                            error_type=ErrorType.PROVENANCE,
                            severity=Severity.CRITICAL,
                            metric=f"revenue/{year}E",
                            expected=f"~{gold_rev}",
                            observed=fy.revenue,
                            message=(
                                f"{year}E revenue ({fy.revenue:.2f}) appears derived from ending "
                                f"ARR (${arr_val:.1f}mm) rather than base GAAP revenue "
                                f"(${base_revenue:.1f}mm)."
                            ),
                            diagnostic_code="REV_ARR_CONFUSION",
                        )
                    )
            # Check Q2/H1 confusion (Northstar)
            if abs(fy.revenue - _Q2_REVENUE) < 5.0:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.PROVENANCE,
                        severity=Severity.CRITICAL,
                        metric=f"revenue/{year}E",
                        expected=f"~{gold_rev}",
                        observed=fy.revenue,
                        message=(
                            f"{year}E revenue ({fy.revenue}) is close to Q2 standalone "
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
                        metric=f"revenue/{year}E",
                        expected=f"~{gold_rev}",
                        observed=fy.revenue,
                        message=(
                            f"{year}E revenue ({fy.revenue}) is close to H1 YTD revenue "
                            f"({_H1_REVENUE}). Possible quarterly/annual confusion."
                        ),
                        diagnostic_code="REV_QUARTERLY_CONFUSION",
                    )
                )

            # Check defensible range for first forecast year (analyst-chosen growth rate)
            if fy.revenue < rev_low - tol or fy.revenue > rev_high + tol:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.UNSUPPORTED,
                        severity=Severity.WARNING,
                        metric=f"revenue/{year}E",
                        expected=f"{rev_low}–{rev_high}",
                        observed=fy.revenue,
                        message=(
                            f"{year}E revenue {fy.revenue} is outside the defensible "
                            f"{growth_label} growth range ({rev_low:.2f}–{rev_high:.2f}). "
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
        if year > first_forecast_year or (year == first_forecast_year):
            prev_year_rev = (
                base_revenue
                if year == first_forecast_year
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
