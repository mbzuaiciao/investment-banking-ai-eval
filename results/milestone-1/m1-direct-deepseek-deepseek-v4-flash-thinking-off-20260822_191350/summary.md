# Milestone 1 — Direct Analyst Baseline Report

- **Experiment ID**: `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350`
- **Case**: `northstar-v1`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 10 / 10
- **Parse Success**: 9/10 (90.0%)

## Summary Statistics

| Metric | Value |
|---|---|
| **Mean Score** | 90.5 / 100 |
| **Median Score** | 90.4 / 100 |
| **Min / Max Score** | 85.1 / 94.7 |
| **Std Deviation** | 2.7 |
| **Hard-Failure Rate** | 100.0% (9/9 runs) |

## Individual Run Breakdown

| Run | Score | Grade | Hard Failures | Parse Status | Latency |
|---|---:|:---:|:---:|:---:|---:|
| `001` | 89.9 | B+ | 7 | Passed | 18.05s |
| `002` | 92.0 | A | 6 | Passed | 17.68s |
| `003` | 90.4 | A | 11 | Passed | 14.47s |
| `004` | 91.2 | A | 8 | Passed | 16.25s |
| `005` | 88.8 | B+ | 11 | Passed | 16.32s |
| `006` | N/A | N/A | N/A | Failed | 20.83s |
| `007` | 94.7 | A | 6 | Passed | 17.19s |
| `008` | 93.2 | A | 7 | Passed | 16.61s |
| `009` | 89.8 | B+ | 9 | Passed | 15.61s |
| `010` | 85.1 | B+ | 14 | Passed | 18.58s |

## Failure Frequency Analysis

| Diagnostic Code | Description | Count | % of Parsed Runs |
|---|---|---:|---:|
| `FCF_UFCF_ERROR` | UFCF formula error | 36 | 400.0% |
| `TV_FORMULA_ERROR` | Terminal value Gordon Growth formula error | 12 | 133.3% |
| `REV_ARITHMETIC` | Revenue forecast arithmetic error | 10 | 111.1% |
| `TV_PV_ERROR` | Terminal value PV discounting error | 8 | 88.9% |
| `WACC_FORMULA_ERROR` | WACC component weighting error | 6 | 66.7% |
| `MARGIN_EBITDA_INCONSISTENCY` | EBITDA arithmetic inconsistency | 3 | 33.3% |
| `FCF_NOPAT_ERROR` | NOPAT formula error | 2 | 22.2% |
| `COMPS_MEDIAN_ERROR` | Comps median calculated incorrectly | 1 | 11.1% |
| `FCF_PV_ERROR` | PV(UFCF) discounting error | 1 | 11.1% |
| `REV_GROWTH_OUT_OF_RANGE` | Revenue growth assumption out of range | 1 | 11.1% |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| `formula_error` | 56 |
| `arithmetic_error` | 23 |
| `unsupported_assumption` | 1 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 14.7 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 6.2 | 8.0 | 55.6% | 4 | 0 |
| `margin_forecast` | 6.8 | 7.0 | 66.7% | 3 | 0 |
| `free_cash_flow` | 8.3 | 10.0 | 0.0% | 9 | 0 |
| `wacc` | 6.7 | 8.0 | 33.3% | 6 | 0 |
| `terminal_value` | 3.1 | 7.0 | 0.0% | 9 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 9.8 | 10.0 | 88.9% | 1 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
