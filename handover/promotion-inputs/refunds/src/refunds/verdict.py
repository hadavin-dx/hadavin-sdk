"""Scorecard verdict and intervals (eval-contract.md, interval rule and pass^k rule).

The kit caps the verdict at amber for any scripted run: with a scripted model the upper bound measures plumbing (gate vs gold agreement), not
model accuracy. pass^k (pass^k rule): a scripted, deterministic run repeated k times gives the same result every time, so pass^k = pass^1 for every k;
the demo reports k = 1 and says so (a live-model run would need k >= 3 before any consistency claim).
"""

from __future__ import annotations

from math import exp, expm1, lgamma, log, log1p

GREEN_MAX = 0.10
AMBER_MAX = 0.15
K_ONE_NOTE = "k=1: a scripted deterministic run repeats identically, so pass^k equals pass^1; no consistency claim is made"


def upper_bound_zero_wrong(n_answered: int, confidence: float = 0.95) -> float:
    """One-sided exact binomial upper bound when 0 of n answers are wrong: 1 - (1 - confidence) ** (1 / n)."""
    if not isinstance(n_answered, int) or isinstance(n_answered, bool) or n_answered < 1 or not 0 < confidence < 1:
        raise ValueError("need n_answered >= 1 and 0 < confidence < 1")
    return -expm1(log1p(-confidence) / n_answered)  # = 1 - (1 - confidence) ** (1 / n), accurate for a large n


def _pmf_sum(lo: int, hi: int, n: int, p: float) -> float:
    """P(lo <= X <= hi) for X ~ Binomial(n, p), summed in LOG space: `comb(n, i) * p**i` overflows a float above n of about 1030, log-gamma does not
    (same approach as hadavin_sdk.stats). Identical to the plain float sum within rounding for small n (tests/test_review12.py property test)."""
    if p <= 0.0:
        return 1.0 if lo <= 0 <= hi else 0.0
    if p >= 1.0:
        return 1.0 if lo <= n <= hi else 0.0
    lp, lq, ln = log(p), log1p(-p), lgamma(n + 1)
    logs = [ln - lgamma(i + 1) - lgamma(n - i + 1) + i * lp + (n - i) * lq for i in range(lo, hi + 1)]
    m = max(logs)
    return min(1.0, exp(m) * sum(exp(v - m) for v in logs))


def _tail_le(x: int, n: int, p: float) -> float:
    return _pmf_sum(0, x, n, p)


def _tail_ge(x: int, n: int, p: float) -> float:
    return _pmf_sum(x, n, n, p)


def clopper_pearson(x: int, n: int, confidence: float = 0.95, two_sided: bool = True) -> tuple[float, float]:
    """Exact Clopper-Pearson interval for x events of n (interval rule). two_sided=True splits alpha in two; False returns (0, one-sided upper).
    Cost: 2 bisections x 200 steps x O(n) log-gamma terms, with NO timeout (n = 50,000 takes about 15 s); the caller bounds n."""
    if (
        any(isinstance(v, bool) or not isinstance(v, int) for v in (x, n))
        or not (0 <= x <= n)
        or n <= 0
        or not 0 < confidence < 1
    ):
        raise ValueError("need 0 <= x <= n and n > 0")
    alpha = 1 - confidence
    tail = alpha / 2 if two_sided else alpha

    def bisect(f, increasing):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if (f(mid) < tail) == increasing:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    upper = 1.0 if x == n else bisect(lambda p: _tail_le(x, n, p), increasing=False)  # P(X <= x | p) falls as p rises
    lower = 0.0 if x == 0 or not two_sided else bisect(lambda p: _tail_ge(x, n, p), increasing=True)  # P(X >= x | p) rises with p
    return (lower, upper)


MODES = frozenset({"scripted", "live"})  # closed set: a typo must never reach the green branch


def verdict(upper: float | None, mode: str, hard_zero_hit: bool = False) -> str:
    if upper is not None and (
        isinstance(upper, bool) or not isinstance(upper, (int, float)) or not 0.0 <= upper <= 1.0
    ):  # NaN fails the comparison too
        raise ValueError(f"upper must be None or a number in [0, 1], got {upper!r}")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}, got {mode!r}")
    if hard_zero_hit:
        return "aborted"
    if upper is None:
        return "not_demonstrated"
    v = "green" if upper <= GREEN_MAX else "amber" if upper <= AMBER_MAX else "not_demonstrated"
    if mode == "scripted" and v == "green":
        v = "amber"
    return v
