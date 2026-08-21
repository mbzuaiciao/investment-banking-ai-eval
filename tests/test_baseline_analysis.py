"""Tests for aggregate statistics computation and markdown summary generation."""

from __future__ import annotations

import json
from pathlib import Path

from ib_eval.baseline.analysis import (
    compute_aggregate_statistics,
    generate_markdown_summary,
)
from ib_eval.baseline.interface import TrialMetadata, TrialResult
from ib_eval.case import load_case
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission

_CASE_DIR = Path(__file__).parent.parent / "cases" / "northstar-v1"
_GOLD_FILE = Path(__file__).parent.parent / "examples" / "gold_submission" / "submission.json"
_C03_FILE = (
    Path(__file__).parent.parent
    / "examples"
    / "corrupted"
    / "c03_cash_subtracted"
    / "submission.json"
)


def _make_trial_result(
    run_idx: int,
    submission_path: Path | None,
) -> TrialResult:
    case = load_case(_CASE_DIR)
    if submission_path is not None:
        sub_dict = json.loads(submission_path.read_text())
        sub = Submission.model_validate(sub_dict)
        grade = grade_submission(sub, case)
        meta = TrialMetadata(
            run_index=run_idx,
            provider="mock",
            model="test-model",
            timestamp="2026-08-21T12:00:00Z",
            parsed_successfully=True,
            score=grade.total_score,
            hard_failure_count=len(grade.hard_failures),
            hard_failure_codes=[f.diagnostic_code for f in grade.hard_failures],
        )
        return TrialResult(
            metadata=meta,
            raw_response=json.dumps(sub_dict),
            submission=sub,
            grade=grade,
        )

    meta = TrialMetadata(
        run_index=run_idx,
        provider="mock",
        model="test-model",
        timestamp="2026-08-21T12:00:00Z",
        parsed_successfully=False,
        score=None,
    )
    return TrialResult(
        metadata=meta,
        raw_response="not json",
        parse_error="Invalid JSON",
    )


def test_compute_aggregate_statistics_mixed_runs() -> None:
    """Check statistical aggregation across multiple runs with successes and failures."""
    t1 = _make_trial_result(1, _GOLD_FILE)
    t2 = _make_trial_result(2, _C03_FILE)
    t3 = _make_trial_result(3, None)  # parse failure

    summary = compute_aggregate_statistics(
        experiment_id="exp-test-001",
        case_id="northstar-v1",
        provider="mock",
        model="test-model",
        requested_runs=3,
        trial_results=[t1, t2, t3],
    )

    assert summary.requested_runs == 3
    assert summary.completed_model_calls == 3
    assert summary.parsed_runs == 2
    assert summary.parse_failure_count == 1
    assert summary.parse_success_rate == round(2 / 3, 4)

    assert summary.mean_score is not None
    assert summary.mean_score == round((100.0 + t2.metadata.score) / 2, 2)  # type: ignore[operator]
    assert summary.min_score == t2.metadata.score
    assert summary.max_score == 100.0
    assert summary.hard_failure_run_count == 1
    assert summary.hard_failure_rate == 0.5  # 1 out of 2 parsed

    assert "EQ_BRIDGE_CASH_REVERSED" in summary.diagnostic_frequency
    assert summary.diagnostic_frequency["EQ_BRIDGE_CASH_REVERSED"] == 1


def test_generate_markdown_summary() -> None:
    """Markdown summary contains expected sections and tables."""
    t1 = _make_trial_result(1, _GOLD_FILE)
    t2 = _make_trial_result(2, _C03_FILE)

    summary = compute_aggregate_statistics(
        experiment_id="exp-test-002",
        case_id="northstar-v1",
        provider="mock",
        model="test-model",
        requested_runs=2,
        trial_results=[t1, t2],
    )

    md = generate_markdown_summary(summary, [t1, t2])

    assert "# Milestone 1 — Direct Analyst Baseline Report" in md
    assert "## Summary Statistics" in md
    assert "## Individual Run Breakdown" in md
    assert "## Failure Frequency Analysis" in md
    assert "## Grader Performance Breakdown" in md
    assert "EQ_BRIDGE_CASH_REVERSED" in md
    assert "100.0" in md
