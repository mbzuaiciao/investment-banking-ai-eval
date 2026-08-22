"""Prompt construction for Milestone 1 Direct Baseline and Milestone 2 Structured Analyst."""

from __future__ import annotations

import json

from ib_eval.case import NorthstarCase
from ib_eval.schemas import Submission


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
