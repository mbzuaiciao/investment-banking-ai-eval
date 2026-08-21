"""Prompt construction for Milestone 1 Direct Analyst Baseline."""

from __future__ import annotations

import json

from ib_eval.case import NorthstarCase
from ib_eval.schemas import Submission


def build_analyst_prompt(case: NorthstarCase) -> str:
    """Build the direct analyst prompt containing case sources and submission schema.

    Contains no hidden ground-truth valuation values, tolerances, or diagnostic codes.
    """
    sources_dir = case.case_dir / "sources"
    source_files = sorted(sources_dir.glob("*.md"))

    sources_text_blocks: list[str] = []
    for sf in source_files:
        content = sf.read_text().strip()
        sources_text_blocks.append(f"--- DOCUMENT: {sf.name} ---\n{content}")

    all_sources = "\n\n".join(sources_text_blocks)
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
