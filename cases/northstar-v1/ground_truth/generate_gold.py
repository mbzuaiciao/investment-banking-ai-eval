"""Ground-truth gold submission generator for Northstar v1.

Run this script to regenerate examples/gold_submission/submission.json:

    uv run python cases/northstar-v1/ground_truth/generate_gold.py

The submission is derived from first principles using the DCF engine.
Nothing is hard-coded except the model assumptions, which are documented here.
"""

from __future__ import annotations

import json

# Add src to path when run directly
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ib_eval.comps import (
    compute_comps_enterprise_value,
    compute_comps_equity_value,
    compute_comps_share_price,
    compute_median,
    filter_valid_peers,
)
from ib_eval.dcf import run_dcf_model

# ---------------------------------------------------------------------------
# Model assumptions
# ---------------------------------------------------------------------------

CASE_ID = "northstar-v1"
VALUATION_DATE = "2026-06-30"

# Revenue
BASE_REVENUE_2025 = 1000.0
REVENUE_GROWTH_RATES = [0.08, 0.07, 0.06, 0.05, 0.04]  # 2026–2030E
EBITDA_MARGINS = [0.170, 0.175, 0.180, 0.1825, 0.185]   # 2026–2030E

# Ratios (% of revenue)
DA_PCT = 0.04
CAPEX_PCT = 0.045
NWC_PCT = 0.12
PREV_NWC_2025 = 120.0  # historical NWC

# Tax
TAX_RATE = 0.25

# WACC inputs
RISK_FREE_RATE = 0.041
BETA = 1.18
ERP = 0.055
PRE_TAX_COST_OF_DEBT = 0.062
EQUITY_WEIGHT = 0.78
DEBT_WEIGHT = 0.22

# Terminal value
TERMINAL_GROWTH_RATE = 0.025

# Capital structure
GROSS_DEBT = 420.0
CASH = 95.0
NET_DEBT = GROSS_DEBT - CASH
DILUTED_SHARES = 60.0
CURRENT_SHARE_PRICE = 20.00
CONVERTIBLE_FACE = 75.0

# Comps
NTM_MULTIPLES: list[float | None] = [7.9, 8.5, 9.2, 7.3, None]  # None = N/M
LTM_MULTIPLES: list[float | None] = [8.4, 9.1, 10.0, 7.8, None]
PEER_NAMES = [
    "Apex Motion",
    "Beacon Industrial",
    "Crestline Systems",
    "Delta Precision",
    "Evergreen Controls",
]

FORECAST_START_YEAR = 2026


def build_gold_submission() -> dict:  # type: ignore[type-arg]
    """Build the complete gold submission dict from first principles."""

    # -----------------------------------------------------------------------
    # Run DCF model
    # -----------------------------------------------------------------------
    result = run_dcf_model(
        base_revenue=BASE_REVENUE_2025,
        revenue_growth_rates=REVENUE_GROWTH_RATES,
        ebitda_margins=EBITDA_MARGINS,
        da_pct=DA_PCT,
        capex_pct=CAPEX_PCT,
        nwc_pct=NWC_PCT,
        tax_rate=TAX_RATE,
        risk_free_rate=RISK_FREE_RATE,
        beta=BETA,
        equity_risk_premium=ERP,
        pre_tax_cost_of_debt=PRE_TAX_COST_OF_DEBT,
        equity_weight=EQUITY_WEIGHT,
        debt_weight=DEBT_WEIGHT,
        terminal_growth_rate=TERMINAL_GROWTH_RATE,
        net_debt=NET_DEBT,
        diluted_shares=DILUTED_SHARES,
        forecast_start_year=FORECAST_START_YEAR,
        prev_nwc=PREV_NWC_2025,
    )

    # -----------------------------------------------------------------------
    # Comps
    # -----------------------------------------------------------------------
    valid_ntm = filter_valid_peers(NTM_MULTIPLES)
    valid_ltm = filter_valid_peers(LTM_MULTIPLES)
    ntm_median = compute_median(valid_ntm)
    ltm_median = compute_median(valid_ltm)

    assert ntm_median is not None, "NTM median should not be None"
    applied_multiple = ntm_median
    # Use 2026E EBITDA from the model
    applied_ebitda = result.forecast_years[0].ebitda
    comps_ev = compute_comps_enterprise_value(applied_multiple, applied_ebitda)
    comps_equity = compute_comps_equity_value(comps_ev, NET_DEBT)
    comps_price = compute_comps_share_price(comps_equity, DILUTED_SHARES)

    # -----------------------------------------------------------------------
    # Build forecast list
    # -----------------------------------------------------------------------
    historical = [
        {
            "year": 2023,
            "revenue": 820.0,
            "ebitda": 131.2,
            "ebitda_margin": 0.160,
            "da": 32.8,
            "ebit": 98.4,
            "capex": 36.9,
            "nwc": 98.4,
        },
        {
            "year": 2024,
            "revenue": 905.0,
            "ebitda": 149.3,
            "ebitda_margin": 0.165,
            "da": 36.2,
            "ebit": 113.1,
            "capex": 40.7,
            "nwc": 108.6,
        },
        {
            "year": 2025,
            "revenue": 1000.0,
            "ebitda": 165.0,
            "ebitda_margin": 0.165,
            "da": 40.0,
            "ebit": 125.0,
            "capex": 45.0,
            "nwc": 120.0,
        },
    ]

    forecast = []
    for fy in result.forecast_years:
        forecast.append(
            {
                "year": fy.year,
                "revenue": fy.revenue,
                "revenue_growth": fy.revenue_growth,
                "ebitda_margin": fy.ebitda_margin,
                "ebitda": fy.ebitda,
                "da": fy.da,
                "ebit": fy.ebit,
                "nopat": fy.nopat,
                "capex": fy.capex,
                "nwc": fy.nwc,
                "delta_nwc": fy.delta_nwc,
                "ufcf": fy.ufcf,
                "discount_factor": fy.discount_factor,
                "pv_ufcf": fy.pv_ufcf,
            }
        )

    # -----------------------------------------------------------------------
    # Build peers
    # -----------------------------------------------------------------------
    peers = []
    for name, ltm, ntm in zip(PEER_NAMES, LTM_MULTIPLES, NTM_MULTIPLES, strict=True):
        peer: dict = {
            "name": name,
            "ltm_ev_ebitda": ltm,
            "ntm_ev_ebitda": ntm,
            "excluded": ntm is None,
            "exclusion_reason": "negative EBITDA; N/M multiples" if ntm is None else "",
        }
        if name == "Crestline Systems":
            peer["exclusion_reason"] = (
                "fiscal year ends Sep 30 — mismatch with calendar-year peers; "
                "included with disclosure"
            )
            peer["excluded"] = False
        peers.append(peer)

    # -----------------------------------------------------------------------
    # Provenance records
    # -----------------------------------------------------------------------
    provenance = [
        {
            "metric": "revenue_growth",
            "period": "2026E",
            "value": 0.08,
            "source": "management_guidance.md",
            "classification": "analyst_assumption",
            "confidence": 0.85,
            "note": (
                "Management guided to 'high single digits' (qualitative). "
                "Analyst interprets as 8.0%. Range 7–9% is defensible."
            ),
        },
        {
            "metric": "ebitda_margin",
            "period": "2026E",
            "value": 0.17,
            "source": "management_guidance.md",
            "classification": "direct",
            "confidence": 0.90,
            "note": "Management guided to approximately 17% adjusted EBITDA margin.",
        },
        {
            "metric": "capex_pct",
            "period": "2026E",
            "value": 0.045,
            "source": "management_guidance.md",
            "classification": "direct",
            "confidence": 0.90,
            "note": (
                "Management guided capital investment at ~4.5% of sales. "
                "'Capital investment' = 'purchases of property and equipment' "
                "per cash flow statement."
            ),
        },
        {
            "metric": "revenue",
            "period": "2026E_source_selection",
            "value": 1000.0,
            "source": "income_statement.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": (
                "FY2025 annual revenue $1,000mm used as base. "
                "Q2 revenue ($281mm) and H1 revenue ($535mm) from quarterly_report.md "
                "are NOT used as annual figures."
            ),
        },
        {
            "metric": "gross_debt",
            "period": "2026-06-30",
            "value": 420.0,
            "source": "capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": "Total gross debt per Q2 balance sheet.",
        },
        {
            "metric": "convertible_treatment",
            "period": "2026-06-30",
            "value": 0.0,
            "source": "capital_structure.md",
            "classification": "analyst_assumption",
            "confidence": 1.0,
            "note": (
                "$75mm convertible notes treated as DEBT. "
                "Conversion price $27.50 > current price $20.00 → out of money under base case."
            ),
        },
        {
            "metric": "restructuring_treatment",
            "period": "2025A",
            "value": 0.0,
            "source": "income_statement.md",
            "classification": "analyst_assumption",
            "confidence": 0.80,
            "note": (
                "$9mm 2025 restructuring charge: retained in GAAP EBITDA for historical "
                "comparability. Forward model does not include recurring restructuring. "
                "Treatment explicitly documented."
            ),
        },
        {
            "metric": "evergreen_controls_multiple",
            "period": "LTM/NTM",
            "value": 0.0,
            "source": "capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": (
                "Evergreen Controls has negative EBITDA → EV/EBITDA is N/M. "
                "Excluded from median. NOT assigned a zero multiple."
            ),
        },
        {
            "metric": "crestline_fy_mismatch",
            "period": "LTM/NTM",
            "value": 0.0,
            "source": "capital_structure.md",
            "classification": "analyst_assumption",
            "confidence": 0.75,
            "note": (
                "Crestline Systems has Sep 30 fiscal year end. "
                "Included in peer set with disclosure of FY mismatch."
            ),
        },
    ]

    # -----------------------------------------------------------------------
    # Assemble submission
    # -----------------------------------------------------------------------
    submission = {
        "case_id": CASE_ID,
        "analyst": "gold_model",
        "valuation_date": VALUATION_DATE,
        "historical": historical,
        "forecast": forecast,
        "wacc_inputs": {
            "risk_free_rate": RISK_FREE_RATE,
            "equity_risk_premium": ERP,
            "beta": BETA,
            "pre_tax_cost_of_debt": PRE_TAX_COST_OF_DEBT,
            "tax_rate": TAX_RATE,
            "equity_weight": EQUITY_WEIGHT,
            "debt_weight": DEBT_WEIGHT,
        },
        "wacc_outputs": {
            "cost_of_equity": result.cost_of_equity,
            "after_tax_cost_of_debt": result.after_tax_cost_of_debt,
            "wacc": result.wacc,
        },
        "terminal_value_inputs": {
            "terminal_growth_rate": TERMINAL_GROWTH_RATE,
            "method": "perpetual_growth",
        },
        "terminal_value_outputs": {
            "terminal_fcf": result.terminal_fcf,
            "terminal_value_at_horizon": result.terminal_value_at_horizon,
            "pv_terminal_value": result.pv_terminal_value,
        },
        "dcf_outputs": {
            "sum_pv_ufcf": result.sum_pv_ufcf,
            "pv_terminal_value": result.pv_terminal_value,
            "enterprise_value": result.dcf_enterprise_value,
        },
        "capital_structure": {
            "gross_debt": GROSS_DEBT,
            "cash": CASH,
            "net_debt": NET_DEBT,
            "diluted_shares": DILUTED_SHARES,
            "current_share_price": CURRENT_SHARE_PRICE,
            "convertible_face_value": CONVERTIBLE_FACE,
            "convertible_treatment": "debt",
            "note_convertible": (
                "Convertible notes ($75mm) treated as debt. "
                "Conversion price ($27.50) > current price ($20.00); "
                "conversion assumed out-of-the-money under base case."
            ),
        },
        "equity_bridge": {
            "enterprise_value": result.dcf_enterprise_value,
            "minus_net_debt": NET_DEBT,
            "equity_value": result.equity_value,
            "diluted_shares": DILUTED_SHARES,
            "implied_share_price": result.implied_share_price,
        },
        "comps_inputs": {
            "peers": peers,
            "applied_multiple": applied_multiple,
            "applied_ebitda": applied_ebitda,
        },
        "comps_outputs": {
            "ltm_median": ltm_median,
            "ntm_median": ntm_median,
            "enterprise_value": comps_ev,
            "equity_value": comps_equity,
            "implied_share_price": comps_price,
        },
        "headline": {
            "dcf_enterprise_value": result.dcf_enterprise_value,
            "dcf_equity_value": result.equity_value,
            "dcf_share_price": result.implied_share_price,
            "comps_enterprise_value": comps_ev,
            "comps_equity_value": comps_equity,
            "comps_share_price": comps_price,
        },
        "provenance": provenance,
        "notes": {
            "restructuring_2025": (
                "$9mm 2025 restructuring retained in historical GAAP figures; "
                "not normalized. Forward model does not include recurring restructuring."
            ),
            "convertible_treatment": (
                "Convertible notes treated as debt under base case. "
                "See provenance record for rationale."
            ),
            "growth_assumption_2026E": (
                "Management guided to 'high single digits' growth. "
                "Model assumes 8.0% as analyst interpretation. "
                "Management did not guide to exactly 8%."
            ),
        },
    }

    return submission


if __name__ == "__main__":
    submission = build_gold_submission()

    # Print key outputs
    dcf = submission["dcf_outputs"]
    eb = submission["equity_bridge"]
    wacc_out = submission["wacc_outputs"]
    tv = submission["terminal_value_outputs"]
    comps_out = submission["comps_outputs"]

    print("=" * 60)
    print("NORTHSTAR V1 — GOLD MODEL OUTPUT")
    print("=" * 60)
    print(f"WACC:                    {wacc_out['wacc']:.4%}")
    print(f"Cost of equity (Ke):     {wacc_out['cost_of_equity']:.4%}")
    print(f"After-tax Kd:            {wacc_out['after_tax_cost_of_debt']:.4%}")
    print("Terminal growth rate:    2.5%")
    print(f"Terminal FCF:            ${tv['terminal_fcf']:.2f}mm")
    print(f"TV at horizon:           ${tv['terminal_value_at_horizon']:.2f}mm")
    print(f"PV(TV):                  ${tv['pv_terminal_value']:.2f}mm")
    print(f"Σ PV(UFCF):              ${dcf['sum_pv_ufcf']:.2f}mm")
    print(f"DCF Enterprise value:    ${dcf['enterprise_value']:.2f}mm")
    print(f"Less: net debt:          ${eb['minus_net_debt']:.2f}mm")
    print(f"DCF Equity value:        ${eb['equity_value']:.2f}mm")
    print(f"Implied share price:     ${eb['implied_share_price']:.4f}")
    print(f"Comps NTM median:        {comps_out['ntm_median']:.2f}x")
    print(f"Comps EV:                ${comps_out['enterprise_value']:.2f}mm")
    print(f"Comps equity:            ${comps_out['equity_value']:.2f}mm")
    print(f"Comps share price:       ${comps_out['implied_share_price']:.4f}")
    print("=" * 60)

    # Write to file
    out_path = (
        Path(__file__).parent.parent.parent.parent
        / "examples"
        / "gold_submission"
        / "submission.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(submission, indent=2))
    print(f"\nWrote gold submission to {out_path}")
