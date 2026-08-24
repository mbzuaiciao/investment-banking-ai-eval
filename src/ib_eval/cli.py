"""CLI entry point for ib-eval."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from ib_eval.case import load_case
from ib_eval.paths import resolve_default_output_dir
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission

# Load local .env if present; shell environment takes precedence (override=False by default)
load_dotenv()

_CASES_DIR = Path(__file__).parent.parent.parent / "cases"
_CORRUPTED_DIR = Path(__file__).parent.parent.parent / "examples" / "corrupted"


def _find_submission_file(submission_dir: Path) -> Path:
    """Locate the submission JSON file in a directory."""
    candidate = submission_dir / "submission.json"
    if candidate.exists():
        return candidate
    # Fall back to any .json file
    jsons = list(submission_dir.glob("*.json"))
    if len(jsons) == 1:
        return jsons[0]
    if jsons:
        raise click.ClickException(
            f"Multiple JSON files found in {submission_dir}. "
            "Please rename one to 'submission.json'."
        )
    raise click.ClickException(f"No submission.json found in {submission_dir}")


@click.group()
def main() -> None:
    """IB-Eval — Investment Banking AI Evaluation Harness."""


@main.command()
@click.argument("submission_path", type=click.Path(exists=True))
@click.option("--case-dir", default=None, help="Path to case directory (auto-detected if omitted)")
@click.option("--json-output", is_flag=True, default=False, help="Output full JSON report")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Only print final score line")
def grade(
    submission_path: str,
    case_dir: str | None,
    json_output: bool,
    quiet: bool,
) -> None:
    """Grade a submission directory or JSON file."""
    path = Path(submission_path)
    submission_file = _find_submission_file(path) if path.is_dir() else path

    try:
        raw = json.loads(submission_file.read_text())
        submission = Submission.model_validate(raw)
    except Exception as exc:
        raise click.ClickException(f"Failed to parse submission: {exc}") from exc

    # Load case
    if case_dir is not None:
        case = load_case(Path(case_dir))
    else:
        case_path = _CASES_DIR / submission.case_id
        if not case_path.exists():
            if "meridian" in submission.case_id.lower() and (_CASES_DIR / "meridian-v1").exists():
                case_path = _CASES_DIR / "meridian-v1"
            elif (
                "northstar" in submission.case_id.lower()
                and (_CASES_DIR / "northstar-v1").exists()
            ):
                case_path = _CASES_DIR / "northstar-v1"
            else:
                raise click.ClickException(
                    f"Case directory not found: {case_path}. Use --case-dir to specify manually."
                )
        case = load_case(case_path)

    report = grade_submission(submission, case)

    if json_output:
        click.echo(json.dumps(report.model_dump(), indent=2))
        return

    if quiet:
        click.echo(f"{report.total_score:.0f} / {report.max_score:.0f}")
        return

    # Human-readable output
    click.echo()
    click.echo(f"  Case:     {report.case_id}")
    click.echo(f"  Analyst:  {report.analyst}")
    click.echo(f"  Score:    {report.total_score:.1f} / {report.max_score:.0f}  ({report.grade})")
    click.echo()

    # Per-grader breakdown
    click.echo("  Grader breakdown:")
    for r in report.grader_results:
        status = "✓" if r.passed else "✗"
        click.echo(f"    {status} {r.grader:<25} {r.points_earned:5.1f} / {r.max_points:5.1f}")

    click.echo()

    # Hard failures
    if report.hard_failures:
        click.echo(f"  Hard failures ({len(report.hard_failures)}):")
        for f in report.hard_failures:
            click.echo(f"    [{f.severity.value.upper()}] {f.diagnostic_code}: {f.message}")
        click.echo()
    else:
        click.echo("  No hard failures.")
        click.echo()

    # Final score line — must be exactly this format for test matching
    score_int = round(report.total_score)
    max_int = round(report.max_score)
    click.echo(f"{score_int} / {max_int}")

    if report.total_score < report.max_score:
        sys.exit(1)


@main.command()
@click.option(
    "--case",
    "case_id",
    default="northstar-v1",
    help="Case ID to evaluate (default: northstar-v1)",
)
@click.option(
    "--case-dir",
    default=None,
    help="Explicit path to case directory (overrides --case)",
)
@click.option(
    "--provider",
    default="openai",
    help="Provider name: openai, deepseek, mock (default: openai)",
)
@click.option(
    "--model",
    default="gpt-4o",
    help="Model name identifier (default: gpt-4o)",
)
@click.option(
    "--mode",
    type=click.Choice(["direct", "structured", "repair"], case_sensitive=False),
    default="direct",
    help="Experiment mode: direct (M1), structured (M2), or repair (M3) (default: direct)",
)
@click.option(
    "--runs",
    default=1,
    type=int,
    help="Number of independent trials to execute (default: 1)",
)
@click.option(
    "--output",
    "output_dir",
    default=None,
    help=(
        "Output directory for artifacts "
        "(default: results/milestone-1 for direct, "
        "results/milestone-2 for structured, "
        "results/milestone-3 for repair)"
    ),
)
@click.option(
    "--temperature",
    type=float,
    default=None,
    help="Sampling temperature",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for provider calls",
)
@click.option(
    "--thinking",
    type=click.Choice(["on", "off", "true", "false"], case_sensitive=False),
    default=None,
    help="Enable or disable thinking / reasoning mode (on, off)",
)
@click.option(
    "--reasoning-effort",
    type=click.Choice(["low", "medium", "high"], case_sensitive=False),
    default=None,
    help="Reasoning effort level for thinking mode (low, medium, high)",
)
@click.option(
    "--execute",
    is_flag=True,
    default=False,
    help="Execute live API calls (required guardrail)",
)
def baseline(
    case_id: str,
    case_dir: str | None,
    provider: str,
    model: str,
    mode: str,
    runs: int,
    output_dir: str | None,
    temperature: float | None,
    seed: int | None,
    thinking: str | None,
    reasoning_effort: str | None,
    execute: bool,
) -> None:
    """Run Direct (M1), Structured (M2), or Repair (M3) Analyst Baseline experiment."""
    from ib_eval.baseline.interface import ProviderConfig
    from ib_eval.baseline.providers import DeepSeekAnalyst, MockAnalyst, OpenAIAnalyst
    from ib_eval.baseline.runner import run_baseline_experiment

    # Resolve case
    case_path = Path(case_dir) if case_dir is not None else _CASES_DIR / case_id
    if not case_path.exists():
        raise click.ClickException(f"Case directory not found: {case_path}")

    case_obj = load_case(case_path)
    mode_normalized = mode.lower()

    # Resolve output directory based on case and mode if not explicitly provided
    if output_dir is not None:
        out_path = Path(output_dir)
    else:
        out_path = resolve_default_output_dir(case_obj.meta.case_id, mode_normalized)

    thinking_bool: bool | None = None
    if thinking is not None:
        thinking_bool = thinking.lower() in ("on", "true")

    if reasoning_effort is not None:
        reasoning_effort = reasoning_effort.lower()
        if thinking_bool is False:
            raise click.ClickException(
                "Cannot specify --reasoning-effort when --thinking is set to 'off'."
            )

    config = ProviderConfig(
        provider=provider,
        model=model,
        mode=mode_normalized,
        temperature=temperature,
        seed=seed,
        thinking=thinking_bool,
        reasoning_effort=reasoning_effort,
    )

    # Cost / Confirmation guardrail
    if "meridian" in case_obj.meta.case_id.lower():
        if mode_normalized == "repair":
            milestone_label = "Milestone 4E: Meridian Deterministic Feedback Repair"
        elif mode_normalized == "structured":
            milestone_label = "Milestone 4D: Meridian Structured Analyst"
        else:
            milestone_label = "Milestone 4C: Meridian Direct Baseline"
    else:
        if mode_normalized == "repair":
            milestone_label = "Milestone 3: Deterministic Feedback Repair"
        elif mode_normalized == "structured":
            milestone_label = "Milestone 2: Structured Analyst"
        else:
            milestone_label = "Milestone 1: Direct Analyst Baseline"
    click.echo("==================================================")
    click.echo(f"  IB-Eval — {milestone_label}")
    click.echo("==================================================")
    click.echo(f"  Case:        {case_obj.meta.case_id} ({case_obj.meta.company})")
    click.echo(f"  Mode:        {mode_normalized}")
    click.echo(f"  Provider:    {provider}")
    click.echo(f"  Model:       {model}")
    click.echo(f"  Trials:      {runs}")
    click.echo(f"  Output Dir:  {out_path}")
    if temperature is not None:
        click.echo(f"  Temperature: {temperature}")
    if seed is not None:
        click.echo(f"  Seed:        {seed}")
    if thinking_bool is not None:
        click.echo(f"  Thinking:    {'on' if thinking_bool else 'off'}")
    if reasoning_effort is not None:
        click.echo(f"  Reasoning:   {reasoning_effort}")
    click.echo("--------------------------------------------------")

    if not execute:
        click.echo()
        click.echo("  [DRY-RUN / GUARDRAIL ACTIVE]")
        click.echo("  Live provider calls were NOT executed.")
        click.echo("  To execute live trials, re-run with the --execute flag:")
        click.echo()
        flags: list[str] = []
        if mode_normalized != "direct":
            flags.append(f"--mode {mode_normalized}")
        if thinking is not None:
            flags.append(f"--thinking {thinking.lower()}")
        if reasoning_effort is not None:
            flags.append(f"--reasoning-effort {reasoning_effort.lower()}")
        if output_dir is not None:
            flags.append(f"--output {output_dir}")
        extra_flags = f" {' '.join(flags)}" if flags else ""
        click.echo(
            f"    uv run ib-eval baseline --case {case_id} --provider {provider} "
            f"--model {model}{extra_flags} --runs {runs} --execute"
        )
        click.echo()
        return

    # Instantiate provider
    if provider == "openai":
        try:
            analyst = OpenAIAnalyst(config=config)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
    elif provider == "deepseek":
        try:
            analyst = DeepSeekAnalyst(config=config)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
    elif provider == "mock":
        # Uses empty mock response by default if not configured
        analyst = MockAnalyst()
    else:
        raise click.ClickException(
            f"Unsupported provider: {provider}. Supported: openai, deepseek, mock"
        )

    click.echo(f"  Running {runs} trial(s)...")
    res = run_baseline_experiment(
        case=case_obj,
        analyst_provider=analyst,
        config=config,
        runs=runs,
        output_dir=out_path,
    )

    click.echo("--------------------------------------------------")
    click.echo(f"  Experiment ID: {res.experiment_id}")
    click.echo(f"  Completed:     {res.summary.completed_model_calls} / {runs}")
    click.echo(
        f"  Parsed:        {res.summary.parsed_runs}/{res.summary.completed_model_calls} "
        f"({res.summary.parse_success_rate:.1%})"
    )
    if res.summary.mean_score is not None:
        click.echo(f"  Mean Score:    {res.summary.mean_score:.1f} / 100")
        click.echo(f"  Median Score:  {res.summary.median_score:.1f} / 100")
    click.echo(f"  Hard Failures: {res.summary.hard_failure_run_count} run(s)")
    click.echo(f"  Artifacts saved to: {res.experiment_dir}")
    click.echo("==================================================")


@main.command()
@click.argument("exp_dir_a", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("exp_dir_b", type=click.Path(exists=True, file_okay=False, path_type=Path))
def compare(exp_dir_a: Path, exp_dir_b: Path) -> None:
    """Compare two experiment runs side-by-side."""
    import json

    from ib_eval.baseline.analysis import ExperimentSummary, compare_experiments

    sum_file_a = exp_dir_a / "summary.json"
    sum_file_b = exp_dir_b / "summary.json"

    if not sum_file_a.exists():
        raise click.ClickException(f"summary.json not found in: {exp_dir_a}")
    if not sum_file_b.exists():
        raise click.ClickException(f"summary.json not found in: {exp_dir_b}")

    try:
        data_a = json.loads(sum_file_a.read_text())
        summary_a = ExperimentSummary.model_validate(data_a)
    except Exception as exc:
        raise click.ClickException(f"Failed to parse {sum_file_a}: {exc}") from exc

    try:
        data_b = json.loads(sum_file_b.read_text())
        summary_b = ExperimentSummary.model_validate(data_b)
    except Exception as exc:
        raise click.ClickException(f"Failed to parse {sum_file_b}: {exc}") from exc

    report = compare_experiments(summary_a, summary_b)
    click.echo(report)


@main.command(name="repair-benchmark")
@click.option(
    "--case",
    "case_id",
    default="northstar-v1",
    help="Case identifier to evaluate against (default: northstar-v1)",
)
@click.option(
    "--case-dir",
    default=None,
    help="Path to case directory (overrides --case)",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "deepseek", "mock"], case_sensitive=False),
    default="deepseek",
    help="Analyst provider to invoke (default: deepseek)",
)
@click.option(
    "--model",
    default="deepseek-v4-flash",
    help="Model identifier (default: deepseek-v4-flash)",
)
@click.option(
    "--fixtures",
    "fixtures_selector",
    default="all",
    help="Fixtures to test: 'all' or comma-separated IDs (e.g. 'c02,c08,c10') (default: all)",
)
@click.option(
    "--output",
    "output_dir",
    default=None,
    help="Output directory for artifacts (default: results/milestone-3b)",
)
@click.option(
    "--temperature",
    type=float,
    default=None,
    help="Sampling temperature",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for provider calls",
)
@click.option(
    "--thinking",
    type=click.Choice(["on", "off", "true", "false"], case_sensitive=False),
    default=None,
    help="Enable or disable thinking / reasoning mode (on, off)",
)
@click.option(
    "--reasoning-effort",
    type=click.Choice(["low", "medium", "high"], case_sensitive=False),
    default=None,
    help="Reasoning effort level for thinking mode (low, medium, high)",
)
@click.option(
    "--execute",
    is_flag=True,
    default=False,
    help="Execute live API calls (required guardrail)",
)
def repair_benchmark(
    case_id: str,
    case_dir: str | None,
    provider: str,
    model: str,
    fixtures_selector: str,
    output_dir: str | None,
    temperature: float | None,
    seed: int | None,
    thinking: str | None,
    reasoning_effort: str | None,
    execute: bool,
) -> None:
    """Run the Milestone 3B Controlled Repair Benchmark against known corrupted fixtures."""
    from ib_eval.baseline.interface import ProviderConfig
    from ib_eval.baseline.providers import DeepSeekAnalyst, MockAnalyst, OpenAIAnalyst
    from ib_eval.controlled_repair import resolve_fixtures, run_controlled_repair_benchmark

    case_path = Path(case_dir) if case_dir is not None else _CASES_DIR / case_id
    if not case_path.exists():
        raise click.ClickException(f"Case directory not found: {case_path}")

    case_obj = load_case(case_path)
    if output_dir is not None:
        out_path = Path(output_dir)
    else:
        out_path = resolve_default_output_dir(case_obj.meta.case_id, "controlled-repair")

    corrupted_dir = (
        Path(__file__).parent.parent.parent / "examples" / "meridian_corrupted"
        if "meridian" in case_obj.meta.case_id.lower()
        else _CORRUPTED_DIR
    )

    try:
        fixtures_to_run = resolve_fixtures(fixtures_selector, corrupted_dir)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    thinking_bool: bool | None = None
    if thinking is not None:
        thinking_bool = thinking.lower() in ("on", "true")

    if reasoning_effort is not None:
        reasoning_effort = reasoning_effort.lower()
        if thinking_bool is False:
            raise click.ClickException(
                "Cannot specify --reasoning-effort when --thinking is set to 'off'."
            )

    config = ProviderConfig(
        provider=provider,
        model=model,
        mode="controlled-repair",
        temperature=temperature,
        seed=seed,
        thinking=thinking_bool,
        reasoning_effort=reasoning_effort,
    )

    fixture_ids = [f.fixture_id for f in fixtures_to_run]
    if "meridian" in case_obj.meta.case_id.lower():
        milestone_label = "Milestone 4E: Meridian Controlled Repair Benchmark"
    else:
        milestone_label = "Milestone 3B: Controlled Repair Benchmark"

    click.echo("==================================================")
    click.echo(f"  IB-Eval — {milestone_label}")
    click.echo("==================================================")
    click.echo(f"  Case:        {case_obj.meta.case_id} ({case_obj.meta.company})")
    click.echo("  Mode:        controlled-repair")
    click.echo(f"  Provider:    {provider}")
    click.echo(f"  Model:       {model}")
    click.echo(f"  Fixtures:    {len(fixtures_to_run)} ({', '.join(fixture_ids)})")
    click.echo(f"  Output Dir:  {out_path}")
    if temperature is not None:
        click.echo(f"  Temperature: {temperature}")
    if seed is not None:
        click.echo(f"  Seed:        {seed}")
    if thinking_bool is not None:
        click.echo(f"  Thinking:    {'on' if thinking_bool else 'off'}")
    if reasoning_effort is not None:
        click.echo(f"  Reasoning:   {reasoning_effort}")
    click.echo("--------------------------------------------------")

    if not execute:
        click.echo()
        click.echo("  [DRY-RUN / GUARDRAIL ACTIVE]")
        click.echo("  Live provider calls were NOT executed.")
        click.echo("  To execute live trials, re-run with the --execute flag:")
        click.echo()
        flags: list[str] = []
        if fixtures_selector != "all":
            flags.append(f"--fixtures {fixtures_selector}")
        if thinking is not None:
            flags.append(f"--thinking {thinking.lower()}")
        if reasoning_effort is not None:
            flags.append(f"--reasoning-effort {reasoning_effort.lower()}")
        if output_dir is not None:
            flags.append(f"--output {output_dir}")
        extra_flags = f" {' '.join(flags)}" if flags else ""
        click.echo(
            f"    uv run ib-eval repair-benchmark --case {case_id} --provider {provider} "
            f"--model {model}{extra_flags} --execute"
        )
        click.echo()
        return

    # Instantiate provider
    if provider == "openai":
        try:
            analyst = OpenAIAnalyst(config=config)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
    elif provider == "deepseek":
        try:
            analyst = DeepSeekAnalyst(config=config)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
    elif provider == "mock":
        analyst = MockAnalyst()
    else:
        raise click.ClickException(
            f"Unsupported provider: {provider}. Supported: openai, deepseek, mock"
        )

    click.echo(f"  Running repair benchmark across {len(fixtures_to_run)} fixture(s)...")
    res = run_controlled_repair_benchmark(
        case=case_obj,
        analyst_provider=analyst,
        config=config,
        fixtures=fixtures_to_run,
        corrupted_dir=corrupted_dir,
        output_dir=out_path,
    )

    s = res.summary
    succ_rate = f"{s.controlled_repair_success_rate:.1%}"
    succ_desc = f"{succ_rate} ({s.controlled_repair_success_count}/{s.total_fixtures_attempted})"
    res_rate = f"{s.target_diagnostic_resolution_rate:.1%}"
    res_desc = f"{res_rate} ({s.target_diagnostic_resolved_count}/{s.total_fixtures_attempted})"
    new_rate = f"{s.new_error_introduction_rate:.1%}"
    new_desc = f"{new_rate} ({s.new_error_introduced_count}/{s.total_fixtures_attempted})"
    click.echo("--------------------------------------------------")
    click.echo(f"  Experiment ID:              {res.experiment_id}")
    click.echo(f"  Controlled Repair Success:  {succ_desc}")
    click.echo(f"  Target Diagnostic Resolved: {res_desc}")
    click.echo(f"  New Error Introduced Rate:  {new_desc}")
    if s.mean_repaired_score is not None:
        click.echo(
            f"  Mean Score Delta:           {s.mean_score_delta:+.1f} "
            f"({s.mean_initial_score:.1f} -> {s.mean_repaired_score:.1f})"
        )
    click.echo(f"  Artifacts saved to:         {res.experiment_dir}")
    click.echo("==================================================")
