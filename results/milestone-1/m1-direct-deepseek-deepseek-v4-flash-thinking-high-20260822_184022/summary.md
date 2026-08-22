# Milestone 1 — Direct Analyst Baseline Report

- **Experiment ID**: `m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_184022`
- **Case**: `northstar-v1`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 3 / 3
- **Parse Success**: 3/3 (100.0%)

## Summary Statistics

| Metric | Value |
|---|---|
| **Mean Score** | 94.4 / 100 |
| **Median Score** | 94.8 / 100 |
| **Min / Max Score** | 91.8 / 96.8 |
| **Std Deviation** | 2.5 |
| **Hard-Failure Rate** | 100.0% (3/3 runs) |

## Individual Run Breakdown

| Run | Score | Grade | Hard Failures | Parse Status | Latency |
|---|---:|:---:|:---:|:---:|---:|
| `001` | 91.8 | A | 3 | Passed | 179.86s |
| `002` | 96.8 | A+ | 1 | Passed | 190.47s |
| `003` | 94.8 | A | 3 | Passed | 171.45s |

## Failure Frequency Analysis

| Diagnostic Code | Description | Count | % of Parsed Runs |
|---|---|---:|---:|
| `TV_FORMULA_ERROR` | Terminal value Gordon Growth formula error | 4 | 133.3% |
| `TV_PV_ERROR` | Terminal value PV discounting error | 3 | 100.0% |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| `formula_error` | 4 |
| `arithmetic_error` | 3 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 13.5 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `margin_forecast` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `free_cash_flow` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `wacc` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `terminal_value` | 2.9 | 7.0 | 0.0% | 3 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
