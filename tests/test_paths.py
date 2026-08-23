"""Unit tests for centralized default output path resolution and case-scoped directory structure."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from ib_eval.cli import main
from ib_eval.paths import resolve_default_output_dir


def test_resolve_default_output_dir_northstar() -> None:
    """Verify default output paths for northstar-v1 across all modes."""
    assert resolve_default_output_dir("northstar-v1", "direct") == Path(
        "results/northstar-v1/milestone-1"
    )
    assert resolve_default_output_dir("northstar-v1", "structured") == Path(
        "results/northstar-v1/milestone-2"
    )
    assert resolve_default_output_dir("northstar-v1", "repair") == Path(
        "results/northstar-v1/milestone-3"
    )
    assert resolve_default_output_dir("northstar-v1", "controlled-repair") == Path(
        "results/northstar-v1/milestone-3b"
    )
    assert resolve_default_output_dir("northstar-v1", "controlled_repair") == Path(
        "results/northstar-v1/milestone-3b"
    )


def test_resolve_default_output_dir_meridian() -> None:
    """Verify default output paths for meridian-v1 across all modes."""
    assert resolve_default_output_dir("meridian-v1", "direct") == Path(
        "results/meridian-v1/milestone-4c-direct"
    )
    assert resolve_default_output_dir("meridian-v1", "structured") == Path(
        "results/meridian-v1/milestone-4d-structured"
    )
    assert resolve_default_output_dir("meridian-v1", "repair") == Path(
        "results/meridian-v1/milestone-4e-repair"
    )
    assert resolve_default_output_dir("meridian-v1", "controlled-repair") == Path(
        "results/meridian-v1/milestone-4e-controlled-repair"
    )
    assert resolve_default_output_dir("meridian-v1", "controlled_repair") == Path(
        "results/meridian-v1/milestone-4e-controlled-repair"
    )


def test_resolve_default_output_dir_generic_fallback() -> None:
    """Verify fallback behavior for future/arbitrary cases."""
    assert resolve_default_output_dir("solaris-v1", "direct") == Path("results/solaris-v1/direct")
    assert resolve_default_output_dir("solaris-v1", "structured") == Path(
        "results/solaris-v1/structured"
    )
    assert resolve_default_output_dir("solaris-v1", "repair") == Path("results/solaris-v1/repair")
    assert resolve_default_output_dir("solaris-v1", "controlled-repair") == Path(
        "results/solaris-v1/controlled-repair"
    )


def test_cli_meridian_baseline_dry_run_direct() -> None:
    """Meridian baseline direct mode displays milestone-4c-direct output path."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "meridian-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "direct",
            "--thinking",
            "off",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/meridian-v1/milestone-4c-direct" in result.output
    assert "Milestone 4C: Meridian Direct Baseline" in result.output


def test_cli_meridian_baseline_dry_run_structured() -> None:
    """Meridian baseline structured mode displays milestone-4d-structured output path."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "meridian-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "structured",
            "--thinking",
            "off",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/meridian-v1/milestone-4d-structured" in result.output
    assert "Milestone 4D: Meridian Structured Analyst" in result.output


def test_cli_meridian_baseline_dry_run_repair() -> None:
    """Meridian baseline repair mode displays milestone-4e-repair output path."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "meridian-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "repair",
            "--thinking",
            "off",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/meridian-v1/milestone-4e-repair" in result.output
    assert "Milestone 4E: Meridian Deterministic Feedback Repair" in result.output


def test_cli_meridian_repair_benchmark_dry_run() -> None:
    """Meridian repair benchmark displays milestone-4e-controlled-repair output path."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "repair-benchmark",
            "--case",
            "meridian-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--fixtures",
            "all",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/meridian-v1/milestone-4e-controlled-repair" in result.output
    assert "Milestone 4E: Meridian Controlled Repair Benchmark" in result.output
    assert "Fixtures:    10" in result.output


def test_cli_meridian_explicit_output_override() -> None:
    """Explicit --output flag overrides default case-scoped path."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "meridian-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "direct",
            "--output",
            "results/custom_meridian_exp",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/custom_meridian_exp" in result.output


def test_mock_execution_writes_to_case_aware_directory(tmp_path: Path) -> None:
    """Live mock execution writes to the case-aware output directory structure."""
    out_dir = tmp_path / "results" / "meridian-v1" / "milestone-4c-direct"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "meridian-v1",
            "--provider",
            "mock",
            "--mode",
            "direct",
            "--output",
            str(out_dir),
            "--runs",
            "1",
            "--execute",
        ],
    )
    assert result.exit_code == 0
    assert out_dir.exists()
    runs = list(out_dir.glob("m1-direct-mock-*"))
    assert len(runs) == 1
    assert (runs[0] / "summary.json").exists()
