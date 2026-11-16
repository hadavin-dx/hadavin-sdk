"""Exact (Clopper-Pearson) binomial bounds, both one-sided and two-sided (two-sided-bound asks two-sided 95%; the kit's verdict thresholds use the one-sided upper bound, so BOTH are reported).
Percentages are rounded UP (an upper bound printed as 2.5% when it is 2.55% understates it), lower bounds are rounded down."""

from __future__ import annotations

import math


def _cdf(x: int, n: int, p: float) -> float:
    """P(X <= x) for X ~ Binomial(n, p), in log space."""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if x >= n else 0.0
    return sum(
        math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * math.log(p) + (n - i) * math.log1p(-p))
        for i in range(x + 1)
    )


def upper(x: int, n: int, alpha: float = 0.05) -> float:
    """The p at which P(X <= x) = alpha (one-sided upper bound at confidence 1 - alpha)."""
    if n <= 0:
        raise ValueError("n must be positive")
    if x >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _cdf(x, n, mid) > alpha else (lo, mid)
    return hi


def lower(x: int, n: int, alpha: float = 0.05) -> float:
    if x <= 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if 1.0 - _cdf(x - 1, n, mid) > alpha else (mid, hi)
    return lo


def two_sided(x: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    a = 1.0 - confidence
    return lower(x, n, a / 2), upper(x, n, a / 2)


def pct_up(v: float, digits: int = 1) -> str:
    f = 10**digits
    return f"{math.ceil(v * 100 * f - 1e-9) / f:.{digits}f}%"


def pct_down(v: float, digits: int = 1) -> str:
    f = 10**digits
    return f"{math.floor(v * 100 * f + 1e-9) / f:.{digits}f}%"
