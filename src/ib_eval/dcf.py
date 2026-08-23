"""DCF computation engine for IB-Eval.

All formulas are implemented explicitly so they can be independently tested.
Nothing is hard-coded; values flow from inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# WACC
# ---------------------------------------------------------------------------


def compute_cost_of_equity(
    risk_free_rate: float,
    beta: float,
    equity_risk_premium: float,
) -> float:
    """CAPM: Ke = rf + β × ERP."""
    return risk_free_rate + beta * equity_risk_premium


def compute_after_tax_cost_of_debt(
    pre_tax_cost_of_debt: float,
    tax_rate: float,
) -> float:
    """Kd_at = Kd × (1 − t)."""
    return pre_tax_cost_of_debt * (1.0 - tax_rate)


def compute_wacc(
    cost_of_equity: float,
    after_tax_cost_of_debt: float,
    equity_weight: float,
    debt_weight: float,
) -> float:
    """WACC = We × Ke + Wd × Kd_at."""
    return equity_weight * cost_of_equity + debt_weight * after_tax_cost_of_debt


# ---------------------------------------------------------------------------
# Forecast helpers
# ---------------------------------------------------------------------------


def compute_nopat(ebit: float, tax_rate: float) -> float:
    """NOPAT = EBIT × (1 − t)."""
    return ebit * (1.0 - tax_rate)


def compute_ufcf(
    nopat: float,
    da: float,
    capex: float,
    delta_nwc: float,
) -> float:
    """Unlevered free cash flow.

    UFCF = NOPAT + D&A − Capex − ΔNWC

    ΔNWC = NWC_t − NWC_{t-1}  (increase in NWC is a use of cash)
    """
    return nopat + da - capex - delta_nwc


def compute_discount_factor(
    wacc: float,
    period: float | int,
    convention: str = "end_of_year",
) -> float:
    """Compute discount factor.

    - end_of_year: df = 1 / (1 + WACC)^n
    - mid_year: df = 1 / (1 + WACC)^(n - 0.5) if n is integer, else 1 / (1 + WACC)^n
    """
    if convention == "mid_year" and isinstance(period, int):
        exponent = float(period) - 0.5
    else:
        exponent = float(period)
    return 1.0 / (1.0 + wacc) ** exponent


# ---------------------------------------------------------------------------
# Terminal value
# ---------------------------------------------------------------------------


def compute_terminal_fcf(
    final_year_ufcf: float,
    terminal_growth_rate: float,
) -> float:
    """Terminal FCF = UFCF_T × (1 + g)."""
    return final_year_ufcf * (1.0 + terminal_growth_rate)


def compute_terminal_value_at_horizon(
    terminal_fcf: float,
    wacc: float,
    terminal_growth_rate: float,
) -> float:
    """Gordon Growth perpetuity at end of forecast horizon.

    TV = FCF_T+1 / (WACC − g)
    """
    if wacc <= terminal_growth_rate:
        msg = f"WACC ({wacc:.4%}) must exceed terminal growth rate ({terminal_growth_rate:.4%})"
        raise ValueError(msg)
    return terminal_fcf / (wacc - terminal_growth_rate)


def compute_pv_terminal_value(
    terminal_value_at_horizon: float,
    wacc: float,
    n_forecast_years: int | float = 5,
) -> float:
    """Discount the terminal value back to the valuation date.

    PV_TV = TV / (1 + WACC)^n
    """
    return terminal_value_at_horizon / ((1.0 + wacc) ** float(n_forecast_years))


# ---------------------------------------------------------------------------
# DCF enterprise value
# ---------------------------------------------------------------------------


def compute_dcf_enterprise_value(
    pv_ufcfs: list[float],
    pv_terminal_value: float,
) -> float:
    """EV = Σ PV(UFCF) + PV(TV)."""
    return sum(pv_ufcfs) + pv_terminal_value


# ---------------------------------------------------------------------------
# Equity bridge
# ---------------------------------------------------------------------------


def compute_equity_value(enterprise_value: float, net_debt: float) -> float:
    """Equity value = EV − net debt."""
    return enterprise_value - net_debt


def compute_implied_share_price(equity_value: float, diluted_shares: float) -> float:
    """Share price = equity value / diluted shares."""
    if diluted_shares <= 0:
        msg = "diluted_shares must be positive"
        raise ValueError(msg)
    return equity_value / diluted_shares


# ---------------------------------------------------------------------------
# Full model runner
# ---------------------------------------------------------------------------


@dataclass
class ForecastYearResult:
    year: int
    revenue: float
    revenue_growth: float
    ebitda_margin: float
    ebitda: float
    da: float
    ebit: float
    nopat: float
    capex: float
    nwc: float
    delta_nwc: float
    ufcf: float
    discount_factor: float
    pv_ufcf: float


@dataclass
class DCFModelResult:
    wacc: float
    cost_of_equity: float
    after_tax_cost_of_debt: float
    forecast_years: list[ForecastYearResult]
    terminal_fcf: float
    terminal_value_at_horizon: float
    pv_terminal_value: float
    sum_pv_ufcf: float
    dcf_enterprise_value: float
    equity_value: float
    implied_share_price: float


def run_dcf_model(
    *,
    # Revenue forecast
    base_revenue: float,
    revenue_growth_rates: list[float],
    ebitda_margins: list[float],
    # Assumption ratios (as % of revenue)
    da_pct: float,
    capex_pct: float,
    nwc_pct: float,
    # Tax
    tax_rate: float,
    # WACC inputs
    risk_free_rate: float,
    beta: float,
    equity_risk_premium: float,
    pre_tax_cost_of_debt: float,
    equity_weight: float,
    debt_weight: float,
    # Terminal value
    terminal_growth_rate: float,
    # Capital structure
    net_debt: float,
    diluted_shares: float,
    # Forecast start year
    forecast_start_year: int = 2026,
    # Previous year NWC (for ΔNWC calculation in first forecast year)
    prev_nwc: float | None = None,
    # Discounting convention ("end_of_year" or "mid_year")
    discounting_convention: str = "end_of_year",
    # Optional SBC schedule (% of revenue)
    sbc_pcts: list[float] | None = None,
) -> DCFModelResult:
    """Run the full DCF model from first principles."""
    n = len(revenue_growth_rates)
    if len(ebitda_margins) != n:
        msg = "revenue_growth_rates and ebitda_margins must have the same length"
        raise ValueError(msg)

    # WACC
    ke = compute_cost_of_equity(risk_free_rate, beta, equity_risk_premium)
    kd_at = compute_after_tax_cost_of_debt(pre_tax_cost_of_debt, tax_rate)
    wacc = compute_wacc(ke, kd_at, equity_weight, debt_weight)

    # Build forecast
    forecast_years: list[ForecastYearResult] = []
    prev_rev = base_revenue
    prev_nwc_val = prev_nwc if prev_nwc is not None else base_revenue * nwc_pct

    for i, (g, margin) in enumerate(zip(revenue_growth_rates, ebitda_margins, strict=True)):
        year = forecast_start_year + i
        rev = prev_rev * (1.0 + g)
        ebitda = rev * margin
        da = rev * da_pct
        if sbc_pcts is not None and i < len(sbc_pcts):
            sbc = rev * sbc_pcts[i]
            ebit = ebitda - sbc - da
        else:
            ebit = ebitda - da
        nopat = compute_nopat(ebit, tax_rate)
        capex = rev * capex_pct
        nwc = rev * nwc_pct
        delta_nwc = nwc - prev_nwc_val
        ufcf = compute_ufcf(nopat, da, capex, delta_nwc)
        period = i + 1
        df = compute_discount_factor(wacc, period, convention=discounting_convention)
        pv = ufcf * df

        forecast_years.append(
            ForecastYearResult(
                year=year,
                revenue=rev,
                revenue_growth=g,
                ebitda_margin=margin,
                ebitda=ebitda,
                da=da,
                ebit=ebit,
                nopat=nopat,
                capex=capex,
                nwc=nwc,
                delta_nwc=delta_nwc,
                ufcf=ufcf,
                discount_factor=df,
                pv_ufcf=pv,
            )
        )
        prev_rev = rev
        prev_nwc_val = nwc

    # Terminal value
    terminal_fcf = compute_terminal_fcf(forecast_years[-1].ufcf, terminal_growth_rate)
    tv_at_horizon = compute_terminal_value_at_horizon(terminal_fcf, wacc, terminal_growth_rate)
    pv_tv = compute_pv_terminal_value(tv_at_horizon, wacc, n)

    # EV → equity
    sum_pv_ufcf = sum(fy.pv_ufcf for fy in forecast_years)
    ev = compute_dcf_enterprise_value([fy.pv_ufcf for fy in forecast_years], pv_tv)
    equity_val = compute_equity_value(ev, net_debt)
    share_price = compute_implied_share_price(equity_val, diluted_shares)

    return DCFModelResult(
        wacc=wacc,
        cost_of_equity=ke,
        after_tax_cost_of_debt=kd_at,
        forecast_years=forecast_years,
        terminal_fcf=terminal_fcf,
        terminal_value_at_horizon=tv_at_horizon,
        pv_terminal_value=pv_tv,
        sum_pv_ufcf=sum_pv_ufcf,
        dcf_enterprise_value=ev,
        equity_value=equity_val,
        implied_share_price=share_price,
    )
