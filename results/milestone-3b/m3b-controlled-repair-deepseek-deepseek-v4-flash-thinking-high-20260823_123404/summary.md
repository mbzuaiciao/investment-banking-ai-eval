# Milestone 3B — Controlled Repair Benchmark Report

- **Experiment ID**: `m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123404`
- **Case**: `northstar-v1`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Fixtures Attempted**: 3
- **Parse Success**: 3/3 (100.0%)

## Headline Benchmark Metrics

| Metric | Value | Meaning |
|---|---|---|
| **Controlled Repair Success Rate** | **100.0%** (3/3) | Target resolved with 0 remaining hard failures |
| **Target Diagnostic Resolution Rate** | **100.0%** (3/3) | Target error disappeared after feedback |
| **New Error Introduction Rate** | **0.0%** (0/3) | Repair turn introduced ≥ 1 new diagnostic |
| **Partial Repair Rate** | 0.0% (0/3) | Target resolved but other hard failures remain |
| **Persistent Failure Rate** | 0.0% (0/3) | Target diagnostic persisted after repair |
| **Mean Score Delta** | +4.3 (95.7 $\rightarrow$ 100.0) | Average score shift across attempted fixtures |

## Per-Fixture Outcome Table

| ID | Fixture Name | Target Diagnostic | Category | Difficulty | Init Score | Rep Score | Δ Score | Target Resolved? | Final HF | Outcome |
|:---:|---|---|---|:---:|---:|---:|---:|:---:|:---:|---|
| `c02` | Terminal Value Not Discounted | `TV_NOT_DISCOUNTED` | valuation | propagating | 98.2 | 100.0 | +1.8 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c08` | Capex Double Counted | `FCF_CAPEX_DOUBLE_COUNTED` | formula | propagating | 96.3 | 100.0 | +3.7 | ✓ Yes | 0 | ✓ Success (Clean) |
| `c10` | Pre-Tax Cost of Debt in WACC | `WACC_PRETAX_DEBT` | formula | propagating | 92.5 | 100.0 | +7.5 | ✓ Yes | 0 | ✓ Success (Clean) |

## Error-Category Repair Performance

| Error Category | Fixtures | Target Resolved | Target Resolution % | Full Clean Success | Clean Success % |
|---|---:|---:|---:|---:|---:|
| `formula` | 2 | 2 | 100.0% | 2 | 100.0% |
| `valuation` | 1 | 1 | 100.0% | 1 | 100.0% |

## Difficulty Analysis (Local vs. Propagating Repairs)

| Difficulty | Description | Fixtures | Target Resolution % | Clean Success % |
|---|---|---:|---:|---:|
| **Propagating** | Cascading dependencies (e.g. WACC, base revenue, Capex, TV discounting) | 3 | 100.0% | 100.0% |

## Diagnostic Transitions & Regression Invariant Auditing

| Fixture ID | Target Diagnostic | Resolved? | Persistent Codes | Newly Introduced Codes |
|:---:|---|:---:|---|---|
| `c02` | `TV_NOT_DISCOUNTED` | Yes | — | — |
| `c08` | `FCF_CAPEX_DOUBLE_COUNTED` | Yes | — | — |
| `c10` | `WACC_PRETAX_DEBT` | Yes | — | — |
