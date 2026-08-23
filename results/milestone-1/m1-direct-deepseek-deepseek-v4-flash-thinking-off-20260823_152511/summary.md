# Milestone 1 — Direct Analyst Baseline Report

- **Experiment ID**: `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260823_152511`
- **Case**: `meridian-v1`
- **Mode**: `direct`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 1 / 1
- **Parse Success**: 1/1 (100.0%)

## Summary Statistics

| Metric | Value |
|---|---|
| **Mean Score** | 83.2 / 100 |
| **Median Score** | 83.2 / 100 |
| **Min / Max Score** | 83.2 / 83.2 |
| **Std Deviation** | 0.0 |
| **Hard-Failure Rate** | 100.0% (1/1 runs) |

## Individual Run Breakdown

| Run | Score | Grade | Hard Failures | Parse Status | Latency |
|---|---:|:---:|:---:|:---:|---:|
| `001` | 83.2 | B | 21 | Passed | 14.64s |

## Failure Frequency Analysis

| Diagnostic Code | Description | Occurrences | Run Incidence | Run % |
|---|---|---:|---:|---:|
| `MARGIN_DA_INCONSISTENCY` | D&A percentage calculation error | 5 | 1 / 1 runs | 100.0% |
| `SBC_EBITDA_INCONSISTENCY` | SBC omitted from GAAP EBIT derivation | 5 | 1 / 1 runs | 100.0% |
| `FCF_UFCF_ERROR` | UFCF formula error | 5 | 1 / 1 runs | 100.0% |
| `REV_ARITHMETIC` | Revenue forecast arithmetic error | 4 | 1 / 1 runs | 100.0% |
| `TV_PV_ERROR` | Terminal value PV discounting error | 1 | 1 / 1 runs | 100.0% |
| `COMPS_MEDIAN_ERROR` | Comps median calculated incorrectly | 1 | 1 / 1 runs | 100.0% |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| `formula_error` | 10 |
| `arithmetic_error` | 6 |
| `accounting_inconsistency` | 5 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 15.0 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 1.6 | 8.0 | 0.0% | 1 | 0 |
| `margin_forecast` | 2.3 | 7.0 | 0.0% | 1 | 0 |
| `free_cash_flow` | 8.0 | 10.0 | 0.0% | 1 | 0 |
| `wacc` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `terminal_value` | 5.2 | 7.0 | 0.0% | 1 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 8.0 | 10.0 | 0.0% | 1 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
