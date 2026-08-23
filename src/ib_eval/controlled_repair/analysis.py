"""Statistical aggregation and reporting for Milestone 3B Controlled Repair Benchmark."""

from __future__ import annotations

import statistics

from pydantic import BaseModel, Field


class ControlledFixtureTrialResult(BaseModel):
    """Execution and evaluation result for a single controlled fixture repair trial."""

    fixture_id: str
    dir_name: str
    name: str
    expected_diagnostic: str
    category: str
    difficulty: str
    initial_score: float
    repaired_score: float | None = None
    score_delta: float | None = None
    initial_hard_failure_count: int = 0
    repaired_hard_failure_count: int = 0
    initial_hard_failure_codes: list[str] = Field(default_factory=list[str])
    repaired_hard_failure_codes: list[str] = Field(default_factory=list[str])
    expected_diagnostic_resolved: bool = False
    persistent_diagnostics: list[str] = Field(default_factory=list[str])
    new_diagnostics: list[str] = Field(default_factory=list[str])
    repair_parse_success: bool = False
    repair_success: bool = False
    partial_repair: bool = False
    outcome: str = "persistent"  # "success", "partial", "persistent", "parse_failure"
    latency_seconds: float | None = None
    token_usage: dict[str, int] | None = None


class CategoryRepairStat(BaseModel):
    """Repair rate statistics grouped by error category."""

    category: str
    total_count: int
    resolved_count: int
    resolution_rate: float
    success_count: int
    success_rate: float


class DifficultyRepairStat(BaseModel):
    """Repair rate statistics grouped by propagation difficulty (local vs. propagating)."""

    difficulty: str
    total_count: int
    resolved_count: int
    resolution_rate: float
    success_count: int
    success_rate: float


class ControlledRepairBenchmarkSummary(BaseModel):
    """Complete summary statistics for a controlled repair benchmark run."""

    experiment_id: str
    case_id: str
    provider: str
    model: str
    timestamp: str
    total_fixtures_attempted: int
    parsed_repair_count: int
    parse_success_rate: float
    target_diagnostic_resolved_count: int
    target_diagnostic_resolution_rate: float
    controlled_repair_success_count: int
    controlled_repair_success_rate: float
    partial_repair_count: int
    partial_repair_rate: float
    persistent_failure_count: int
    persistent_failure_rate: float
    new_error_introduced_count: int
    new_error_introduction_rate: float
    mean_initial_score: float
    mean_repaired_score: float | None = None
    mean_score_delta: float | None = None
    category_statistics: dict[str, CategoryRepairStat] = Field(
        default_factory=dict[str, CategoryRepairStat]
    )
    difficulty_statistics: dict[str, DifficultyRepairStat] = Field(
        default_factory=dict[str, DifficultyRepairStat]
    )
    fixture_results: list[ControlledFixtureTrialResult] = Field(
        default_factory=list[ControlledFixtureTrialResult]
    )
    git_commit: str | None = None


def compute_controlled_repair_statistics(
    experiment_id: str,
    case_id: str,
    provider: str,
    model: str,
    timestamp: str,
    trial_results: list[ControlledFixtureTrialResult],
    git_commit: str | None = None,
) -> ControlledRepairBenchmarkSummary:
    """Compute aggregate statistics across all controlled repair trials."""
    total_attempted = len(trial_results)
    parsed_trials = [t for t in trial_results if t.repair_parse_success]
    parsed_count = len(parsed_trials)
    parse_rate = round(parsed_count / total_attempted, 4) if total_attempted > 0 else 0.0

    target_resolved_count = len([t for t in trial_results if t.expected_diagnostic_resolved])
    target_resolution_rate = (
        round(target_resolved_count / total_attempted, 4) if total_attempted > 0 else 0.0
    )

    full_success_count = len([t for t in trial_results if t.repair_success])
    full_success_rate = (
        round(full_success_count / total_attempted, 4) if total_attempted > 0 else 0.0
    )

    partial_count = len([t for t in trial_results if t.partial_repair])
    partial_rate = round(partial_count / total_attempted, 4) if total_attempted > 0 else 0.0

    persistent_count = len(
        [t for t in trial_results if t.repair_parse_success and not t.expected_diagnostic_resolved]
    )
    persistent_rate = round(persistent_count / total_attempted, 4) if total_attempted > 0 else 0.0

    new_error_count = len([t for t in trial_results if len(t.new_diagnostics) > 0])
    new_error_rate = round(new_error_count / total_attempted, 4) if total_attempted > 0 else 0.0

    init_scores = [t.initial_score for t in trial_results]
    mean_init_score = round(statistics.mean(init_scores), 2) if init_scores else 0.0

    rep_scores = [t.repaired_score for t in parsed_trials if t.repaired_score is not None]
    mean_rep_score = round(statistics.mean(rep_scores), 2) if rep_scores else None

    deltas = [t.score_delta for t in parsed_trials if t.score_delta is not None]
    mean_delta = round(statistics.mean(deltas), 2) if deltas else None

    # Error category grouping
    category_map: dict[str, list[ControlledFixtureTrialResult]] = {}
    for t in trial_results:
        category_map.setdefault(t.category, []).append(t)

    cat_stats: dict[str, CategoryRepairStat] = {}
    for cat, items in sorted(category_map.items()):
        c_tot = len(items)
        c_res = len([i for i in items if i.expected_diagnostic_resolved])
        c_succ = len([i for i in items if i.repair_success])
        cat_stats[cat] = CategoryRepairStat(
            category=cat,
            total_count=c_tot,
            resolved_count=c_res,
            resolution_rate=round(c_res / c_tot, 4) if c_tot > 0 else 0.0,
            success_count=c_succ,
            success_rate=round(c_succ / c_tot, 4) if c_tot > 0 else 0.0,
        )

    # Difficulty grouping
    diff_map: dict[str, list[ControlledFixtureTrialResult]] = {}
    for t in trial_results:
        diff_map.setdefault(t.difficulty, []).append(t)

    diff_stats: dict[str, DifficultyRepairStat] = {}
    for diff, items in sorted(diff_map.items()):
        d_tot = len(items)
        d_res = len([i for i in items if i.expected_diagnostic_resolved])
        d_succ = len([i for i in items if i.repair_success])
        diff_stats[diff] = DifficultyRepairStat(
            difficulty=diff,
            total_count=d_tot,
            resolved_count=d_res,
            resolution_rate=round(d_res / d_tot, 4) if d_tot > 0 else 0.0,
            success_count=d_succ,
            success_rate=round(d_succ / d_tot, 4) if d_tot > 0 else 0.0,
        )

    return ControlledRepairBenchmarkSummary(
        experiment_id=experiment_id,
        case_id=case_id,
        provider=provider,
        model=model,
        timestamp=timestamp,
        total_fixtures_attempted=total_attempted,
        parsed_repair_count=parsed_count,
        parse_success_rate=parse_rate,
        target_diagnostic_resolved_count=target_resolved_count,
        target_diagnostic_resolution_rate=target_resolution_rate,
        controlled_repair_success_count=full_success_count,
        controlled_repair_success_rate=full_success_rate,
        partial_repair_count=partial_count,
        partial_repair_rate=partial_rate,
        persistent_failure_count=persistent_count,
        persistent_failure_rate=persistent_rate,
        new_error_introduced_count=new_error_count,
        new_error_introduction_rate=new_error_rate,
        mean_initial_score=mean_init_score,
        mean_repaired_score=mean_rep_score,
        mean_score_delta=mean_delta,
        category_statistics=cat_stats,
        difficulty_statistics=diff_stats,
        fixture_results=trial_results,
        git_commit=git_commit,
    )


def generate_controlled_repair_markdown_summary(
    summary: ControlledRepairBenchmarkSummary,
) -> str:
    """Deterministically format controlled repair summary into a rich Markdown report."""
    mean_init_str = f"{summary.mean_initial_score:.1f}"
    mean_rep_str = (
        f"{summary.mean_repaired_score:.1f}" if summary.mean_repaired_score is not None else "N/A"
    )
    mean_delta_str = (
        f"{summary.mean_score_delta:+.1f}" if summary.mean_score_delta is not None else "N/A"
    )

    succ_pct = f"{summary.controlled_repair_success_rate:.1%}"
    res_pct = f"{summary.target_diagnostic_resolution_rate:.1%}"
    new_pct = f"{summary.new_error_introduction_rate:.1%}"
    parse_pct = f"{summary.parse_success_rate:.1%}"

    lines: list[str] = [
        "# Milestone 3B — Controlled Repair Benchmark Report",
        "",
        f"- **Experiment ID**: `{summary.experiment_id}`",
        f"- **Case**: `{summary.case_id}`",
        f"- **Provider / Model**: `{summary.provider}` / `{summary.model}`",
        f"- **Fixtures Attempted**: {summary.total_fixtures_attempted}",
        f"- **Parse Success**: {summary.parsed_repair_count}/{summary.total_fixtures_attempted} "
        f"({parse_pct})",
        "",
        "## Headline Benchmark Metrics",
        "",
        "| Metric | Value | Meaning |",
        "|---|---|---|",
        f"| **Controlled Repair Success Rate** | **{succ_pct}** "
        f"({summary.controlled_repair_success_count}/{summary.total_fixtures_attempted}) | "
        "Target resolved with 0 remaining hard failures |",
        f"| **Target Diagnostic Resolution Rate** | **{res_pct}** "
        f"({summary.target_diagnostic_resolved_count}/{summary.total_fixtures_attempted}) | "
        "Target error disappeared after feedback |",
        f"| **New Error Introduction Rate** | **{new_pct}** "
        f"({summary.new_error_introduced_count}/{summary.total_fixtures_attempted}) | "
        "Repair turn introduced ≥ 1 new diagnostic |",
        f"| **Partial Repair Rate** | {summary.partial_repair_rate:.1%} "
        f"({summary.partial_repair_count}/{summary.total_fixtures_attempted}) | "
        "Target resolved but other hard failures remain |",
        f"| **Persistent Failure Rate** | {summary.persistent_failure_rate:.1%} "
        f"({summary.persistent_failure_count}/{summary.total_fixtures_attempted}) | "
        "Target diagnostic persisted after repair |",
        f"| **Mean Score Delta** | {mean_delta_str} "
        f"({mean_init_str} $\\rightarrow$ {mean_rep_str}) | "
        "Average score shift across attempted fixtures |",
        "",
        "## Per-Fixture Outcome Table",
        "",
        "| ID | Fixture Name | Target Diagnostic | Category | Difficulty | "
        "Init Score | Rep Score | Δ Score | Target Resolved? | Final HF | Outcome |",
        "|:---:|---|---|---|:---:|---:|---:|---:|:---:|:---:|---|",
    ]

    for t in summary.fixture_results:
        rep_s = f"{t.repaired_score:.1f}" if t.repaired_score is not None else "N/A"
        delta_s = f"{t.score_delta:+.1f}" if t.score_delta is not None else "N/A"
        res_flag = "✓ Yes" if t.expected_diagnostic_resolved else "✗ No"

        outcome_display = {
            "success": "✓ Success (Clean)",
            "partial": "⚠ Partial Repair",
            "persistent": "✗ Persistent Error",
            "parse_failure": "✗ Parse Failure",
        }.get(t.outcome, t.outcome)

        lines.append(
            f"| `{t.fixture_id}` | {t.name} | `{t.expected_diagnostic}` | "
            f"{t.category} | {t.difficulty} | {t.initial_score:.1f} | "
            f"{rep_s} | {delta_s} | {res_flag} | {t.repaired_hard_failure_count} | "
            f"{outcome_display} |"
        )

    lines.extend(
        [
            "",
            "## Error-Category Repair Performance",
            "",
            "| Error Category | Fixtures | Target Resolved | Target Resolution % | "
            "Full Clean Success | Clean Success % |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )

    for cat, c_stat in summary.category_statistics.items():
        lines.append(
            f"| `{cat}` | {c_stat.total_count} | {c_stat.resolved_count} | "
            f"{c_stat.resolution_rate:.1%} | {c_stat.success_count} | "
            f"{c_stat.success_rate:.1%} |"
        )

    lines.extend(
        [
            "",
            "## Difficulty Analysis (Local vs. Propagating Repairs)",
            "",
            "| Difficulty | Description | Fixtures | Target Resolution % | Clean Success % |",
            "|---|---|---:|---:|---:|",
        ]
    )

    for diff, d_stat in summary.difficulty_statistics.items():
        desc = (
            "Single-schedule / localized edits (e.g. Comps median, provenance tag, headline)"
            if diff == "local"
            else "Cascading dependencies (e.g. WACC, base revenue, Capex, TV discounting)"
        )
        lines.append(
            f"| **{diff.capitalize()}** | {desc} | {d_stat.total_count} | "
            f"{d_stat.resolution_rate:.1%} | {d_stat.success_rate:.1%} |"
        )

    # Diagnostic Transitions & New Errors
    lines.extend(
        [
            "",
            "## Diagnostic Transitions & Regression Invariant Auditing",
            "",
            "| Fixture ID | Target Diagnostic | Resolved? | Persistent Codes | "
            "Newly Introduced Codes |",
            "|:---:|---|:---:|---|---|",
        ]
    )

    for t in summary.fixture_results:
        res_flag = "Yes" if t.expected_diagnostic_resolved else "No"
        pers_str = (
            ", ".join(f"`{c}`" for c in t.persistent_diagnostics)
            if t.persistent_diagnostics
            else "—"
        )
        new_str = ", ".join(f"`{c}`" for c in t.new_diagnostics) if t.new_diagnostics else "—"
        lines.append(
            f"| `{t.fixture_id}` | `{t.expected_diagnostic}` | {res_flag} | "
            f"{pers_str} | {new_str} |"
        )

    lines.append("")
    return "\n".join(lines)
