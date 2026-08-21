from __future__ import annotations

from ib_eval.provenance import validate_provenance_records
from ib_eval.schemas import ProvenanceRecord


def _make_record(**kwargs: object) -> ProvenanceRecord:
    defaults: dict[str, object] = {
        "metric": "revenue_growth",
        "period": "2026E",
        "value": 0.08,
        "source": "management_guidance.md",
        "classification": "analyst_assumption",
        "confidence": 0.85,
        "note": "",
    }
    defaults.update(kwargs)
    return ProvenanceRecord.model_validate(defaults)


def test_valid_provenance_no_issues() -> None:
    """Clean provenance records produce no issues."""
    rec = _make_record(classification="analyst_assumption")
    issues = validate_provenance_records([rec])
    assert issues == []


def test_direct_classification_for_growth_is_flagged() -> None:
    """revenue_growth/2026E classified as direct triggers an issue."""
    rec = _make_record(classification="direct")
    issues = validate_provenance_records([rec])
    assert len(issues) == 1
    assert "analyst assumption" in issues[0].lower()


def test_derived_classification_ok() -> None:
    """'derived' classification for growth is acceptable."""
    rec = _make_record(classification="derived")
    issues = validate_provenance_records([rec])
    assert issues == []


def test_unrelated_metric_direct_is_ok() -> None:
    """Direct classification for non-growth metrics is fine."""
    rec = _make_record(
        metric="ebitda_margin",
        period="2026E",
        classification="direct",
    )
    issues = validate_provenance_records([rec])
    assert issues == []


def test_zero_confidence_direct_flagged() -> None:
    """confidence=0 + direct is suspicious."""
    rec = _make_record(
        metric="revenue",
        period="2026E",
        classification="direct",
        confidence=0.0,
    )
    issues = validate_provenance_records([rec])
    assert any("confidence" in i for i in issues)


def test_classification_enum_values() -> None:
    """All three classification values are valid."""
    for cls in ["direct", "derived", "analyst_assumption"]:
        ProvenanceRecord.model_validate(
            {
                "metric": "x",
                "period": "2026E",
                "value": 1.0,
                "source": "income_statement.md",
                "classification": cls,
            }
        )


def test_invalid_classification_raises() -> None:
    """Unknown classification raises ValidationError."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ProvenanceRecord.model_validate(
            {
                "metric": "x",
                "period": "2026E",
                "value": 1.0,
                "source": "x.md",
                "classification": "TOTALLY_WRONG",
            }
        )


def test_confidence_out_of_range_raises() -> None:
    """confidence > 1.0 raises ValidationError."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ProvenanceRecord.model_validate(
            {
                "metric": "x",
                "period": "2026E",
                "value": 1.0,
                "source": "x.md",
                "classification": "direct",
                "confidence": 1.5,
            }
        )
