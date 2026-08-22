# Milestone 1 — Direct Analyst Baseline Report

- **Experiment ID**: `m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143`
- **Case**: `northstar-v1`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 10 / 10
- **Parse Success**: 10/10 (100.0%)

## Summary Statistics

| Metric | Value |
|---|---|
| **Mean Score** | 97.2 / 100 |
| **Median Score** | 97.5 / 100 |
| **Min / Max Score** | 94.8 / 98.2 |
| **Std Deviation** | 1.2 |
| **Hard-Failure Rate** | 100.0% (10/10 runs) |

## Individual Run Breakdown

| Run | Score | Grade | Hard Failures | Parse Status | Latency |
|---|---:|:---:|:---:|:---:|---:|
| `001` | 96.8 | A+ | 1 | Passed | 211.82s |
| `002` | 98.2 | A+ | 1 | Passed | 201.61s |
| `003` | 94.8 | A | 3 | Passed | 174.72s |
| `004` | 96.8 | A+ | 1 | Passed | 164.84s |
| `005` | 98.2 | A+ | 1 | Passed | 162.18s |
| `006` | 98.2 | A+ | 1 | Passed | 241.45s |
| `007` | 96.2 | A+ | 6 | Passed | 187.57s |
| `008` | 98.2 | A+ | 1 | Passed | 219.93s |
| `009` | 98.2 | A+ | 1 | Passed | 176.61s |
| `010` | 96.8 | A+ | 1 | Passed | 164.86s |

## Failure Frequency Analysis

| Diagnostic Code | Description | Count | % of Parsed Runs |
|---|---|---:|---:|
| `TV_PV_ERROR` | Terminal value PV discounting error | 10 | 100.0% |
| `FCF_NOPAT_ERROR` | NOPAT formula error | 5 | 50.0% |
| `TV_FORMULA_ERROR` | Terminal value Gordon Growth formula error | 2 | 20.0% |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| `arithmetic_error` | 10 |
| `formula_error` | 7 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 14.6 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `margin_forecast` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `free_cash_flow` | 9.8 | 10.0 | 90.0% | 1 | 0 |
| `wacc` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `terminal_value` | 4.9 | 7.0 | 0.0% | 10 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
