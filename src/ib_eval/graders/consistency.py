"""Grader 10 — Cross-Artifact Consistency.

Validates that the headline valuation matches the underlying model outputs
and that values are internally consistent across artifacts.

Hard failure codes:
  CONSISTENCY_HEADLINE_DCF  : headline DCF values don't match model
  CONSISTENCY_HEADLINE_COMPS: headline comps values don't match model
  CONSISTENCY_EV_BRIDGE     : equity bridge EV doesn't match DCF EV
  CONSISTENCY_SHARES        : diluted shares inconsistent across sections
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

GRADER_NAME = "consistency"

_ABS_TOL = 0.1      # $0.1mm for EV/equity
_PRICE_TOL = 0.01   # $0.01 for share price


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    h = submission.headline
    eb = submission.equity_bridge
    do = submission.dcf_outputs
    co = submission.comps_outputs
    cs = submission.capital_structure

    # 1. Headline DCF EV matches DCF model output
    if abs(h.dcf_enterprise_value - do.enterprise_value) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="headline.dcf_enterprise_value",
                expected=do.enterprise_value,
                observed=h.dcf_enterprise_value,
                message=(
                    f"Headline DCF EV ({h.dcf_enterprise_value:.2f}) ≠ "
                    f"DCF model EV ({do.enterprise_value:.2f})"
                ),
                diagnostic_code="CONSISTENCY_HEADLINE_DCF",
            )
        )

    # 2. Headline DCF equity matches equity bridge
    if abs(h.dcf_equity_value - eb.equity_value) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="headline.dcf_equity_value",
                expected=eb.equity_value,
                observed=h.dcf_equity_value,
                message=(
                    f"Headline DCF equity ({h.dcf_equity_value:.2f}) ≠ "
                    f"equity bridge ({eb.equity_value:.2f})"
                ),
                diagnostic_code="CONSISTENCY_HEADLINE_DCF",
            )
        )

    # 3. Headline DCF share price matches equity bridge
    if abs(h.dcf_share_price - eb.implied_share_price) > _PRICE_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="headline.dcf_share_price",
                expected=eb.implied_share_price,
                observed=h.dcf_share_price,
                message=(
                    f"Headline DCF share price ({h.dcf_share_price:.4f}) ≠ "
                    f"equity bridge ({eb.implied_share_price:.4f})"
                ),
                diagnostic_code="CONSISTENCY_HEADLINE_DCF",
            )
        )

    # 4. Headline comps EV matches comps outputs
    if abs(h.comps_enterprise_value - co.enterprise_value) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="headline.comps_enterprise_value",
                expected=co.enterprise_value,
                observed=h.comps_enterprise_value,
                message=(
                    f"Headline comps EV ({h.comps_enterprise_value:.2f}) ≠ "
                    f"comps model EV ({co.enterprise_value:.2f})"
                ),
                diagnostic_code="CONSISTENCY_HEADLINE_COMPS",
            )
        )

    # 5. Headline comps equity matches comps outputs
    if abs(h.comps_equity_value - co.equity_value) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="headline.comps_equity_value",
                expected=co.equity_value,
                observed=h.comps_equity_value,
                message=(
                    f"Headline comps equity ({h.comps_equity_value:.2f}) ≠ "
                    f"comps model equity ({co.equity_value:.2f})"
                ),
                diagnostic_code="CONSISTENCY_HEADLINE_COMPS",
            )
        )

    # 6. Headline comps share price matches comps outputs
    if abs(h.comps_share_price - co.implied_share_price) > _PRICE_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="headline.comps_share_price",
                expected=co.implied_share_price,
                observed=h.comps_share_price,
                message=(
                    f"Headline comps share price ({h.comps_share_price:.4f}) ≠ "
                    f"comps model ({co.implied_share_price:.4f})"
                ),
                diagnostic_code="CONSISTENCY_HEADLINE_COMPS",
            )
        )

    # 7. Diluted shares consistent between capital structure and equity bridge
    if abs(cs.diluted_shares - eb.diluted_shares) > 0.001:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.WARNING,
                metric="diluted_shares",
                expected=cs.diluted_shares,
                observed=eb.diluted_shares,
                message=(
                    f"Diluted shares mismatch: capital_structure={cs.diluted_shares}, "
                    f"equity_bridge={eb.diluted_shares}"
                ),
                diagnostic_code="CONSISTENCY_SHARES",
            )
        )

    # 8. Equity bridge EV matches DCF EV
    if abs(eb.enterprise_value - do.enterprise_value) > _ABS_TOL:
        failures.append(
            GraderFailure(
                error_type=ErrorType.CROSS_ARTIFACT,
                severity=Severity.CRITICAL,
                metric="equity_bridge.enterprise_value",
                expected=do.enterprise_value,
                observed=eb.enterprise_value,
                message=(
                    f"Equity bridge EV ({eb.enterprise_value:.2f}) ≠ "
                    f"DCF EV ({do.enterprise_value:.2f})"
                ),
                diagnostic_code="CONSISTENCY_EV_BRIDGE",
            )
        )

    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    n_warnings_list = [f for f in failures if f.severity == Severity.WARNING]
    deduction = n_critical * (max_points / 8) + len(n_warnings_list) * (max_points * 0.05)
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
