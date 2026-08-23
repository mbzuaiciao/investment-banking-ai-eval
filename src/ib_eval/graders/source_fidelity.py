"""Grader 1 — Source Fidelity.

Checks that provenance records are correctly classified and that no
fabricated claims are present.

Hard failure codes:
  SF_GUIDANCE_FABRICATED   : candidate claims management stated exact %-growth
  SF_MISSING_PROVENANCE    : no provenance records at all
  SF_DIRECT_ANALYST_ASSUMPTION : analyst_assumption flagged as direct
"""

from __future__ import annotations

from ib_eval.case import GraderConfig
from ib_eval.provenance import validate_provenance_records
from ib_eval.schemas import (
    ErrorType,
    GraderFailure,
    GraderResult,
    ProvenanceClassification,
    Severity,
    Submission,
)

GRADER_NAME = "source_fidelity"


def grade(submission: Submission, config: GraderConfig) -> GraderResult:
    max_points = config.weight
    failures: list[GraderFailure] = []
    warnings: list[str] = []
    info: list[str] = []

    # 1. Check that provenance records exist
    if not submission.provenance:
        failures.append(
            GraderFailure(
                error_type=ErrorType.PROVENANCE,
                severity=Severity.CRITICAL,
                metric="provenance_records",
                expected="at least 1 record",
                observed=0,
                message="No provenance records provided.",
                diagnostic_code="SF_MISSING_PROVENANCE",
            )
        )

    # 2. Validate provenance records
    issues = validate_provenance_records(submission.provenance)
    for issue in issues:
        failures.append(
            GraderFailure(
                error_type=ErrorType.PROVENANCE,
                severity=Severity.CRITICAL,
                metric="revenue_growth/2026E",
                expected="analyst_assumption or derived",
                observed="direct",
                message=issue,
                diagnostic_code="SF_GUIDANCE_FABRICATED",
            )
        )

    # 3. Check for any notes field claiming management guided to an exact number
    notes_str = str(submission.notes).lower()
    default_fabrication_phrases = [
        "management guided to 8%",
        "management stated 8%",
        "management explicitly guided 8",
        "management provided 8%",
    ]
    fabrication_phrases = config.params.get("fabrication_phrases", default_fabrication_phrases)
    for phrase in fabrication_phrases:
        if phrase.lower() in notes_str:
            failures.append(
                GraderFailure(
                    error_type=ErrorType.PROVENANCE,
                    severity=Severity.CRITICAL,
                    metric="revenue_growth/2026E",
                    expected="qualitative or range guidance only",
                    observed=phrase,
                    message=(
                        f"Submission notes contain fabricated claim: '{phrase}'. "
                        "Management did not provide a single exact point commitment."
                    ),
                    diagnostic_code="SF_GUIDANCE_FABRICATED",
                )
            )

    # 4. Check for note in provenance that explicitly calls out the Q2/H1 distinction
    has_quarterly_note = any(
        "quarterly" in r.note.lower() or "h1" in r.note.lower() or "ytd" in r.note.lower()
        for r in submission.provenance
        if r.metric in ("revenue", "revenue_h1", "revenue_q2")
    )
    if not has_quarterly_note:
        info.append(
            "No provenance note found distinguishing Q2 vs H1 revenue. "
            "Consider adding a note to document source selection."
        )

    # 5. Check classification coherence: direct must reference a known source
    default_known_sources = {
        "management_guidance.md",
        "quarterly_report.md",
        "income_statement.md",
        "capital_structure.md",
    }
    known_sources = set(config.params.get("known_sources", default_known_sources))
    for rec in submission.provenance:
        if (
            rec.classification == ProvenanceClassification.DIRECT
            and rec.source not in known_sources
        ):
            warnings.append(
                f"Provenance record {rec.metric}/{rec.period} classified 'direct' "
                f"but source '{rec.source}' is not a recognized source document."
            )

    # Scoring: deduct proportionally for each failure
    n_critical = sum(1 for f in failures if f.severity == Severity.CRITICAL)
    n_warnings = len(warnings)
    deduction = n_critical * (max_points * 0.5) + n_warnings * (max_points * 0.1)
    points = max(0.0, max_points - deduction)
    score = points / max_points if max_points > 0 else 0.0

    return GraderResult(
        grader=GRADER_NAME,
        score=score,
        max_points=max_points,
        points_earned=points,
        passed=len(failures) == 0,
        failures=failures,
        warnings=warnings,
        info=info,
    )
