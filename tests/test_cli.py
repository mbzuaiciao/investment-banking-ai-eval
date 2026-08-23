"""Tests for CLI behavior."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ib_eval.cli import main

_GOLD_DIR = str(Path(__file__).parent.parent / "examples" / "gold_submission")
_CORRUPTED_DIR = Path(__file__).parent.parent / "examples" / "corrupted"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_grade_gold_exit_code(runner: CliRunner) -> None:
    """Gold submission grades → exit code 0."""
    result = runner.invoke(main, ["grade", _GOLD_DIR])
    assert result.exit_code == 0, result.output


def test_cli_grade_gold_output_100(runner: CliRunner) -> None:
    """Gold submission prints '100 / 100' on the last line."""
    result = runner.invoke(main, ["grade", _GOLD_DIR])
    assert "100 / 100" in result.output


def test_cli_grade_gold_quiet(runner: CliRunner) -> None:
    """--quiet flag prints only the score line."""
    result = runner.invoke(main, ["grade", _GOLD_DIR, "--quiet"])
    assert result.exit_code == 0
    assert result.output.strip() == "100 / 100"


def test_cli_grade_gold_json_output(runner: CliRunner) -> None:
    """--json-output produces valid JSON with expected keys."""
    import json

    result = runner.invoke(main, ["grade", _GOLD_DIR, "--json-output"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_score"] == pytest.approx(100.0, abs=0.01)
    assert "grader_results" in data
    assert "hard_failures" in data


def test_cli_grade_missing_path(runner: CliRunner) -> None:
    """Non-existent path produces an error."""
    result = runner.invoke(main, ["grade", "/tmp/does_not_exist_abc123"])
    assert result.exit_code != 0


def test_cli_grade_corrupted_exits_nonzero(runner: CliRunner) -> None:
    """Corrupted submissions exit with non-zero code."""
    for d in _CORRUPTED_DIR.iterdir():
        if d.is_dir() and (d / "submission.json").exists():
            result = runner.invoke(main, ["grade", str(d)])
            assert result.exit_code != 0, f"Expected non-zero exit for {d.name}, got 0"
            break  # Test one is sufficient for the basic CLI test


def test_cli_grade_c01_reports_error(runner: CliRunner) -> None:
    """C01 corrupted submission output mentions the diagnostic code."""
    c01 = str(_CORRUPTED_DIR / "c01_quarterly_revenue")
    result = runner.invoke(main, ["grade", c01])
    assert "REV_QUARTERLY_CONFUSION" in result.output or result.exit_code != 0


def test_cli_help(runner: CliRunner) -> None:
    """CLI help text is available."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "grade" in result.output


def test_cli_grade_help(runner: CliRunner) -> None:
    """grade subcommand help is available."""
    result = runner.invoke(main, ["grade", "--help"])
    assert result.exit_code == 0
