# Milestone 2 — Structured Analyst Report

- **Experiment ID**: `m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042`
- **Case**: `northstar-v1`
- **Mode**: `structured`
- **Provider / Model**: `deepseek` / `deepseek-v4-flash`
- **Completed Runs**: 10 / 10
- **Parse Success**: 10/10 (100.0%)

## Summary Statistics

| Metric | Value |
|---|---|
| **Mean Score** | 99.0 / 100 |
| **Median Score** | 99.2 / 100 |
| **Min / Max Score** | 97.0 / 100.0 |
| **Std Deviation** | 1.2 |
| **Hard-Failure Rate** | 30.0% (3/10 runs) |

## Individual Run Breakdown

| Run | Score | Grade | Hard Failures | Parse Status | Latency |
|---|---:|:---:|:---:|:---:|---:|
| `001` | 100.0 | A+ | 0 | Passed | 196.00s |
| `002` | 97.0 | A+ | 0 | Passed | 165.89s |
| `003` | 98.0 | A+ | 1 | Passed | 144.14s |
| `004` | 100.0 | A+ | 0 | Passed | 125.04s |
| `005` | 98.0 | A+ | 5 | Passed | 152.57s |
| `006` | 100.0 | A+ | 0 | Passed | 238.76s |
| `007` | 98.0 | A+ | 5 | Passed | 194.14s |
| `008` | 100.0 | A+ | 0 | Passed | 203.29s |
| `009` | 98.5 | A+ | 0 | Passed | 168.22s |
| `010` | 100.0 | A+ | 0 | Passed | 191.40s |

## Failure Frequency Analysis

| Diagnostic Code | Description | Occurrences | Run Incidence | Run % |
|---|---|---:|---:|---:|
| `FCF_NOPAT_ERROR` | NOPAT formula error | 10 | 2 / 10 runs | 20.0% |
| `COMPS_MEDIAN_ERROR` | Comps median calculated incorrectly | 1 | 1 / 10 runs | 10.0% |

## Failure Categories

| Error Category | Occurrences |
|---|---:|
| `formula_error` | 10 |
| `arithmetic_error` | 1 |

## Grader Performance Breakdown

| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |
|---|---:|---:|---:|---:|---:|
| `source_fidelity` | 14.6 | 15.0 | 100.0% | 0 | 0 |
| `revenue_forecast` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `margin_forecast` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `free_cash_flow` | 9.6 | 10.0 | 80.0% | 2 | 0 |
| `wacc` | 8.0 | 8.0 | 100.0% | 0 | 0 |
| `terminal_value` | 7.0 | 7.0 | 100.0% | 0 | 0 |
| `enterprise_value` | 5.0 | 5.0 | 100.0% | 0 | 0 |
| `equity_bridge` | 10.0 | 10.0 | 100.0% | 0 | 0 |
| `comps` | 9.8 | 10.0 | 90.0% | 1 | 0 |
| `consistency` | 20.0 | 20.0 | 100.0% | 0 | 0 |
