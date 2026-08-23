"""Tests for Milestone 3 Deterministic Feedback Repair."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ib_eval.baseline.analysis import (
    ExperimentSummary,
    compare_experiments,
    compute_aggregate_statistics,
)
from ib_eval.baseline.interface import ProviderConfig
from ib_eval.baseline.prompt import build_repair_prompt
from ib_eval.baseline.providers.mock import MockAnalyst
from ib_eval.baseline.runner import DirectAnalyst, run_baseline_experiment
from ib_eval.case import NorthstarCase, load_case
from ib_eval.cli import main
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission

_CASES_DIR = Path(__file__).resolve().parent.parent / "cases" / "northstar-v1"
_CORRUPTED_DIR = Path(__file__).resolve().parent.parent / "examples" / "corrupted"


@pytest.fixture
def case() -> NorthstarCase:
    return load_case(_CASES_DIR)


@pytest.fixture
def gold_submission() -> Submission:
    gold_path = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "gold_submission"
        / "submission.json"
    )
    return Submission.model_validate_json(gold_path.read_text())


@pytest.fixture
def corrupted_c02_submission() -> Submission:
    c02_path = _CORRUPTED_DIR / "c02_tv_not_discounted" / "submission.json"
    return Submission.model_validate_json(c02_path.read_text())


@pytest.fixture
def corrupted_c08_submission() -> Submission:
    c08_path = _CORRUPTED_DIR / "c08_capex_double_counted" / "submission.json"
    return Submission.model_validate_json(c08_path.read_text())


def test_build_repair_prompt_structure_and_no_gold_leakage(
    case: NorthstarCase,
    corrupted_c02_submission: Submission,
) -> None:
    """Repair prompt includes submitted values and invariants without leaking gold answers."""
    grade_report = grade_submission(corrupted_c02_submission, case)
    repair_prompt = build_repair_prompt(case, corrupted_c02_submission, grade_report)

    # 1. Contains diagnostic code and invariant guidance
    assert "TV_NOT_DISCOUNTED" in repair_prompt
    assert "Terminal value must be discounted back to valuation date" in repair_prompt
    assert "Your Submitted Value" in repair_prompt

    # 2. Contains initial submission JSON
    assert "Your Previous Submission" in repair_prompt
    assert "Northstar Components, Inc." in repair_prompt

    # 3. Contains revision instructions and cascade warning
    assert "Recompute All Downstream Dependent Values" in repair_prompt
    assert "Single Complete Submission" in repair_prompt

    # 4. Zero gold leakage safeguards: ensure hidden benchmark valuation values are NOT in prompt
    assert "1712.97" not in repair_prompt
    assert "1441.69" not in repair_prompt
    assert "23.13" not in repair_prompt
    assert "9.2832" not in repair_prompt


def test_repair_trial_successful_repair(
    tmp_path: Path,
    case: NorthstarCase,
    corrupted_c02_submission: Submission,
    gold_submission: Submission,
) -> None:
    """Trial with initial error successfully repairs to 100% clean on second call."""
    mock = MockAnalyst(
        responses=[
            json.dumps(corrupted_c02_submission.model_dump()),
            json.dumps(gold_submission.model_dump()),
        ]
    )
    analyst = DirectAnalyst(mock)
    config = ProviderConfig(provider="mock", model="mock-analyst", mode="repair")
    trial_dir = tmp_path / "run_001"

    result = analyst.run_trial(
        prompt="initial structured prompt",
        case=case,
        config=config,
        run_index=1,
        trial_dir=trial_dir,
    )

    # Verify call count: exactly 2 calls
    assert mock.call_count == 2

    # Verify artifacts preserved
    assert (trial_dir / "initial_raw_response.txt").exists()
    assert (trial_dir / "initial_submission.json").exists()
    assert (trial_dir / "initial_grade.json").exists()
    assert (trial_dir / "repair_prompt.txt").exists()
    assert (trial_dir / "repair_raw_response.txt").exists()
    assert (trial_dir / "repaired_submission.json").exists()
    assert (trial_dir / "repaired_grade.json").exists()
    assert (trial_dir / "submission.json").exists()
    assert (trial_dir / "grade.json").exists()
    assert (trial_dir / "metadata.json").exists()

    # Verify score improvement and diagnostic transitions
    m = result.metadata
    assert m.repair_attempted is True
    assert m.initial_score is not None and m.initial_score < 100.0
    assert m.repaired_score == 100.0
    assert m.score == 100.0
    assert m.score_delta is not None and m.score_delta > 0
    assert m.initial_hard_failure_count >= 1
    assert m.repaired_hard_failure_count == 0
    assert "TV_NOT_DISCOUNTED" in m.resolved_diagnostics
    assert len(m.persistent_diagnostics) == 0
    assert len(m.new_diagnostics) == 0


def test_repair_trial_persistent_failure(
    tmp_path: Path,
    case: NorthstarCase,
    corrupted_c02_submission: Submission,
) -> None:
    """Trial where repair attempt fails to fix the diagnostic."""
    mock = MockAnalyst(
        responses=[
            json.dumps(corrupted_c02_submission.model_dump()),
            json.dumps(corrupted_c02_submission.model_dump()),
        ]
    )
    analyst = DirectAnalyst(mock)
    config = ProviderConfig(provider="mock", model="mock-analyst", mode="repair")
    trial_dir = tmp_path / "run_002"

    result = analyst.run_trial(
        prompt="initial structured prompt",
        case=case,
        config=config,
        run_index=2,
        trial_dir=trial_dir,
    )

    assert mock.call_count == 2
    m = result.metadata
    assert m.repair_attempted is True
    assert m.score_delta == 0.0
    assert "TV_NOT_DISCOUNTED" in m.persistent_diagnostics
    assert "TV_NOT_DISCOUNTED" not in m.resolved_diagnostics
    assert m.repaired_hard_failure_count >= 1


def test_repair_trial_new_failure_introduced(
    tmp_path: Path,
    case: NorthstarCase,
    corrupted_c08_submission: Submission,
    corrupted_c02_submission: Submission,
) -> None:
    """Trial where repair fixes initial error but introduces a new error."""
    mock = MockAnalyst(
        responses=[
            json.dumps(corrupted_c08_submission.model_dump()),
            json.dumps(corrupted_c02_submission.model_dump()),
        ]
    )
    analyst = DirectAnalyst(mock)
    config = ProviderConfig(provider="mock", model="mock-analyst", mode="repair")
    trial_dir = tmp_path / "run_003"

    result = analyst.run_trial(
        prompt="initial structured prompt",
        case=case,
        config=config,
        run_index=3,
        trial_dir=trial_dir,
    )

    assert mock.call_count == 2
    m = result.metadata
    assert m.repair_attempted is True
    assert "FCF_CAPEX_DOUBLE_COUNTED" in m.resolved_diagnostics
    assert "TV_NOT_DISCOUNTED" in m.new_diagnostics


def test_repair_trial_already_clean_skips_repair(
    tmp_path: Path,
    case: NorthstarCase,
    gold_submission: Submission,
) -> None:
    """Trial with clean initial submission (0 hard failures) skips repair call."""
    mock = MockAnalyst(responses=[json.dumps(gold_submission.model_dump())])
    analyst = DirectAnalyst(mock)
    config = ProviderConfig(provider="mock", model="mock-analyst", mode="repair")
    trial_dir = tmp_path / "run_004"

    result = analyst.run_trial(
        prompt="initial structured prompt",
        case=case,
        config=config,
        run_index=4,
        trial_dir=trial_dir,
    )

    # Exactly 1 call made!
    assert mock.call_count == 1
    assert not (trial_dir / "repair_prompt.txt").exists()
    assert not (trial_dir / "repair_raw_response.txt").exists()

    m = result.metadata
    assert m.repair_attempted is False
    assert m.repair_skipped_reason == "initial_submission_clean"
    assert m.score == 100.0
    assert m.hard_failure_count == 0


def test_repair_trial_initial_parse_failure_skips_repair(
    tmp_path: Path,
    case: NorthstarCase,
) -> None:
    """Trial with unparseable initial response skips repair call."""
    mock = MockAnalyst(responses=["I am an AI and cannot generate JSON."])
    analyst = DirectAnalyst(mock)
    config = ProviderConfig(provider="mock", model="mock-analyst", mode="repair")
    trial_dir = tmp_path / "run_005"

    result = analyst.run_trial(
        prompt="initial structured prompt",
        case=case,
        config=config,
        run_index=5,
        trial_dir=trial_dir,
    )

    # Exactly 1 call made!
    assert mock.call_count == 1
    assert (trial_dir / "initial_parse_error.json").exists()
    assert (trial_dir / "parse_error.json").exists()
    assert not (trial_dir / "repair_prompt.txt").exists()

    m = result.metadata
    assert m.parsed_successfully is False
    assert m.repair_attempted is False
    assert m.repair_skipped_reason == "initial_parse_failure"


def test_repair_trial_repair_parse_failure(
    tmp_path: Path,
    case: NorthstarCase,
    corrupted_c02_submission: Submission,
) -> None:
    """Trial where initial submission parses but repair completion fails parsing."""
    mock = MockAnalyst(
        responses=[
            json.dumps(corrupted_c02_submission.model_dump()),
            "Here is the revised JSON: { broken json",
        ]
    )
    analyst = DirectAnalyst(mock)
    config = ProviderConfig(provider="mock", model="mock-analyst", mode="repair")
    trial_dir = tmp_path / "run_006"

    result = analyst.run_trial(
        prompt="initial structured prompt",
        case=case,
        config=config,
        run_index=6,
        trial_dir=trial_dir,
    )

    assert mock.call_count == 2
    assert (trial_dir / "initial_submission.json").exists()
    assert (trial_dir / "initial_grade.json").exists()
    assert (trial_dir / "repair_prompt.txt").exists()
    assert (trial_dir / "repair_raw_response.txt").exists()
    assert (trial_dir / "repaired_parse_error.json").exists()

    m = result.metadata
    assert m.repair_attempted is True
    assert m.initial_parsed_successfully is True
    assert m.repaired_parsed_successfully is False
    assert m.parsed_successfully is False


def test_repair_full_experiment_and_summary_statistics(
    tmp_path: Path,
    case: NorthstarCase,
    corrupted_c02_submission: Submission,
    gold_submission: Submission,
) -> None:
    """Full repair experiment calculates aggregate repair metrics and markdown tables."""
    # 2 runs: Run 1 fixes c02 -> gold; Run 2 is already gold
    mock = MockAnalyst(
        responses=[
            json.dumps(corrupted_c02_submission.model_dump()),
            json.dumps(gold_submission.model_dump()),
            json.dumps(gold_submission.model_dump()),
        ]
    )
    config = ProviderConfig(provider="mock", model="mock-model", mode="repair")
    out_dir = tmp_path / "results" / "milestone-3"

    exp_res = run_baseline_experiment(
        case=case,
        analyst_provider=mock,
        config=config,
        runs=2,
        output_dir=out_dir,
    )

    # 3 calls total: 2 for Run 1, 1 for Run 2
    assert mock.call_count == 3

    assert exp_res.experiment_id.startswith("m3-repair-mock-mock-model")
    assert exp_res.summary.mode == "repair"
    assert exp_res.summary.repair_stats is not None

    rs = exp_res.summary.repair_stats
    assert rs.trials_repair_attempted == 1
    assert rs.trials_repair_skipped_clean == 1
    assert rs.initially_failing_runs_count == 1
    assert rs.initially_failing_runs_repaired_to_zero_hf == 1
    assert rs.repair_success_rate == 1.0
    assert rs.trials_improved_count == 1
    assert rs.total_diagnostics_resolved == 1

    # Check markdown report
    md_text = (exp_res.experiment_dir / "summary.md").read_text()
    assert "Milestone 3 — Deterministic Feedback Repair Report" in md_text
    assert "Repair Performance Summary" in md_text
    assert "Repair Success Rate" in md_text
    assert "Diagnostic Transition Analysis" in md_text
    assert "Already Clean" in md_text
    assert "Repaired (Clean)" in md_text


def test_compare_experiments_with_milestone_3(
    tmp_path: Path,
) -> None:
    """Compare utility formats M2 vs M3 comparison cleanly."""
    dir_m2 = tmp_path / "exp_m2"
    dir_m3 = tmp_path / "exp_m3"
    dir_m2.mkdir()
    dir_m3.mkdir()

    summary_m2 = ExperimentSummary(
        experiment_id="m2-structured-mock-20260822",
        case_id="northstar-v1",
        provider="mock",
        model="mock-v4",
        mode="structured",
        requested_runs=5,
        completed_model_calls=5,
        parsed_runs=5,
        parse_failure_count=0,
        parse_success_rate=1.0,
        mean_score=85.0,
        hard_failure_rate=0.4,
    )
    summary_m3 = compute_aggregate_statistics(
        experiment_id="m3-repair-mock-20260822",
        case_id="northstar-v1",
        provider="mock",
        model="mock-v4",
        requested_runs=5,
        trial_results=[],
        mode="repair",
    )
    summary_m3.mean_score = 98.0
    summary_m3.hard_failure_rate = 0.0

    report = compare_experiments(summary_m2, summary_m3)
    assert "Experiment Comparison Report" in report
    assert "m2-structured" in report
    assert "m3-repair" in report
    assert "+13.0" in report  # 98.0 - 85.0


def test_cli_baseline_repair_default_output() -> None:
    """CLI baseline repair mode defaults to results/milestone-3 in dry-run."""
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
            "repair",
            "--thinking",
            "on",
            "--reasoning-effort",
            "high",
            "--runs",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "Milestone 3: Deterministic Feedback Repair" in result.output
    assert "Mode:        repair" in result.output
    assert "Output Dir:  results/milestone-3" in result.output
    assert "--mode repair" in result.output


def test_cli_baseline_repair_explicit_output_override() -> None:
    """CLI baseline repair mode respects explicit --output override."""
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
            "repair",
            "--output",
            "results/custom-m3-run",
            "--runs",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "Output Dir:  results/custom-m3-run" in result.output
    assert "--output results/custom-m3-run" in result.output
