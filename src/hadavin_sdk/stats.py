"""Small statistics helpers shared by the eval gate and the K1b replay check."""

from __future__ import annotations

import math


def upper_error_bound(x: int, n: int, confidence: float = 0.95) -> float | None:
    """Exact one-sided Clopper-Pearson upper bound on a failure rate after x failures in n items.

    The p at which P(X <= x | n, p) = 1 - confidence, found by bisection (the CDF falls as p rises).
    """
    if n == 0:
        return None
    if not 0 <= x <= n:
        raise ValueError(f"failures {x} outside 0..{n}")
    if x == n:
        return 1.0
    alpha = 1 - confidence

    # In log space: comb(n, i) overflows a float above n of about 1030. Computed once, not per bisection step.
    log_combs = [math.log(math.comb(n, i)) for i in range(x + 1)]

    def cdf(p: float) -> float:
        return sum(
            math.exp(lc + i * math.log(p) + (n - i) * math.log1p(-p))
            for i, lc in enumerate(log_combs)
        )

    lo, hi = 0.0, 1.0
    for _ in range(60):  # 2**-60: far below any reported precision
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) > alpha else (lo, mid)
    return hi
