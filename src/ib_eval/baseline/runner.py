"""Experiment runner for Direct (M1), Structured (M2), and Repair (M3) Analyst Baselines."""

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
from ib_eval.baseline.prompt import (
    DIRECT_PROMPT_VERSION,
    STRUCTURED_PROMPT_VERSION,
    build_analyst_prompt,
    build_repair_prompt,
    build_structured_analyst_prompt,
)
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
    match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
    if match:
        return match.group(1).strip()
    return text


def classify_parse_error(error_str: str | None) -> str:
    """Classify parse failure type: json_syntax_error vs structural_schema_error."""
    if not error_str:
        return "unknown_error"
    if (
        error_str.startswith("JSON parse error")
        or "Empty response" in error_str
        or "Expected JSON object" in error_str
    ):
        return "json_syntax_error"
    return "structural_schema_error"


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


def combine_usages(
    u1: dict[str, int] | None,
    u2: dict[str, int] | None,
) -> dict[str, int] | None:
    """Combine token usage dictionaries from two calls."""
    if u1 is None and u2 is None:
        return None
    res: dict[str, int] = {}
    for k in set((u1 or {}).keys()) | set((u2 or {}).keys()):
        res[k] = (u1 or {}).get(k, 0) + (u2 or {}).get(k, 0)
    return res


class DirectAnalyst:
    """Analyst execution harness supporting Direct (M1), Structured (M2), and Repair (M3)."""

    def __init__(self, provider: Analyst) -> None:
        self.provider = provider

    def run_single_pass_trial(
        self,
        prompt: str,
        case: NorthstarCase,
        config: ProviderConfig,
        run_index: int,
        trial_dir: Path,
    ) -> TrialResult:
        """Execute a single-call trial (direct or structured mode)."""
        trial_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).isoformat()

        # 1. Model completion
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

        # 2. Preserve raw response
        (trial_dir / "raw_response.txt").write_text(raw_text)

        # 3. Parse and grade
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
            (trial_dir / "provider_error.json").write_text(json.dumps(provider_payload, indent=2))
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
                    "error_type": classify_parse_error(parse_error),
                    "error": parse_error or "Unknown parse error",
                    "raw_response_preserved": True,
                }
                (trial_dir / "parse_error.json").write_text(json.dumps(parse_payload, indent=2))

        # 4. Save metadata
        prompt_version = (
            STRUCTURED_PROMPT_VERSION
            if config.mode in ("structured", "repair")
            else DIRECT_PROMPT_VERSION
        )
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
            prompt_version=prompt_version,
            git_commit=get_git_commit(),
        )

        (trial_dir / "metadata.json").write_text(json.dumps(metadata.__dict__, indent=2))

        return TrialResult(
            metadata=metadata,
            raw_response=raw_text,
            submission=submission,
            parse_error=parse_error,
            grade=grade_report,
        )

    def run_repair_trial(
        self,
        prompt: str,
        case: NorthstarCase,
        config: ProviderConfig,
        run_index: int,
        trial_dir: Path,
    ) -> TrialResult:
        """Execute a Milestone 3 repair trial (initial call + deterministic feedback repair)."""
        trial_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).isoformat()

        # ===================================================================
        # CALL 1: Initial Structured Submission
        # ===================================================================
        try:
            completion1 = self.provider.complete(prompt)
            init_raw_text = completion1.raw_response
            init_latency = completion1.latency_seconds
            init_usage = completion1.usage
            provider_error: str | None = None
        except Exception as exc:
            init_raw_text = ""
            init_latency = None
            init_usage = None
            provider_error = str(exc)

        # Always preserve initial raw response
        (trial_dir / "initial_raw_response.txt").write_text(init_raw_text)

        if provider_error is not None:
            provider_payload = {
                "status": "provider_error",
                "error": provider_error,
                "provider": config.provider,
                "model": config.model,
            }
            (trial_dir / "provider_error.json").write_text(json.dumps(provider_payload, indent=2))
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
                latency_seconds=init_latency,
                first_call_latency_seconds=init_latency,
                token_usage=init_usage,
                first_call_token_usage=init_usage,
                parsed_successfully=False,
                initial_parsed_successfully=False,
                repair_attempted=False,
                repair_skipped_reason="provider_error",
                git_commit=get_git_commit(),
            )
            (trial_dir / "metadata.json").write_text(json.dumps(metadata.__dict__, indent=2))
            return TrialResult(
                metadata=metadata,
                raw_response=init_raw_text,
                initial_raw_response=init_raw_text,
                parse_error=f"Provider error: {provider_error}",
            )

        # Parse initial submission
        initial_sub, init_parse_err = parse_submission_response(init_raw_text)

        # If initial response fails parsing, do NOT attempt repair call
        if initial_sub is None:
            parse_payload = {
                "status": "initial_parse_failure",
                "error_type": classify_parse_error(init_parse_err),
                "error": init_parse_err or "Unknown initial parse error",
                "raw_response_preserved": True,
            }
            (trial_dir / "initial_parse_error.json").write_text(json.dumps(parse_payload, indent=2))
            (trial_dir / "parse_error.json").write_text(json.dumps(parse_payload, indent=2))
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
                latency_seconds=init_latency,
                first_call_latency_seconds=init_latency,
                token_usage=init_usage,
                first_call_token_usage=init_usage,
                parsed_successfully=False,
                initial_parsed_successfully=False,
                repair_attempted=False,
                repair_skipped_reason="initial_parse_failure",
                git_commit=get_git_commit(),
            )
            (trial_dir / "metadata.json").write_text(json.dumps(metadata.__dict__, indent=2))
            return TrialResult(
                metadata=metadata,
                raw_response=init_raw_text,
                initial_raw_response=init_raw_text,
                parse_error=init_parse_err,
            )

        # Initial parse succeeded
        (trial_dir / "initial_submission.json").write_text(
            json.dumps(initial_sub.model_dump(), indent=2)
        )
        initial_grade = grade_submission(initial_sub, case)
        (trial_dir / "initial_grade.json").write_text(
            json.dumps(initial_grade.model_dump(), indent=2)
        )

        initial_score = initial_grade.total_score
        initial_hf_codes = [f.diagnostic_code for f in initial_grade.hard_failures]
        all_initial_diagnostics = [
            f.diagnostic_code for r in initial_grade.grader_results for f in r.failures
        ]

        # ===================================================================
        # CHECK: If initial submission has 0 hard failures, skip repair call
        # ===================================================================
        if len(initial_hf_codes) == 0:
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
                latency_seconds=init_latency,
                first_call_latency_seconds=init_latency,
                token_usage=init_usage,
                first_call_token_usage=init_usage,
                parsed_successfully=True,
                initial_parsed_successfully=True,
                score=initial_score,
                initial_score=initial_score,
                repaired_score=initial_score,
                score_delta=0.0,
                hard_failure_count=0,
                hard_failure_codes=[],
                initial_hard_failure_count=0,
                initial_hard_failure_codes=[],
                repaired_hard_failure_count=0,
                repaired_hard_failure_codes=[],
                resolved_diagnostics=[],
                persistent_diagnostics=[],
                new_diagnostics=[],
                repair_attempted=False,
                repair_skipped_reason="initial_submission_clean",
                git_commit=get_git_commit(),
            )
            (trial_dir / "metadata.json").write_text(json.dumps(metadata.__dict__, indent=2))
            (trial_dir / "submission.json").write_text(
                json.dumps(initial_sub.model_dump(), indent=2)
            )
            (trial_dir / "grade.json").write_text(json.dumps(initial_grade.model_dump(), indent=2))
            return TrialResult(
                metadata=metadata,
                raw_response=init_raw_text,
                initial_raw_response=init_raw_text,
                initial_submission=initial_sub,
                initial_grade=initial_grade,
                submission=initial_sub,
                grade=initial_grade,
            )

        # ===================================================================
        # CALL 2: Deterministic Feedback Repair Revision
        # ===================================================================
        repair_prompt = build_repair_prompt(case, initial_sub, initial_grade)
        (trial_dir / "repair_prompt.txt").write_text(repair_prompt)

        try:
            completion2 = self.provider.complete(repair_prompt)
            repair_raw_text = completion2.raw_response
            repair_latency = completion2.latency_seconds
            repair_usage = completion2.usage
            repair_provider_error: str | None = None
        except Exception as exc:
            repair_raw_text = ""
            repair_latency = None
            repair_usage = None
            repair_provider_error = str(exc)

        (trial_dir / "repair_raw_response.txt").write_text(repair_raw_text)
        (trial_dir / "raw_response.txt").write_text(repair_raw_text)

        total_latency: float | None = None
        if init_latency is not None or repair_latency is not None:
            total_latency = (init_latency or 0.0) + (repair_latency or 0.0)
        combined_usage = combine_usages(init_usage, repair_usage)

        if repair_provider_error is not None:
            repair_payload = {
                "status": "repair_provider_error",
                "error": repair_provider_error,
            }
            (trial_dir / "repaired_parse_error.json").write_text(
                json.dumps(repair_payload, indent=2)
            )
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
                latency_seconds=total_latency,
                first_call_latency_seconds=init_latency,
                repair_call_latency_seconds=repair_latency,
                token_usage=combined_usage,
                first_call_token_usage=init_usage,
                repair_call_token_usage=repair_usage,
                parsed_successfully=False,
                initial_parsed_successfully=True,
                repaired_parsed_successfully=False,
                initial_score=initial_score,
                repaired_score=None,
                score=None,
                initial_hard_failure_count=len(initial_hf_codes),
                initial_hard_failure_codes=initial_hf_codes,
                repaired_hard_failure_count=len(initial_hf_codes),
                repaired_hard_failure_codes=initial_hf_codes,
                persistent_diagnostics=all_initial_diagnostics,
                repair_attempted=True,
                prompt_version=STRUCTURED_PROMPT_VERSION,
                git_commit=get_git_commit(),
            )
            (trial_dir / "metadata.json").write_text(json.dumps(metadata.__dict__, indent=2))
            return TrialResult(
                metadata=metadata,
                raw_response=repair_raw_text,
                initial_raw_response=init_raw_text,
                initial_submission=initial_sub,
                initial_grade=initial_grade,
                repair_prompt=repair_prompt,
                repair_raw_response=repair_raw_text,
                parse_error=f"Repair provider error: {repair_provider_error}",
            )

        repaired_sub, repair_parse_err = parse_submission_response(repair_raw_text)

        if repaired_sub is None:
            repair_parse_payload = {
                "status": "repair_parse_failure",
                "error_type": classify_parse_error(repair_parse_err),
                "error": repair_parse_err or "Unknown repair parse error",
                "raw_response_preserved": True,
            }
            (trial_dir / "repaired_parse_error.json").write_text(
                json.dumps(repair_parse_payload, indent=2)
            )
            (trial_dir / "parse_error.json").write_text(json.dumps(repair_parse_payload, indent=2))
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
                latency_seconds=total_latency,
                first_call_latency_seconds=init_latency,
                repair_call_latency_seconds=repair_latency,
                token_usage=combined_usage,
                first_call_token_usage=init_usage,
                repair_call_token_usage=repair_usage,
                parsed_successfully=False,
                initial_parsed_successfully=True,
                repaired_parsed_successfully=False,
                initial_score=initial_score,
                repaired_score=None,
                score=None,
                initial_hard_failure_count=len(initial_hf_codes),
                initial_hard_failure_codes=initial_hf_codes,
                repaired_hard_failure_count=len(initial_hf_codes),
                repaired_hard_failure_codes=initial_hf_codes,
                persistent_diagnostics=all_initial_diagnostics,
                repair_attempted=True,
                prompt_version=STRUCTURED_PROMPT_VERSION,
                git_commit=get_git_commit(),
            )
            (trial_dir / "metadata.json").write_text(json.dumps(metadata.__dict__, indent=2))
            return TrialResult(
                metadata=metadata,
                raw_response=repair_raw_text,
                initial_raw_response=init_raw_text,
                initial_submission=initial_sub,
                initial_grade=initial_grade,
                repair_prompt=repair_prompt,
                repair_raw_response=repair_raw_text,
                parse_error=repair_parse_err,
            )

        # Repaired response successfully parsed
        repaired_grade = grade_submission(repaired_sub, case)
        repaired_score = repaired_grade.total_score
        repaired_hf_codes = [f.diagnostic_code for f in repaired_grade.hard_failures]
        all_repaired_diagnostics = [
            f.diagnostic_code
            for g_res in repaired_grade.grader_results
            for f in g_res.failures
        ]

        (trial_dir / "repaired_submission.json").write_text(
            json.dumps(repaired_sub.model_dump(), indent=2)
        )
        (trial_dir / "submission.json").write_text(json.dumps(repaired_sub.model_dump(), indent=2))
        (trial_dir / "repaired_grade.json").write_text(
            json.dumps(repaired_grade.model_dump(), indent=2)
        )
        (trial_dir / "grade.json").write_text(json.dumps(repaired_grade.model_dump(), indent=2))

        set_init = set(all_initial_diagnostics)
        set_rep = set(all_repaired_diagnostics)

        resolved_codes = sorted(list(set_init - set_rep))
        persistent_codes = sorted(list(set_init & set_rep))
        new_codes = sorted(list(set_rep - set_init))
        score_delta = round(repaired_score - initial_score, 2)

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
            latency_seconds=total_latency,
            first_call_latency_seconds=init_latency,
            repair_call_latency_seconds=repair_latency,
            token_usage=combined_usage,
            first_call_token_usage=init_usage,
            repair_call_token_usage=repair_usage,
            parsed_successfully=True,
            initial_parsed_successfully=True,
            repaired_parsed_successfully=True,
            score=repaired_score,
            initial_score=initial_score,
            repaired_score=repaired_score,
            score_delta=score_delta,
            hard_failure_count=len(repaired_hf_codes),
            hard_failure_codes=repaired_hf_codes,
            initial_hard_failure_count=len(initial_hf_codes),
            initial_hard_failure_codes=initial_hf_codes,
            repaired_hard_failure_count=len(repaired_hf_codes),
            repaired_hard_failure_codes=repaired_hf_codes,
            resolved_diagnostics=resolved_codes,
            persistent_diagnostics=persistent_codes,
            new_diagnostics=new_codes,
            repair_attempted=True,
            prompt_version=STRUCTURED_PROMPT_VERSION,
            git_commit=get_git_commit(),
        )

        (trial_dir / "metadata.json").write_text(json.dumps(metadata.__dict__, indent=2))

        return TrialResult(
            metadata=metadata,
            raw_response=repair_raw_text,
            submission=repaired_sub,
            grade=repaired_grade,
            initial_raw_response=init_raw_text,
            initial_submission=initial_sub,
            initial_grade=initial_grade,
            repair_prompt=repair_prompt,
            repair_raw_response=repair_raw_text,
            repaired_submission=repaired_sub,
            repaired_grade=repaired_grade,
        )

    def run_trial(
        self,
        prompt: str,
        case: NorthstarCase,
        config: ProviderConfig,
        run_index: int,
        trial_dir: Path,
    ) -> TrialResult:
        """Route to standard or repair trial based on config mode."""
        if config.mode == "repair":
            return self.run_repair_trial(
                prompt=prompt,
                case=case,
                config=config,
                run_index=run_index,
                trial_dir=trial_dir,
            )
        return self.run_single_pass_trial(
            prompt=prompt,
            case=case,
            config=config,
            run_index=run_index,
            trial_dir=trial_dir,
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

    if config.mode == "repair":
        milestone_prefix = "m3"
    elif config.mode == "structured":
        milestone_prefix = "m2"
    else:
        milestone_prefix = "m1"

    exp_id = (
        f"{milestone_prefix}-{sanitized_mode}-{sanitized_provider}-"
        f"{sanitized_model}{condition_suffix}-{timestamp_slug}"
    )

    exp_dir = output_dir / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build and save initial prompt based on mode
    if config.mode in ("structured", "repair"):
        prompt = build_structured_analyst_prompt(case)
        prompt_version = STRUCTURED_PROMPT_VERSION
    else:
        prompt = build_analyst_prompt(case)
        prompt_version = DIRECT_PROMPT_VERSION
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
        "prompt_version": prompt_version,
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
