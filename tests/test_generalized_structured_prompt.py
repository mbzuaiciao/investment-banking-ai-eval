"""Tests for generalized structured analyst prompt (structured_v2).

Verifies that:
1. Northstar structured prompt directs the model to all 8 stages without Northstar hardcoding.
2. Meridian structured prompt does not hardcode EBITDA-D&A or EBITDA-comps formulas.
3. Both prompts instruct model to reconcile case-specific bridges and primary comps metrics.
4. No gold benchmark values or diagnostic codes are leaked.
"""

from __future__ import annotations

from pathlib import Path

from ib_eval.baseline.prompt import (
    STRUCTURED_PROMPT_VERSION,
    build_structured_analyst_prompt,
)
from ib_eval.case import load_case


def test_northstar_structured_prompt_regression() -> None:
    """Northstar structured prompt preserves the 8-stage workflow without hardcoded equations."""
    case = load_case(Path("cases/northstar-v1"))
    prompt = build_structured_analyst_prompt(case)

    # 8 stages present
    assert "Stage 1 — Source Extraction" in prompt
    assert "Stage 2 — Assumption Ledger" in prompt
    assert "Stage 3 — 5-Year Forecast Schedules" in prompt
    assert "Stage 4 — WACC Derivation" in prompt
    assert "Stage 5 — Terminal Value Calculation" in prompt
    assert "Stage 6 — Enterprise Value & Equity Bridge" in prompt
    assert "Stage 7 — Comparable Companies Analysis" in prompt
    assert "Stage 8 — Final Invariant Pre-Submission Self-Check" in prompt

    # No hardcoded Northstar-only equation
    assert "EBIT_t = EBITDA_t - DA_t" not in prompt

    # Case-generalized instructions present
    assert "reconcile" in prompt.lower()
    assert "GAAP EBIT" in prompt
    assert "Reconcile the reported profitability metric to GAAP EBIT" in prompt
    assert "Median Multiple * Target Metric" in prompt

    # DCF / WACC / Terminal / Bridge / Comps universal structures
    assert "Cost of Equity (Ke) = Rf + (Beta * ERP)" in prompt
    assert "After-Tax Cost of Debt" in prompt
    assert "Terminal Value at Horizon" in prompt
    assert "Enterprise Value (EV) = Sum(PV(UFCF)" in prompt
    assert "Net Debt = Gross Debt - Cash" in prompt

    # Purity: no gold values leaked
    assert "1712.97" not in prompt
    assert "1387.97" not in prompt
    assert "23.13" not in prompt


def test_meridian_structured_prompt_generalization() -> None:
    """Meridian structured prompt contains case-aware guidance without hardcoded assumptions."""
    case = load_case(Path("cases/meridian-v1"))
    prompt = build_structured_analyst_prompt(case)

    # 8 stages present
    for stage_num in range(1, 9):
        assert f"Stage {stage_num}" in prompt

    # Does NOT contain Northstar hardcoded formulas
    assert "EBIT_t = EBITDA_t - DA_t" not in prompt
    assert "Median Multiple * Target EBITDA" not in prompt
    assert "Target EBITDA" not in prompt

    # DOES contain generalized reconciliation instructions
    assert "carefully distinguish GAAP vs. non-GAAP / adjusted metrics" in prompt
    assert "Reconcile the reported profitability metric to GAAP EBIT" in prompt
    assert "Identify the primary valuation multiple and target metric" in prompt
    assert "Median Multiple * Target Metric" in prompt
    assert "GAAP EBIT" in prompt

    # Purity: no Meridian DCF gold answers leaked in instructions
    assert "1375.92" not in prompt  # Gold DCF EV
    assert "1575.92" not in prompt  # Gold DCF Equity
    assert "17.91" not in prompt  # Gold DCF Share Price
    assert "SBC_EBITDA_INCONSISTENCY" not in prompt  # No diagnostic codes leaked


def test_prompt_version_constant() -> None:
    """Structured prompt version is defined as structured_v2."""
    assert STRUCTURED_PROMPT_VERSION == "structured_v2"
