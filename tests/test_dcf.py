"""Tests for DCF math functions."""

from __future__ import annotations

import pytest

from ib_eval.dcf import (
    compute_after_tax_cost_of_debt,
    compute_cost_of_equity,
    compute_dcf_enterprise_value,
    compute_discount_factor,
    compute_equity_value,
    compute_implied_share_price,
    compute_nopat,
    compute_pv_terminal_value,
    compute_terminal_fcf,
    compute_terminal_value_at_horizon,
    compute_ufcf,
    compute_wacc,
    run_dcf_model,
)

# ---------------------------------------------------------------------------
# WACC components
# ---------------------------------------------------------------------------


def test_cost_of_equity_capm() -> None:
    """Ke = rf + β × ERP."""
    ke = compute_cost_of_equity(risk_free_rate=0.041, beta=1.18, equity_risk_premium=0.055)
    assert abs(ke - 0.1059) < 1e-6


def test_after_tax_cost_of_debt() -> None:
    """Kd_at = Kd × (1 − t)."""
    kd_at = compute_after_tax_cost_of_debt(pre_tax_cost_of_debt=0.062, tax_rate=0.25)
    assert abs(kd_at - 0.0465) < 1e-6


def test_wacc_formula() -> None:
    """WACC = We × Ke + Wd × Kd_at."""
    ke = compute_cost_of_equity(0.041, 1.18, 0.055)
    kd_at = compute_after_tax_cost_of_debt(0.062, 0.25)
    wacc = compute_wacc(ke, kd_at, equity_weight=0.78, debt_weight=0.22)
    assert abs(wacc - 0.092832) < 1e-5


def test_wacc_northstar_gold() -> None:
    """Full WACC matches spec: 9.2832%."""
    ke = compute_cost_of_equity(0.041, 1.18, 0.055)
    kd_at = compute_after_tax_cost_of_debt(0.062, 0.25)
    wacc = compute_wacc(ke, kd_at, 0.78, 0.22)
    assert abs(wacc - 0.092832) < 1e-5, f"WACC = {wacc:.6f}, expected 0.092832"


# ---------------------------------------------------------------------------
# Forecast helpers
# ---------------------------------------------------------------------------


def test_nopat() -> None:
    """NOPAT = EBIT × (1 − t)."""
    assert abs(compute_nopat(ebit=140.4, tax_rate=0.25) - 105.3) < 1e-6


def test_ufcf() -> None:
    """UFCF = NOPAT + D&A − Capex − ΔNWC."""
    ufcf = compute_ufcf(nopat=105.3, da=43.2, capex=48.6, delta_nwc=9.6)
    assert abs(ufcf - 90.3) < 1e-6


def test_discount_factor_period_1() -> None:
    """df = 1/(1+WACC)^1."""
    df = compute_discount_factor(wacc=0.092832, period=1)
    expected = 1.0 / 1.092832
    assert abs(df - expected) < 1e-9


def test_discount_factor_period_5() -> None:
    """df = 1/(1+WACC)^5."""
    df = compute_discount_factor(wacc=0.092832, period=5)
    expected = 1.0 / (1.092832**5)
    assert abs(df - expected) < 1e-9


# ---------------------------------------------------------------------------
# NWC and ΔNWC
# ---------------------------------------------------------------------------


def test_delta_nwc_first_year() -> None:
    """ΔNWC for 2026E: NWC_2026 - NWC_2025."""
    nwc_2026 = 1080.0 * 0.12  # 129.6
    nwc_2025 = 120.0
    delta = nwc_2026 - nwc_2025
    assert abs(delta - 9.6) < 1e-6


def test_delta_nwc_formula_in_model() -> None:
    """Check ΔNWC flows correctly through the full model."""
    result = run_dcf_model(
        base_revenue=1000.0,
        revenue_growth_rates=[0.08],
        ebitda_margins=[0.17],
        da_pct=0.04,
        capex_pct=0.045,
        nwc_pct=0.12,
        tax_rate=0.25,
        risk_free_rate=0.041,
        beta=1.18,
        equity_risk_premium=0.055,
        pre_tax_cost_of_debt=0.062,
        equity_weight=0.78,
        debt_weight=0.22,
        terminal_growth_rate=0.025,
        net_debt=325.0,
        diluted_shares=60.0,
        prev_nwc=120.0,
    )
    fy = result.forecast_years[0]
    assert abs(fy.nwc - 1080.0 * 0.12) < 1e-6
    assert abs(fy.delta_nwc - (1080.0 * 0.12 - 120.0)) < 1e-6


# ---------------------------------------------------------------------------
# Terminal value
# ---------------------------------------------------------------------------


def test_terminal_fcf() -> None:
    """Terminal FCF = final UFCF × (1 + g)."""
    final_ufcf = 100.0
    g = 0.025
    tv_fcf = compute_terminal_fcf(final_ufcf, g)
    assert abs(tv_fcf - 102.5) < 1e-9


def test_terminal_value_at_horizon() -> None:
    """TV = FCF_T+1 / (WACC - g)."""
    tv = compute_terminal_value_at_horizon(
        terminal_fcf=102.5, wacc=0.092832, terminal_growth_rate=0.025
    )
    expected = 102.5 / (0.092832 - 0.025)
    assert abs(tv - expected) < 1e-6


def test_terminal_value_growth_exceeds_wacc() -> None:
    """Should raise ValueError when g >= WACC."""
    with pytest.raises(ValueError, match="must exceed"):
        compute_terminal_value_at_horizon(100.0, wacc=0.03, terminal_growth_rate=0.05)


def test_pv_terminal_value() -> None:
    """PV(TV) = TV × discount_factor."""
    tv = 2003.0
    wacc = 0.092832
    n = 5
    pv_tv = compute_pv_terminal_value(tv, wacc, n)
    expected = tv / (1.092832**5)
    assert abs(pv_tv - expected) < 1e-6


# ---------------------------------------------------------------------------
# DCF EV
# ---------------------------------------------------------------------------


def test_dcf_enterprise_value() -> None:
    """EV = Σ PV(UFCF) + PV(TV)."""
    pv_ufcfs = [80.0, 75.0, 70.0, 65.0, 60.0]
    pv_tv = 1200.0
    ev = compute_dcf_enterprise_value(pv_ufcfs, pv_tv)
    assert abs(ev - 1550.0) < 1e-9


# ---------------------------------------------------------------------------
# Equity bridge
# ---------------------------------------------------------------------------


def test_equity_value() -> None:
    """Equity = EV - net_debt."""
    eq = compute_equity_value(enterprise_value=1712.97, net_debt=325.0)
    assert abs(eq - 1387.97) < 1e-6


def test_implied_share_price() -> None:
    """Share price = equity / shares."""
    price = compute_implied_share_price(equity_value=1387.97, diluted_shares=60.0)
    assert abs(price - 23.13283333) < 1e-4


def test_implied_share_price_zero_shares() -> None:
    """Should raise ValueError for zero shares."""
    with pytest.raises(ValueError):
        compute_implied_share_price(1000.0, 0.0)


# ---------------------------------------------------------------------------
# Full model integration
# ---------------------------------------------------------------------------


def test_full_model_northstar_gold() -> None:
    """Full model produces gold values to within reasonable precision."""
    result = run_dcf_model(
        base_revenue=1000.0,
        revenue_growth_rates=[0.08, 0.07, 0.06, 0.05, 0.04],
        ebitda_margins=[0.170, 0.175, 0.180, 0.1825, 0.185],
        da_pct=0.04,
        capex_pct=0.045,
        nwc_pct=0.12,
        tax_rate=0.25,
        risk_free_rate=0.041,
        beta=1.18,
        equity_risk_premium=0.055,
        pre_tax_cost_of_debt=0.062,
        equity_weight=0.78,
        debt_weight=0.22,
        terminal_growth_rate=0.025,
        net_debt=325.0,
        diluted_shares=60.0,
        prev_nwc=120.0,
    )

    # WACC
    assert abs(result.wacc - 0.092832) < 1e-5

    # 2026E revenue
    assert abs(result.forecast_years[0].revenue - 1080.0) < 1e-6

    # 2026E EBITDA
    assert abs(result.forecast_years[0].ebitda - 183.6) < 1e-4

    # DCF EV approximately $1,713mm
    assert abs(result.dcf_enterprise_value - 1712.97) < 1.0

    # Equity value approximately $1,388mm
    assert abs(result.equity_value - 1387.97) < 1.0

    # Share price approximately $23.13
    assert abs(result.implied_share_price - 23.13) < 0.01


def test_model_forecast_revenue_arithmetic() -> None:
    """Each forecast year revenue = prev × (1 + g)."""
    result = run_dcf_model(
        base_revenue=1000.0,
        revenue_growth_rates=[0.08, 0.07],
        ebitda_margins=[0.17, 0.175],
        da_pct=0.04,
        capex_pct=0.045,
        nwc_pct=0.12,
        tax_rate=0.25,
        risk_free_rate=0.041,
        beta=1.18,
        equity_risk_premium=0.055,
        pre_tax_cost_of_debt=0.062,
        equity_weight=0.78,
        debt_weight=0.22,
        terminal_growth_rate=0.025,
        net_debt=325.0,
        diluted_shares=60.0,
    )
    fy0 = result.forecast_years[0]
    fy1 = result.forecast_years[1]
    assert abs(fy0.revenue - 1080.0) < 1e-6
    assert abs(fy1.revenue - fy0.revenue * 1.07) < 1e-6


def test_model_mismatched_inputs() -> None:
    """Should raise ValueError if growth_rates and margins differ in length."""
    with pytest.raises(ValueError):
        run_dcf_model(
            base_revenue=1000.0,
            revenue_growth_rates=[0.08, 0.07],
            ebitda_margins=[0.17],  # wrong length
            da_pct=0.04,
            capex_pct=0.045,
            nwc_pct=0.12,
            tax_rate=0.25,
            risk_free_rate=0.041,
            beta=1.18,
            equity_risk_premium=0.055,
            pre_tax_cost_of_debt=0.062,
            equity_weight=0.78,
            debt_weight=0.22,
            terminal_growth_rate=0.025,
            net_debt=325.0,
            diluted_shares=60.0,
        )
