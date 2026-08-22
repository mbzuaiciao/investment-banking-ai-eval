"""CLI entry point for ib-eval."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from ib_eval.case import load_case
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission

_CASES_DIR = Path(__file__).parent.parent.parent / "cases"


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
            raise click.ClickException(
                f"Case directory not found: {case_path}. "
                "Use --case-dir to specify manually."
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
        click.echo(
            f"    {status} {r.grader:<25} {r.points_earned:5.1f} / {r.max_points:5.1f}"
        )

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
    type=click.Choice(["direct", "structured"], case_sensitive=False),
    default="direct",
    help="Experiment mode: direct (M1) or structured (M2) (default: direct)",
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
        "(default: results/milestone-1 for direct, results/milestone-2 for structured)"
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
    """Run the Direct (M1) or Structured (M2) Analyst Baseline experiment."""
    from ib_eval.baseline.interface import ProviderConfig
    from ib_eval.baseline.providers import DeepSeekAnalyst, MockAnalyst, OpenAIAnalyst
    from ib_eval.baseline.runner import run_baseline_experiment

    # Resolve case
    case_path = Path(case_dir) if case_dir is not None else _CASES_DIR / case_id
    if not case_path.exists():
        raise click.ClickException(f"Case directory not found: {case_path}")

    case_obj = load_case(case_path)
    mode_normalized = mode.lower()

    # Resolve output directory based on mode if not explicitly provided
    if output_dir is not None:
        out_path = Path(output_dir)
    elif mode_normalized == "structured":
        out_path = Path("results/milestone-2")
    else:
        out_path = Path("results/milestone-1")

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
    milestone_label = (
        "Milestone 2: Structured Analyst"
        if mode_normalized == "structured"
        else "Milestone 1: Direct Analyst Baseline"
    )
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

