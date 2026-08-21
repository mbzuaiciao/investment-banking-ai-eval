"""Grader 5 — WACC.

Validates WACC computation from first principles.

Hard failure codes:
  WACC_PRETAX_DEBT         : pre-tax cost of debt used without tax shield
  WACC_FORMULA_ERROR       : WACC components do not combine correctly
  WACC_WEIGHTS_ERROR       : equity/debt weights do not sum to 1
"""

from __future__ import annotations

from ib_eval.case import GraderConfig
from ib_eval.dcf import (
    compute_after_tax_cost_of_debt,
    compute_cost_of_equity,
    compute_wacc,
)
from ib_eval.schemas import (
    ErrorType,
    GraderFailure,
    GraderResult,
    Severity,
    Submission,
)

GRADER_NAME = "wacc"

_TOL = 0.0001  # 1 bps


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    tol = config.tolerances.get("wacc_abs", _TOL)
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    wi = submission.wacc_inputs
    wo = submission.wacc_outputs

    # 1. Weight validation
    weight_sum = wi.equity_weight + wi.debt_weight
    if abs(weight_sum - 1.0) > 0.001:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="wacc_weights",
                expected=1.0,
                observed=weight_sum,
                message=f"Equity weight + debt weight = {weight_sum:.4f} ≠ 1.0",
                diagnostic_code="WACC_WEIGHTS_ERROR",
            )
        )

    # 2. Cost of equity: Ke = rf + β × ERP
    expected_ke = compute_cost_of_equity(wi.risk_free_rate, wi.beta, wi.equity_risk_premium)
    if abs(expected_ke - wo.cost_of_equity) > tol:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="cost_of_equity",
                expected=expected_ke,
                observed=wo.cost_of_equity,
                message=(
                    f"Ke = rf + β × ERP = {wi.risk_free_rate} + {wi.beta} × "
                    f"{wi.equity_risk_premium} = {expected_ke:.6f} ≠ {wo.cost_of_equity}"
                ),
                diagnostic_code="WACC_KE_ERROR",
            )
        )

    # 3. After-tax cost of debt
    expected_kd_at = compute_after_tax_cost_of_debt(wi.pre_tax_cost_of_debt, wi.tax_rate)
    if abs(expected_kd_at - wo.after_tax_cost_of_debt) > tol:
        # Check whether they used pre-tax Kd directly (a common error)
        if abs(wi.pre_tax_cost_of_debt - wo.after_tax_cost_of_debt) < tol:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.FORMULA,
                    severity=Severity.CRITICAL,
                    metric="after_tax_cost_of_debt",
                    expected=expected_kd_at,
                    observed=wo.after_tax_cost_of_debt,
                    message=(
                        "Pre-tax cost of debt used without tax adjustment. "
                        f"Kd_at = Kd × (1 − t) = {wi.pre_tax_cost_of_debt} × "
                        f"{1 - wi.tax_rate} = {expected_kd_at:.6f}, "
                        f"not {wo.after_tax_cost_of_debt}."
                    ),
                    diagnostic_code="WACC_PRETAX_DEBT",
                )
            )
        else:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.FORMULA,
                    severity=Severity.CRITICAL,
                    metric="after_tax_cost_of_debt",
                    expected=expected_kd_at,
                    observed=wo.after_tax_cost_of_debt,
                    message=(
                        f"After-tax Kd = Kd × (1 − t) = {wi.pre_tax_cost_of_debt} × "
                        f"{1 - wi.tax_rate} = {expected_kd_at:.6f} ≠ {wo.after_tax_cost_of_debt}"
                    ),
                    diagnostic_code="WACC_KD_ERROR",
                )
            )

    # 4. WACC formula
    expected_wacc = compute_wacc(expected_ke, expected_kd_at, wi.equity_weight, wi.debt_weight)
    if abs(expected_wacc - wo.wacc) > tol:
        failures.append(
            GraderFailure(
                error_type=ErrorType.FORMULA,
                severity=Severity.CRITICAL,
                metric="wacc",
                expected=expected_wacc,
                observed=wo.wacc,
                message=(
                    f"WACC = We × Ke + Wd × Kd_at = "
                    f"{wi.equity_weight} × {expected_ke:.6f} + "
                    f"{wi.debt_weight} × {expected_kd_at:.6f} = {expected_wacc:.6f} "
                    f"≠ {wo.wacc}"
                ),
                diagnostic_code="WACC_FORMULA_ERROR",
            )
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
