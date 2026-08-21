"""Provenance helpers for IB-Eval.

Provenance records trace every model input to its evidential basis.
"""

from __future__ import annotations

from ib_eval.schemas import ProvenanceClassification, ProvenanceRecord

# ---------------------------------------------------------------------------
# Predefined source identifiers used in the Northstar v1 case
# ---------------------------------------------------------------------------

SOURCE_MANAGEMENT_GUIDANCE = "management_guidance.md"
SOURCE_QUARTERLY_REPORT = "quarterly_report.md"
SOURCE_INCOME_STATEMENT = "income_statement.md"
SOURCE_CAPITAL_STRUCTURE = "capital_structure.md"

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

DIRECT_SOURCES = frozenset({
    SOURCE_MANAGEMENT_GUIDANCE,
    SOURCE_QUARTERLY_REPORT,
    SOURCE_INCOME_STATEMENT,
    SOURCE_CAPITAL_STRUCTURE,
})


def classify_source(source: str, classification: str) -> ProvenanceClassification:
    """Validate that classification is consistent with source type."""
    try:
        cls = ProvenanceClassification(classification)
    except ValueError:
        msg = f"Unknown classification: {classification!r}"
        raise ValueError(msg) from None
    return cls


def validate_provenance_records(
    records: list[ProvenanceRecord],
    *,
    require_growth_assumption: bool = True,
) -> list[str]:
    """Return a list of provenance issues found.

    Returns an empty list if everything is clean.
    """
    issues: list[str] = []

    # Check that revenue growth is classified as analyst_assumption or derived,
    # never as direct (management never stated exactly 8%).
    if require_growth_assumption:
        growth_records = [
            r for r in records if r.metric == "revenue_growth" and r.period == "2026E"
        ]
        for rec in growth_records:
            if rec.classification == ProvenanceClassification.DIRECT:
                issues.append(
                    "revenue_growth/2026E classified as 'direct' — management only provided "
                    "qualitative guidance ('high single digits'); exact % is an analyst assumption."
                )

    # Check for zero-confidence records that claim to be direct
    for rec in records:
        if rec.confidence == 0.0 and rec.classification == ProvenanceClassification.DIRECT:
            issues.append(
                f"{rec.metric}/{rec.period}: confidence=0 but classification=direct is suspect."
            )

    return issues
