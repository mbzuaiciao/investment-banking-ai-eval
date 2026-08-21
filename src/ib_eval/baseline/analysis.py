"""Aggregate statistics and reporting for Milestone 1 Direct Analyst Baseline."""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ib_eval.baseline.interface import TrialResult


# Mapping of diagnostic codes to human-readable explanations
DIAGNOSTIC_DESCRIPTIONS: dict[str, str] = {
    "SF_GUIDANCE_FABRICATED": "Fabricated explicit guidance claim",
    "SF_MISSING_PROVENANCE": "Missing provenance records",
    "REV_QUARTERLY_CONFUSION": "Quarterly/YTD revenue confused with annual",
    "REV_GROWTH_OUT_OF_RANGE": "Revenue growth assumption out of range",
    "REV_ARITHMETIC": "Revenue forecast arithmetic error",
    "MARGIN_EBITDA_INCONSISTENCY": "EBITDA arithmetic inconsistency",
    "MARGIN_DA_INCONSISTENCY": "D&A percentage calculation error",
    "MARGIN_EBIT_INCONSISTENCY": "EBIT ≠ EBITDA − D&A",
    "FCF_NOPAT_ERROR": "NOPAT formula error",
    "FCF_CAPEX_DOUBLE_COUNTED": "Capex double counted",
    "FCF_CAPEX_ERROR": "Capex calculation error",
    "FCF_NWC_DELTA_ERROR": "ΔNWC arithmetic error",
    "FCF_UFCF_ERROR": "UFCF formula error",
    "FCF_PV_ERROR": "PV(UFCF) discounting error",
    "WACC_PRETAX_DEBT": "Pre-tax cost of debt used without tax shield",
    "WACC_FORMULA_ERROR": "WACC component weighting error",
    "WACC_WEIGHTS_ERROR": "Capital structure weights do not sum to 1",
    "WACC_KE_ERROR": "Cost of equity CAPM formula error",
    "WACC_KD_ERROR": "After-tax cost of debt error",
    "TV_NOT_DISCOUNTED": "Terminal value not discounted to valuation date",
    "TV_FORMULA_ERROR": "Terminal value Gordon Growth formula error",
    "TV_GROWTH_GT_WACC": "Terminal growth rate exceeds WACC",
    "TV_PV_ERROR": "Terminal value PV discounting error",
    "EV_SUM_PVUFCF_MISMATCH": "Sum of PV(UFCF) mismatch",
    "EV_SUM_ERROR": "EV ≠ Σ PV(UFCF) + PV(TV)",
    "EQ_BRIDGE_CASH_REVERSED": "Cash added to debt instead of subtracted",
    "EQ_BRIDGE_DEBT_OMITTED": "Net debt omitted from equity bridge",
    "EQ_BRIDGE_NET_DEBT_ERROR": "Net debt arithmetic error",
    "EQ_BRIDGE_ARITHMETIC": "Equity value arithmetic error",
    "EQ_BRIDGE_SHARE_PRICE": "Implied share price arithmetic error",
    "EQ_BRIDGE_EV_MISMATCH": "Equity bridge EV does not match DCF EV",
    "COMPS_NM_COERCED_ZERO": "N/M peer multiple coerced to zero in median",
    "COMPS_MEDIAN_ERROR": "Comps median calculated incorrectly",
    "COMPS_EV_ARITHMETIC": "Comps EV arithmetic error",
    "COMPS_EQUITY_ARITHMETIC": "Comps equity arithmetic error",
    "COMPS_SHARE_PRICE_ERROR": "Comps share price arithmetic error",
    "CONSISTENCY_HEADLINE_DCF": "Headline DCF values do not match model",
    "CONSISTENCY_HEADLINE_COMPS": "Headline comps values do not match model",
    "CONSISTENCY_EV_BRIDGE": "Equity bridge EV differs from DCF EV",
    "CONSISTENCY_SHARES": "Diluted shares inconsistent across sections",
}


class GraderSummaryStat(BaseModel):
    """Aggregate statistics for a specific grader."""

    grader_name: str
    mean_score: float
    max_points: float
    pass_rate: float
    failure_count: int
    zero_score_count: int


class ExperimentSummary(BaseModel):
    """Complete aggregate statistics for an experiment."""

    experiment_id: str
    case_id: str
    provider: str
    model: str
    requested_runs: int
    completed_model_calls: int
    parsed_runs: int
    parse_failure_count: int
    parse_success_rate: float

    mean_score: float | None = None
    median_score: float | None = None
    min_score: float | None = None
    max_score: float | None = None
    standard_deviation: float | None = None

    hard_failure_run_count: int = 0
    hard_failure_rate: float = 0.0

    diagnostic_frequency: dict[str, int] = Field(default_factory=dict[str, int])
    failure_category_frequency: dict[str, int] = Field(default_factory=dict[str, int])
    grader_statistics: dict[str, GraderSummaryStat] = Field(
        default_factory=dict[str, GraderSummaryStat]
    )


def compute_aggregate_statistics(
    experiment_id: str,
    case_id: str,
    provider: str,
    model: str,
    requested_runs: int,
    trial_results: list[TrialResult],
) -> ExperimentSummary:
    """Calculate statistical summaries and error distributions across all trials."""
    completed_calls = len(trial_results)
    parsed_trials = [t for t in trial_results if t.submission is not None and t.grade is not None]
    parsed_count = len(parsed_trials)
    parse_failure_count = completed_calls - parsed_count
    parse_success_rate = round(parsed_count / completed_calls, 4) if completed_calls > 0 else 0.0

    scores = [t.grade.total_score for t in parsed_trials if t.grade is not None]

    mean_score = round(statistics.mean(scores), 2) if scores else None
    median_score = round(statistics.median(scores), 2) if scores else None
    min_score = round(min(scores), 2) if scores else None
    max_score = round(max(scores), 2) if scores else None
    if len(scores) >= 2:
        stdev_score = round(statistics.stdev(scores), 2)
    elif len(scores) == 1:
        stdev_score = 0.0
    else:
        stdev_score = None

    # Hard failures
    hard_failure_runs = [
        t for t in parsed_trials if t.grade is not None and len(t.grade.hard_failures) > 0
    ]
    hard_failure_run_count = len(hard_failure_runs)
    hard_failure_rate = (
        round(hard_failure_run_count / parsed_count, 4) if parsed_count > 0 else 0.0
    )

    # Diagnostic code frequency
    diagnostic_counts: dict[str, int] = {}
    for t in parsed_trials:
        if t.grade is not None:
            for g_res in t.grade.grader_results:
                for f in g_res.failures:
                    code = f.diagnostic_code
                    diagnostic_counts[code] = diagnostic_counts.get(code, 0) + 1

    sorted_diagnostics = dict(
        sorted(diagnostic_counts.items(), key=lambda item: item[1], reverse=True)
    )

    # Failure category frequency
    category_counts: dict[str, int] = {}
    for t in parsed_trials:
        if t.grade is not None:
            for g_res in t.grade.grader_results:
                for f in g_res.failures:
                    cat = str(f.error_type.value)
                    category_counts[cat] = category_counts.get(cat, 0) + 1

    sorted_categories = dict(
        sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
    )

    # Per-grader statistics
    grader_stats: dict[str, GraderSummaryStat] = {}
    if parsed_trials and parsed_trials[0].grade is not None:
        all_grader_names = [r.grader for r in parsed_trials[0].grade.grader_results]
        for g_name in all_grader_names:
            g_scores: list[float] = []
            g_max = 0.0
            g_fails = 0
            g_zeros = 0
            for t in parsed_trials:
                if t.grade is not None:
                    res = next((r for r in t.grade.grader_results if r.grader == g_name), None)
                    if res is not None:
                        g_scores.append(res.points_earned)
                        g_max = res.max_points
                        if not res.passed:
                            g_fails += 1
                        if res.points_earned == 0.0 and res.max_points > 0.0:
                            g_zeros += 1

            mean_g_score = round(statistics.mean(g_scores), 2) if g_scores else 0.0
            pass_rate = round((len(g_scores) - g_fails) / len(g_scores), 4) if g_scores else 0.0
            grader_stats[g_name] = GraderSummaryStat(
                grader_name=g_name,
                mean_score=mean_g_score,
                max_points=g_max,
                pass_rate=pass_rate,
                failure_count=g_fails,
                zero_score_count=g_zeros,
            )

    return ExperimentSummary(
        experiment_id=experiment_id,
        case_id=case_id,
        provider=provider,
        model=model,
        requested_runs=requested_runs,
        completed_model_calls=completed_calls,
        parsed_runs=parsed_count,
        parse_failure_count=parse_failure_count,
        parse_success_rate=parse_success_rate,
        mean_score=mean_score,
        median_score=median_score,
        min_score=min_score,
        max_score=max_score,
        standard_deviation=stdev_score,
        hard_failure_run_count=hard_failure_run_count,
        hard_failure_rate=hard_failure_rate,
        diagnostic_frequency=sorted_diagnostics,
        failure_category_frequency=sorted_categories,
        grader_statistics=grader_stats,
    )


def generate_markdown_summary(
    summary: ExperimentSummary,
    trial_results: list[TrialResult],
) -> str:
    """Deterministically format experiment summary into a human-readable Markdown report."""
    mean_str = f"{summary.mean_score:.1f}" if summary.mean_score is not None else "N/A"
    median_str = f"{summary.median_score:.1f}" if summary.median_score is not None else "N/A"
    stdev_val = summary.standard_deviation
    stdev_str = f"{stdev_val:.1f}" if stdev_val is not None else "N/A"
    min_str = f"{summary.min_score:.1f}" if summary.min_score is not None else "N/A"
    max_str = f"{summary.max_score:.1f}" if summary.max_score is not None else "N/A"

    parse_rate_pct = f"{summary.parse_success_rate:.1%}"
    hard_rate_pct = f"{summary.hard_failure_rate:.1%}"

    lines: list[str] = [
        "# Milestone 1 — Direct Analyst Baseline Report",
        "",
        f"- **Experiment ID**: `{summary.experiment_id}`",
        f"- **Case**: `{summary.case_id}`",
        f"- **Provider / Model**: `{summary.provider}` / `{summary.model}`",
        f"- **Completed Runs**: {summary.completed_model_calls} / {summary.requested_runs}",
        f"- **Parse Success**: {summary.parsed_runs}/{summary.completed_model_calls} "
        f"({parse_rate_pct})",
        "",
        "## Summary Statistics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Mean Score** | {mean_str} / 100 |",
        f"| **Median Score** | {median_str} / 100 |",
        f"| **Min / Max Score** | {min_str} / {max_str} |",
        f"| **Std Deviation** | {stdev_str} |",
        f"| **Hard-Failure Rate** | {hard_rate_pct} "
        f"({summary.hard_failure_run_count}/{summary.parsed_runs} runs) |",
        "",
        "## Individual Run Breakdown",
        "",
        "| Run | Score | Grade | Hard Failures | Parse Status | Latency |",
        "|---|---:|:---:|:---:|:---:|---:|",
    ]

    for t in trial_results:
        m = t.metadata
        score_val = f"{m.score:.1f}" if m.score is not None else "N/A"
        grade_letter = t.grade.grade if t.grade is not None else "N/A"
        hard_str = str(m.hard_failure_count) if m.parsed_successfully else "N/A"
        status_str = "Passed" if m.parsed_successfully else "Failed"
        latency_str = f"{m.latency_seconds:.2f}s" if m.latency_seconds is not None else "N/A"
        lines.append(
            f"| `{m.run_index:03d}` | {score_val} | {grade_letter} | "
            f"{hard_str} | {status_str} | {latency_str} |"
        )

    lines.extend([
        "",
        "## Failure Frequency Analysis",
        "",
        "| Diagnostic Code | Description | Count | % of Parsed Runs |",
        "|---|---|---:|---:|",
    ])

    if summary.diagnostic_frequency:
        for code, count in summary.diagnostic_frequency.items():
            desc = DIAGNOSTIC_DESCRIPTIONS.get(code, "Diagnostic error")
            pct = (count / summary.parsed_runs) * 100 if summary.parsed_runs > 0 else 0.0
            lines.append(f"| `{code}` | {desc} | {count} | {pct:.1f}% |")
    else:
        lines.append("| *(none)* | No diagnostic failures recorded | 0 | 0.0% |")

    lines.extend([
        "",
        "## Failure Categories",
        "",
        "| Error Category | Occurrences |",
        "|---|---:|",
    ])

    if summary.failure_category_frequency:
        for cat, count in summary.failure_category_frequency.items():
            lines.append(f"| `{cat}` | {count} |")
    else:
        lines.append("| *(none)* | 0 |")

    lines.extend([
        "",
        "## Grader Performance Breakdown",
        "",
        "| Grader | Mean Score | Max Points | Pass Rate | Failures | Zero Scores |",
        "|---|---:|---:|---:|---:|---:|",
    ])

    if summary.grader_statistics:
        for g_name, g_stat in summary.grader_statistics.items():
            lines.append(
                f"| `{g_name}` | {g_stat.mean_score:.1f} | {g_stat.max_points:.1f} | "
                f"{g_stat.pass_rate:.1%} | {g_stat.failure_count} | {g_stat.zero_score_count} |"
            )

    lines.append("")
    return "\n".join(lines)
