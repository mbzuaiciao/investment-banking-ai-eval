"""Trading comps computation engine for IB-Eval."""

from __future__ import annotations

import statistics


def filter_valid_peers(
    multiples: list[float | None],
) -> list[float]:
    """Return only non-None (non-N/M) peer multiples.

    N/M entries MUST be represented as None, not coerced to 0.
    Callers are responsible for never passing 0 in place of None.
    """
    return [m for m in multiples if m is not None]


def compute_median(values: list[float]) -> float | None:
    """Return the median of a non-empty list, or None if the list is empty."""
    if not values:
        return None
    return statistics.median(values)


def compute_comps_enterprise_value(
    applied_multiple: float,
    applied_ebitda: float,
) -> float:
    """EV = multiple × EBITDA."""
    return applied_multiple * applied_ebitda


def compute_comps_equity_value(enterprise_value: float, net_debt: float) -> float:
    """Equity value = EV − net debt."""
    return enterprise_value - net_debt


def compute_comps_share_price(equity_value: float, diluted_shares: float) -> float:
    """Share price = equity value / diluted shares."""
    if diluted_shares <= 0:
        msg = "diluted_shares must be positive"
        raise ValueError(msg)
    return equity_value / diluted_shares


def compute_comps_range(
    multiples: list[float | None],
    applied_ebitda: float,
    net_debt: float,
    diluted_shares: float,
    low_multiple: float,
    high_multiple: float,
) -> tuple[float, float]:
    """Return the (low, high) implied share price range.

    Uses the provided low/high multiples rather than the peer min/max
    so the range can reflect a selected reference band.
    """
    ev_low = compute_comps_enterprise_value(low_multiple, applied_ebitda)
    ev_high = compute_comps_enterprise_value(high_multiple, applied_ebitda)
    eq_low = compute_comps_equity_value(ev_low, net_debt)
    eq_high = compute_comps_equity_value(ev_high, net_debt)
    price_low = compute_comps_share_price(eq_low, diluted_shares)
    price_high = compute_comps_share_price(eq_high, diluted_shares)
    return price_low, price_high
