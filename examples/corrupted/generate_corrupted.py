#!/usr/bin/env python3
"""Generate all 10 corrupted submission fixtures for IB-Eval.

Run with:
    uv run python examples/corrupted/generate_corrupted.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

GOLD_PATH = Path(__file__).parent.parent / "gold_submission" / "submission.json"
OUT_DIR = Path(__file__).parent


def load_gold() -> dict:  # type: ignore[type-arg]
    return json.loads(GOLD_PATH.read_text())


def write(name: str, submission: dict) -> None:  # type: ignore[type-arg]
    d = OUT_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "submission.json").write_text(json.dumps(submission, indent=2))
    print(f"  Wrote {name}/submission.json")


# ---------------------------------------------------------------------------
# C01: Q2 revenue used as 2026E annual revenue
# ---------------------------------------------------------------------------
def make_c01_quarterly_revenue() -> dict:  # type: ignore[type-arg]
    """Revenue confused: 2026E revenue set to Q2 standalone ($281mm)."""
    sub = load_gold()
    # Replace 2026E revenue with Q2 value and propagate errors
    for fy in sub["forecast"]:
        if fy["year"] == 2026:
            fy["revenue"] = 281.0  # Q2 standalone — wrong!
            fy["ebitda"] = 281.0 * fy["ebitda_margin"]
            fy["da"] = 281.0 * 0.04
            fy["ebit"] = fy["ebitda"] - fy["da"]
            fy["nopat"] = fy["ebit"] * 0.75
            fy["capex"] = 281.0 * 0.045
            fy["nwc"] = 281.0 * 0.12
            fy["delta_nwc"] = fy["nwc"] - 120.0
            fy["ufcf"] = fy["nopat"] + fy["da"] - fy["capex"] - fy["delta_nwc"]
            fy["pv_ufcf"] = fy["ufcf"] * fy["discount_factor"]
    sub["analyst"] = "corrupted_c01"
    sub["notes"]["corruption"] = (
        "C01: 2026E revenue incorrectly set to Q2 standalone revenue ($281mm) "
        "instead of annual projection."
    )
    return sub


# ---------------------------------------------------------------------------
# C02: Terminal value not discounted
# ---------------------------------------------------------------------------
def make_c02_tv_not_discounted() -> dict:  # type: ignore[type-arg]
    """TV at horizon used directly as PV(TV) without discounting."""
    sub = load_gold()
    tv_at_horizon = sub["terminal_value_outputs"]["terminal_value_at_horizon"]
    # Use TV at horizon directly as PV — forgetting to discount
    sub["terminal_value_outputs"]["pv_terminal_value"] = tv_at_horizon
    sub["dcf_outputs"]["pv_terminal_value"] = tv_at_horizon
    # Recalculate EV with wrong PV(TV)
    wrong_ev = sub["dcf_outputs"]["sum_pv_ufcf"] + tv_at_horizon
    sub["dcf_outputs"]["enterprise_value"] = wrong_ev
    sub["equity_bridge"]["enterprise_value"] = wrong_ev
    eq_val = wrong_ev - sub["equity_bridge"]["minus_net_debt"]
    sub["equity_bridge"]["equity_value"] = eq_val
    sub["equity_bridge"]["implied_share_price"] = eq_val / 60.0
    sub["headline"]["dcf_enterprise_value"] = wrong_ev
    sub["headline"]["dcf_equity_value"] = eq_val
    sub["headline"]["dcf_share_price"] = eq_val / 60.0
    sub["analyst"] = "corrupted_c02"
    sub["notes"]["corruption"] = (
        "C02: Terminal value at horizon used directly as PV(TV) — discounting step omitted."
    )
    return sub


# ---------------------------------------------------------------------------
# C03: Cash subtracted instead of added in equity bridge
# ---------------------------------------------------------------------------
def make_c03_cash_subtracted() -> dict:  # type: ignore[type-arg]
    """Net debt computed as gross_debt + cash (cash reversed)."""
    sub = load_gold()
    gross_debt = 420.0
    cash = 95.0
    wrong_net_debt = gross_debt + cash  # 515 instead of 325
    ev = sub["dcf_outputs"]["enterprise_value"]
    wrong_eq = ev - wrong_net_debt
    wrong_price = wrong_eq / 60.0
    sub["equity_bridge"]["minus_net_debt"] = wrong_net_debt
    sub["equity_bridge"]["equity_value"] = wrong_eq
    sub["equity_bridge"]["implied_share_price"] = wrong_price
    sub["headline"]["dcf_equity_value"] = wrong_eq
    sub["headline"]["dcf_share_price"] = wrong_price
    sub["analyst"] = "corrupted_c03"
    sub["notes"]["corruption"] = (
        "C03: Cash added to gross debt (net_debt = 420 + 95 = 515) "
        "instead of subtracted (420 - 95 = 325)."
    )
    return sub


# ---------------------------------------------------------------------------
# C04: Debt omitted from equity bridge
# ---------------------------------------------------------------------------
def make_c04_debt_omitted() -> dict:  # type: ignore[type-arg]
    """Net debt set to zero — all debt omitted."""
    sub = load_gold()
    ev = sub["dcf_outputs"]["enterprise_value"]
    wrong_net_debt = 0.0
    wrong_eq = ev - wrong_net_debt  # equity = EV
    wrong_price = wrong_eq / 60.0
    sub["equity_bridge"]["minus_net_debt"] = wrong_net_debt
    sub["equity_bridge"]["equity_value"] = wrong_eq
    sub["equity_bridge"]["implied_share_price"] = wrong_price
    sub["headline"]["dcf_equity_value"] = wrong_eq
    sub["headline"]["dcf_share_price"] = wrong_price
    sub["analyst"] = "corrupted_c04"
    sub["notes"]["corruption"] = (
        "C04: Net debt omitted from equity bridge (set to 0). Equity value = EV."
    )
    return sub


# ---------------------------------------------------------------------------
# C05: N/M peer (Evergreen) treated as zero multiple
# ---------------------------------------------------------------------------
def make_c05_nm_peer_zero() -> dict:  # type: ignore[type-arg]
    """Evergreen Controls assigned 0.0 EV/EBITDA instead of None."""
    sub = load_gold()
    for peer in sub["comps_inputs"]["peers"]:
        if peer["name"] == "Evergreen Controls":
            peer["ntm_ev_ebitda"] = 0.0  # coerced to zero — wrong!
            peer["ltm_ev_ebitda"] = 0.0
            peer["excluded"] = False
            peer["exclusion_reason"] = ""
    # Recompute median with zero included: [7.9, 8.5, 9.2, 7.3, 0.0]
    # sorted: [0.0, 7.3, 7.9, 8.5, 9.2] → median = 7.9
    wrong_median = 7.9  # median including 0
    sub["comps_outputs"]["ntm_median"] = wrong_median
    ebitda_2026 = sub["comps_inputs"]["applied_ebitda"]
    wrong_ev = wrong_median * ebitda_2026
    wrong_eq = wrong_ev - 325.0
    wrong_price = wrong_eq / 60.0
    sub["comps_inputs"]["applied_multiple"] = wrong_median
    sub["comps_outputs"]["enterprise_value"] = wrong_ev
    sub["comps_outputs"]["equity_value"] = wrong_eq
    sub["comps_outputs"]["implied_share_price"] = wrong_price
    sub["headline"]["comps_enterprise_value"] = wrong_ev
    sub["headline"]["comps_equity_value"] = wrong_eq
    sub["headline"]["comps_share_price"] = wrong_price
    sub["analyst"] = "corrupted_c05"
    sub["notes"]["corruption"] = (
        "C05: Evergreen Controls N/M EV/EBITDA coerced to 0.0, "
        "included in median calculation."
    )
    return sub


# ---------------------------------------------------------------------------
# C06: Fabricated guidance — claims management stated exactly 8%
# ---------------------------------------------------------------------------
def make_c06_fabricated_guidance() -> dict:  # type: ignore[type-arg]
    """Provenance record claims management guided to 8% as direct fact."""
    sub = load_gold()
    for rec in sub["provenance"]:
        if rec["metric"] == "revenue_growth" and rec["period"] == "2026E":
            rec["classification"] = "direct"  # Should be analyst_assumption!
            rec["note"] = (
                "Management guided to 8% revenue growth for FY2026."
            )
            rec["confidence"] = 1.0
    sub["analyst"] = "corrupted_c06"
    sub["notes"]["corruption"] = (
        "C06: revenue_growth/2026E provenance classified as 'direct' — "
        "fabricated claim that management stated exactly 8%."
    )
    return sub


# ---------------------------------------------------------------------------
# C07: EBITDA / D&A / EBIT inconsistency
# ---------------------------------------------------------------------------
def make_c07_ebitda_inconsistency() -> dict:  # type: ignore[type-arg]
    """EBIT does not equal EBITDA - D&A in 2026E."""
    sub = load_gold()
    for fy in sub["forecast"]:
        if fy["year"] == 2026:
            # EBITDA and D&A are correct, but EBIT is set wrong
            fy["ebit"] = fy["ebitda"] - fy["da"] + 15.0  # +15 error
            # NOPAT derived from wrong EBIT
            fy["nopat"] = fy["ebit"] * 0.75
            # UFCF recomputed with wrong NOPAT
            fy["ufcf"] = fy["nopat"] + fy["da"] - fy["capex"] - fy["delta_nwc"]
            fy["pv_ufcf"] = fy["ufcf"] * fy["discount_factor"]
    sub["analyst"] = "corrupted_c07"
    sub["notes"]["corruption"] = (
        "C07: 2026E EBIT set 15mm higher than EBITDA - D&A — accounting inconsistency."
    )
    return sub


# ---------------------------------------------------------------------------
# C08: Capex double counted
# ---------------------------------------------------------------------------
def make_c08_capex_double_counted() -> dict:  # type: ignore[type-arg]
    """Capex appears twice in 2026E UFCF calculation."""
    sub = load_gold()
    for fy in sub["forecast"]:
        if fy["year"] == 2026:
            fy["capex"] = fy["capex"] * 2  # doubled
            fy["ufcf"] = fy["nopat"] + fy["da"] - fy["capex"] - fy["delta_nwc"]
            fy["pv_ufcf"] = fy["ufcf"] * fy["discount_factor"]
    sub["analyst"] = "corrupted_c08"
    sub["notes"]["corruption"] = (
        "C08: 2026E capex double-counted (48.6 instead of 48.6... wait, "
        "capex = 2 × 4.5% × revenue)."
    )
    return sub


# ---------------------------------------------------------------------------
# C09: Headline valuation inconsistent with model output
# ---------------------------------------------------------------------------
def make_c09_headline_mismatch() -> dict:  # type: ignore[type-arg]
    """Headline DCF equity value differs from equity bridge."""
    sub = load_gold()
    # Headline shows a different (higher) equity value
    sub["headline"]["dcf_equity_value"] = 1578.0  # wrong
    sub["headline"]["dcf_share_price"] = 1578.0 / 60.0  # wrong
    sub["analyst"] = "corrupted_c09"
    sub["notes"]["corruption"] = (
        "C09: Headline DCF equity value ($1,578mm) inconsistent with "
        "equity bridge ($1,387.97mm)."
    )
    return sub


# ---------------------------------------------------------------------------
# C10: WACC computed using pre-tax cost of debt (no tax shield)
# ---------------------------------------------------------------------------
def make_c10_pretax_wacc() -> dict:  # type: ignore[type-arg]
    """WACC uses pre-tax cost of debt instead of after-tax."""
    sub = load_gold()
    # Pre-tax Kd = 6.2%, after-tax = 4.65%
    pre_tax_kd = 0.062
    ke = sub["wacc_outputs"]["cost_of_equity"]
    wrong_wacc = 0.78 * ke + 0.22 * pre_tax_kd  # no tax shield
    sub["wacc_outputs"]["after_tax_cost_of_debt"] = pre_tax_kd  # wrong
    sub["wacc_outputs"]["wacc"] = wrong_wacc
    sub["analyst"] = "corrupted_c10"
    sub["notes"]["corruption"] = (
        f"C10: WACC computed with pre-tax cost of debt ({pre_tax_kd:.1%}) "
        f"without tax adjustment. Wrong WACC = {wrong_wacc:.4%}."
    )
    return sub


if __name__ == "__main__":
    print("Generating corrupted fixtures...")
    corruptions = [
        ("c01_quarterly_revenue", make_c01_quarterly_revenue),
        ("c02_tv_not_discounted", make_c02_tv_not_discounted),
        ("c03_cash_subtracted", make_c03_cash_subtracted),
        ("c04_debt_omitted", make_c04_debt_omitted),
        ("c05_nm_peer_zero", make_c05_nm_peer_zero),
        ("c06_fabricated_guidance", make_c06_fabricated_guidance),
        ("c07_ebitda_inconsistency", make_c07_ebitda_inconsistency),
        ("c08_capex_double_counted", make_c08_capex_double_counted),
        ("c09_headline_mismatch", make_c09_headline_mismatch),
        ("c10_pretax_wacc", make_c10_pretax_wacc),
    ]
    for name, fn in corruptions:
        write(name, fn())
    print("Done.")
