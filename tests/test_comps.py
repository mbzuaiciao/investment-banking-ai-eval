"""Tests for trading comps functions."""

from __future__ import annotations

from ib_eval.comps import (
    compute_comps_enterprise_value,
    compute_comps_equity_value,
    compute_comps_range,
    compute_comps_share_price,
    compute_median,
    filter_valid_peers,
)


def test_filter_valid_peers_excludes_none() -> None:
    """None values (N/M) are excluded from valid peers."""
    multiples = [7.9, 8.5, 9.2, 7.3, None]
    valid = filter_valid_peers(multiples)
    assert valid == [7.9, 8.5, 9.2, 7.3]
    assert None not in valid


def test_filter_valid_peers_all_nm() -> None:
    """All N/M → empty list."""
    assert filter_valid_peers([None, None]) == []


def test_filter_valid_peers_no_nm() -> None:
    """No N/M → full list unchanged."""
    assert filter_valid_peers([7.9, 8.5]) == [7.9, 8.5]


def test_compute_median_northstar() -> None:
    """Median NTM EV/EBITDA for Northstar v1 (excluding Evergreen) = 8.2x."""
    valid = filter_valid_peers([7.9, 8.5, 9.2, 7.3, None])
    # sorted: [7.3, 7.9, 8.5, 9.2] → median of 4 = (7.9+8.5)/2 = 8.2
    median = compute_median(valid)
    assert median is not None
    assert abs(median - 8.2) < 1e-9


def test_compute_median_odd_count() -> None:
    """Median of odd-count list is middle value."""
    median = compute_median([7.3, 7.9, 8.5])
    assert median is not None
    assert abs(median - 7.9) < 1e-9


def test_compute_median_even_count() -> None:
    """Median of even-count list is average of two middle values."""
    median = compute_median([7.0, 8.0, 9.0, 10.0])
    assert median is not None
    assert abs(median - 8.5) < 1e-9


def test_compute_median_empty() -> None:
    """Empty list → None."""
    assert compute_median([]) is None


def test_compute_median_nm_included_would_shift() -> None:
    """Demonstrates that coercing N/M to 0 shifts the median incorrectly."""
    # Without Evergreen (None): [7.3, 7.9, 8.5, 9.2] → 8.2
    # With Evergreen as 0: [0.0, 7.3, 7.9, 8.5, 9.2] → 7.9 (wrong)
    correct = compute_median(filter_valid_peers([7.9, 8.5, 9.2, 7.3, None]))
    with_zero = compute_median(filter_valid_peers([7.9, 8.5, 9.2, 7.3, 0.0]))
    assert correct is not None
    assert with_zero is not None
    assert abs(correct - 8.2) < 1e-9
    assert abs(with_zero - 7.9) < 1e-9
    assert correct != with_zero


def test_comps_ev() -> None:
    """Comps EV = multiple × EBITDA."""
    ev = compute_comps_enterprise_value(applied_multiple=8.2, applied_ebitda=183.6)
    assert abs(ev - 1505.52) < 0.01


def test_comps_equity() -> None:
    """Comps equity = EV - net_debt."""
    eq = compute_comps_equity_value(enterprise_value=1505.52, net_debt=325.0)
    assert abs(eq - 1180.52) < 0.01


def test_comps_share_price() -> None:
    """Comps share price = equity / shares."""
    price = compute_comps_share_price(equity_value=1180.52, diluted_shares=60.0)
    assert abs(price - 19.6753) < 0.001


def test_comps_range() -> None:
    """Comps range uses provided low/high multiples."""
    low_price, high_price = compute_comps_range(
        multiples=[7.9, 8.5, 9.2, 7.3, None],
        applied_ebitda=183.6,
        net_debt=325.0,
        diluted_shares=60.0,
        low_multiple=7.9,
        high_multiple=8.5,
    )
    # Low: 7.9 × 183.6 = 1450.44; (1450.44 - 325) / 60 = 18.757
    expected_low = (7.9 * 183.6 - 325.0) / 60.0
    expected_high = (8.5 * 183.6 - 325.0) / 60.0
    assert abs(low_price - expected_low) < 0.01
    assert abs(high_price - expected_high) < 0.01


def test_comps_share_price_zero_shares() -> None:
    """Should raise ValueError for zero shares."""
    import pytest

    with pytest.raises(ValueError):
        compute_comps_share_price(equity_value=1000.0, diluted_shares=0.0)
