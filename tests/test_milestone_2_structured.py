"""Tests for Milestone 2 Structured Analyst, prompt construction, reporting fix, and comparison."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from click.testing import CliRunner

from ib_eval.baseline.analysis import (
    ExperimentSummary,
    compare_experiments,
    compute_aggregate_statistics,
)
from ib_eval.baseline.interface import ProviderConfig, TrialMetadata, TrialResult
from ib_eval.baseline.prompt import build_analyst_prompt, build_structured_analyst_prompt
from ib_eval.baseline.providers.mock import MockAnalyst
from ib_eval.baseline.runner import run_baseline_experiment
from ib_eval.case import load_case
from ib_eval.cli import main
from ib_eval.schemas import (
    ErrorType,
    GraderFailure,
    GraderResult,
    ScoringReport,
    Severity,
    Submission,
)

_CASE_DIR = Path(__file__).parent.parent / "cases" / "northstar-v1"
_GOLD_FILE = Path(__file__).parent.parent / "examples" / "gold_submission" / "submission.json"


def test_structured_prompt_contains_all_8_stages() -> None:
    """Structured analyst prompt contains all 8 explicit workflow stages."""
    case = load_case(_CASE_DIR)
    prompt = build_structured_analyst_prompt(case)

    assert "Stage 1 — Source Extraction" in prompt
    assert "Stage 2 — Assumption Ledger" in prompt
    assert "Stage 3 — 5-Year Forecast Schedules" in prompt
    assert "Stage 4 — WACC Derivation" in prompt
    assert "Stage 5 — Terminal Value Calculation" in prompt
    assert "Stage 6 — Enterprise Value & Equity Bridge" in prompt
    assert "Stage 7 — Comparable Companies Analysis" in prompt
    assert "Stage 8 — Final Invariant Pre-Submission Self-Check" in prompt
    assert "Perpetual growth (Gordon Growth)" in prompt or "Terminal FCF" in prompt
    assert "PV(TV)" in prompt
    assert "Net Debt = Gross Debt - Cash" in prompt


def test_structured_prompt_has_no_gold_leakage() -> None:
    """Structured analyst prompt contains zero ground truth numbers or diagnostic codes."""
    case = load_case(_CASE_DIR)
    prompt = build_structured_analyst_prompt(case)

    # No exact gold answers leaked
    assert "1712.97" not in prompt
    assert "1387.97" not in prompt
    assert "23.13" not in prompt
    assert "1505.52" not in prompt
    assert "1180.52" not in prompt
    assert "19.68" not in prompt
    assert "9.2832" not in prompt
    assert "1285.53" not in prompt

    # No diagnostic code constants leaked
    assert "TV_NOT_DISCOUNTED" not in prompt
    assert "EQ_BRIDGE_CASH_REVERSED" not in prompt
    assert "FCF_UFCF_ERROR" not in prompt
    assert "WACC_PRETAX_DEBT" not in prompt
    assert "COMPS_NM_COERCED_ZERO" not in prompt


def test_structured_prompt_uses_same_sources_as_direct() -> None:
    """Structured prompt includes the exact same 4 markdown source files as direct prompt."""
    case = load_case(_CASE_DIR)
    direct_prompt = build_analyst_prompt(case)
    structured_prompt = build_structured_analyst_prompt(case)

    for doc_name in [
        "capital_structure.md",
        "income_statement.md",
        "management_guidance.md",
        "quarterly_report.md",
    ]:
        assert f"DOCUMENT: {doc_name}" in direct_prompt
        assert f"DOCUMENT: {doc_name}" in structured_prompt


def test_structured_mode_runner_execution_and_artifacts(tmp_path: Path) -> None:
    """Structured mode creates m2-structured exp_id and records mode in config and metadata."""
    gold_text = _GOLD_FILE.read_text()
    mock_provider = MockAnalyst(gold_text)
    case = load_case(_CASE_DIR)

    config = ProviderConfig(
        provider="mock",
        model="mock-analyst",
        mode="structured",
        thinking=True,
        reasoning_effort="high",
    )

    res = run_baseline_experiment(
        case=case,
        analyst_provider=mock_provider,
        config=config,
        runs=2,
        output_dir=tmp_path,
    )

    assert res.experiment_id.startswith("m2-structured-")
    assert "thinking-high" in res.experiment_id

    # Check config.json
    config_file = res.experiment_dir / "config.json"
    assert config_file.exists()
    saved_config = json.loads(config_file.read_text())
    assert saved_config["mode"] == "structured"
    assert saved_config["thinking"] is True
    assert saved_config["reasoning_effort"] == "high"

    # Check run metadata
    meta_file = res.experiment_dir / "run_001" / "metadata.json"
    assert meta_file.exists()
    saved_meta = json.loads(meta_file.read_text())
    assert saved_meta["mode"] == "structured"
    assert saved_meta["thinking"] is True
    assert saved_meta["reasoning_effort"] == "high"

    # Check summary.json and summary.md
    assert res.summary.mode == "structured"
    summary_file = res.experiment_dir / "summary.json"
    assert summary_file.exists()
    saved_sum = json.loads(summary_file.read_text())
    assert saved_sum["mode"] == "structured"

    summary_md = (res.experiment_dir / "summary.md").read_text()
    assert "# Milestone 2 — Structured Analyst Report" in summary_md

    # Check one provider call per trial
    assert mock_provider.call_count == 2


def test_reporting_repeated_diagnostics_incidence_bounded() -> None:
    """Repeated diagnostics in one trial produce correct count and bounded run incidence."""
    # Create mock trial results where run 1 has 4 FCF errors and run 2 has 2 FCF errors
    failures_run_1 = [
        GraderFailure(
            error_type=ErrorType.ACCOUNTING,
            severity=Severity.CRITICAL,
            metric=f"ufcf_{year}",
            expected=100.0,
            observed=80.0,
            message=f"FCF error {year}",
            diagnostic_code="FCF_UFCF_ERROR",
        )
        for year in [2026, 2027, 2028, 2029]
    ]

    failures_run_2 = [
        GraderFailure(
            error_type=ErrorType.ACCOUNTING,
            severity=Severity.CRITICAL,
            metric=f"ufcf_{year}",
            expected=100.0,
            observed=80.0,
            message=f"FCF error {year}",
            diagnostic_code="FCF_UFCF_ERROR",
        )
        for year in [2026, 2027]
    ]

    grade_1 = ScoringReport(
        case_id="northstar-v1",
        analyst="model_1",
        total_score=80.0,
        max_score=100.0,
        pct_score=80.0,
        grade="B",
        grader_results=[
            GraderResult(
                grader="free_cash_flow",
                score=0.0,
                passed=False,
                points_earned=0.0,
                max_points=10.0,
                failures=failures_run_1,
            )
        ],
        hard_failures=failures_run_1,
        summary="Test report 1",
    )

    grade_2 = ScoringReport(
        case_id="northstar-v1",
        analyst="model_2",
        total_score=85.0,
        max_score=100.0,
        pct_score=85.0,
        grade="B",
        grader_results=[
            GraderResult(
                grader="free_cash_flow",
                score=0.0,
                passed=False,
                points_earned=0.0,
                max_points=10.0,
                failures=failures_run_2,
            )
        ],
        hard_failures=failures_run_2,
        summary="Test report 2",
    )

    meta_1 = TrialMetadata(
        run_index=1,
        provider="mock",
        model="mock",
        timestamp="2026-08-22T00:00:00Z",
        parsed_successfully=True,
    )
    meta_2 = TrialMetadata(
        run_index=2,
        provider="mock",
        model="mock",
        timestamp="2026-08-22T00:00:00Z",
        parsed_successfully=True,
    )

    mock_sub = MagicMock(spec=Submission)

    trials = [
        TrialResult(metadata=meta_1, raw_response="{}", submission=mock_sub, grade=grade_1),
        TrialResult(metadata=meta_2, raw_response="{}", submission=mock_sub, grade=grade_2),
    ]

    summary = compute_aggregate_statistics(
        experiment_id="test-exp",
        case_id="northstar-v1",
        provider="mock",
        model="mock",
        requested_runs=2,
        trial_results=trials,
    )

    stat = summary.diagnostic_stats["FCF_UFCF_ERROR"]
    # 4 + 2 = 6 total occurrences
    assert stat.occurrence_count == 6
    # 2 out of 2 runs had at least one occurrence
    assert stat.run_count == 2
    # Incidence rate is 100%, bounded
    assert stat.run_incidence_rate == 1.0


def test_experiment_comparison_utility() -> None:
    """compare_experiments generates side-by-side metrics and delta columns."""
    exp_a = ExperimentSummary(
        experiment_id="m1-direct-deepseek-deepseek_v4_flash-20260822_100000",
        case_id="northstar-v1",
        provider="deepseek",
        model="deepseek-v4-flash",
        mode="direct",
        requested_runs=10,
        completed_model_calls=10,
        parsed_runs=10,
        parse_failure_count=0,
        parse_success_rate=1.0,
        mean_score=82.0,
        median_score=85.0,
        standard_deviation=6.5,
        hard_failure_run_count=4,
        hard_failure_rate=0.4,
    )

    exp_b = ExperimentSummary(
        experiment_id="m2-structured-deepseek-deepseek_v4_flash-20260822_110000",
        case_id="northstar-v1",
        provider="deepseek",
        model="deepseek-v4-flash",
        mode="structured",
        requested_runs=10,
        completed_model_calls=10,
        parsed_runs=10,
        parse_failure_count=0,
        parse_success_rate=1.0,
        mean_score=94.5,
        median_score=96.0,
        standard_deviation=2.1,
        hard_failure_run_count=1,
        hard_failure_rate=0.1,
    )

    report = compare_experiments(exp_a, exp_b)

    assert "# Experiment Comparison Report" in report
    assert "m1-direct" in report
    assert "m2-structured" in report
    assert "+12.5" in report  # Mean score delta: 94.5 - 82.0
    assert "-30.0%" in report  # Hard failure delta: 0.1 - 0.4


def test_cli_baseline_structured_dry_run() -> None:
    """CLI baseline supports --mode structured in dry-run mode."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "structured",
            "--thinking",
            "on",
            "--reasoning-effort",
            "high",
            "--runs",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "Milestone 2: Structured Analyst" in result.output
    assert "Mode:        structured" in result.output
    assert "--mode structured" in result.output


def test_cli_compare_command(tmp_path: Path) -> None:
    """CLI compare command loads summary.json from two directories and outputs report."""
    dir_a = tmp_path / "exp_a"
    dir_b = tmp_path / "exp_b"
    dir_a.mkdir()
    dir_b.mkdir()

    exp_a = ExperimentSummary(
        experiment_id="exp_a_id",
        case_id="northstar-v1",
        provider="openai",
        model="gpt-4o",
        mode="direct",
        requested_runs=5,
        completed_model_calls=5,
        parsed_runs=5,
        parse_failure_count=0,
        parse_success_rate=1.0,
        mean_score=80.0,
    )
    exp_b = ExperimentSummary(
        experiment_id="exp_b_id",
        case_id="northstar-v1",
        provider="openai",
        model="gpt-4o",
        mode="structured",
        requested_runs=5,
        completed_model_calls=5,
        parsed_runs=5,
        parse_failure_count=0,
        parse_success_rate=1.0,
        mean_score=95.0,
    )

    (dir_a / "summary.json").write_text(json.dumps(exp_a.model_dump()))
    (dir_b / "summary.json").write_text(json.dumps(exp_b.model_dump()))

    runner = CliRunner()
    result = runner.invoke(main, ["compare", str(dir_a), str(dir_b)])

    assert result.exit_code == 0
    assert "Experiment Comparison Report" in result.output
    assert "exp_a_id" in result.output
    assert "exp_b_id" in result.output


def test_cli_baseline_direct_default_output() -> None:
    """CLI baseline direct mode defaults to results/northstar-v1/milestone-1."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "direct",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/northstar-v1/milestone-1" in result.output


def test_cli_baseline_structured_default_output() -> None:
    """CLI baseline structured mode defaults to results/northstar-v1/milestone-2."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "structured",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/northstar-v1/milestone-2" in result.output


def test_cli_baseline_structured_explicit_output_override() -> None:
    """CLI baseline structured mode respects explicit --output override."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--mode",
            "structured",
            "--output",
            "results/custom-exp",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/custom-exp" in result.output
    assert "--output results/custom-exp" in result.output


def test_cli_baseline_direct_explicit_output_override() -> None:
    """CLI baseline direct mode respects explicit --output override."""
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
            "--mode",
            "direct",
            "--output",
            "results/custom-direct",
            "--runs",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Output Dir:  results/custom-direct" in result.output
    assert "--output results/custom-direct" in result.output


def test_cli_baseline_mock_execution_writes_to_custom_directory(tmp_path: Path) -> None:
    """Live mock execution writes artifacts to the resolved parent directory."""
    custom_dir = tmp_path / "custom_milestone_output"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "mock",
            "--mode",
            "structured",
            "--output",
            str(custom_dir),
            "--runs",
            "1",
            "--execute",
        ],
    )
    assert result.exit_code == 0
    assert custom_dir.exists()
    exp_dirs = list(custom_dir.glob("m2-structured-mock-*"))
    assert len(exp_dirs) == 1
    assert (exp_dirs[0] / "summary.json").exists()
    assert (exp_dirs[0] / "summary.md").exists()
    assert (exp_dirs[0] / "config.json").exists()
