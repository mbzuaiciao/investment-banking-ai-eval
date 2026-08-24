"""Benchmark execution engine for Milestone 3B Controlled Repair."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ib_eval.baseline.interface import Analyst, ProviderConfig
from ib_eval.baseline.prompt import STRUCTURED_PROMPT_VERSION, build_repair_prompt
from ib_eval.baseline.runner import (
    get_git_commit,
    parse_submission_response,
    sanitize_name,
)
from ib_eval.case import NorthstarCase
from ib_eval.controlled_repair.analysis import (
    ControlledFixtureTrialResult,
    ControlledRepairBenchmarkSummary,
    compute_controlled_repair_statistics,
    generate_controlled_repair_markdown_summary,
)
from ib_eval.controlled_repair.fixtures import ControlledFixture
from ib_eval.scoring import grade_submission


class BenchmarkDriftError(Exception):
    """Raised when a corrupted fixture does not emit its expected diagnostic code."""


@dataclass
class ControlledRepairBenchmarkResult:
    """Complete outcome of a controlled repair benchmark run."""

    experiment_id: str
    experiment_dir: Path
    config: ProviderConfig
    case_id: str
    summary: ControlledRepairBenchmarkSummary
    trial_results: list[ControlledFixtureTrialResult]


def run_controlled_repair_benchmark(
    case: NorthstarCase,
    analyst_provider: Analyst,
    config: ProviderConfig,
    fixtures: list[ControlledFixture],
    corrupted_dir: Path,
    output_dir: Path,
) -> ControlledRepairBenchmarkResult:
    """Execute controlled repair benchmark trials across selected corrupted fixtures."""
    timestamp_slug = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    sanitized_provider = sanitize_name(config.provider)
    sanitized_model = sanitize_name(config.model)

    condition_suffix = ""
    if config.thinking is not None:
        if config.thinking:
            if config.reasoning_effort:
                condition_suffix = f"-thinking-{config.reasoning_effort.lower()}"
            else:
                condition_suffix = "-thinking-on"
        else:
            condition_suffix = "-thinking-off"

    exp_id = (
        f"m3b-controlled-repair-{sanitized_provider}-"
        f"{sanitized_model}{condition_suffix}-{timestamp_slug}"
    )

    exp_dir = output_dir / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save benchmark configuration
    config_dict = {
        "experiment_id": exp_id,
        "case_id": case.meta.case_id,
        "mode": "controlled-repair",
        "provider": config.provider,
        "model": config.model,
        "fixtures_count": len(fixtures),
        "fixtures": [f.fixture_id for f in fixtures],
        "temperature": config.temperature,
        "seed": config.seed,
        "thinking": config.thinking,
        "reasoning_effort": config.reasoning_effort,
        "prompt_version": STRUCTURED_PROMPT_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": get_git_commit(),
    }
    (exp_dir / "config.json").write_text(json.dumps(config_dict, indent=2))

    # 2. Execute each controlled fixture trial
    trial_results: list[ControlledFixtureTrialResult] = []

    for fixture in fixtures:
        fixture_dir = exp_dir / fixture.fixture_id
        fixture_dir.mkdir(parents=True, exist_ok=True)

        # Step 2a: Load and grade initial corrupted submission
        initial_sub = fixture.load_submission(corrupted_dir)
        (fixture_dir / "initial_submission.json").write_text(
            json.dumps(initial_sub.model_dump(), indent=2)
        )

        initial_grade = grade_submission(initial_sub, case)
        (fixture_dir / "initial_grade.json").write_text(
            json.dumps(initial_grade.model_dump(), indent=2)
        )

        initial_all_codes = [
            f.diagnostic_code for r in initial_grade.grader_results for f in r.failures
        ]
        initial_hf_codes = [f.diagnostic_code for f in initial_grade.hard_failures]

        # Step 2b: Protect against benchmark drift
        if fixture.expected_diagnostic not in initial_all_codes:
            raise BenchmarkDriftError(
                f"Benchmark drift detected: Fixture '{fixture.fixture_id}' ({fixture.dir_name}) "
                f"did not emit expected diagnostic '{fixture.expected_diagnostic}'. "
                f"Emitted diagnostics: {initial_all_codes}"
            )

        # Step 2c: Build zero-gold-leakage repair prompt
        repair_prompt = build_repair_prompt(case, initial_sub, initial_grade)
        (fixture_dir / "repair_prompt.txt").write_text(repair_prompt)

        # Step 2d: Execute single repair completion
        try:
            completion = analyst_provider.complete(repair_prompt)
            raw_text = completion.raw_response
            latency = completion.latency_seconds
            usage = completion.usage
            provider_error: str | None = None
        except Exception as exc:
            raw_text = ""
            latency = None
            usage = None
            provider_error = str(exc)

        (fixture_dir / "repair_raw_response.txt").write_text(raw_text)

        # Step 2e: Parse and grade repair response
        if provider_error is not None:
            error_payload = {
                "status": "provider_error",
                "error": provider_error,
                "provider": config.provider,
                "model": config.model,
            }
            (fixture_dir / "repair_parse_error.json").write_text(
                json.dumps(error_payload, indent=2)
            )
            t_res = ControlledFixtureTrialResult(
                fixture_id=fixture.fixture_id,
                dir_name=fixture.dir_name,
                name=fixture.name,
                expected_diagnostic=fixture.expected_diagnostic,
                category=fixture.category.value,
                difficulty=fixture.difficulty.value,
                initial_score=initial_grade.total_score,
                repaired_score=None,
                score_delta=None,
                initial_hard_failure_count=len(initial_hf_codes),
                repaired_hard_failure_count=len(initial_hf_codes),
                initial_hard_failure_codes=initial_hf_codes,
                repaired_hard_failure_codes=initial_hf_codes,
                expected_diagnostic_resolved=False,
                persistent_diagnostics=initial_all_codes,
                new_diagnostics=[],
                repair_parse_success=False,
                repair_success=False,
                partial_repair=False,
                outcome="parse_failure",
                prompt_version=STRUCTURED_PROMPT_VERSION,
                latency_seconds=latency,
                token_usage=usage,
            )
        else:
            repaired_sub, parse_err = parse_submission_response(raw_text)
            if repaired_sub is None:
                parse_payload = {
                    "status": "repair_parse_failure",
                    "error": parse_err or "Unknown repair parse error",
                    "raw_response_preserved": True,
                }
                (fixture_dir / "repair_parse_error.json").write_text(
                    json.dumps(parse_payload, indent=2)
                )
                t_res = ControlledFixtureTrialResult(
                    fixture_id=fixture.fixture_id,
                    dir_name=fixture.dir_name,
                    name=fixture.name,
                    expected_diagnostic=fixture.expected_diagnostic,
                    category=fixture.category.value,
                    difficulty=fixture.difficulty.value,
                    initial_score=initial_grade.total_score,
                    repaired_score=None,
                    score_delta=None,
                    initial_hard_failure_count=len(initial_hf_codes),
                    repaired_hard_failure_count=len(initial_hf_codes),
                    initial_hard_failure_codes=initial_hf_codes,
                    repaired_hard_failure_codes=initial_hf_codes,
                    expected_diagnostic_resolved=False,
                    persistent_diagnostics=initial_all_codes,
                    new_diagnostics=[],
                    repair_parse_success=False,
                    repair_success=False,
                    partial_repair=False,
                    outcome="parse_failure",
                    prompt_version=STRUCTURED_PROMPT_VERSION,
                    latency_seconds=latency,
                    token_usage=usage,
                )
            else:
                (fixture_dir / "repaired_submission.json").write_text(
                    json.dumps(repaired_sub.model_dump(), indent=2)
                )
                repaired_grade = grade_submission(repaired_sub, case)
                (fixture_dir / "repaired_grade.json").write_text(
                    json.dumps(repaired_grade.model_dump(), indent=2)
                )

                repaired_all_codes = [
                    f.diagnostic_code for r in repaired_grade.grader_results for f in r.failures
                ]
                repaired_hf_codes = [f.diagnostic_code for f in repaired_grade.hard_failures]

                resolved = fixture.expected_diagnostic not in repaired_all_codes
                persisting = sorted(list(set(initial_all_codes) & set(repaired_all_codes)))
                new_errors = sorted(list(set(repaired_all_codes) - set(initial_all_codes)))

                is_success = resolved and (len(repaired_hf_codes) == 0)
                is_partial = resolved and (len(repaired_hf_codes) > 0)
                outcome = "success" if is_success else ("partial" if is_partial else "persistent")

                score_delta = round(repaired_grade.total_score - initial_grade.total_score, 2)

                t_res = ControlledFixtureTrialResult(
                    fixture_id=fixture.fixture_id,
                    dir_name=fixture.dir_name,
                    name=fixture.name,
                    expected_diagnostic=fixture.expected_diagnostic,
                    category=fixture.category.value,
                    difficulty=fixture.difficulty.value,
                    initial_score=initial_grade.total_score,
                    repaired_score=repaired_grade.total_score,
                    score_delta=score_delta,
                    initial_hard_failure_count=len(initial_hf_codes),
                    repaired_hard_failure_count=len(repaired_hf_codes),
                    initial_hard_failure_codes=initial_hf_codes,
                    repaired_hard_failure_codes=repaired_hf_codes,
                    expected_diagnostic_resolved=resolved,
                    persistent_diagnostics=persisting,
                    new_diagnostics=new_errors,
                    repair_parse_success=True,
                    repair_success=is_success,
                    partial_repair=is_partial,
                    outcome=outcome,
                    prompt_version=STRUCTURED_PROMPT_VERSION,
                    latency_seconds=latency,
                    token_usage=usage,
                )

        (fixture_dir / "metadata.json").write_text(json.dumps(t_res.model_dump(), indent=2))
        trial_results.append(t_res)

    # 3. Compute aggregate statistics
    summary = compute_controlled_repair_statistics(
        experiment_id=exp_id,
        case_id=case.meta.case_id,
        provider=config.provider,
        model=config.model,
        timestamp=datetime.now(UTC).isoformat(),
        trial_results=trial_results,
        git_commit=get_git_commit(),
    )

    # 4. Save summary.json and summary.md
    (exp_dir / "summary.json").write_text(json.dumps(summary.model_dump(), indent=2))
    md_report = generate_controlled_repair_markdown_summary(summary)
    (exp_dir / "summary.md").write_text(md_report)

    return ControlledRepairBenchmarkResult(
        experiment_id=exp_id,
        experiment_dir=exp_dir,
        config=config,
        case_id=case.meta.case_id,
        summary=summary,
        trial_results=trial_results,
    )
