"""Experiment runner for Milestone 1 Direct Analyst Baseline."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ib_eval.baseline.analysis import (
    ExperimentSummary,
    compute_aggregate_statistics,
    generate_markdown_summary,
)
from ib_eval.baseline.interface import (
    Analyst,
    ProviderConfig,
    TrialMetadata,
    TrialResult,
)
from ib_eval.baseline.prompt import build_analyst_prompt, build_structured_analyst_prompt
from ib_eval.case import NorthstarCase
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission


def get_git_commit() -> str | None:
    """Safely get current git commit hash if available."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


def extract_json_payload(raw_text: str) -> str:
    """Extract JSON payload from raw text, stripping optional markdown code fences."""
    text = raw_text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if match:
        return match.group(1).strip()
    return text


def parse_submission_response(raw_text: str) -> tuple[Submission | None, str | None]:
    """Attempt to parse model response into Submission schema.

    Returns (submission, None) on success or (None, error_str) on failure.
    """
    clean_text = extract_json_payload(raw_text)
    if not clean_text:
        return None, "Empty response from model"

    try:
        raw_dict = json.loads(clean_text)
    except Exception as exc:
        return None, f"JSON parse error: {exc}"

    if not isinstance(raw_dict, dict):
        return None, f"Expected JSON object (dict), got {type(raw_dict).__name__}"

    try:
        submission = Submission.model_validate(raw_dict)
        return submission, None
    except Exception as exc:
        return None, f"Submission schema validation error: {exc}"


class DirectAnalyst:
    """Direct, single-call analyst wrapper around an Analyst provider."""

    def __init__(self, provider: Analyst) -> None:
        self.provider = provider

    def run_trial(
        self,
        prompt: str,
        case: NorthstarCase,
        config: ProviderConfig,
        run_index: int,
        trial_dir: Path,
    ) -> TrialResult:
        """Execute a single trial: prompt -> complete -> parse -> grade -> save artifacts."""
        trial_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).isoformat()

        # 1. Model completion (with provider error handling)
        try:
            completion = self.provider.complete(prompt)
            raw_text = completion.raw_response
            latency = completion.latency_seconds
            usage = completion.usage
            provider_error: str | None = None
        except Exception as exc:
            raw_text = ""
            latency = None
            usage = None
            provider_error = str(exc)

        # 2. Always preserve raw response
        raw_file = trial_dir / "raw_response.txt"
        raw_file.write_text(raw_text)

        # 3. Parse submission or record provider error
        score: float | None = None
        hard_failure_codes: list[str] = []
        grade_report = None
        submission = None
        parse_error: str | None = None

        if provider_error is not None:
            provider_payload = {
                "status": "provider_error",
                "error": provider_error,
                "provider": config.provider,
                "model": config.model,
            }
            (trial_dir / "provider_error.json").write_text(
                json.dumps(provider_payload, indent=2)
            )
            parse_error = f"Provider error: {provider_error}"
        else:
            submission, parse_error = parse_submission_response(raw_text)
            if submission is not None:
                (trial_dir / "submission.json").write_text(
                    json.dumps(submission.model_dump(), indent=2)
                )
                grade_report = grade_submission(submission, case)
                (trial_dir / "grade.json").write_text(
                    json.dumps(grade_report.model_dump(), indent=2)
                )
                score = grade_report.total_score
                hard_failure_codes = [f.diagnostic_code for f in grade_report.hard_failures]
            else:
                parse_payload = {
                    "status": "parse_failure",
                    "error": parse_error or "Unknown parse error",
                    "raw_response_preserved": True,
                }
                (trial_dir / "parse_error.json").write_text(
                    json.dumps(parse_payload, indent=2)
                )

        # 4. Save metadata
        metadata = TrialMetadata(
            run_index=run_index,
            provider=config.provider,
            model=config.model,
            mode=config.mode,
            timestamp=timestamp,
            temperature=config.temperature,
            seed=config.seed,
            thinking=config.thinking,
            reasoning_effort=config.reasoning_effort,
            latency_seconds=latency,
            token_usage=usage,
            parsed_successfully=submission is not None,
            score=score,
            hard_failure_count=len(hard_failure_codes),
            hard_failure_codes=hard_failure_codes,
            git_commit=get_git_commit(),
        )

        (trial_dir / "metadata.json").write_text(
            json.dumps(metadata.__dict__, indent=2)
        )

        return TrialResult(
            metadata=metadata,
            raw_response=raw_text,
            submission=submission,
            parse_error=parse_error,
            grade=grade_report,
        )


@dataclass
class ExperimentResult:
    """Full outcome of a multi-trial baseline experiment."""

    experiment_id: str
    experiment_dir: Path
    config: ProviderConfig
    case_id: str
    trials: list[TrialResult]
    summary: ExperimentSummary


def sanitize_name(name: str) -> str:
    """Sanitize provider and model names for safe filesystem directories."""
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)


def run_baseline_experiment(
    case: NorthstarCase,
    analyst_provider: Analyst,
    config: ProviderConfig,
    runs: int,
    output_dir: Path,
) -> ExperimentResult:
    """Run repeated independent trials and record all artifacts and aggregate statistics."""
    timestamp_slug = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    sanitized_provider = sanitize_name(config.provider)
    sanitized_model = sanitize_name(config.model)
    sanitized_mode = sanitize_name(config.mode)

    condition_suffix = ""
    if config.thinking is not None:
        if config.thinking:
            if config.reasoning_effort:
                condition_suffix = f"-thinking-{config.reasoning_effort.lower()}"
            else:
                condition_suffix = "-thinking-on"
        else:
            condition_suffix = "-thinking-off"

    milestone_prefix = "m2" if config.mode == "structured" else "m1"
    exp_id = (
        f"{milestone_prefix}-{sanitized_mode}-{sanitized_provider}-"
        f"{sanitized_model}{condition_suffix}-{timestamp_slug}"
    )

    exp_dir = output_dir / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build and save prompt based on mode
    if config.mode == "structured":
        prompt = build_structured_analyst_prompt(case)
    else:
        prompt = build_analyst_prompt(case)
    (exp_dir / "prompt.txt").write_text(prompt)

    # 2. Save experiment configuration
    config_dict = {
        "experiment_id": exp_id,
        "case_id": case.meta.case_id,
        "mode": config.mode,
        "provider": config.provider,
        "model": config.model,
        "runs": runs,
        "temperature": config.temperature,
        "seed": config.seed,
        "thinking": config.thinking,
        "reasoning_effort": config.reasoning_effort,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": get_git_commit(),
    }
    (exp_dir / "config.json").write_text(json.dumps(config_dict, indent=2))

    # 3. Execute runs
    direct_analyst = DirectAnalyst(analyst_provider)
    trial_results: list[TrialResult] = []

    for i in range(1, runs + 1):
        run_folder = exp_dir / f"run_{i:03d}"
        res = direct_analyst.run_trial(
            prompt=prompt,
            case=case,
            config=config,
            run_index=i,
            trial_dir=run_folder,
        )
        trial_results.append(res)

    # 4. Compute aggregate statistics
    summary = compute_aggregate_statistics(
        experiment_id=exp_id,
        case_id=case.meta.case_id,
        provider=config.provider,
        model=config.model,
        mode=config.mode,
        requested_runs=runs,
        trial_results=trial_results,
    )

    # 5. Persist summary.json and summary.md
    (exp_dir / "summary.json").write_text(json.dumps(summary.model_dump(), indent=2))

    md_report = generate_markdown_summary(summary, trial_results)
    (exp_dir / "summary.md").write_text(md_report)

    return ExperimentResult(
        experiment_id=exp_id,
        experiment_dir=exp_dir,
        config=config,
        case_id=case.meta.case_id,
        trials=trial_results,
        summary=summary,
    )
