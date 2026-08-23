# Milestone 3 — Deterministic Feedback Repair Report

- **Experiment ID**: `m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546`
- **Case**: `northstar-v1`
- **Mode**: `repair`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 10 / 10
- **Parse Success**: 10/10 (100.0%)

## Repair Performance Summary

| Metric | Initial | Repaired / Final | Delta |
|---|---:|---:|---:|
| **Mean Score** | 98.8 / 100 | 98.8 / 100 | +0.5 |
| **Hard-Failure Rate** | 10.0% (1 runs) | 0.0% (0 runs) | -10.0% |
| **Repair Success Rate** | — | **100.0%** (1/1 runs) | — |

### Repair Effectiveness
- **Trials Improved**: 1 (100.0%)
- **Trials Unchanged**: 0 (0.0%)
- **Trials Worsened**: 0 (0.0%)
- **Diagnostics Resolved**: 1
- **Diagnostics Persistent**: 0
- **Diagnostics Newly Introduced**: 0

## Individual Run Breakdown

| Run | Initial | Repaired | Δ Score | Init HF | Rep HF | Result | Latency |
|---|---:|---:|---:|:---:|:---:|---|---:|
| `001` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 155.25s |
| `002` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 114.22s |
| `003` | 98.0 | 98.5 | +0.5 | 5 | 0 | Repaired (Clean) | 329.06s |
| `004` | 98.5 | 98.5 | +0.0 | 0 | 0 | Already Clean | 220.68s |
| `005` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 222.22s |
| `006` | 95.5 | 95.5 | +0.0 | 0 | 0 | Already Clean | 165.21s |
| `007` | 95.5 | 95.5 | +0.0 | 0 | 0 | Already Clean | 175.93s |
| `008` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 165.62s |
| `009` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 167.82s |
| `010` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 200.06s |

## Diagnostic Transition Analysis

| Diagnostic Code | Description | Init Runs | Rep Runs | Resolved | Persistent | New |
|---|---|---:|---:|---:|---:|---:|
| `FCF_NOPAT_ERROR` | NOPAT formula error | 1 | 0 | 1 | 0 | 0 |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| *(none)* | 0 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 13.8 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `margin_forecast` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `free_cash_flow` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `wacc` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `terminal_value` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
