"""Unit tests for Meridian Cloud Systems benchmark (Milestone 4B)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ib_eval.case import load_case
from ib_eval.dcf import compute_discount_factor, compute_pv_terminal_value, run_dcf_model
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission

MERIDIAN_CASE_DIR = Path(__file__).parent.parent / "cases" / "meridian-v1"
MERIDIAN_GOLD_FILE = (
    Path(__file__).parent.parent / "examples" / "meridian_gold_submission" / "submission.json"
)


def test_meridian_case_loading() -> None:
    """Validate case metadata and rubric loading for meridian-v1."""
    case = load_case(MERIDIAN_CASE_DIR)
    assert case.meta.case_id == "meridian-v1"
    assert "Meridian" in case.meta.company
    assert case.rubric.max_score == 100.0
    assert len(case.rubric.graders) == 10

    # Graders present
    grader_names = {g.name for g in case.rubric.graders}
    assert grader_names == {
        "source_fidelity",
        "revenue_forecast",
        "margin_forecast",
        "free_cash_flow",
        "wacc",
        "terminal_value",
        "enterprise_value",
        "equity_bridge",
        "comps",
        "consistency",
    }


def test_meridian_gold_submission_grading() -> None:
    """Validate that the canonical Meridian gold submission grades 100/100 with 0 hard failures."""
    case = load_case(MERIDIAN_CASE_DIR)
    assert MERIDIAN_GOLD_FILE.exists(), f"Missing {MERIDIAN_GOLD_FILE}"
    raw = json.loads(MERIDIAN_GOLD_FILE.read_text())
    sub = Submission.model_validate(raw)

    report = grade_submission(sub, case)
    assert report.total_score == pytest.approx(100.0, abs=1e-3)
    assert report.grade == "A+"
    assert len(report.hard_failures) == 0
    assert all(r.passed for r in report.grader_results)


def test_meridian_midyear_discounting() -> None:
    """Validate mid-year discounting formula and TV horizon convention."""
    wacc = 0.10775
    # Explicit periods use t - 0.5
    df_1 = compute_discount_factor(wacc, 1, convention="mid_year")
    assert df_1 == pytest.approx(1.0 / (1.0 + wacc) ** 0.5, rel=1e-6)

    df_5 = compute_discount_factor(wacc, 5, convention="mid_year")
    assert df_5 == pytest.approx(1.0 / (1.0 + wacc) ** 4.5, rel=1e-6)

    # Terminal value discounted across full 5-year horizon (t=5.0)
    tv = 1000.0
    pv_tv = compute_pv_terminal_value(tv, wacc, 5.0)
    assert pv_tv == pytest.approx(tv / (1.0 + wacc) ** 5.0, rel=1e-6)


def test_meridian_dcf_model_run() -> None:
    """Validate DCF engine execution with SaaS parameters and mid-year timing."""
    result = run_dcf_model(
        base_revenue=760.0,
        revenue_growth_rates=[0.20, 0.17, 0.14, 0.11, 0.08],
        ebitda_margins=[0.140, 0.170, 0.200, 0.230, 0.260],
        da_pct=0.020,
        capex_pct=0.050,
        nwc_pct=-0.050,
        tax_rate=0.25,
        risk_free_rate=0.0425,
        beta=1.25,
        equity_risk_premium=0.055,
        pre_tax_cost_of_debt=0.055,
        equity_weight=0.95,
        debt_weight=0.05,
        terminal_growth_rate=0.030,
        net_debt=-200.0,  # Net Cash = +200M
        diluted_shares=88.0,
        forecast_start_year=2026,
        prev_nwc=-38.0,
        discounting_convention="mid_year",
        sbc_pcts=[0.110, 0.100, 0.090, 0.080, 0.070],
    )

    assert result.forecast_years[0].revenue == pytest.approx(912.0)
    assert result.forecast_years[0].ebitda == pytest.approx(127.68)
    assert result.forecast_years[0].ebit == pytest.approx(
        9.12
    )  # 127.68 - 100.32 (SBC) - 18.24 (D&A)
    assert result.equity_value == pytest.approx(result.dcf_enterprise_value + 200.0)
    assert result.implied_share_price == pytest.approx(result.equity_value / 88.0)
