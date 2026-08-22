# Milestone 1 — Direct Analyst Baseline Report

- **Experiment ID**: `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_165003`
- **Case**: `northstar-v1`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 3 / 3
- **Parse Success**: 3/3 (100.0%)

## Summary Statistics

| Metric | Value |
|---|---|
| **Mean Score** | 88.8 / 100 |
| **Median Score** | 86.9 / 100 |
| **Min / Max Score** | 86.8 / 92.9 |
| **Std Deviation** | 3.5 |
| **Hard-Failure Rate** | 100.0% (3/3 runs) |

## Individual Run Breakdown

| Run | Score | Grade | Hard Failures | Parse Status | Latency |
|---|---:|:---:|:---:|:---:|---:|
| `001` | 86.8 | B+ | 11 | Passed | 22.10s |
| `002` | 92.9 | A | 5 | Passed | 19.37s |
| `003` | 86.9 | B+ | 10 | Passed | 17.77s |

## Failure Frequency Analysis

| Diagnostic Code | Description | Count | % of Parsed Runs |
|---|---|---:|---:|
| `REV_ARITHMETIC` | Revenue forecast arithmetic error | 10 | 333.3% |
| `FCF_UFCF_ERROR` | UFCF formula error | 8 | 266.7% |
| `TV_FORMULA_ERROR` | Terminal value Gordon Growth formula error | 5 | 166.7% |
| `TV_PV_ERROR` | Terminal value PV discounting error | 2 | 66.7% |
| `WACC_FORMULA_ERROR` | WACC component weighting error | 1 | 33.3% |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| `formula_error` | 14 |
| `arithmetic_error` | 12 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 15.0 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 2.7 | 8.0 | 0.0% | 3 | 0 |
| `margin_forecast` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `free_cash_flow` | 8.9 | 10.0 | 0.0% | 3 | 0 |
| `wacc` | 7.3 | 8.0 | 66.7% | 1 | 0 |
| `terminal_value` | 2.9 | 7.0 | 0.0% | 3 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
