"""Grader 4 — Free Cash Flow.

Validates NOPAT, ΔNWC, capex, and UFCF for each forecast year.

Hard failure codes:
  FCF_NOPAT_ERROR          : NOPAT ≠ EBIT × (1 − tax)
  FCF_CAPEX_DOUBLE_COUNTED : capex appears duplicated
  FCF_NWC_DELTA_ERROR      : ΔNWC arithmetic is wrong
  FCF_UFCF_ERROR           : UFCF formula is wrong
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

GRADER_NAME = "free_cash_flow"

_TAX_RATE = 0.25
_CAPEX_PCT = 0.045
_NWC_PCT = 0.12
_PREV_NWC_2025 = 120.0  # historical NWC for ΔNWC in 2026E
_ABS_TOL = 0.05


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    tol = config.tolerances.get("fcf_abs", _ABS_TOL)
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    tax_rate = float(config.params.get("tax_rate", _TAX_RATE))
    capex_pct = float(config.params.get("capex_pct", _CAPEX_PCT))
    nwc_pct = float(config.params.get("nwc_pct", _NWC_PCT))
    prev_nwc_base = float(config.params.get("prev_nwc", _PREV_NWC_2025))

    sorted_years = sorted(submission.forecast, key=lambda x: x.year)
    prev_nwc: dict[int, float] = {}
    prev_nwc[sorted_years[0].year - 1] = prev_nwc_base

    for fy in sorted_years:
        year = fy.year
        prev = prev_nwc.get(year - 1, prev_nwc_base)

        # 1. NOPAT = EBIT × (1 − tax)
        expected_nopat = fy.ebit * (1.0 - tax_rate)
        if abs(expected_nopat - fy.nopat) > tol:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.FORMULA,
                    severity=Severity.CRITICAL,
                    metric=f"nopat/{year}E",
                    expected=expected_nopat,
                    observed=fy.nopat,
                    message=(
                        f"NOPAT = EBIT × (1 − {tax_rate}): "
                        f"{fy.ebit} × {1 - tax_rate} = {expected_nopat:.4f} ≠ {fy.nopat}"
                    ),
                    diagnostic_code="FCF_NOPAT_ERROR",
                )
            )

        # 2. Capex = capex_pct of revenue
        expected_capex = fy.revenue * capex_pct
        if abs(expected_capex - fy.capex) > tol:
            # Check if capex is double the expected (double-counting)
            if (
                abs(fy.capex - 2 * expected_capex) < tol * 2
                or abs(fy.capex - (expected_capex + fy.revenue * 0.035)) < tol
            ):
                diag_code = (
                    "FCF_SOFTWARE_DOUBLE_COUNTED"
                    if "software_capex_pct" in config.params
                    else "FCF_CAPEX_DOUBLE_COUNTED"
                )
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.ACCOUNTING,
                        severity=Severity.CRITICAL,
                        metric=f"capex/{year}E",
                        expected=expected_capex,
                        observed=fy.capex,
                        message=(
                            f"Capex appears double-counted: submitted {fy.capex:.4f}, "
                            f"expected {expected_capex:.4f} ({capex_pct:.1%} of revenue)."
                        ),
                        diagnostic_code=diag_code,
                    )
                )
            else:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.FORMULA,
                        severity=Severity.CRITICAL,
                        metric=f"capex/{year}E",
                        expected=expected_capex,
                        observed=fy.capex,
                        message=(
                            f"Capex should be {capex_pct:.1%} of revenue: "
                            f"{fy.revenue} × {capex_pct} = {expected_capex:.4f} ≠ {fy.capex}"
                        ),
                        diagnostic_code="FCF_CAPEX_ERROR",
                    )
                )

        # 3. NWC = nwc_pct of revenue
        expected_nwc = fy.revenue * nwc_pct
        if abs(expected_nwc - fy.nwc) > tol:
            warnings.append(
                f"nwc/{year}E: expected {expected_nwc:.4f} ({nwc_pct:.1%} of revenue), "
                f"got {fy.nwc:.4f}"
            )

        # 4. ΔNWC = NWC_t − NWC_{t-1}
        expected_delta_nwc = fy.nwc - prev
        if abs(expected_delta_nwc - fy.delta_nwc) > tol:
            # Check if sign was reversed on negative NWC / deferred revenue
            if abs(fy.delta_nwc + expected_delta_nwc) < tol * 2 and expected_delta_nwc < 0:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.ACCOUNTING,
                        severity=Severity.CRITICAL,
                        metric=f"delta_nwc/{year}E",
                        expected=expected_delta_nwc,
                        observed=fy.delta_nwc,
                        message=(
                            "Deferred revenue / working capital sign reversed: growth in "
                            f"contract liabilities is a cash inflow. "
                            f"Expected ΔNWC = {expected_delta_nwc:.4f}, got {fy.delta_nwc:.4f}."
                        ),
                        diagnostic_code="WC_DEFERRED_REV_REVERSED",
                    )
                )
            else:
                failures.append(
                    GraderFailure(
                        error_type=ErrorType.ARITHMETIC,
                        severity=Severity.CRITICAL,
                        metric=f"delta_nwc/{year}E",
                        expected=expected_delta_nwc,
                        observed=fy.delta_nwc,
                        message=(
                            f"ΔNWC = NWC_t − NWC_{{t-1}}: {fy.nwc:.4f} − {prev:.4f} "
                            f"= {expected_delta_nwc:.4f} ≠ {fy.delta_nwc}"
                        ),
                        diagnostic_code="FCF_NWC_DELTA_ERROR",
                    )
                )

        # 5. UFCF = NOPAT + D&A − Capex − ΔNWC
        expected_ufcf = fy.nopat + fy.da - fy.capex - fy.delta_nwc
        if abs(expected_ufcf - fy.ufcf) > tol:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.FORMULA,
                    severity=Severity.CRITICAL,
                    metric=f"ufcf/{year}E",
                    expected=expected_ufcf,
                    observed=fy.ufcf,
                    message=(
                        f"UFCF = NOPAT + D&A − Capex − ΔNWC: "
                        f"{fy.nopat:.4f} + {fy.da:.4f} − {fy.capex:.4f} − {fy.delta_nwc:.4f} "
                        f"= {expected_ufcf:.4f} ≠ {fy.ufcf}"
                    ),
                    diagnostic_code="FCF_UFCF_ERROR",
                )
            )

        # 6. PV check
        if abs(fy.pv_ufcf - fy.ufcf * fy.discount_factor) > tol:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ARITHMETIC,
                    severity=Severity.CRITICAL,
                    metric=f"pv_ufcf/{year}E",
                    expected=fy.ufcf * fy.discount_factor,
                    observed=fy.pv_ufcf,
                    message=f"PV(UFCF) = UFCF × discount_factor inconsistency for {year}E",
                    diagnostic_code="FCF_PV_ERROR",
                )
            )

        prev_nwc[year] = fy.nwc

    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    items_per_year = 5  # nopat, capex, delta_nwc, ufcf, pv
    deduction = n_critical * (max_points / (len(sorted_years) * items_per_year))
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
