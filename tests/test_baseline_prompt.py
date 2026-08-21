"""Tests for prompt construction and ground-truth leakage safeguards."""

from __future__ import annotations

from pathlib import Path

from ib_eval.baseline.prompt import build_analyst_prompt
from ib_eval.case import load_case

_CASE_DIR = Path(__file__).parent.parent / "cases" / "northstar-v1"


def test_prompt_includes_case_metadata() -> None:
    """Prompt must include public case metadata."""
    case = load_case(_CASE_DIR)
    prompt = build_analyst_prompt(case)

    assert "Northstar Components, Inc." in prompt
    assert "industrial components" in prompt
    assert "2026-06-30" in prompt
    assert "USD" in prompt


def test_prompt_includes_all_source_documents() -> None:
    """Prompt must contain all four source documents from the case."""
    case = load_case(_CASE_DIR)
    prompt = build_analyst_prompt(case)

    assert "DOCUMENT: management_guidance.md" in prompt
    assert "DOCUMENT: quarterly_report.md" in prompt
    assert "DOCUMENT: income_statement.md" in prompt
    assert "DOCUMENT: capital_structure.md" in prompt

    # Specific evidence items from sources
    assert "high single digits" in prompt
    assert "281.0" in prompt  # Q2 revenue trap
    assert "535.0" in prompt  # H1 revenue trap
    assert "Evergreen Controls" in prompt
    assert "Crestline Systems" in prompt


def test_prompt_includes_submission_schema() -> None:
    """Prompt must include the JSON Schema for Submission."""
    case = load_case(_CASE_DIR)
    prompt = build_analyst_prompt(case)

    assert "$defs" in prompt or "properties" in prompt
    assert "wacc_inputs" in prompt
    assert "dcf_outputs" in prompt
    assert "equity_bridge" in prompt
    assert "comps_inputs" in prompt
    assert "headline" in prompt
    assert "provenance" in prompt


def test_no_ground_truth_leakage() -> None:
    """SAFEGUARD: Prompt must NOT leak gold valuation answers, diagnostic codes, or tolerances."""
    case = load_case(_CASE_DIR)
    prompt = build_analyst_prompt(case)

    # 1. Exact canonical DCF valuation answers must not appear in prompt
    forbidden_values = [
        "1712.9659",
        "1712.97",
        "1,712.97",
        "1387.9659",
        "1387.97",
        "1,387.97",
        "23.1328",
        "23.13",
        "1285.5341",
        "427.4318",
        "2003.7826",
    ]
    for val in forbidden_values:
        assert val not in prompt, f"Prompt leaked canonical gold value: {val}"

    # 2. Comps canonical final answers must not appear in prompt
    forbidden_comps = [
        "1505.52",
        "1180.52",
        "19.6753",
        "19.68",
    ]
    for val in forbidden_comps:
        assert val not in prompt, f"Prompt leaked canonical comps answer: {val}"

    # 3. Diagnostic error codes must not appear in prompt
    forbidden_diagnostics = [
        "SF_GUIDANCE_FABRICATED",
        "SF_MISSING_PROVENANCE",
        "REV_QUARTERLY_CONFUSION",
        "REV_GROWTH_OUT_OF_RANGE",
        "MARGIN_EBITDA_INCONSISTENCY",
        "MARGIN_EBIT_INCONSISTENCY",
        "FCF_CAPEX_DOUBLE_COUNTED",
        "WACC_PRETAX_DEBT",
        "TV_NOT_DISCOUNTED",
        "EQ_BRIDGE_CASH_REVERSED",
        "EQ_BRIDGE_DEBT_OMITTED",
        "COMPS_NM_COERCED_ZERO",
        "CONSISTENCY_HEADLINE_DCF",
    ]
    for code in forbidden_diagnostics:
        assert code not in prompt, f"Prompt leaked internal diagnostic code: {code}"

    # 4. Rubric tolerance names must not appear in prompt
    forbidden_rubric_items = [
        "revenue_abs",
        "margin_abs",
        "fcf_abs",
        "wacc_abs",
        "tv_rel",
        "equity_abs",
        "hard_failure_codes",
    ]
    for item in forbidden_rubric_items:
        assert item not in prompt, f"Prompt leaked internal rubric configuration: {item}"
