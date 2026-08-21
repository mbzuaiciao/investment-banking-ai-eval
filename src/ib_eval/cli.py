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
