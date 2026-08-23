#!/usr/bin/env python3
"""Generate all 10 corrupted submission fixtures for Meridian Cloud Systems (meridian-v1).

Run with:
    uv run python examples/meridian_corrupted/generate_corrupted.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

GOLD_PATH = Path(__file__).parent.parent / "meridian_gold_submission" / "submission.json"
OUT_DIR = Path(__file__).parent


def load_gold() -> dict:  # type: ignore[type-arg]
    return json.loads(GOLD_PATH.read_text())


def write(name: str, submission: dict) -> None:  # type: ignore[type-arg]
    d = OUT_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "submission.json").write_text(json.dumps(submission, indent=2))
    print(f"  Wrote {name}/submission.json")


# ---------------------------------------------------------------------------
# M01: Ending ARR ($880M) confused with base GAAP revenue ($760M)
# Triggers: REV_ARR_CONFUSION
# ---------------------------------------------------------------------------
def make_m01_arr_revenue_confusion() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    # 2026E revenue compounded from $880M ARR instead of $760M GAAP revenue
    for fy in sub["forecast"]:
        if fy["year"] == 2026:
            fy["revenue"] = 880.0 * 1.20  # 1056.0 instead of 912.0
            fy["ebitda"] = fy["revenue"] * fy["ebitda_margin"]
            fy["da"] = fy["revenue"] * 0.02
            fy["ebit"] = fy["ebitda"] - fy["revenue"] * 0.11 - fy["da"]
            fy["nopat"] = fy["ebit"] * 0.75
            fy["capex"] = fy["revenue"] * 0.05
            fy["nwc"] = fy["revenue"] * -0.05
            fy["delta_nwc"] = fy["nwc"] - (-38.0)
            fy["ufcf"] = fy["nopat"] + fy["da"] - fy["capex"] - fy["delta_nwc"]
            fy["pv_ufcf"] = fy["ufcf"] * fy["discount_factor"]
    sub["analyst"] = "corrupted_m01"
    sub["notes"]["corruption"] = (
        "M01: 2026E revenue compounded from FY2025 ending ARR ($880.0M) "
        "rather than base GAAP revenue ($760.0M)."
    )
    return sub


# ---------------------------------------------------------------------------
# M02: Deferred revenue / working capital change sign reversed
# Triggers: WC_DEFERRED_REV_REVERSED
# ---------------------------------------------------------------------------
def make_m02_deferred_rev_reversed() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    for fy in sub["forecast"]:
        # Reverse delta_nwc sign so positive cash from contract liabilities is treated as cash drain
        fy["delta_nwc"] = -fy["delta_nwc"]
        fy["ufcf"] = fy["nopat"] + fy["da"] - fy["capex"] - fy["delta_nwc"]
        fy["pv_ufcf"] = fy["ufcf"] * fy["discount_factor"]
    sub["analyst"] = "corrupted_m02"
    sub["notes"]["corruption"] = (
        "M02: Change in deferred revenue / NWC liability growth treated as a cash outflow "
        "instead of positive operating cash flow."
    )
    return sub


# ---------------------------------------------------------------------------
# M03: Capitalized software double counted in capex
# Triggers: FCF_SOFTWARE_DOUBLE_COUNTED
# ---------------------------------------------------------------------------
def make_m03_software_double_counted() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    for fy in sub["forecast"]:
        # Capitalized software (3.5% of rev) added again on top of total 5.0% capex
        fy["capex"] = fy["revenue"] * 0.05 + fy["revenue"] * 0.035
        fy["ufcf"] = fy["nopat"] + fy["da"] - fy["capex"] - fy["delta_nwc"]
        fy["pv_ufcf"] = fy["ufcf"] * fy["discount_factor"]
    sub["analyst"] = "corrupted_m03"
    sub["notes"]["corruption"] = (
        "M03: Capitalized software development costs deducted twice in cash flow schedule."
    )
    return sub


# ---------------------------------------------------------------------------
# M04: Net cash reversed (subtracted from EV instead of added)
# Triggers: EQ_BRIDGE_NET_CASH_REVERSED
# ---------------------------------------------------------------------------
def make_m04_net_cash_reversed() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    ev = sub["dcf_outputs"]["enterprise_value"]
    # Net debt entered as +200 (subtracting positive cash)
    wrong_net_debt = 200.0
    wrong_eq = ev - wrong_net_debt
    wrong_price = wrong_eq / 88.0
    sub["equity_bridge"]["minus_net_debt"] = wrong_net_debt
    sub["equity_bridge"]["equity_value"] = wrong_eq
    sub["equity_bridge"]["implied_share_price"] = wrong_price
    sub["headline"]["dcf_equity_value"] = wrong_eq
    sub["headline"]["dcf_share_price"] = wrong_price
    sub["analyst"] = "corrupted_m04"
    sub["notes"]["corruption"] = (
        "M04: Net cash ($200.0M) subtracted from enterprise value instead of added, "
        "implying equity value is less than enterprise value."
    )
    return sub


# ---------------------------------------------------------------------------
# M05: Stock-based compensation omitted from GAAP EBIT derivation
# Triggers: SBC_EBITDA_INCONSISTENCY
# ---------------------------------------------------------------------------
def make_m05_sbc_ebitda_inconsistency() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    for fy in sub["forecast"]:
        # GAAP EBIT computed as EBITDA - D&A, omitting non-cash SBC deduction
        fy["ebit"] = fy["ebitda"] - fy["da"]
        fy["nopat"] = fy["ebit"] * 0.75
    sub["analyst"] = "corrupted_m05"
    sub["notes"]["corruption"] = (
        "M05: Adjusted EBITDA treated as GAAP EBITDA without deducting SBC to reach GAAP EBIT."
    )
    return sub


# ---------------------------------------------------------------------------
# M06: Basic shares (80M) used instead of fully diluted shares (88M)
# Triggers: SHARES_BASIC_USED
# ---------------------------------------------------------------------------
def make_m06_basic_shares_used() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    eq = sub["equity_bridge"]["equity_value"]
    # Uses 80.0M basic shares instead of 88.0M diluted shares
    wrong_price = eq / 80.0
    sub["equity_bridge"]["diluted_shares"] = 80.0
    sub["equity_bridge"]["implied_share_price"] = wrong_price
    sub["headline"]["dcf_share_price"] = wrong_price
    sub["capital_structure"]["diluted_shares"] = 80.0
    sub["analyst"] = "corrupted_m06"
    sub["notes"]["corruption"] = (
        "M06: Basic common shares (80.0M) used as denominator instead of "
        "fully diluted shares (88.0M)."
    )
    return sub


# ---------------------------------------------------------------------------
# M07: Terminal value discounted at t=4.5 instead of horizon t=5.0
# Triggers: DCF_MIDYEAR_CONVENTION_ERROR
# ---------------------------------------------------------------------------
def make_m07_midyear_convention_error() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    wacc = sub["wacc_outputs"]["wacc"]
    tv_horizon = sub["terminal_value_outputs"]["terminal_value_at_horizon"]
    # Uses t=4.5 exponent for terminal value discounting instead of t=5.0
    wrong_pv_tv = tv_horizon / ((1.0 + wacc) ** 4.5)
    sub["terminal_value_outputs"]["pv_terminal_value"] = wrong_pv_tv
    sub["dcf_outputs"]["pv_terminal_value"] = wrong_pv_tv
    wrong_ev = sub["dcf_outputs"]["sum_pv_ufcf"] + wrong_pv_tv
    sub["dcf_outputs"]["enterprise_value"] = wrong_ev
    sub["equity_bridge"]["enterprise_value"] = wrong_ev
    eq_val = wrong_ev - sub["equity_bridge"]["minus_net_debt"]
    sub["equity_bridge"]["equity_value"] = eq_val
    sub["equity_bridge"]["implied_share_price"] = eq_val / 88.0
    sub["headline"]["dcf_enterprise_value"] = wrong_ev
    sub["headline"]["dcf_equity_value"] = eq_val
    sub["headline"]["dcf_share_price"] = eq_val / 88.0
    sub["analyst"] = "corrupted_m07"
    sub["notes"]["corruption"] = (
        "M07: Terminal Value discounted using mid-year exponent (t=4.5) "
        "rather than horizon (t=5.0)."
    )
    return sub


# ---------------------------------------------------------------------------
# M08: Strata Platform negative FCF peer coerced to 0.0x in comps
# Triggers: COMPS_NM_FCF_COERCED_ZERO
# ---------------------------------------------------------------------------
def make_m08_nm_fcf_coerced_zero() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    for p in sub["comps_inputs"]["peers"]:
        if p["name"] == "Strata Platform":
            p["ntm_ev_ebitda"] = 0.0  # Coerced to 0.0x instead of None (N/M)
    sub["analyst"] = "corrupted_m08"
    sub["notes"]["corruption"] = (
        "M08: Strata Platform negative cash flow multiple coerced to 0.0x instead of N/M (None)."
    )
    return sub


# ---------------------------------------------------------------------------
# M09: Management guidance claim fabricated in submission notes
# Triggers: SF_GUIDANCE_FABRICATED
# ---------------------------------------------------------------------------
def make_m09_fabricated_guidance() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    # Fabricate exact point guidance claim in notes
    sub["notes"]["growth_assumption_2026E"] = (
        "Management guided to 20% revenue growth for full year 2026."
    )
    sub["analyst"] = "corrupted_m09"
    sub["notes"]["corruption"] = (
        "M09: Notes claim 'Management guided to 20% revenue growth' verbatim."
    )
    return sub


# ---------------------------------------------------------------------------
# M10: Pre-tax cost of debt used without tax shield in WACC
# Triggers: WACC_PRETAX_DEBT
# ---------------------------------------------------------------------------
def make_m10_pretax_wacc() -> dict:  # type: ignore[type-arg]
    sub = load_gold()
    kd_pre = sub["wacc_inputs"]["pre_tax_cost_of_debt"]  # 0.055
    ke = sub["wacc_outputs"]["cost_of_equity"]
    we = sub["wacc_inputs"]["equity_weight"]
    wd = sub["wacc_inputs"]["debt_weight"]
    # Use pre-tax Kd directly in after-tax Kd and WACC
    sub["wacc_outputs"]["after_tax_cost_of_debt"] = kd_pre
    wrong_wacc = we * ke + wd * kd_pre
    sub["wacc_outputs"]["wacc"] = wrong_wacc
    sub["analyst"] = "corrupted_m10"
    sub["notes"]["corruption"] = (
        "M10: Pre-tax cost of debt (5.50%) used in WACC without (1 - tax) adjustment."
    )
    return sub


def main() -> None:
    print("Generating 10 corrupted Meridian submission fixtures...")
    write("m01_arr_revenue_confusion", make_m01_arr_revenue_confusion())
    write("m02_deferred_rev_reversed", make_m02_deferred_rev_reversed())
    write("m03_software_double_counted", make_m03_software_double_counted())
    write("m04_net_cash_reversed", make_m04_net_cash_reversed())
    write("m05_sbc_ebitda_inconsistency", make_m05_sbc_ebitda_inconsistency())
    write("m06_basic_shares_used", make_m06_basic_shares_used())
    write("m07_midyear_convention_error", make_m07_midyear_convention_error())
    write("m08_nm_fcf_coerced_zero", make_m08_nm_fcf_coerced_zero())
    write("m09_fabricated_guidance", make_m09_fabricated_guidance())
    write("m10_pretax_wacc", make_m10_pretax_wacc())
    print("Done.")


if __name__ == "__main__":
    main()
