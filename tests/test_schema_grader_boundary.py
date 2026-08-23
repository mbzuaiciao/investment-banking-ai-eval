"""Regression tests for schema vs. grader abstraction boundary.

Design Principle:
"Parsing validates representability; graders validate financial correctness."
"""

from __future__ import annotations

import json
from pathlib import Path

from ib_eval.case import load_case
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission


def test_wacc_decimal_weights_parse_and_grade() -> None:
    """1. Correct decimal WACC weights (0.95 / 0.05) parse and pass grading."""
    case = load_case(Path("cases/meridian-v1"))
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    data = json.loads(gold_path.read_text())

    data["wacc_inputs"]["equity_weight"] = 0.95
    data["wacc_inputs"]["debt_weight"] = 0.05

    sub = Submission.model_validate(data)
    assert sub.wacc_inputs.equity_weight == 0.95
    assert sub.wacc_inputs.debt_weight == 0.05

    report = grade_submission(sub, case)
    wacc_res = next(r for r in report.grader_results if r.grader == "wacc")
    assert wacc_res.passed
    assert not any(f.diagnostic_code == "WACC_WEIGHTS_ERROR" for f in wacc_res.failures)


def test_wacc_percentage_scale_weights_parse() -> None:
    """2. Percentage-scale WACC weights (95.0 / 5.0) parse successfully."""
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    data = json.loads(gold_path.read_text())

    data["wacc_inputs"]["equity_weight"] = 95.0
    data["wacc_inputs"]["debt_weight"] = 5.0

    sub = Submission.model_validate(data)
    assert sub.wacc_inputs.equity_weight == 95.0
    assert sub.wacc_inputs.debt_weight == 5.0


def test_wacc_percentage_scale_preserved_not_normalized() -> None:
    """3. 95/5 weights are preserved exactly without silent schema normalization."""
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    data = json.loads(gold_path.read_text())

    data["wacc_inputs"]["equity_weight"] = 95.0
    data["wacc_inputs"]["debt_weight"] = 5.0

    sub = Submission.model_validate(data)
    dumped = sub.model_dump()
    assert dumped["wacc_inputs"]["equity_weight"] == 95.0
    assert dumped["wacc_inputs"]["debt_weight"] == 5.0


def test_wacc_percentage_scale_fails_deterministic_grading() -> None:
    """4. 95/5 weights fail deterministic WACC grading and trigger WACC_WEIGHTS_ERROR."""
    case = load_case(Path("cases/meridian-v1"))
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    data = json.loads(gold_path.read_text())

    data["wacc_inputs"]["equity_weight"] = 95.0
    data["wacc_inputs"]["debt_weight"] = 5.0

    sub = Submission.model_validate(data)
    report = grade_submission(sub, case)

    wacc_res = next(r for r in report.grader_results if r.grader == "wacc")
    assert not wacc_res.passed
    assert any(f.diagnostic_code == "WACC_WEIGHTS_ERROR" for f in wacc_res.failures)


def test_inconsistent_equity_bridge_parses_successfully() -> None:
    """5. Internally inconsistent equity bridge (EV - net_debt != equity_value) parses."""
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    data = json.loads(gold_path.read_text())

    # Inconsistent: EV=2499.23, minus_net_debt=200.0, but equity_value=2699.23 instead of 2299.23
    data["equity_bridge"]["enterprise_value"] = 2499.23
    data["equity_bridge"]["minus_net_debt"] = 200.0
    data["equity_bridge"]["equity_value"] = 2699.23

    sub = Submission.model_validate(data)
    assert sub.equity_bridge.enterprise_value == 2499.23
    assert sub.equity_bridge.minus_net_debt == 200.0
    assert sub.equity_bridge.equity_value == 2699.23


def test_inconsistent_equity_bridge_fails_deterministic_grading() -> None:
    """6. Inconsistent equity bridge fails deterministic grading and triggers diagnostic."""
    case = load_case(Path("cases/meridian-v1"))
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    data = json.loads(gold_path.read_text())

    # EV=2499.23, minus_net_debt=200.0, but equity_value=2699.23 instead of 2299.23
    data["equity_bridge"]["enterprise_value"] = 2499.23
    data["equity_bridge"]["minus_net_debt"] = 200.0
    data["equity_bridge"]["equity_value"] = 2699.23

    sub = Submission.model_validate(data)
    report = grade_submission(sub, case)

    eq_res = next(r for r in report.grader_results if r.grader == "equity_bridge")
    assert not eq_res.passed
    assert any(
        f.diagnostic_code in ("EQ_BRIDGE_ARITHMETIC", "EQ_BRIDGE_NET_CASH_REVERSED")
        for f in eq_res.failures
    )


def test_inconsistent_share_price_parses_and_fails_grading() -> None:
    """Internally inconsistent share price parses and fails deterministic grading."""
    case = load_case(Path("cases/meridian-v1"))
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    data = json.loads(gold_path.read_text())

    # Correct equity = 1575.92, diluted_shares = 88.0 -> price should be ~17.91, but submitted 25.00
    data["equity_bridge"]["implied_share_price"] = 25.00

    sub = Submission.model_validate(data)
    assert sub.equity_bridge.implied_share_price == 25.00

    report = grade_submission(sub, case)
    eq_res = next(r for r in report.grader_results if r.grader == "equity_bridge")
    assert not eq_res.passed
    assert any(f.diagnostic_code == "EQ_BRIDGE_SHARE_PRICE" for f in eq_res.failures)


def test_northstar_gold_score_remains_perfect() -> None:
    """7. Northstar gold submission scores 100/100 with 0 hard failures."""
    case = load_case(Path("cases/northstar-v1"))
    gold_path = Path("examples/gold_submission/submission.json")
    sub = Submission.model_validate_json(gold_path.read_text())
    report = grade_submission(sub, case)

    assert report.total_score == 100.0
    assert report.grade == "A+"
    assert len(report.hard_failures) == 0


def test_meridian_gold_score_remains_perfect() -> None:
    """8. Meridian gold submission scores 100/100 with 0 hard failures."""
    case = load_case(Path("cases/meridian-v1"))
    gold_path = Path("examples/meridian_gold_submission/submission.json")
    sub = Submission.model_validate_json(gold_path.read_text())
    report = grade_submission(sub, case)

    assert report.total_score == 100.0
    assert report.grade == "A+"
    assert len(report.hard_failures) == 0


def test_corrupted_fixtures_parse_and_grade_expected_diagnostics() -> None:
    """9. Existing corrupted fixtures still parse and grade as expected."""
    meridian_case = load_case(Path("cases/meridian-v1"))
    meridian_fixtures = [
        ("m01_arr_revenue_confusion", "REV_ARR_CONFUSION"),
        ("m02_deferred_rev_reversed", "WC_DEFERRED_REV_REVERSED"),
        ("m04_net_cash_reversed", "EQ_BRIDGE_NET_CASH_REVERSED"),
        ("m05_sbc_ebitda_inconsistency", "SBC_EBITDA_INCONSISTENCY"),
        ("m06_basic_shares_used", "SHARES_BASIC_USED"),
        ("m07_midyear_convention_error", "DCF_MIDYEAR_CONVENTION_ERROR"),
        ("m08_nm_fcf_coerced_zero", "COMPS_NM_FCF_COERCED_ZERO"),
        ("m10_pretax_wacc", "WACC_PRETAX_DEBT"),
    ]

    for dir_name, exp_diag in meridian_fixtures:
        fixture_path = Path("examples/meridian_corrupted") / dir_name / "submission.json"
        sub = Submission.model_validate_json(fixture_path.read_text())
        report = grade_submission(sub, meridian_case)
        codes = [f.diagnostic_code for f in report.hard_failures]
        assert exp_diag in codes, f"Fixture {dir_name} expected {exp_diag}, got {codes}"


def test_serialization_roundtrip_preserves_bad_financial_inputs() -> None:
    """10. Serialization and deserialization preserves bad financial inputs exactly."""
    bad_data = {
        "wacc_inputs": {
            "risk_free_rate": 4.25,
            "equity_risk_premium": 5.5,
            "beta": 1.25,
            "pre_tax_cost_of_debt": 5.5,
            "tax_rate": 25.0,
            "equity_weight": 95.0,
            "debt_weight": 5.0,
        },
        "capital_structure": {
            "gross_debt": 80.0,
            "cash": 280.0,
            "net_debt": 500.0,  # Deliberately inconsistent (80 - 280 != 500)
            "diluted_shares": 88.0,
            "current_share_price": 32.0,
            "convertible_face_value": 0.0,
            "convertible_treatment": "debt",
        },
        "equity_bridge": {
            "enterprise_value": 1500.0,
            "minus_net_debt": -200.0,
            "equity_value": 9999.0,  # Deliberately inconsistent
            "diluted_shares": 88.0,
            "implied_share_price": 999.0,  # Deliberately inconsistent
        },
    }

    gold_path = Path("examples/meridian_gold_submission/submission.json")
    full_data = json.loads(gold_path.read_text())
    full_data["wacc_inputs"] = bad_data["wacc_inputs"]
    full_data["capital_structure"] = bad_data["capital_structure"]
    full_data["equity_bridge"] = bad_data["equity_bridge"]

    sub = Submission.model_validate(full_data)
    json_str = sub.model_dump_json()
    sub_reloaded = Submission.model_validate_json(json_str)

    assert sub_reloaded.wacc_inputs.equity_weight == 95.0
    assert sub_reloaded.wacc_inputs.debt_weight == 5.0
    assert sub_reloaded.capital_structure.net_debt == 500.0
    assert sub_reloaded.equity_bridge.equity_value == 9999.0
    assert sub_reloaded.equity_bridge.implied_share_price == 999.0
