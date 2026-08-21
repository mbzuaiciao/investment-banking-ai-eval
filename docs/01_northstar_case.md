# Chapter 01 — Understanding the Northstar Case

Welcome to your first case briefing as an analyst.

This chapter walks through **Northstar Components, Inc.**, the synthetic target company at the heart of our evaluation suite.

---

## 1. Company Profile & Overview

- **Company**: Northstar Components, Inc.
- **Industry**: Industrial Components & Automation Parts
- **Valuation Date**: June 30, 2026
- **Fiscal Year End**: December 31
- **Units**: USD Millions (except share count and per-share figures)

Northstar manufactures precision industrial components for robotics, factory automation, and heavy machinery. The company has demonstrated steady historical growth and margin improvement following a corporate restructuring program in 2025.

---

## 2. The Evidence Packet

An analyst (human or AI) evaluating Northstar receives four source documents located in `cases/northstar-v1/sources/`:

1. **[`management_guidance.md`](../cases/northstar-v1/sources/management_guidance.md)**: Qualitative forward-looking outlook for FY2026.
2. **[`quarterly_report.md`](../cases/northstar-v1/sources/quarterly_report.md)**: Q2 2026 unaudited financial statements and interim balance sheet.
3. **[`income_statement.md`](../cases/northstar-v1/sources/income_statement.md)**: Annual historical GAAP income statements for 2023A, 2024A, and 2025A.
4. **[`capital_structure.md`](../cases/northstar-v1/sources/capital_structure.md)**: Debt schedule, cash balance, diluted share count, and trading peer multiples as of June 30, 2026.

---

## 3. Historical Financial Summary (2023A–2025A)

The company's historical performance reflects solid revenue expansion:

| Metric | 2023A | 2024A | 2025A | Historical Operating Ratio |
|---|---:|---:|---:|---|
| **Revenue** | \$820.0 | \$905.0 | \$1,000.0 | Base for forward projections |
| **GAAP EBITDA** | \$131.2 | \$149.3 | \$165.0 | Margin: 16.0% → 16.5% |
| **D&A** | \$32.8 | \$36.2 | \$40.0 | Exactly **4.0% of revenue** |
| **GAAP EBIT** | \$98.4 | \$113.1 | \$125.0 | EBITDA − D&A |
| **Capex** | \$36.9 | \$40.7 | \$45.0 | Exactly **4.5% of revenue** |
| **Net Working Capital (NWC)** | \$98.4 | \$108.6 | \$120.0 | Exactly **12.0% of revenue** |

---

## 4. The 8 Deliberate Source Traps

Real-world financial filings are messy, ambiguous, and filled with subtleties. To test whether an AI agent performs rigorous financial analysis rather than naive keyword matching, Northstar contains **8 deliberate traps**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        8 DELIBERATE SOURCE TRAPS                       │
├────────────────────────────────┬───────────────────────────────────────┤
│ 1. Quarterly vs YTD Revenue    │ 5. Convertible Debt Treatment         │
│ 2. Adjusted vs GAAP EBITDA     │ 6. Negative EBITDA Peer (N/M)         │
│ 3. Qualitative Guidance Truth  │ 7. Fiscal Year End Mismatch           │
│ 4. Restructuring Normalization │ 8. Capex Terminology Divergence       │
└────────────────────────────────┴───────────────────────────────────────┘
```

Let's examine each trap in detail:

---

### Trap 1: Quarterly Standalone vs. YTD Revenue
- **The Evidence**: In `quarterly_report.md`, the income statement shows **Q2 standalone revenue = \$281.0mm** and **H1 YTD revenue = \$535.0mm**.
- **Why a weak AI fails**: Naive regex or retrieval models often grab `$281.0mm` or `$535.0mm` and plug it into 2026E annual revenue.
- **What a careful analyst notices**: An annual forecast must project from full-year 2025A revenue (\$1,000mm), not a single quarter or half-year.
- **Grading Nature**: **Objective hard error** (`REV_QUARTERLY_CONFUSION`).

---

### Trap 2: Adjusted EBITDA vs. GAAP Operating Profit
- **The Evidence**: Management guidance targets "approximately 17% Adjusted EBITDA margin." However, the income statement provides GAAP EBIT and D&A.
- **Why a weak AI fails**: Confuses Adjusted EBITDA with GAAP operating income, or forgets to subtract D&A when deriving EBIT.
- **What a careful analyst notices**: EBITDA is an intermediate cash flow proxy; GAAP operating profit (EBIT) must explicitly subtract D&A.
- **Grading Nature**: **Objective accounting requirement** (`MARGIN_EBIT_INCONSISTENCY`).

---

### Trap 3: "High-Single-Digit" Guidance vs. Exact Numbers (Provenance)
- **The Evidence**: Management guidance states: *"FY2026 revenue growth expected to be in the high single digits."* Management never mentions a specific percentage.
- **Why a weak AI fails**: The model assumes 8.0% growth, but writes in its notes: *"Management guided to 8% revenue growth."*
- **What a careful analyst notices**:
  - ❌ **Incorrect Claim**: *"Management guided to 8% growth."* (Fabricated source claim!)
  - ✅ **Correct Claim**: *"Management guided to high-single-digit growth; the model assumes 8.0% as an analyst interpretation."*
- **Grading Nature**: **Evidentiary hard failure** (`SF_GUIDANCE_FABRICATED`). Choosing 8% is fine; claiming management stated 8% is an error.

---

### Trap 4: Non-Recurring Restructuring Charge Treatment
- **The Evidence**: In 2025A, Northstar incurred a separately disclosed **\$9.0mm restructuring charge** included in SG&A.
- **Why a weak AI fails**: Silently absorbs the charge or ignores the disclosure entirely without documenting whether it is normalized in baseline margins.
- **What a careful analyst notices**: Whether an analyst retains GAAP figures or adds back the \$9mm for an adjusted historical baseline is an analyst decision, but it must be explicitly classified and documented in model notes.
- **Grading Nature**: **Defensible judgment call with required disclosure**.

---

### Trap 5: Convertible Debt ($75mm Face Value)
- **The Evidence**: Northstar has \$420.0mm of gross debt, of which **\$75.0mm is convertible notes** with a conversion price of **\$27.50**. Northstar's current share price is **\$20.00**.
- **Why a weak AI fails**: Treats the convertible notes as common equity or double-counts them as both debt and shares.
- **What a careful analyst notices**: Because the conversion price (\$27.50) is well above the current market price (\$20.00), the conversion option is out-of-the-money under the base case. Under the base case, the notes should be treated as **debt** in the net debt bridge.
- **Grading Nature**: **Financial structure requirement** (`EQ_BRIDGE_DEBT_OMITTED`).

---

### Trap 6: Negative EBITDA Peer (Evergreen Controls)
- **The Evidence**: In the comparable companies table, Evergreen Controls has negative EBITDA. Its EV/EBITDA multiple is marked **N/M** (Not Meaningful).
- **Why a weak AI fails**: Replaces `N/M` with `0.0` or `null -> 0.0`. When calculating the peer median across `[7.9, 8.5, 9.2, 7.3, 0.0]`, the median collapses from **8.2x** down to **7.9x**.
- **What a careful analyst notices**: A negative multiple is undefined and economically meaningless. Evergreen must be excluded entirely from median multiple calculations.
- **Grading Nature**: **Objective valuation error** (`COMPS_NM_COERCED_ZERO`).

---

### Trap 7: Fiscal Year End Mismatch (Crestline Systems)
- **The Evidence**: Peer company Crestline Systems has a **September 30** fiscal year end, whereas Northstar and other peers end December 31.
- **Why a weak AI fails**: Omits any acknowledgment of timing mismatch or discards the comp entirely without explanation.
- **What a careful analyst notices**: Including Crestline is standard practice in banking if the peer is operationally relevant, but the calendarization mismatch must be explicitly surfaced.
- **Grading Nature**: **Financial reasonableness warning**.

---

### Trap 8: Capex Terminology Divergence
- **The Evidence**: Management guidance mentions *"capital investment of approximately 4.5% of sales."* The cash flow statement lists *"purchases of property and equipment."*
- **Why a weak AI fails**: Assumes "capital investment" and "capex" are two distinct items and deducts both from cash flows (double counting capex).
- **What a careful analyst notices**: In industrial corporate finance, "purchases of property and equipment" and "capital investment" represent the same Capex outflow.
- **Grading Nature**: **Objective accounting error** (`FCF_CAPEX_DOUBLE_COUNTED`).

---

## Summary

The Northstar case is designed so that a model that only looks at keywords will trigger multiple traps. A model with genuine financial reasoning will navigate all eight effortlessly.

Next, proceed to **[Chapter 02 — DCF and Trading Comps from First Principles](02_dcf_and_comps.md)** to see the exact mathematics behind the valuation.
