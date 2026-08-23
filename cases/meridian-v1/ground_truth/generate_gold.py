"""Ground-truth gold submission generator for Meridian v1.

Run this script to regenerate examples/meridian_gold_submission/submission.json:

    uv run python cases/meridian-v1/ground_truth/generate_gold.py

The submission is derived from first principles using the DCF engine.
Nothing is hard-coded except the model assumptions, which are documented here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path when run directly
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

CASE_ID = "meridian-v1"
VALUATION_DATE = "2026-06-30"

# Revenue
BASE_REVENUE_2025 = 760.0
REVENUE_GROWTH_RATES = [0.20, 0.17, 0.14, 0.11, 0.08]  # 2026–2030E
EBITDA_MARGINS = [0.140, 0.170, 0.200, 0.230, 0.260]  # Adjusted EBITDA 2026–2030E
SBC_PCTS = [0.110, 0.100, 0.090, 0.080, 0.070]  # SBC % of revenue

# Ratios (% of revenue)
DA_PCT = 0.020
CAPEX_PCT = 0.050  # Physical capex (1.5%) + capitalized software (3.5%)
NWC_PCT = -0.050  # Working capital liability driven by deferred revenue
PREV_NWC_2025 = -38.0  # Base 2025 NWC (760.0 * -0.05)

# Tax
TAX_RATE = 0.25

# WACC inputs
RISK_FREE_RATE = 0.0425
BETA = 1.25
ERP = 0.055
PRE_TAX_COST_OF_DEBT = 0.055
EQUITY_WEIGHT = 0.95
DEBT_WEIGHT = 0.05

# Terminal value
TERMINAL_GROWTH_RATE = 0.030
DISCOUNTING_CONVENTION = "mid_year"

# Capital structure
GROSS_DEBT = 80.0
CASH = 280.0
NET_DEBT = GROSS_DEBT - CASH  # -200.0 (Net Cash = +200.0)
BASIC_SHARES = 80.0
DILUTED_SHARES = 88.0
CURRENT_SHARE_PRICE = 52.00
CONVERTIBLE_FACE = 80.0

# Comps (EV / NTM Revenue)
PEER_NAMES = [
    "Aether Data",
    "Vanguard SaaS",
    "Kestrel Systems",
    "Strata Platform",
    "Nimbus Cloud",
    "Helix Software",
]
NTM_REVENUE_MULTIPLES: list[float | None] = [7.5, 6.2, 5.4, 8.8, 3.5, 6.5]
LTM_REVENUE_MULTIPLES: list[float | None] = [8.8, 7.3, 6.1, 10.2, 3.8, 7.6]

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
        discounting_convention=DISCOUNTING_CONVENTION,
        sbc_pcts=SBC_PCTS,
    )

    # -----------------------------------------------------------------------
    # Trading Comps
    # -----------------------------------------------------------------------
    valid_multiples = filter_valid_peers(NTM_REVENUE_MULTIPLES)
    median_multiple = compute_median(valid_multiples)
    assert median_multiple is not None, "Median multiple could not be computed"

    applied_rev_2026 = result.forecast_years[0].revenue
    comps_ev = compute_comps_enterprise_value(median_multiple, applied_rev_2026)
    comps_equity = compute_comps_equity_value(comps_ev, NET_DEBT)
    comps_share_price = compute_comps_share_price(comps_equity, DILUTED_SHARES)

    # Peer objects
    peers_data = []
    for name, ntm_m, ltm_m in zip(
        PEER_NAMES, NTM_REVENUE_MULTIPLES, LTM_REVENUE_MULTIPLES, strict=True
    ):
        if name == "Strata Platform":
            peers_data.append(
                {
                    "name": name,
                    "ticker": "STRT",
                    "ntm_ev_ebitda": ntm_m,  # Using standard multiple field in schema
                    "ltm_ev_ebitda": ltm_m,
                    "excluded": False,
                    "exclusion_reason": "Negative FCF peer (EV/FCF = N/M); EV/NTM Revenue is 8.8x",
                }
            )
        else:
            ticker_map = {
                "Aether Data": "ADAT",
                "Vanguard SaaS": "VGSD",
                "Kestrel Systems": "KSTL",
                "Nimbus Cloud": "NMBS",
                "Helix Software": "HLXS",
            }
            peers_data.append(
                {
                    "name": name,
                    "ticker": ticker_map.get(name, "PEER"),
                    "ntm_ev_ebitda": ntm_m,
                    "ltm_ev_ebitda": ltm_m,
                    "excluded": False,
                    "exclusion_reason": "",
                }
            )

    # -----------------------------------------------------------------------
    # Historical data
    # -----------------------------------------------------------------------
    historical = [
        {
            "year": 2023,
            "revenue": 550.0,
            "ebitda": 17.0,
            "ebitda_margin": round(17.0 / 550.0, 4),
            "da": 12.0,
            "ebit": -61.0,
            "capex": 26.0,
            "nwc": -27.5,
        },
        {
            "year": 2024,
            "revenue": 650.0,
            "ebitda": 52.7,
            "ebitda_margin": round(52.7 / 650.0, 4),
            "da": 14.0,
            "ebit": -39.3,
            "capex": 31.0,
            "nwc": -32.5,
        },
        {
            "year": 2025,
            "revenue": 760.0,
            "ebitda": 93.7,
            "ebitda_margin": round(93.7 / 760.0, 4),
            "da": 16.0,
            "ebit": -13.5,
            "capex": 36.0,
            "nwc": -38.0,
        },
    ]

    # -----------------------------------------------------------------------
    # Forecast years payload
    # -----------------------------------------------------------------------
    forecast_payload = []
    for fy in result.forecast_years:
        forecast_payload.append(
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
    # Provenance records
    # -----------------------------------------------------------------------
    provenance = [
        {
            "metric": "base_revenue",
            "period": "2025A",
            "value": 760.0,
            "source": "source_02_historical_financials.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": (
                "GAAP revenue from consolidated statements ($760.0M), distinct from ending ARR "
                "($880.0M)."
            ),
        },
        {
            "metric": "revenue_growth",
            "period": "2026E",
            "value": 0.20,
            "source": "source_03_management_guidance.md",
            "classification": "analyst_assumption",
            "confidence": 0.90,
            "note": "20.0% is the midpoint of management guidance range (18%–22%).",
        },
        {
            "metric": "ebitda_margin",
            "period": "2026E",
            "value": 0.14,
            "source": "source_03_management_guidance.md",
            "classification": "analyst_assumption",
            "confidence": 0.90,
            "note": (
                "Adjusted EBITDA margin assumption aligned with management guidance target "
                "of 14.0%."
            ),
        },
        {
            "metric": "risk_free_rate",
            "period": "2026",
            "value": 0.0425,
            "source": "source_04_capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": "10-Year U.S. Treasury yield at valuation date.",
        },
        {
            "metric": "beta",
            "period": "2026",
            "value": 1.25,
            "source": "source_04_capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": "Levered beta for enterprise SaaS software peer group.",
        },
        {
            "metric": "equity_risk_premium",
            "period": "2026",
            "value": 0.055,
            "source": "source_04_capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": "Equity risk premium.",
        },
        {
            "metric": "gross_debt",
            "period": "2026",
            "value": 80.0,
            "source": "source_04_capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": "Out-of-the-money convertible senior notes treated as gross debt.",
        },
        {
            "metric": "cash",
            "period": "2026",
            "value": 280.0,
            "source": "source_04_capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": "Unrestricted corporate cash yielding net cash of +$200.0M.",
        },
        {
            "metric": "diluted_shares",
            "period": "2026",
            "value": 88.0,
            "source": "source_04_capital_structure.md",
            "classification": "direct",
            "confidence": 1.0,
            "note": "80.0M basic shares + 8.0M options and RSUs under treasury stock method.",
        },
        {
            "metric": "terminal_growth_rate",
            "period": "terminal",
            "value": 0.030,
            "source": "source_08_accounting_notes.md",
            "classification": "analyst_assumption",
            "confidence": 0.85,
            "note": "Long-term perpetual growth rate aligned with enterprise IT spending.",
        },
    ]

    # -----------------------------------------------------------------------
    # Complete submission object
    # -----------------------------------------------------------------------
    submission = {
        "case_id": CASE_ID,
        "analyst": "Gold Standard Model (Automated Ground Truth)",
        "valuation_date": VALUATION_DATE,
        "notes": {
            "model_narrative": (
                "Canonical gold submission for Meridian Cloud Systems, Inc. (meridian-v1). "
                "Derived from first principles using mid-year DCF discounting (t=0.5..4.5 "
                "for UFCF, t=5.0 for terminal horizon), SaaS non-cash SBC accounting, deferred "
                "revenue working capital dynamics, net cash equity bridge (EV + $200M), "
                "and EV / NTM Revenue trading comps."
            ),
            "growth_assumption_2026E": (
                "Management guided to approximately 18% to 22% GAAP revenue growth. "
                "Model assumes 20.0% as analyst interpretation midpoint."
            ),
            "convertible_notes": (
                "Convertible notes ($80.0M) have conversion price $75.00 > current price $52.00; "
                "treated as gross debt in capital structure."
            ),
        },
        "historical": historical,
        "provenance": provenance,
        "forecast": forecast_payload,
        "wacc_inputs": {
            "risk_free_rate": RISK_FREE_RATE,
            "beta": BETA,
            "equity_risk_premium": ERP,
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
            "method": "gordon_growth",
            "terminal_growth_rate": TERMINAL_GROWTH_RATE,
            "exit_multiple": None,
            "metric": None,
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
                "Convertible notes ($80.0M) are out-of-the-money ($75.00 strike vs $52.00 "
                "share price) and treated as gross debt."
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
            "peers": peers_data,
            "applied_multiple": median_multiple,
            "applied_ebitda": applied_rev_2026,
            "multiple_type": "ntm_ev_ebitda",
        },
        "comps_outputs": {
            "ntm_median": median_multiple,
            "ltm_median": compute_median(filter_valid_peers(LTM_REVENUE_MULTIPLES)),
            "enterprise_value": comps_ev,
            "equity_value": comps_equity,
            "implied_share_price": comps_share_price,
        },
        "headline": {
            "dcf_enterprise_value": result.dcf_enterprise_value,
            "dcf_equity_value": result.equity_value,
            "dcf_share_price": result.implied_share_price,
            "comps_enterprise_value": comps_ev,
            "comps_equity_value": comps_equity,
            "comps_share_price": comps_share_price,
        },
    }

    return submission


def main() -> None:
    submission = build_gold_submission()
    output_dir = (
        Path(__file__).parent.parent.parent.parent / "examples" / "meridian_gold_submission"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "submission.json"
    out_file.write_text(json.dumps(submission, indent=2))
    print(f"Generated gold submission -> {out_file}")
    print(f"DCF EV:           ${submission['dcf_outputs']['enterprise_value']:,.2f}M")
    print(f"DCF Equity:       ${submission['equity_bridge']['equity_value']:,.2f}M")
    print(f"DCF Share Price:  ${submission['equity_bridge']['implied_share_price']:,.2f}")
    print(f"Comps EV:         ${submission['comps_outputs']['enterprise_value']:,.2f}M")
    print(f"Comps Share Price:${submission['comps_outputs']['implied_share_price']:,.2f}")


if __name__ == "__main__":
    main()
