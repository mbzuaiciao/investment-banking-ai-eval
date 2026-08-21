"""Tests for CLI baseline command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from ib_eval.cli import main


def test_cli_baseline_dry_run() -> None:
    """Dry run (without --execute) prints planned run info and exits 0 without running."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "openai",
            "--model",
            "gpt-4o",
            "--runs",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "DRY-RUN / GUARDRAIL ACTIVE" in result.output
    assert "northstar-v1" in result.output
    assert "gpt-4o" in result.output
    assert "5" in result.output
    assert "--execute" in result.output


def test_cli_baseline_execute_mock(tmp_path: Path) -> None:
    """Baseline with --execute and mock provider runs successfully."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "mock",
            "--model",
            "mock-test",
            "--runs",
            "2",
            "--output",
            str(tmp_path),
            "--execute",
        ],
    )

    assert result.exit_code == 0
    assert "Running 2 trial(s)..." in result.output
    assert "Completed:     2 / 2" in result.output
    assert "Artifacts saved to:" in result.output


def test_cli_baseline_invalid_case() -> None:
    """Baseline with non-existent case fails gracefully."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["baseline", "--case", "non_existent_case_xyz", "--execute"],
    )

    assert result.exit_code != 0
    assert "Case directory not found" in result.output


def test_cli_baseline_invalid_provider() -> None:
    """Baseline with unsupported provider fails gracefully."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["baseline", "--provider", "unsupported_provider", "--execute"],
    )

    assert result.exit_code != 0
    assert "Unsupported provider" in result.output
