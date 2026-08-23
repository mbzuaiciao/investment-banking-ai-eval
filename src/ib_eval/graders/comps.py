"""Grader 9 — Trading Comps.

Validates the trading comparable companies analysis.

Hard failure codes:
  COMPS_NM_COERCED_ZERO    : N/M peer used in median as zero
  COMPS_MEDIAN_ERROR       : median multiple computed incorrectly
  COMPS_EV_ARITHMETIC      : comps EV ≠ multiple × EBITDA
  COMPS_FY_MISMATCH_HIDDEN : fiscal-year mismatch for Crestline not surfaced
"""

from __future__ import annotations

from ib_eval.case import GraderConfig
from ib_eval.comps import compute_median, filter_valid_peers
from ib_eval.schemas import (
    ErrorType,
    GraderFailure,
    GraderResult,
    Severity,
    Submission,
)

GRADER_NAME = "comps"

# Expected peers from Northstar v1
_EVERGREEN_NAME = "Evergreen Controls"
_CRESTLINE_NAME = "Crestline Systems"
_DELTA_NAME = "Delta Precision"

_GOLD_NTM_MULTIPLES: dict[str, float | None] = {
    "Apex Motion": 7.9,
    "Beacon Industrial": 8.5,
    "Crestline Systems": 9.2,
    "Delta Precision": 7.3,
    "Evergreen Controls": None,  # N/M
}

# Gold median NTM EV/EBITDA (excluding Evergreen)
_GOLD_MEDIAN_NTM = 8.2

_ABS_TOL = 0.01
_MULTIPLE_TOL = 0.05  # 0.05x tolerance for median


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    ci = submission.comps_inputs
    co = submission.comps_outputs
    cs = submission.capital_structure

    nm_peer_name = str(config.params.get("nm_peer_name", _EVERGREEN_NAME))
    gold_median = float(config.params.get("gold_median_ntm", _GOLD_MEDIAN_NTM))
    is_meridian = "strata" in nm_peer_name.lower()

    # 1. Check N/M peer is NOT coerced to zero in the NTM multiples
    nm_peers = [p for p in ci.peers if p.name == nm_peer_name]
    if nm_peers:
        ep = nm_peers[0]
        # If N/M peer has multiple = 0, that is a hard failure
        if ep.ntm_ev_ebitda == 0.0 or ep.ltm_ev_ebitda == 0.0:
            diag_code = "COMPS_NM_FCF_COERCED_ZERO" if is_meridian else "COMPS_NM_COERCED_ZERO"
            failures.append(
                GraderFailure(
                    error_type=ErrorType.VALUATION,
                    severity=Severity.CRITICAL,
                    metric=f"comps.{nm_peer_name.lower().replace(' ', '_')}_ntm",
                    expected="None (N/M)",
                    observed=0.0,
                    message=(
                        f"{nm_peer_name} has negative cash flow / EBITDA and should be marked N/M "
                        "(None), not coerced to zero."
                    ),
                    diagnostic_code=diag_code,
                )
            )
        elif ep.ntm_ev_ebitda is None and not ep.excluded:
            # Good — it's N/M and should be excluded from median
            info.append(f"{nm_peer_name}: correctly marked N/M.")
    else:
        if not is_meridian:
            warnings.append(f"{nm_peer_name} not found in submission peers.")

    # 2. Check Crestline fiscal-year mismatch is surfaced (Northstar specific)
    crestline_peers = [p for p in ci.peers if p.name == _CRESTLINE_NAME]
    if crestline_peers:
        cp = crestline_peers[0]
        fy_note = (
            "fiscal" in cp.exclusion_reason.lower()
            or "fy" in cp.exclusion_reason.lower()
            or "fiscal" in cp.name.lower()
        )
        if not fy_note:
            # Check submission notes
            notes_str = str(submission.notes).lower()
            if "crestline" not in notes_str or (
                "fiscal" not in notes_str and "fy mismatch" not in notes_str
            ):
                warnings.append(
                    f"{_CRESTLINE_NAME} has a fiscal-year mismatch. "
                    "Consider noting this in peer exclusion_reason or submission notes."
                )

    # 3. Validate median calculation
    ntm_multiples = [p.ntm_ev_ebitda for p in ci.peers]
    valid_ntm = filter_valid_peers(ntm_multiples)
    computed_median = compute_median(valid_ntm)

    if computed_median is None:
        failures.append(
            GraderFailure(
                error_type=ErrorType.VALUATION,
                severity=Severity.CRITICAL,
                metric="comps.ntm_median",
                expected=gold_median,
                observed=None,
                message="No valid NTM peers found — cannot compute median.",
                diagnostic_code="COMPS_MEDIAN_ERROR",
            )
        )
    else:
        if co.ntm_median is not None and abs(co.ntm_median - computed_median) > _MULTIPLE_TOL:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ARITHMETIC,
                    severity=Severity.CRITICAL,
                    metric="comps.ntm_median",
                    expected=computed_median,
                    observed=co.ntm_median,
                    message=(
                        f"NTM median computed as {computed_median:.2f}x "
                        f"from valid peers, but submission reports {co.ntm_median:.2f}x. "
                        "Possible N/M peer included in median."
                    ),
                    diagnostic_code="COMPS_MEDIAN_ERROR",
                )
            )

    # 4. Comps EV = applied_multiple × applied metric
    applied_metric_val = (
        ci.applied_metric_value if ci.applied_metric_value is not None else ci.applied_ebitda
    )
    metric_label = ci.applied_metric or config.params.get("applied_metric_name", "EBITDA")
    if applied_metric_val is None:
        if config.params.get("multiple_type") == "ev_revenue":
            applied_metric_val = (
                submission.forecast[0].revenue if submission.forecast else None
            )
            metric_label = "Revenue"
        else:
            applied_metric_val = (
                submission.forecast[0].ebitda if submission.forecast else None
            )
            metric_label = "EBITDA"

    if applied_metric_val is not None:
        expected_ev = ci.applied_multiple * applied_metric_val
        if abs(expected_ev - co.enterprise_value) > _ABS_TOL:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ARITHMETIC,
                    severity=Severity.CRITICAL,
                    metric="comps.enterprise_value",
                    expected=expected_ev,
                    observed=co.enterprise_value,
                    message=(
                        f"Comps EV = multiple × {metric_label}: {ci.applied_multiple} × "
                        f"{applied_metric_val} = {expected_ev:.4f} ≠ {co.enterprise_value:.4f}"
                    ),
                    diagnostic_code="COMPS_EV_ARITHMETIC",
                )
            )

    # 5. Comps equity = comps EV − net_debt
    net_debt = cs.gross_debt - cs.cash
    expected_comps_equity = co.enterprise_value - net_debt
    if abs(expected_comps_equity - co.equity_value) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.ARITHMETIC,
                severity=Severity.CRITICAL,
                metric="comps.equity_value",
                expected=expected_comps_equity,
                observed=co.equity_value,
                message=(
                    f"Comps equity = comps EV − net debt: {co.enterprise_value:.4f} − "
                    f"{net_debt:.4f} = {expected_comps_equity:.4f} ≠ {co.equity_value:.4f}"
                ),
                diagnostic_code="COMPS_EQUITY_ARITHMETIC",
            )
        )

    # 6. Comps share price
    if cs.diluted_shares > 0:
        expected_price = co.equity_value / cs.diluted_shares
        if abs(expected_price - co.implied_share_price) > 0.01:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ARITHMETIC,
                    severity=Severity.CRITICAL,
                    metric="comps.implied_share_price",
                    expected=expected_price,
                    observed=co.implied_share_price,
                    message=(
                        f"Comps share price = equity / shares: {co.equity_value:.4f} / "
                        f"{cs.diluted_shares} = {expected_price:.4f} ≠ {co.implied_share_price}"
                    ),
                    diagnostic_code="COMPS_SHARE_PRICE_ERROR",
                )
            )

    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    deduction = n_critical * (max_points / 5)
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
