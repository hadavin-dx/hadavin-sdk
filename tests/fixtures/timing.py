"""One rule for the linear-time tests (a test file never imports another test file).

A cost is "linear enough" when growing the input by a factor `g` grows the time by at most `PER_SIZE * g`. The limit is a
RATIO of the two sizes, so it has no fixed seconds figure that a fast or a slow machine could miss: a linear function
grows by about `g`, a quadratic one by about `g * g`, and with `g` of 4 or more the two are far apart from `PER_SIZE * g`.
Only the small run is floored (`MIN_SMALL_S`): a small input can time at zero on a fast machine, and a ratio to zero says
nothing."""

from __future__ import annotations

from collections.abc import Callable

PER_SIZE, MIN_SMALL_S = 3.0, 0.004


def time_limit(t_small: float, small: int, big: int) -> float:
    """The most the big run may take."""
    return PER_SIZE * (big / small) * max(t_small, MIN_SMALL_S)


def grows_faster_than_size(t_small: float, t_big: float, small: int, big: int) -> bool:
    return t_big > time_limit(t_small, small, big)


def is_superlinear(measure: Callable[[str], float], unit: str, small: int, big: int) -> bool:
    """`measure(text)` returns seconds; the texts are `unit` repeated to `small` and `big` characters."""
    t_small, t_big = (measure((unit * (n // len(unit) + 1))[:n]) for n in (small, big))
    return grows_faster_than_size(t_small, t_big, small, big)
