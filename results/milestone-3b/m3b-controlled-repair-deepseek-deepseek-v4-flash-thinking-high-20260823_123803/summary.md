# Milestone 3B — Controlled Repair Benchmark Report

- **Experiment ID**: `m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803`
- **Case**: `northstar-v1`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Fixtures Attempted**: 10
- **Parse Success**: 10/10 (100.0%)

## Headline Benchmark Metrics

| Metric | Value | Meaning |
|---|---|---|
| **Controlled Repair Success Rate** | **100.0%** (10/10) | Target resolved with 0 remaining hard failures |
| **Target Diagnostic Resolution Rate** | **100.0%** (10/10) | Target error disappeared after feedback |
| **New Error Introduction Rate** | **0.0%** (0/10) | Repair turn introduced ≥ 1 new diagnostic |
| **Partial Repair Rate** | 0.0% (0/10) | Target resolved but other hard failures remain |
| **Persistent Failure Rate** | 0.0% (0/10) | Target diagnostic persisted after repair |
| **Mean Score Delta** | +4.4 (95.6 $\rightarrow$ 100.0) | Average score shift across attempted fixtures |

## Per-Fixture Outcome Table

| ID | Fixture Name | Target Diagnostic | Category | Difficulty | Init Score | Rep Score | Δ Score | Target Resolved? | Final HF | Outcome |
|:---:|---|---|---|:---:|---:|---:|---:|:---:|:---:|---|
| `c01` | Quarterly Revenue Confusion | `REV_QUARTERLY_CONFUSION` | valuation | propagating | 92.7 | 100.0 | +7.3 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c02` | Terminal Value Not Discounted | `TV_NOT_DISCOUNTED` | valuation | propagating | 98.2 | 100.0 | +1.8 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c03` | Cash Subtracted in Bridge | `EQ_BRIDGE_CASH_REVERSED` | accounting_bridge | propagating | 97.5 | 100.0 | +2.5 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c04` | Debt Omitted from Bridge | `EQ_BRIDGE_DEBT_OMITTED` | accounting_bridge | propagating | 97.5 | 100.0 | +2.5 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c05` | N/M Peer Multiple Coerced to Zero | `COMPS_NM_COERCED_ZERO` | comps | local | 98.0 | 100.0 | +2.0 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c06` | Fabricated Explicit Guidance | `SF_GUIDANCE_FABRICATED` | source_fidelity | local | 92.5 | 100.0 | +7.5 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c07` | EBITDA / D&A / EBIT Inconsistency | `MARGIN_EBIT_INCONSISTENCY` | arithmetic | propagating | 96.2 | 100.0 | +3.8 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c08` | Capex Double Counted | `FCF_CAPEX_DOUBLE_COUNTED` | formula | propagating | 96.3 | 100.0 | +3.7 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c09` | Headline / Schedule Mismatch | `CONSISTENCY_HEADLINE_DCF` | consistency | local | 95.0 | 100.0 | +5.0 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c10` | Pre-Tax Cost of Debt in WACC | `WACC_PRETAX_DEBT` | formula | propagating | 92.5 | 100.0 | +7.5 | ✓ Yes | 0 | ✓ Success (Clean) |

## Error-Category Repair Performance

| Error Category | Fixtures | Target Resolved | Target Resolution % | Full Clean Success | Clean Success % |
|---|---:|---:|---:|---:|---:|
| `accounting_bridge` | 2 | 2 | 100.0% | 2 | 100.0% |
| `arithmetic` | 1 | 1 | 100.0% | 1 | 100.0% |
| `comps` | 1 | 1 | 100.0% | 1 | 100.0% |
| `consistency` | 1 | 1 | 100.0% | 1 | 100.0% |
| `formula` | 2 | 2 | 100.0% | 2 | 100.0% |
| `source_fidelity` | 1 | 1 | 100.0% | 1 | 100.0% |
| `valuation` | 2 | 2 | 100.0% | 2 | 100.0% |

## Difficulty Analysis (Local vs. Propagating Repairs)

| Difficulty | Description | Fixtures | Target Resolution % | Clean Success % |
|---|---|---:|---:|---:|
| **Local** | Single-schedule / localized edits (e.g. Comps median, provenance tag, headline) | 3 | 100.0% | 100.0% |
| **Propagating** | Cascading dependencies (e.g. WACC, base revenue, Capex, TV discounting) | 7 | 100.0% | 100.0% |

## Diagnostic Transitions & Regression Invariant Auditing

| Fixture ID | Target Diagnostic | Resolved? | Persistent Codes | Newly Introduced Codes |
|:---:|---|:---:|---|---|
| `c01` | `REV_QUARTERLY_CONFUSION` | Yes | — | — |
| `c02` | `TV_NOT_DISCOUNTED` | Yes | — | — |
| `c03` | `EQ_BRIDGE_CASH_REVERSED` | Yes | — | — |
| `c04` | `EQ_BRIDGE_DEBT_OMITTED` | Yes | — | — |
| `c05` | `COMPS_NM_COERCED_ZERO` | Yes | — | — |
| `c06` | `SF_GUIDANCE_FABRICATED` | Yes | — | — |
| `c07` | `MARGIN_EBIT_INCONSISTENCY` | Yes | — | — |
| `c08` | `FCF_CAPEX_DOUBLE_COUNTED` | Yes | — | — |
| `c09` | `CONSISTENCY_HEADLINE_DCF` | Yes | — | — |
| `c10` | `WACC_PRETAX_DEBT` | Yes | — | — |
