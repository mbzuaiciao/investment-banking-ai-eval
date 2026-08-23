"""Prompt construction for Direct Baseline (M1), Structured Analyst (M2), and Repair (M3)."""

from __future__ import annotations

import json

from ib_eval.case import NorthstarCase
from ib_eval.schemas import GraderFailure, ScoringReport, Submission

DIAGNOSTIC_INVARIANT_GUIDES: dict[str, str] = {
    "SF_GUIDANCE_FABRICATED": (
        "Management guidance was qualitative ('high single digits'); do not classify exact "
        "numerical choices as direct guidance. Set classification to 'analyst_assumption'."
    ),
    "SF_MISSING_PROVENANCE": (
        "Missing provenance records for key financial inputs. Provide explicit provenance records."
    ),
    "REV_QUARTERLY_CONFUSION": (
        "Historical base revenue must use full-year annual figures (2025A = 1000.0), not quarterly "
        "(Q2 = 281.0) or half-year (H1 = 535.0) figures."
    ),
    "REV_GROWTH_OUT_OF_RANGE": (
        "Revenue growth assumption falls outside the defensible range supported by "
        "management guidance."
    ),
    "REV_ARITHMETIC": (
        "Revenue forecast arithmetic inconsistency: Revenue_t must equal "
        "Revenue_(t-1) * (1 + growth_t) for all forecast years."
    ),
    "MARGIN_EBITDA_INCONSISTENCY": (
        "EBITDA arithmetic error: EBITDA_t must equal Revenue_t * EBITDA_Margin_t."
    ),
    "MARGIN_DA_INCONSISTENCY": (
        "D&A percentage calculation error: D&A_t must equal Revenue_t * DA_Margin_t."
    ),
    "MARGIN_EBIT_INCONSISTENCY": (
        "EBIT arithmetic error: EBIT_t must equal EBITDA_t - D&A_t."
    ),
    "FCF_NOPAT_ERROR": (
        "NOPAT formula error: NOPAT_t must equal EBIT_t * (1 - tax_rate)."
    ),
    "FCF_CAPEX_DOUBLE_COUNTED": (
        "Capex was subtracted multiple times or deducted incorrectly."
    ),
    "FCF_CAPEX_ERROR": (
        "Capex calculation error: Capex_t must equal Revenue_t * Capex_pct_t."
    ),
    "FCF_NWC_DELTA_ERROR": (
        "ΔNWC arithmetic error: ΔNWC_t must equal NWC_t - NWC_(t-1)."
    ),
    "FCF_UFCF_ERROR": (
        "UFCF formula error: UFCF_t must equal NOPAT_t + D&A_t - Capex_t - ΔNWC_t."
    ),
    "FCF_PV_ERROR": (
        "PV(UFCF) discounting error: PV(UFCF)_t must equal UFCF_t / (1 + WACC)^t."
    ),
    "WACC_PRETAX_DEBT": (
        "After-tax cost of debt must reflect the interest tax shield: "
        "Kd_after_tax = Kd * (1 - tax_rate)."
    ),
    "WACC_FORMULA_ERROR": (
        "WACC formula error: WACC must equal (We * Ke) + (Wd * Kd_after_tax)."
    ),
    "WACC_WEIGHTS_ERROR": (
        "Capital structure weights must sum to 1.0 (We + Wd = 1.0)."
    ),
    "WACC_KE_ERROR": (
        "Cost of equity CAPM error: Ke = Rf + Beta * ERP."
    ),
    "WACC_KD_ERROR": (
        "After-tax cost of debt error: Kd_after_tax = Kd * (1 - tax_rate)."
    ),
    "TV_NOT_DISCOUNTED": (
        "Terminal value must be discounted back to valuation date (t=0): "
        "PV(TV) = TV / (1 + WACC)^n. Do not add undiscounted TV directly to Enterprise Value."
    ),
    "TV_FORMULA_ERROR": (
        "Terminal value Gordon Growth error: TV = Terminal FCF / (WACC - g), "
        "where Terminal FCF = UFCF_final * (1 + g)."
    ),
    "TV_GROWTH_GT_WACC": (
        "Terminal growth rate g must be strictly less than WACC (g < WACC)."
    ),
    "TV_PV_ERROR": (
        "Terminal value present value discounting error: PV(TV) = TV / (1 + WACC)^n."
    ),
    "EV_SUM_PVUFCF_MISMATCH": (
        "Sum of PV(UFCF) must equal the sum of annual PV(UFCF)_t values."
    ),
    "EV_SUM_ERROR": (
        "Enterprise Value must equal Sum of PV(UFCF) + PV(TV)."
    ),
    "EQ_BRIDGE_CASH_REVERSED": (
        "Cash reduces net debt: Net Debt = Gross Debt - Cash. Do not add cash to debt."
    ),
    "EQ_BRIDGE_DEBT_OMITTED": (
        "Net debt must be deducted from Enterprise Value: "
        "Equity Value = Enterprise Value - Net Debt."
    ),
    "EQ_BRIDGE_NET_DEBT_ERROR": (
        "Net debt arithmetic error: Net Debt = Gross Debt - Cash."
    ),
    "EQ_BRIDGE_ARITHMETIC": (
        "Equity value arithmetic error: Equity Value = Enterprise Value - Net Debt."
    ),
    "EQ_BRIDGE_SHARE_PRICE": (
        "Implied share price error: Implied Share Price = Equity Value / Diluted Shares."
    ),
    "EQ_BRIDGE_EV_MISMATCH": (
        "Equity bridge Enterprise Value must match the DCF Enterprise Value."
    ),
    "COMPS_NM_COERCED_ZERO": (
        "Non-meaningful (N/M) peer multiple (negative EBITDA) must be excluded from "
        "median calculation, not coerced to 0.0x."
    ),
    "COMPS_MEDIAN_ERROR": (
        "Peer multiple median calculated incorrectly across valid peers."
    ),
    "COMPS_EV_ARITHMETIC": (
        "Comps EV arithmetic error: Comps EV = Median Multiple * Target EBITDA."
    ),
    "COMPS_EQUITY_ARITHMETIC": (
        "Comps Equity Value arithmetic error: Equity Value = Comps EV - Net Debt."
    ),
    "COMPS_SHARE_PRICE_ERROR": (
        "Comps implied share price arithmetic error: Share Price = Comps Equity / Diluted Shares."
    ),
    "CONSISTENCY_HEADLINE_DCF": (
        "Headline DCF outputs must match detailed DCF model values exactly."
    ),
    "CONSISTENCY_HEADLINE_COMPS": (
        "Headline Comps outputs must match detailed Comps model values exactly."
    ),
    "CONSISTENCY_EV_BRIDGE": (
        "Equity bridge Enterprise Value must match DCF Enterprise Value."
    ),
    "CONSISTENCY_SHARES": (
        "Diluted shares count must be identical across all model sections."
    ),
}


def _load_sources_block(case: NorthstarCase) -> str:
    """Format all markdown documents in the case sources directory."""
    sources_dir = case.case_dir / "sources"
    source_files = sorted(sources_dir.glob("*.md"))

    sources_text_blocks: list[str] = []
    for sf in source_files:
        content = sf.read_text().strip()
        sources_text_blocks.append(f"--- DOCUMENT: {sf.name} ---\n{content}")

    return "\n\n".join(sources_text_blocks)


def build_analyst_prompt(case: NorthstarCase) -> str:
    """Build the direct analyst prompt containing case sources and submission schema.

    Contains no hidden ground-truth valuation values, tolerances, or diagnostic codes.
    """
    all_sources = _load_sources_block(case)
    schema_json = json.dumps(Submission.model_json_schema(), indent=2)

    prompt = f"""You are an investment-banking analyst.
Review the supplied source packet for {case.meta.company}
and produce a complete, structured valuation submission in JSON format.

## General Instructions

1. **Evidence-Based Modeling**: Use only the facts and guidance provided in the source packet below.
2. **Provenance & Assumptions**: Clearly classify each input as:
   - `direct`: an explicit statement directly transcribed from the source.
   - `derived`: calculated directly from historical or stated financial items.
   - `analyst_assumption`: an interpretive judgment or forward projection made by the analyst.
   Never classify an analyst assumption as direct source guidance (e.g. if management provides
   qualitative guidance such as "high single digits", do not claim management stated a specific
   exact percentage).
3. **Financial Consistency**:
   - Ensure all DCF projections (Revenue, EBITDA, D&A, EBIT, NOPAT, Capex, NWC, ΔNWC, UFCF)
     are internally consistent and mathematically reconciled.
   - Calculate WACC using CAPM and after-tax cost of debt: WACC = We × Ke + Wd × Kd × (1 − t).
   - Compute terminal value using perpetual growth (Gordon Growth) and discount to valuation date.
   - Ensure the equity bridge (EV − Net Debt = Equity Value) and implied share price
     (Equity Value / Diluted Shares) correctly reflect capital structure.
   - In comparable companies analysis, exclude non-meaningful (N/M) multiples from median
     calculations and do not treat N/M peers as zero. Disclose any fiscal year end differences.
   - Ensure headline valuation outputs match the underlying detailed DCF and comps models.

## Case Information
- Company: {case.meta.company}
- Industry: {case.meta.industry}
- Valuation Date: {case.meta.valuation_date}
- Currency: {case.meta.currency}
- Units: {case.meta.units}

## Source Packet

{all_sources}

## Submission Schema

Your response must be a single, valid JSON object matching the following JSON Schema:

```json
{schema_json}
```

Return ONLY the raw JSON object conforming to this schema (or inside a ```json ``` block).
Do not include conversational filler.
"""
    return prompt.strip()


def build_structured_analyst_prompt(case: NorthstarCase) -> str:
    """Build the Milestone 2 structured analyst prompt.

    Guides the model through an explicit 8-stage financial workflow before
    generating the canonical submission. Contains zero ground-truth leakage.
    """
    all_sources = _load_sources_block(case)
    schema_json = json.dumps(Submission.model_json_schema(), indent=2)

    prompt = f"""You are an investment-banking analyst.
Review the supplied source packet for {case.meta.company} and produce a complete,
structured valuation submission in JSON format.

Follow the structured 8-stage financial analysis workflow detailed below.

---

## 8-Stage Financial Analysis Workflow

### Stage 1 — Source Extraction & Fact Provenance
Extract all relevant quantitative and qualitative data from the source packet:
- Historical income statement and balance sheet items (2023A–2025A).
- Management guidance statements and forward expectations.
- Capital structure details (gross debt, cash balances, convertible instruments, share counts).
- Market parameters for WACC (risk-free rate, equity risk premium, beta, pre-tax debt cost).
- Comparable peer universe (trading multiples, profitability status).

For every key parameter, explicitly establish its provenance:
- direct: an explicit number directly stated in the source documents.
- derived: calculated directly from historical financial statements.
- analyst_assumption: forward-looking projection or judgment choice made by the analyst.
Crucial Rule: Do not classify an analyst judgment as direct guidance (e.g. if management
states qualitative "high single digits" revenue growth, the exact percentage chosen is an
analyst_assumption, not a direct fact).

### Stage 2 — Assumption Ledger
Explicitly formalize all modeling assumptions before performing calculations:
- 5-year forecast revenue growth trajectory (2026E–2030E).
- Operating profitability: EBITDA margins, D&A schedule (% of revenue), EBIT margins.
- Tax rate: effective corporate tax rate.
- Reinvestment parameters: Capex (% of revenue), Net Working Capital (% of revenue).
- WACC parameters: risk-free rate, ERP, beta, cost of debt, target capital structure weights.
- Perpetual terminal growth rate (g).

### Stage 3 — 5-Year Forecast Schedules (2026E–2030E)
For each projection year t in [2026E..2030E], compute and verify the exact forecast schedule:
1. Revenue_t = Revenue_(t-1) * (1 + growth_t)
2. EBITDA_t = Revenue_t * EBITDA_Margin_t
3. DA_t = Revenue_t * DA_Margin_t
4. EBIT_t = EBITDA_t - DA_t
5. NOPAT_t = EBIT_t * (1 - tax_rate)
6. Capex_t = Revenue_t * Capex_pct_t
7. NWC_t = Revenue_t * NWC_pct_t
8. Delta_NWC_t = NWC_t - NWC_(t-1)
9. UFCF_t = NOPAT_t + DA_t - Capex_t - Delta_NWC_t
10. Discount_Factor_t = 1 / (1 + WACC)^t
11. PV(UFCF)_t = UFCF_t * Discount_Factor_t

### Stage 4 — WACC Derivation
Reconcile and compute the weighted average cost of capital:
1. Cost of Equity (Ke) = Rf + (Beta * ERP)
2. After-Tax Cost of Debt (Kd_after_tax) = Kd * (1 - tax_rate)
3. Ensure capital structure weights sum to 1.0: We + Wd = 1.0
4. WACC = (We * Ke) + (Wd * Kd_after_tax)

### Stage 5 — Terminal Value Calculation & Present Value Discounting
Explicitly compute the terminal value and discount it to the valuation date:
1. Normalized Terminal Cash Flow:
   Terminal FCF = UFCF_2030E * (1 + g)
2. Terminal Value at Horizon (T = 5):
   TV = Terminal FCF / (WACC - g)  [ensure g < WACC]
3. Present Value of Terminal Value at Valuation Date (T = 0):
   PV(TV) = TV / (1 + WACC)^5 = TV * Discount_Factor_5
Critical Warning: Terminal value must be discounted back to the valuation date.
Do not add undiscounted TV to Enterprise Value.

### Stage 6 — Enterprise Value & Equity Bridge
Reconcile the enterprise-to-equity valuation bridge:
1. Enterprise Value (EV) = Sum(PV(UFCF)_t for t=1..5) + PV(TV)
2. Net Debt = Gross Debt - Cash  (Cash reduces net debt; do NOT add cash to debt)
3. Equity Value = Enterprise Value - Net Debt
4. Implied Share Price = Equity Value / Diluted Shares Outstanding

### Stage 7 — Comparable Companies Analysis (Trading Comps)
1. Exclude non-meaningful (N/M) multiples (e.g. peers with negative EBITDA) from the peer
   median calculation. Do not coerce negative or non-meaningful peers to 0.0x.
2. Calculate the benchmark median multiple across valid peers.
3. Explicitly note fiscal year end differences where applicable.
4. Bridge Comps Enterprise Value (Median Multiple * Target EBITDA) to Equity Value
   (EV - Net Debt) and implied per-share value.

### Stage 8 — Final Invariant Pre-Submission Self-Check
Before generating your final JSON output, verify each internal invariant:
- [ ] 1. Revenue arithmetic: Revenue_t = Revenue_(t-1) * (1 + growth_t) for all forecast years.
- [ ] 2. Operating margins: EBITDA_t = Revenue_t * margin_t.
- [ ] 3. Operating profit: EBIT_t = EBITDA_t - DA_t.
- [ ] 4. After-tax earnings: NOPAT_t = EBIT_t * (1 - tax_rate).
- [ ] 5. UFCF formula: UFCF_t = NOPAT_t + DA_t - Capex_t - Delta_NWC_t.
- [ ] 6. WACC components: Ke uses CAPM; Kd incorporates tax shield; weights sum to 100%.
- [ ] 7. Terminal FCF: Correctly escalated by (1 + g) from 2030E UFCF.
- [ ] 8. Terminal Value formula: TV = Terminal FCF / (WACC - g).
- [ ] 9. Terminal Value discounting: PV(TV) = TV * (1 / (1 + WACC)^5).
- [ ] 10. Equity bridge: Net Debt = Debt - Cash, Equity = EV - Net Debt, Price = Equity / Shares.
- [ ] 11. Trading comps: N/M peer excluded from median; fiscal year differences disclosed.
- [ ] 12. Cross-artifact consistency: Headline values match detailed model schedules exactly.

---

## Case Information
- Company: {case.meta.company}
- Industry: {case.meta.industry}
- Valuation Date: {case.meta.valuation_date}
- Currency: {case.meta.currency}
- Units: {case.meta.units}

## Source Packet

{all_sources}

## Submission Schema

Your response must be a single, valid JSON object matching the following JSON Schema:

```json
{schema_json}
```

Return ONLY the raw JSON object conforming to this schema (or inside a ```json ``` block).
Do not include conversational filler.
"""
    return prompt.strip()


def build_repair_prompt(
    case: NorthstarCase,
    initial_submission: Submission,
    grade_report: ScoringReport,
) -> str:
    """Build the Milestone 3 deterministic feedback repair prompt.

    Contains initial submission JSON, machine-readable diagnostic feedback,
    and instructions to recompute all dependent fields without leaking gold benchmark answers.
    """
    initial_sub_json = json.dumps(initial_submission.model_dump(), indent=2)
    schema_json = json.dumps(Submission.model_json_schema(), indent=2)

    all_failures: list[GraderFailure] = []
    seen_failures: set[tuple[str, str, str]] = set()
    for g_res in grade_report.grader_results:
        for f in g_res.failures:
            key = (f.diagnostic_code, f.metric, str(f.observed))
            if key not in seen_failures:
                seen_failures.add(key)
                all_failures.append(f)

    diag_blocks: list[str] = []
    for f in all_failures:
        code = f.diagnostic_code
        guide = DIAGNOSTIC_INVARIANT_GUIDES.get(
            code,
            f.message or "A valuation invariant or arithmetic constraint was violated.",
        )
        obs_val = f.observed if f.observed is not None else "N/A"
        diag_blocks.append(
            f"- **DIAGNOSTIC**: `{code}`\n"
            f"  - Severity: `{f.severity}`\n"
            f"  - Affected Metric: `{f.metric}`\n"
            f"  - Your Submitted Value: `{obs_val}`\n"
            f"  - Violated Invariant & Correction Rule: {guide}"
        )

    diagnostics_text = "\n\n".join(diag_blocks) if diag_blocks else "No failures detected."

    prompt = f"""You previously submitted an investment-banking valuation for {case.meta.company}.

The evaluation harness graded your initial submission and identified the following errors:

## Deterministic Grader Diagnostics

{diagnostics_text}

---

## Your Previous Submission

```json
{initial_sub_json}
```

---

## Revision Instructions

Revise your submission to fix all identified errors.

### Critical Requirements:
1. **Preserve Valid Assumptions**: Do not change valid historical facts or defensible assumptions
   unless a diagnostic specifically requires doing so.
2. **Recompute All Downstream Dependent Values**: A fix to an upstream metric (such as Revenue,
   NOPAT, Capex, ΔNWC, UFCF, WACC, or Terminal Value) cascades into all downstream outputs.
   You must explicitly recalculate:
   - Forecast Free Cash Flows (UFCF_t) and Discount Factors
   - Terminal FCF (UFCF_2030E * (1 + g)) and Terminal Value (TV)
   - Present Value of Terminal Value (PV(TV) = TV / (1 + WACC)^5) discounted to valuation date
   - Enterprise Value (EV = Sum PV(UFCF) + PV(TV))
   - Net Debt (Gross Debt - Cash) and Equity Value (EV - Net Debt)
   - Implied Share Price (Equity Value / Diluted Shares)
3. **Cross-Artifact Consistency**: Ensure headline valuation outputs match your detailed DCF and
   Comparable Companies model schedules exactly.
4. **No Fabricated Evidence**: Use only stated facts from the Northstar case sources.
5. **Single Complete Submission**: Return one complete canonical JSON object matching the schema.

## Submission Schema

```json
{schema_json}
```

Return ONLY the raw JSON object conforming to this schema (or inside a ```json ``` block).
Do not include conversational filler.
"""
    return prompt.strip()
