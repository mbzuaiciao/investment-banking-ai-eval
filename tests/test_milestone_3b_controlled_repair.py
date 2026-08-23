"""Tests for Milestone 3B Controlled Repair Benchmark."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ib_eval.baseline.interface import ProviderConfig
from ib_eval.baseline.providers.mock import MockAnalyst
from ib_eval.case import NorthstarCase, load_case
from ib_eval.cli import main
from ib_eval.controlled_repair import (
    CONTROLLED_FIXTURES,
    BenchmarkDriftError,
    ControlledFixture,
    DifficultyType,
    ErrorCategory,
    resolve_fixtures,
    run_controlled_repair_benchmark,
)
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
        Path(__file__).resolve().parent.parent / "examples" / "gold_submission" / "submission.json"
    )
    return Submission.model_validate_json(gold_path.read_text())


def test_fixture_discovery_and_resolution() -> None:
    """All 10 fixtures are discovered and can be selected by ID or name."""
    assert len(CONTROLLED_FIXTURES) == 10

    # 1. Resolve 'all'
    all_fixtures = resolve_fixtures("all", _CORRUPTED_DIR)
    assert len(all_fixtures) == 10

    # 2. Targeted resolution by ID
    subset = resolve_fixtures("c02,c08,c10", _CORRUPTED_DIR)
    assert len(subset) == 3
    assert [f.fixture_id for f in subset] == ["c02", "c08", "c10"]

    # 3. Targeted resolution by directory name
    subset_names = resolve_fixtures("c02_tv_not_discounted,c05_nm_peer_zero", _CORRUPTED_DIR)
    assert len(subset_names) == 2
    assert [f.fixture_id for f in subset_names] == ["c02", "c05"]

    # 4. Unknown fixture raises ValueError
    with pytest.raises(ValueError, match="Unknown fixture identifier"):
        resolve_fixtures("c99_unknown", _CORRUPTED_DIR)


def test_benchmark_drift_protection(case: NorthstarCase) -> None:
    """Each controlled fixture must emit its expected diagnostic before repair."""
    for fixture in CONTROLLED_FIXTURES:
        sub = fixture.load_submission(_CORRUPTED_DIR)
        grade_report = grade_submission(sub, case)
        emitted_codes = [f.diagnostic_code for r in grade_report.grader_results for f in r.failures]
        assert fixture.expected_diagnostic in emitted_codes, (
            f"Fixture {fixture.fixture_id} did not emit expected "
            f"diagnostic {fixture.expected_diagnostic}"
        )


def test_benchmark_drift_error_raised_on_mismatch(
    tmp_path: Path,
    case: NorthstarCase,
    gold_submission: Submission,
) -> None:
    """BenchmarkDriftError is raised if a fixture does not emit its expected diagnostic."""
    # Create a mock fixture expecting an error, but pointing to gold submission (clean)
    bad_fixture_dir = tmp_path / "bad_fixture"
    bad_fixture_dir.mkdir()
    (bad_fixture_dir / "submission.json").write_text(json.dumps(gold_submission.model_dump()))

    bad_fixture = ControlledFixture(
        fixture_id="bad",
        dir_name="bad_fixture",
        name="Bad Fixture",
        expected_diagnostic="TV_NOT_DISCOUNTED",
        category=ErrorCategory.VALUATION,
        difficulty=DifficultyType.PROPAGATING,
        description="Clean submission falsely tagged as corrupted.",
    )

    mock = MockAnalyst()
    config = ProviderConfig(provider="mock", model="mock-analyst", mode="controlled-repair")
    out_dir = tmp_path / "results"

    with pytest.raises(BenchmarkDriftError, match="Benchmark drift detected"):
        run_controlled_repair_benchmark(
            case=case,
            analyst_provider=mock,
            config=config,
            fixtures=[bad_fixture],
            corrupted_dir=tmp_path,
            output_dir=out_dir,
        )


def test_controlled_repair_successful_repair(
    tmp_path: Path,
    case: NorthstarCase,
    gold_submission: Submission,
) -> None:
    """Repairing a corrupted fixture to gold results in full clean success."""
    c02 = next(f for f in CONTROLLED_FIXTURES if f.fixture_id == "c02")
    mock = MockAnalyst(responses=[json.dumps(gold_submission.model_dump())])
    config = ProviderConfig(provider="mock", model="mock-model", mode="controlled-repair")
    out_dir = tmp_path / "results" / "milestone-3b"

    res = run_controlled_repair_benchmark(
        case=case,
        analyst_provider=mock,
        config=config,
        fixtures=[c02],
        corrupted_dir=_CORRUPTED_DIR,
        output_dir=out_dir,
    )

    assert mock.call_count == 1
    assert res.summary.controlled_repair_success_count == 1
    assert res.summary.controlled_repair_success_rate == 1.0
    assert res.summary.target_diagnostic_resolved_count == 1
    assert res.summary.new_error_introduced_count == 0

    t = res.trial_results[0]
    assert t.fixture_id == "c02"
    assert t.expected_diagnostic == "TV_NOT_DISCOUNTED"
    assert t.expected_diagnostic_resolved is True
    assert t.repair_success is True
    assert t.partial_repair is False
    assert t.outcome == "success"
    assert t.repaired_hard_failure_count == 0
    assert t.repaired_score == 100.0


def test_controlled_repair_partial_success_with_new_error(
    tmp_path: Path,
    case: NorthstarCase,
) -> None:
    """Fixing the target diagnostic but introducing a new error results in partial repair."""
    c08 = next(f for f in CONTROLLED_FIXTURES if f.fixture_id == "c08")  # FCF_CAPEX_DOUBLE_COUNTED
    c02_sub = (_CORRUPTED_DIR / "c02_tv_not_discounted" / "submission.json").read_text()

    # Response fixes capex but introduces TV_NOT_DISCOUNTED
    mock = MockAnalyst(responses=[c02_sub])
    config = ProviderConfig(provider="mock", model="mock-model", mode="controlled-repair")
    out_dir = tmp_path / "results" / "milestone-3b"

    res = run_controlled_repair_benchmark(
        case=case,
        analyst_provider=mock,
        config=config,
        fixtures=[c08],
        corrupted_dir=_CORRUPTED_DIR,
        output_dir=out_dir,
    )

    assert mock.call_count == 1
    assert res.summary.controlled_repair_success_count == 0
    assert res.summary.target_diagnostic_resolved_count == 1  # Target was resolved
    assert res.summary.partial_repair_count == 1
    assert res.summary.new_error_introduced_count == 1

    t = res.trial_results[0]
    assert t.expected_diagnostic_resolved is True
    assert t.repair_success is False
    assert t.partial_repair is True
    assert t.outcome == "partial"
    assert "TV_NOT_DISCOUNTED" in t.new_diagnostics


def test_controlled_repair_persistent_diagnostic(
    tmp_path: Path,
    case: NorthstarCase,
) -> None:
    """Failing to fix target diagnostic results in persistent failure outcome."""
    c02 = next(f for f in CONTROLLED_FIXTURES if f.fixture_id == "c02")
    c02_sub = (_CORRUPTED_DIR / "c02_tv_not_discounted" / "submission.json").read_text()

    mock = MockAnalyst(responses=[c02_sub])
    config = ProviderConfig(provider="mock", model="mock-model", mode="controlled-repair")
    out_dir = tmp_path / "results" / "milestone-3b"

    res = run_controlled_repair_benchmark(
        case=case,
        analyst_provider=mock,
        config=config,
        fixtures=[c02],
        corrupted_dir=_CORRUPTED_DIR,
        output_dir=out_dir,
    )

    assert res.summary.controlled_repair_success_count == 0
    assert res.summary.target_diagnostic_resolved_count == 0
    assert res.summary.persistent_failure_count == 1

    t = res.trial_results[0]
    assert t.expected_diagnostic_resolved is False
    assert t.repair_success is False
    assert t.outcome == "persistent"
    assert "TV_NOT_DISCOUNTED" in t.persistent_diagnostics


def test_controlled_repair_parse_failure(
    tmp_path: Path,
    case: NorthstarCase,
) -> None:
    """Unparseable repair response is recorded as parse_failure without crashing."""
    c02 = next(f for f in CONTROLLED_FIXTURES if f.fixture_id == "c02")
    mock = MockAnalyst(responses=["Invalid JSON response"])
    config = ProviderConfig(provider="mock", model="mock-model", mode="controlled-repair")
    out_dir = tmp_path / "results" / "milestone-3b"

    res = run_controlled_repair_benchmark(
        case=case,
        analyst_provider=mock,
        config=config,
        fixtures=[c02],
        corrupted_dir=_CORRUPTED_DIR,
        output_dir=out_dir,
    )

    assert res.summary.parsed_repair_count == 0
    assert res.summary.parse_success_rate == 0.0
    t = res.trial_results[0]
    assert t.repair_parse_success is False
    assert t.outcome == "parse_failure"
    assert (res.experiment_dir / "c02" / "repair_parse_error.json").exists()


def test_controlled_repair_gold_leakage_safeguards(
    tmp_path: Path,
    case: NorthstarCase,
    gold_submission: Submission,
) -> None:
    """Repair prompts for all 10 fixtures never leak hidden benchmark values."""
    mock = MockAnalyst(responses=[json.dumps(gold_submission.model_dump())])
    config = ProviderConfig(provider="mock", model="mock-model", mode="controlled-repair")
    out_dir = tmp_path / "results" / "milestone-3b"

    res = run_controlled_repair_benchmark(
        case=case,
        analyst_provider=mock,
        config=config,
        fixtures=CONTROLLED_FIXTURES,
        corrupted_dir=_CORRUPTED_DIR,
        output_dir=out_dir,
    )

    for f in CONTROLLED_FIXTURES:
        prompt_path = res.experiment_dir / f.fixture_id / "repair_prompt.txt"
        assert prompt_path.exists()
        prompt_text = prompt_path.read_text()
        # Ensure diagnostics section contains zero leaked benchmark answers
        diag_section = prompt_text.split("## Deterministic Grader Diagnostics")[1].split("---")[0]
        assert "1712.97" not in diag_section
        assert "1441.69" not in diag_section
        assert "23.13" not in diag_section
        assert "9.2832" not in diag_section


def test_controlled_repair_full_summary_and_markdown(
    tmp_path: Path,
    case: NorthstarCase,
    gold_submission: Submission,
) -> None:
    """Full benchmark produces summary.json, summary.md with category and difficulty tables."""
    c02 = next(f for f in CONTROLLED_FIXTURES if f.fixture_id == "c02")
    c05 = next(f for f in CONTROLLED_FIXTURES if f.fixture_id == "c05")
    mock = MockAnalyst(responses=[json.dumps(gold_submission.model_dump())])
    config = ProviderConfig(provider="mock", model="mock-v4", mode="controlled-repair")
    out_dir = tmp_path / "results" / "milestone-3b"

    res = run_controlled_repair_benchmark(
        case=case,
        analyst_provider=mock,
        config=config,
        fixtures=[c02, c05],
        corrupted_dir=_CORRUPTED_DIR,
        output_dir=out_dir,
    )

    assert res.experiment_id.startswith("m3b-controlled-repair-mock-mock-v4")
    assert (res.experiment_dir / "summary.json").exists()
    assert (res.experiment_dir / "summary.md").exists()

    md_text = (res.experiment_dir / "summary.md").read_text()
    assert "Milestone 3B — Controlled Repair Benchmark Report" in md_text
    assert "Headline Benchmark Metrics" in md_text
    assert "Per-Fixture Outcome Table" in md_text
    assert "Error-Category Repair Performance" in md_text
    assert "Difficulty Analysis (Local vs. Propagating Repairs)" in md_text
    assert "Diagnostic Transitions & Regression Invariant Auditing" in md_text


def test_cli_repair_benchmark_dry_run() -> None:
    """CLI repair-benchmark dry run displays all parameters and default output directory."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "repair-benchmark",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--thinking",
            "on",
            "--reasoning-effort",
            "high",
            "--fixtures",
            "c02,c08,c10",
        ],
    )

    assert result.exit_code == 0
    assert "Milestone 3B: Controlled Repair Benchmark" in result.output
    assert "Output Dir:  results/milestone-3b" in result.output
    assert "Fixtures:    3 (c02, c08, c10)" in result.output
    assert "--fixtures c02,c08,c10" in result.output


def test_cli_repair_benchmark_explicit_output_override() -> None:
    """CLI repair-benchmark respects explicit --output override."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "repair-benchmark",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--output",
            "results/custom-repair-bench",
        ],
    )

    assert result.exit_code == 0
    assert "Output Dir:  results/custom-repair-bench" in result.output
    assert "--output results/custom-repair-bench" in result.output
