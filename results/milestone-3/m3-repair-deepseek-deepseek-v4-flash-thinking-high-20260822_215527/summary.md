# Milestone 3 — Deterministic Feedback Repair Report

- **Experiment ID**: `m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_215527`
- **Case**: `northstar-v1`
- **Mode**: `repair`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 3 / 3
- **Parse Success**: 3/3 (100.0%)

## Repair Performance Summary

| Metric | Initial | Repaired / Final | Delta |
|---|---:|---:|---:|
| **Mean Score** | 99.5 / 100 | 99.5 / 100 | +0.0 |
| **Hard-Failure Rate** | 0.0% (0 runs) | 0.0% (0 runs) | +0.0% |
| **Repair Success Rate** | — | **0.0%** (0/0 runs) | — |

### Repair Effectiveness
- **Trials Improved**: 0 (0.0%)
- **Trials Unchanged**: 0 (0.0%)
- **Trials Worsened**: 0 (0.0%)
- **Diagnostics Resolved**: 0
- **Diagnostics Persistent**: 0
- **Diagnostics Newly Introduced**: 0

## Individual Run Breakdown

| Run | Initial | Repaired | Δ Score | Init HF | Rep HF | Result | Latency |
|---|---:|---:|---:|:---:|:---:|---|---:|
| `001` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 143.94s |
| `002` | 98.5 | 98.5 | +0.0 | 0 | 0 | Already Clean | 187.33s |
| `003` | 100.0 | 100.0 | +0.0 | 0 | 0 | Already Clean | 192.72s |

## Diagnostic Transition Analysis

| Diagnostic Code | Description | Init Runs | Rep Runs | Resolved | Persistent | New |
|---|---|---:|---:|---:|---:|---:|
| *(none)* | No diagnostics recorded | 0 | 0 | 0 | 0 | 0 |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| *(none)* | 0 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 14.5 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `margin_forecast` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `free_cash_flow` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `wacc` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `terminal_value` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
