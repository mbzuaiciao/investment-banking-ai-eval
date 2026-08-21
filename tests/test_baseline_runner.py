"""Tests for baseline runner, trial execution, and artifact generation."""

from __future__ import annotations

import json
from pathlib import Path

from ib_eval.baseline.interface import ProviderConfig
from ib_eval.baseline.providers import MockAnalyst
from ib_eval.baseline.runner import (
    DirectAnalyst,
    extract_json_payload,
    parse_submission_response,
    run_baseline_experiment,
)
from ib_eval.case import load_case

_CASE_DIR = Path(__file__).parent.parent / "cases" / "northstar-v1"
_GOLD_FILE = Path(__file__).parent.parent / "examples" / "gold_submission" / "submission.json"
_C03_FILE = (
    Path(__file__).parent.parent
    / "examples"
    / "corrupted"
    / "c03_cash_subtracted"
    / "submission.json"
)


def test_extract_json_payload_raw() -> None:
    """Extract raw JSON string without markdown fences."""
    raw = '{"key": "value"}'
    assert extract_json_payload(raw) == '{"key": "value"}'


def test_extract_json_payload_with_code_fences() -> None:
    """Extract JSON enclosed in markdown code fences."""
    raw = "```json\n{\n  \"key\": \"value\"\n}\n```"
    assert extract_json_payload(raw) == '{\n  "key": "value"\n}'


def test_parse_submission_response_valid_gold() -> None:
    """Valid gold submission JSON parses cleanly."""
    gold_text = _GOLD_FILE.read_text()
    sub, err = parse_submission_response(gold_text)
    assert sub is not None
    assert err is None
    assert sub.case_id == "northstar-v1"


def test_parse_submission_response_invalid_json() -> None:
    """Malformed JSON string returns parse error."""
    raw = "This is not valid JSON"
    sub, err = parse_submission_response(raw)
    assert sub is None
    assert err is not None
    assert "JSON parse error" in err


def test_parse_submission_response_invalid_schema() -> None:
    """Syntactically valid JSON missing required fields fails validation."""
    raw = '{"incomplete": true}'
    sub, err = parse_submission_response(raw)
    assert sub is None
    assert err is not None
    assert "validation error" in err.lower()


def test_direct_analyst_perfect_mock_trial(tmp_path: Path) -> None:
    """Single trial with perfect gold mock outputs 100/100 and creates all files."""
    case = load_case(_CASE_DIR)
    gold_text = _GOLD_FILE.read_text()
    mock_provider = MockAnalyst(gold_text)
    analyst = DirectAnalyst(mock_provider)

    config = ProviderConfig(provider="mock", model="mock-perfect")
    trial_dir = tmp_path / "run_001"

    result = analyst.run_trial(
        prompt="Test prompt",
        case=case,
        config=config,
        run_index=1,
        trial_dir=trial_dir,
    )

    assert result.metadata.parsed_successfully is True
    assert result.metadata.score == 100.0
    assert result.metadata.hard_failure_count == 0
    assert result.parse_error is None

    # Check generated files
    assert (trial_dir / "raw_response.txt").exists()
    assert (trial_dir / "submission.json").exists()
    assert (trial_dir / "grade.json").exists()
    assert (trial_dir / "metadata.json").exists()
    assert not (trial_dir / "parse_error.json").exists()


def test_direct_analyst_imperfect_mock_trial(tmp_path: Path) -> None:
    """Single trial with corrupted mock (c03) records failures properly."""
    case = load_case(_CASE_DIR)
    c03_text = _C03_FILE.read_text()
    mock_provider = MockAnalyst(c03_text)
    analyst = DirectAnalyst(mock_provider)

    config = ProviderConfig(provider="mock", model="mock-c03")
    trial_dir = tmp_path / "run_001"

    result = analyst.run_trial(
        prompt="Test prompt",
        case=case,
        config=config,
        run_index=1,
        trial_dir=trial_dir,
    )

    assert result.metadata.parsed_successfully is True
    assert result.metadata.score is not None
    assert result.metadata.score < 100.0
    assert "EQ_BRIDGE_CASH_REVERSED" in result.metadata.hard_failure_codes
    assert (trial_dir / "grade.json").exists()


def test_direct_analyst_malformed_mock_trial(tmp_path: Path) -> None:
    """Single trial with malformed mock output records parse_error.json without crashing."""
    case = load_case(_CASE_DIR)
    mock_provider = MockAnalyst("MALFORMED TEXT NOT JSON")
    analyst = DirectAnalyst(mock_provider)

    config = ProviderConfig(provider="mock", model="mock-malformed")
    trial_dir = tmp_path / "run_001"

    result = analyst.run_trial(
        prompt="Test prompt",
        case=case,
        config=config,
        run_index=1,
        trial_dir=trial_dir,
    )

    assert result.metadata.parsed_successfully is False
    assert result.metadata.score is None
    assert result.parse_error is not None
    assert (trial_dir / "raw_response.txt").exists()
    assert (trial_dir / "parse_error.json").exists()
    assert not (trial_dir / "submission.json").exists()
    assert not (trial_dir / "grade.json").exists()


def test_multi_run_baseline_experiment(tmp_path: Path) -> None:
    """Multi-trial baseline experiment creates experiment directory and summaries."""
    case = load_case(_CASE_DIR)
    gold_text = _GOLD_FILE.read_text()
    c03_text = _C03_FILE.read_text()
    malformed_text = "I am a financial analyst memo without valid JSON."

    # 3 runs: 1 perfect, 1 imperfect, 1 malformed
    mock_provider = MockAnalyst([gold_text, c03_text, malformed_text])
    config = ProviderConfig(provider="mock", model="mock-trio")

    res = run_baseline_experiment(
        case=case,
        analyst_provider=mock_provider,
        config=config,
        runs=3,
        output_dir=tmp_path,
    )

    assert res.summary.requested_runs == 3
    assert res.summary.completed_model_calls == 3
    assert res.summary.parsed_runs == 2
    assert res.summary.parse_failure_count == 1
    assert res.summary.hard_failure_run_count == 1

    # Check filesystem structure
    exp_dir = res.experiment_dir
    assert (exp_dir / "prompt.txt").exists()
    assert (exp_dir / "config.json").exists()
    assert (exp_dir / "summary.json").exists()
    assert (exp_dir / "summary.md").exists()
    assert (exp_dir / "run_001").exists()
    assert (exp_dir / "run_002").exists()
    assert (exp_dir / "run_003").exists()

    # Validate summary.json content
    summary_raw = json.loads((exp_dir / "summary.json").read_text())
    assert summary_raw["parsed_runs"] == 2
    assert "EQ_BRIDGE_CASH_REVERSED" in summary_raw["diagnostic_frequency"]

    # Validate summary.md content
    md_content = (exp_dir / "summary.md").read_text()
    assert "Milestone 1 — Direct Analyst Baseline Report" in md_content
    assert "EQ_BRIDGE_CASH_REVERSED" in md_content
    assert "run_001" in md_content or "001" in md_content
