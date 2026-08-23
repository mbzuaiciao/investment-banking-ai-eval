"""Aggregate statistics and reporting for Direct, Structured, and Repair Analyst Baselines."""

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


class DiagnosticStat(BaseModel):
    """Occurrence and run-incidence statistics for a diagnostic code."""

    diagnostic_code: str
    description: str
    occurrence_count: int  # Total event count across all parsed runs
    run_count: int  # Number of parsed runs containing >= 1 occurrence
    run_incidence_rate: float  # run_count / parsed_runs (bounded in [0.0, 1.0])


class DiagnosticTransitionStat(BaseModel):
    """Transition statistics for a single diagnostic code across repair trials."""

    diagnostic_code: str
    description: str
    initial_run_count: int = 0
    repaired_run_count: int = 0
    resolved_count: int = 0
    persistent_count: int = 0
    newly_introduced_count: int = 0


class RepairSummaryStats(BaseModel):
    """Aggregate statistics specific to Milestone 3 repair mode."""

    trials_repair_attempted: int = 0
    trials_repair_skipped_clean: int = 0
    initially_failing_runs_count: int = 0
    initially_failing_runs_repaired_to_zero_hf: int = 0
    repair_success_rate: float = 0.0

    initial_mean_score: float | None = None
    initial_median_score: float | None = None
    initial_hard_failure_run_count: int = 0
    initial_hard_failure_rate: float = 0.0

    repaired_mean_score: float | None = None
    repaired_median_score: float | None = None
    repaired_hard_failure_run_count: int = 0
    repaired_hard_failure_rate: float = 0.0

    mean_score_delta: float | None = None
    trials_improved_count: int = 0
    trials_improved_pct: float = 0.0
    trials_unchanged_count: int = 0
    trials_unchanged_pct: float = 0.0
    trials_worsened_count: int = 0
    trials_worsened_pct: float = 0.0

    total_diagnostics_resolved: int = 0
    total_diagnostics_persistent: int = 0
    total_diagnostics_introduced: int = 0

    diagnostic_transitions: dict[str, DiagnosticTransitionStat] = Field(
        default_factory=dict[str, DiagnosticTransitionStat]
    )


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
    mode: str = "direct"
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
    diagnostic_incidence: dict[str, int] = Field(default_factory=dict[str, int])
    diagnostic_stats: dict[str, DiagnosticStat] = Field(default_factory=dict[str, DiagnosticStat])
    failure_category_frequency: dict[str, int] = Field(default_factory=dict[str, int])
    grader_statistics: dict[str, GraderSummaryStat] = Field(
        default_factory=dict[str, GraderSummaryStat]
    )

    # Milestone 3 specific repair summary
    repair_stats: RepairSummaryStats | None = None


def compute_aggregate_statistics(
    experiment_id: str,
    case_id: str,
    provider: str,
    model: str,
    requested_runs: int,
    trial_results: list[TrialResult],
    mode: str = "direct",
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

    # Hard failures (final / effective grade)
    hard_failure_runs = [
        t for t in parsed_trials if t.grade is not None and len(t.grade.hard_failures) > 0
    ]
    hard_failure_run_count = len(hard_failure_runs)
    hard_failure_rate = (
        round(hard_failure_run_count / parsed_count, 4) if parsed_count > 0 else 0.0
    )

    # Diagnostic occurrence counts & run incidence counts
    occurrence_counts: dict[str, int] = {}
    run_incidence_counts: dict[str, int] = {}

    for t in parsed_trials:
        if t.grade is not None:
            seen_in_run: set[str] = set()
            for g_res in t.grade.grader_results:
                for f in g_res.failures:
                    code = f.diagnostic_code
                    occurrence_counts[code] = occurrence_counts.get(code, 0) + 1
                    seen_in_run.add(code)
            for code in seen_in_run:
                run_incidence_counts[code] = run_incidence_counts.get(code, 0) + 1

    sorted_codes = sorted(
        occurrence_counts.keys(),
        key=lambda c: (run_incidence_counts.get(c, 0), occurrence_counts.get(c, 0)),
        reverse=True,
    )

    sorted_frequency = {c: occurrence_counts[c] for c in sorted_codes}
    sorted_incidence = {c: run_incidence_counts[c] for c in sorted_codes}
    diagnostic_stats_map: dict[str, DiagnosticStat] = {}

    for c in sorted_codes:
        r_cnt = run_incidence_counts.get(c, 0)
        r_rate = round(r_cnt / parsed_count, 4) if parsed_count > 0 else 0.0
        diagnostic_stats_map[c] = DiagnosticStat(
            diagnostic_code=c,
            description=DIAGNOSTIC_DESCRIPTIONS.get(c, "Diagnostic error"),
            occurrence_count=occurrence_counts[c],
            run_count=r_cnt,
            run_incidence_rate=r_rate,
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

    # Milestone 3 Repair summary statistics
    repair_summary: RepairSummaryStats | None = None
    if mode == "repair":
        init_parsed_trials = [t for t in trial_results if t.metadata.initial_parsed_successfully]
        init_scores = [
            t.metadata.initial_score
            for t in init_parsed_trials
            if t.metadata.initial_score is not None
        ]
        init_mean_score = round(statistics.mean(init_scores), 2) if init_scores else None
        init_median_score = round(statistics.median(init_scores), 2) if init_scores else None

        init_hf_runs = [
            t for t in init_parsed_trials if t.metadata.initial_hard_failure_count > 0
        ]
        init_hf_count = len(init_hf_runs)
        init_hf_rate = (
            round(init_hf_count / len(init_parsed_trials), 4) if init_parsed_trials else 0.0
        )

        rep_attempted_trials = [t for t in trial_results if t.metadata.repair_attempted]
        rep_skipped_clean = [
            t
            for t in trial_results
            if t.metadata.repair_skipped_reason == "initial_submission_clean"
        ]

        init_failing_count = init_hf_count
        repaired_to_zero_hf_count = len(
            [
                t
                for t in init_hf_runs
                if t.metadata.hard_failure_count == 0 and t.metadata.parsed_successfully
            ]
        )
        repair_success_rate = (
            round(repaired_to_zero_hf_count / init_failing_count, 4)
            if init_failing_count > 0
            else 0.0
        )

        deltas = [
            t.metadata.score_delta
            for t in rep_attempted_trials
            if t.metadata.score_delta is not None
        ]
        mean_delta = round(statistics.mean(deltas), 2) if deltas else 0.0
        improved_cnt = len([d for d in deltas if d > 0])
        unchanged_cnt = len([d for d in deltas if d == 0])
        worsened_cnt = len([d for d in deltas if d < 0])
        n_deltas = len(deltas)
        improved_pct = round(improved_cnt / n_deltas, 4) if n_deltas > 0 else 0.0
        unchanged_pct = round(unchanged_cnt / n_deltas, 4) if n_deltas > 0 else 0.0
        worsened_pct = round(worsened_cnt / n_deltas, 4) if n_deltas > 0 else 0.0

        # Diagnostic transitions across all repair trials
        all_trans_codes: set[str] = set()
        for t in trial_results:
            all_trans_codes.update(t.metadata.initial_hard_failure_codes)
            all_trans_codes.update(t.metadata.hard_failure_codes)
            all_trans_codes.update(t.metadata.resolved_diagnostics)
            all_trans_codes.update(t.metadata.persistent_diagnostics)
            all_trans_codes.update(t.metadata.new_diagnostics)

        trans_map: dict[str, DiagnosticTransitionStat] = {}
        tot_resolved = 0
        tot_persistent = 0
        tot_new = 0

        for code in sorted(all_trans_codes):
            init_runs_c = len(
                [
                    t
                    for t in trial_results
                    if code in t.metadata.initial_hard_failure_codes
                    or code in t.metadata.resolved_diagnostics
                    or code in t.metadata.persistent_diagnostics
                ]
            )
            rep_runs_c = len(
                [
                    t
                    for t in trial_results
                    if code in t.metadata.hard_failure_codes
                    or code in t.metadata.persistent_diagnostics
                    or code in t.metadata.new_diagnostics
                ]
            )
            res_c = len([t for t in trial_results if code in t.metadata.resolved_diagnostics])
            pers_c = len([t for t in trial_results if code in t.metadata.persistent_diagnostics])
            new_c = len([t for t in trial_results if code in t.metadata.new_diagnostics])

            tot_resolved += res_c
            tot_persistent += pers_c
            tot_new += new_c

            trans_map[code] = DiagnosticTransitionStat(
                diagnostic_code=code,
                description=DIAGNOSTIC_DESCRIPTIONS.get(code, "Diagnostic error"),
                initial_run_count=init_runs_c,
                repaired_run_count=rep_runs_c,
                resolved_count=res_c,
                persistent_count=pers_c,
                newly_introduced_count=new_c,
            )

        repair_summary = RepairSummaryStats(
            trials_repair_attempted=len(rep_attempted_trials),
            trials_repair_skipped_clean=len(rep_skipped_clean),
            initially_failing_runs_count=init_failing_count,
            initially_failing_runs_repaired_to_zero_hf=repaired_to_zero_hf_count,
            repair_success_rate=repair_success_rate,
            initial_mean_score=init_mean_score,
            initial_median_score=init_median_score,
            initial_hard_failure_run_count=init_hf_count,
            initial_hard_failure_rate=init_hf_rate,
            repaired_mean_score=mean_score,
            repaired_median_score=median_score,
            repaired_hard_failure_run_count=hard_failure_run_count,
            repaired_hard_failure_rate=hard_failure_rate,
            mean_score_delta=mean_delta,
            trials_improved_count=improved_cnt,
            trials_improved_pct=improved_pct,
            trials_unchanged_count=unchanged_cnt,
            trials_unchanged_pct=unchanged_pct,
            trials_worsened_count=worsened_cnt,
            trials_worsened_pct=worsened_pct,
            total_diagnostics_resolved=tot_resolved,
            total_diagnostics_persistent=tot_persistent,
            total_diagnostics_introduced=tot_new,
            diagnostic_transitions=trans_map,
        )

    return ExperimentSummary(
        experiment_id=experiment_id,
        case_id=case_id,
        provider=provider,
        model=model,
        mode=mode,
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
        diagnostic_frequency=sorted_frequency,
        diagnostic_incidence=sorted_incidence,
        diagnostic_stats=diagnostic_stats_map,
        failure_category_frequency=sorted_categories,
        grader_statistics=grader_stats,
        repair_stats=repair_summary,
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

    if summary.mode == "repair":
        mode_title = "Deterministic Feedback Repair"
        milestone_num = 3
    elif summary.mode == "structured":
        mode_title = "Structured Analyst"
        milestone_num = 2
    else:
        mode_title = "Direct Analyst Baseline"
        milestone_num = 1

    lines: list[str] = [
        f"# Milestone {milestone_num} — {mode_title} Report",
        "",
        f"- **Experiment ID**: `{summary.experiment_id}`",
        f"- **Case**: `{summary.case_id}`",
        f"- **Mode**: `{summary.mode}`",
        f"- **Provider / Model**: `{summary.provider}` / `{summary.model}`",
        f"- **Completed Runs**: {summary.completed_model_calls} / {summary.requested_runs}",
        f"- **Parse Success**: {summary.parsed_runs}/{summary.completed_model_calls} "
        f"({parse_rate_pct})",
        "",
    ]

    # If repair mode, show repair-specific summary section
    if summary.mode == "repair" and summary.repair_stats is not None:
        rs = summary.repair_stats
        init_m = f"{rs.initial_mean_score:.1f}" if rs.initial_mean_score is not None else "N/A"
        rep_m = f"{rs.repaired_mean_score:.1f}" if rs.repaired_mean_score is not None else "N/A"
        succ_rate_pct = f"{rs.repair_success_rate:.1%}"
        succ_str = (
            f"{rs.initially_failing_runs_repaired_to_zero_hf}/"
            f"{rs.initially_failing_runs_count} runs"
        )
        init_hf_desc = (
            f"{rs.initial_hard_failure_rate:.1%} "
            f"({rs.initial_hard_failure_run_count} runs)"
        )
        rep_hf_desc = (
            f"{rs.repaired_hard_failure_rate:.1%} "
            f"({rs.repaired_hard_failure_run_count} runs)"
        )
        hf_delta_desc = (
            f"{(rs.repaired_hard_failure_rate - rs.initial_hard_failure_rate):+.1%}"
        )

        lines.extend([
            "## Repair Performance Summary",
            "",
            "| Metric | Initial | Repaired / Final | Delta |",
            "|---|---:|---:|---:|",
            f"| **Mean Score** | {init_m} / 100 | {rep_m} / 100 | {rs.mean_score_delta:+.1f} |",
            f"| **Hard-Failure Rate** | {init_hf_desc} | {rep_hf_desc} | {hf_delta_desc} |",
            f"| **Repair Success Rate** | — | **{succ_rate_pct}** ({succ_str}) | — |",
            "",
            "### Repair Effectiveness",
            f"- **Trials Improved**: {rs.trials_improved_count} ({rs.trials_improved_pct:.1%})",
            f"- **Trials Unchanged**: {rs.trials_unchanged_count} ({rs.trials_unchanged_pct:.1%})",
            f"- **Trials Worsened**: {rs.trials_worsened_count} ({rs.trials_worsened_pct:.1%})",
            f"- **Diagnostics Resolved**: {rs.total_diagnostics_resolved}",
            f"- **Diagnostics Persistent**: {rs.total_diagnostics_persistent}",
            f"- **Diagnostics Newly Introduced**: {rs.total_diagnostics_introduced}",
            "",
            "## Individual Run Breakdown",
            "",
            "| Run | Initial | Repaired | Δ Score | Init HF | Rep HF | Result | Latency |",
            "|---|---:|---:|---:|:---:|:---:|---|---:|",
        ])

        for t in trial_results:
            m = t.metadata
            init_s = f"{m.initial_score:.1f}" if m.initial_score is not None else "N/A"
            rep_s = f"{m.score:.1f}" if m.score is not None else "N/A"
            d_s = f"{m.score_delta:+.1f}" if m.score_delta is not None else "N/A"
            init_hf = str(m.initial_hard_failure_count) if m.initial_parsed_successfully else "N/A"
            rep_hf = str(m.hard_failure_count) if m.parsed_successfully else "N/A"

            if m.repair_skipped_reason == "initial_submission_clean":
                res_str = "Already Clean"
            elif m.repair_attempted:
                if m.hard_failure_count == 0 and m.parsed_successfully:
                    res_str = "Repaired (Clean)"
                elif m.score_delta is not None and m.score_delta > 0:
                    res_str = "Partially Repaired"
                elif m.score_delta is not None and m.score_delta < 0:
                    res_str = "Worsened"
                else:
                    res_str = "Unchanged"
            else:
                res_str = "Parse Failure"

            lat_str = f"{m.latency_seconds:.2f}s" if m.latency_seconds is not None else "N/A"
            lines.append(
                f"| `{m.run_index:03d}` | {init_s} | {rep_s} | {d_s} | "
                f"{init_hf} | {rep_hf} | {res_str} | {lat_str} |"
            )

        # Diagnostic Transitions Table
        lines.extend([
            "",
            "## Diagnostic Transition Analysis",
            "",
            "| Diagnostic Code | Description | Init Runs | Rep Runs | "
            "Resolved | Persistent | New |",
            "|---|---|---:|---:|---:|---:|---:|",
        ])

        if rs.diagnostic_transitions:
            for code, tr in rs.diagnostic_transitions.items():
                lines.append(
                    f"| `{code}` | {tr.description} | {tr.initial_run_count} | "
                    f"{tr.repaired_run_count} | {tr.resolved_count} | {tr.persistent_count} | "
                    f"{tr.newly_introduced_count} |"
                )
        else:
            lines.append("| *(none)* | No diagnostics recorded | 0 | 0 | 0 | 0 | 0 |")

    else:
        # Standard summary table for direct and structured modes
        lines.extend([
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
        ])

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
            "| Diagnostic Code | Description | Occurrences | Run Incidence | Run % |",
            "|---|---|---:|---:|---:|",
        ])

        if summary.diagnostic_stats:
            for code, stat in summary.diagnostic_stats.items():
                run_pct = f"{stat.run_incidence_rate:.1%}"
                inc_str = f"{stat.run_count} / {summary.parsed_runs} runs"
                lines.append(
                    f"| `{code}` | {stat.description} | {stat.occurrence_count} | "
                    f"{inc_str} | {run_pct} |"
                )
        else:
            lines.append("| *(none)* | No diagnostic failures recorded | 0 | 0 / 0 runs | 0.0% |")

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


def compare_experiments(exp_a: ExperimentSummary, exp_b: ExperimentSummary) -> str:
    """Generate a side-by-side comparative Markdown report between two experiment summaries."""
    lines: list[str] = [
        "# Experiment Comparison Report",
        "",
        "| Parameter | Experiment A | Experiment B |",
        "|---|---|---|",
        f"| **ID** | `{exp_a.experiment_id}` | `{exp_b.experiment_id}` |",
        f"| **Mode** | `{exp_a.mode}` | `{exp_b.mode}` |",
        f"| **Provider / Model** | `{exp_a.provider}` / `{exp_a.model}` | "
        f"`{exp_b.provider}` / `{exp_b.model}` |",
        f"| **Requested Runs** | {exp_a.requested_runs} | {exp_b.requested_runs} |",
        f"| **Parsed Runs** | {exp_a.parsed_runs} ({exp_a.parse_success_rate:.1%}) | "
        f"{exp_b.parsed_runs} ({exp_b.parse_success_rate:.1%}) |",
        "",
        "## Summary Metrics Comparison",
        "",
        "| Metric | Experiment A | Experiment B | Delta (B − A) |",
        "|---|---:|---:|---:|",
    ]

    def fmt_score(val: float | None) -> str:
        return f"{val:.1f}" if val is not None else "N/A"

    def fmt_delta(a: float | None, b: float | None) -> str:
        if a is None or b is None:
            return "N/A"
        diff = b - a
        sign = "+" if diff > 0 else ""
        return f"{sign}{diff:.1f}"

    def fmt_pct_delta(a: float, b: float) -> str:
        diff = b - a
        sign = "+" if diff > 0 else ""
        return f"{sign}{diff:.1%}"

    lines.extend([
        f"| **Mean Score** | {fmt_score(exp_a.mean_score)} | {fmt_score(exp_b.mean_score)} | "
        f"{fmt_delta(exp_a.mean_score, exp_b.mean_score)} |",
        f"| **Median Score** | {fmt_score(exp_a.median_score)} | {fmt_score(exp_b.median_score)} | "
        f"{fmt_delta(exp_a.median_score, exp_b.median_score)} |",
        f"| **Std Deviation** | {fmt_score(exp_a.standard_deviation)} | "
        f"{fmt_score(exp_b.standard_deviation)} | "
        f"{fmt_delta(exp_a.standard_deviation, exp_b.standard_deviation)} |",
        f"| **Parse Success Rate** | {exp_a.parse_success_rate:.1%} | "
        f"{exp_b.parse_success_rate:.1%} | "
        f"{fmt_pct_delta(exp_a.parse_success_rate, exp_b.parse_success_rate)} |",
        f"| **Hard-Failure Rate** | {exp_a.hard_failure_rate:.1%} | "
        f"{exp_b.hard_failure_rate:.1%} | "
        f"{fmt_pct_delta(exp_a.hard_failure_rate, exp_b.hard_failure_rate)} |",
    ])

    # If Experiment B is a repair run, report repair effectiveness
    if exp_b.repair_stats is not None:
        rs_b = exp_b.repair_stats
        lines.extend([
            "",
            "## Repair Effectiveness (Experiment B)",
            "",
            f"- **Repair Success Rate**: **{rs_b.repair_success_rate:.1%}** "
            f"({rs_b.initially_failing_runs_repaired_to_zero_hf}/"
            f"{rs_b.initially_failing_runs_count} initially failing runs)",
            f"- **Trials Improved**: {rs_b.trials_improved_count} ({rs_b.trials_improved_pct:.1%})",
            f"- **Trials Unchanged**: {rs_b.trials_unchanged_count} "
            f"({rs_b.trials_unchanged_pct:.1%})",
            f"- **Trials Worsened**: {rs_b.trials_worsened_count} ({rs_b.trials_worsened_pct:.1%})",
            f"- **Diagnostics Resolved**: {rs_b.total_diagnostics_resolved}",
            f"- **Diagnostics Persistent**: {rs_b.total_diagnostics_persistent}",
            f"- **Diagnostics Introduced**: {rs_b.total_diagnostics_introduced}",
        ])

    # Key Diagnostic Run Incidence Comparison
    all_diag_codes = sorted(
        set(exp_a.diagnostic_stats.keys()) | set(exp_b.diagnostic_stats.keys())
    )

    lines.extend([
        "",
        "## Key Diagnostic Run-Level Incidence",
        "",
        "| Diagnostic Code | Description | Exp A Run % | Exp B Run % | Incidence Delta |",
        "|---|---|---:|---:|---:|",
    ])

    if all_diag_codes:
        for code in all_diag_codes:
            stat_a = exp_a.diagnostic_stats.get(code)
            stat_b = exp_b.diagnostic_stats.get(code)
            rate_a = stat_a.run_incidence_rate if stat_a else 0.0
            rate_b = stat_b.run_incidence_rate if stat_b else 0.0
            desc = (
                (stat_a.description if stat_a else None)
                or (stat_b.description if stat_b else None)
                or DIAGNOSTIC_DESCRIPTIONS.get(code, "Diagnostic error")
            )
            diff = rate_b - rate_a
            diff_sign = "+" if diff > 0 else ""
            lines.append(
                f"| `{code}` | {desc} | {rate_a:.1%} | {rate_b:.1%} | {diff_sign}{diff:.1%} |"
            )
    else:
        lines.append("| *(none)* | No diagnostics recorded | 0.0% | 0.0% | 0.0% |")

    # Grader Pass Rate Comparison
    all_graders = sorted(
        set(exp_a.grader_statistics.keys()) | set(exp_b.grader_statistics.keys())
    )
    lines.extend([
        "",
        "## Grader Pass Rate Comparison",
        "",
        "| Grader | Exp A Pass Rate | Exp B Pass Rate | Delta |",
        "|---|---:|---:|---:|",
    ])

    for g in all_graders:
        g_a = exp_a.grader_statistics.get(g)
        g_b = exp_b.grader_statistics.get(g)
        p_a = g_a.pass_rate if g_a else 0.0
        p_b = g_b.pass_rate if g_b else 0.0
        diff = p_b - p_a
        diff_sign = "+" if diff > 0 else ""
        lines.append(f"| `{g}` | {p_a:.1%} | {p_b:.1%} | {diff_sign}{diff:.1%} |")

    lines.append("")
    return "\n".join(lines)
