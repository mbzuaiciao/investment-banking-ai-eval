"""Grader 8 — Equity Bridge.

Validates the EV → equity value → share price bridge.

Hard failure codes:
  EQ_BRIDGE_CASH_REVERSED  : cash added to net debt instead of subtracted
  EQ_BRIDGE_DEBT_OMITTED   : debt not subtracted from EV
  EQ_BRIDGE_ARITHMETIC     : equity value arithmetic error
  EQ_BRIDGE_SHARE_PRICE    : share price arithmetic error
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

GRADER_NAME = "equity_bridge"

# Approximate gold values for cross-check
_GOLD_EQ_VALUE_APPROX = 1388.0
_GOLD_SHARE_PRICE_APPROX = 23.13
_ABS_TOL = 0.01
_SHARE_PRICE_TOL = 0.01


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    tol = config.tolerances.get("equity_abs", _ABS_TOL)
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    eb = submission.equity_bridge
    cs = submission.capital_structure
    do = submission.dcf_outputs

    # 1. EV in bridge matches DCF EV
    if abs(eb.enterprise_value - do.enterprise_value) > tol:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="equity_bridge.enterprise_value",
                expected=do.enterprise_value,
                observed=eb.enterprise_value,
                message=(
                    f"Equity bridge EV ({eb.enterprise_value:.4f}) ≠ "
                    f"DCF EV ({do.enterprise_value:.4f})"
                ),
                diagnostic_code="EQ_BRIDGE_EV_MISMATCH",
            )
        )

    # 2. net_debt in bridge matches capital structure
    expected_net_debt = cs.gross_debt - cs.cash
    if abs(eb.minus_net_debt - expected_net_debt) > tol:
        # Detect cash reversed (net_debt = gross_debt + cash instead of gross_debt - cash)
        cash_reversed_net_debt = cs.gross_debt + cs.cash
        if abs(eb.minus_net_debt - cash_reversed_net_debt) < tol * 2:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ACCOUNTING,
                    severity=Severity.CRITICAL,
                    metric="equity_bridge.minus_net_debt",
                    expected=expected_net_debt,
                    observed=eb.minus_net_debt,
                    message=(
                        f"Cash appears to have been ADDED to gross debt rather than subtracted. "
                        f"Net debt = gross_debt − cash = {cs.gross_debt} − {cs.cash} "
                        f"= {expected_net_debt}, not {eb.minus_net_debt}."
                    ),
                    diagnostic_code="EQ_BRIDGE_CASH_REVERSED",
                )
            )
        # Detect debt omitted (net_debt ≈ negative cash = just cash subtracted with wrong sign)
        elif abs(eb.minus_net_debt - (-cs.cash)) < tol * 5:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ACCOUNTING,
                    severity=Severity.CRITICAL,
                    metric="equity_bridge.minus_net_debt",
                    expected=expected_net_debt,
                    observed=eb.minus_net_debt,
                    message=(
                        f"Debt appears omitted from equity bridge. "
                        f"Net debt should be {expected_net_debt}, not {eb.minus_net_debt}."
                    ),
                    diagnostic_code="EQ_BRIDGE_DEBT_OMITTED",
                )
            )
        elif abs(eb.minus_net_debt) < tol:
            # Net debt is zero — likely debt omitted entirely
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ACCOUNTING,
                    severity=Severity.CRITICAL,
                    metric="equity_bridge.minus_net_debt",
                    expected=expected_net_debt,
                    observed=eb.minus_net_debt,
                    message=(
                        "Net debt in equity bridge is ~0. Debt may be entirely omitted."
                    ),
                    diagnostic_code="EQ_BRIDGE_DEBT_OMITTED",
                )
            )
        else:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ARITHMETIC,
                    severity=Severity.CRITICAL,
                    metric="equity_bridge.minus_net_debt",
                    expected=expected_net_debt,
                    observed=eb.minus_net_debt,
                    message=(
                        f"Net debt mismatch: expected {expected_net_debt:.4f}, "
                        f"got {eb.minus_net_debt:.4f}."
                    ),
                    diagnostic_code="EQ_BRIDGE_NET_DEBT_ERROR",
                )
            )

    # 3. Equity value = EV − net_debt
    expected_equity = eb.enterprise_value - eb.minus_net_debt
    if abs(expected_equity - eb.equity_value) > tol:
        failures.append(
            GraderFailure(
                error_type=ErrorType.ARITHMETIC,
                severity=Severity.CRITICAL,
                metric="equity_bridge.equity_value",
                expected=expected_equity,
                observed=eb.equity_value,
                message=(
                    f"Equity value = EV − net debt: {eb.enterprise_value:.4f} − "
                    f"{eb.minus_net_debt:.4f} = {expected_equity:.4f} ≠ {eb.equity_value:.4f}"
                ),
                diagnostic_code="EQ_BRIDGE_ARITHMETIC",
            )
        )

    # 4. Share price = equity / shares
    if eb.diluted_shares > 0:
        expected_price = eb.equity_value / eb.diluted_shares
        if abs(expected_price - eb.implied_share_price) > _SHARE_PRICE_TOL:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.ARITHMETIC,
                    severity=Severity.CRITICAL,
                    metric="equity_bridge.implied_share_price",
                    expected=expected_price,
                    observed=eb.implied_share_price,
                    message=(
                        f"Share price = equity / shares: {eb.equity_value:.4f} / "
                        f"{eb.diluted_shares} = {expected_price:.4f} "
                        f"≠ {eb.implied_share_price}"
                    ),
                    diagnostic_code="EQ_BRIDGE_SHARE_PRICE",
                )
            )

    # 5. Convertible treatment — must be explicit
    if cs.convertible_treatment.value not in ("debt", "equity", "treasury_stock"):
        warnings.append(
            f"Convertible treatment '{cs.convertible_treatment}' is not a recognized value."
        )
    if not cs.note_convertible:
        warnings.append(
            "No note explaining convertible debt treatment. Consider adding an explanation."
        )

    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    deduction = n_critical * (max_points / 4)
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
