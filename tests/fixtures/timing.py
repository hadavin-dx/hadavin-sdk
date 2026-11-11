"""One rule for the linear-time tests (a test file never imports another test file).

THE RULE. A cost is "linear enough" when growing the input by a factor `g` grows the time of one call by at most
`PER_SIZE * g`. The limit is a RATIO of the two sizes, so it has no fixed seconds figure that a fast or a slow machine
could miss: a linear function grows by about `g`, an "n log n" one by a little more than `g`, a quadratic one by about
`g * g`, and with `g` of 4 or more the quadratic one is far from `PER_SIZE * g`. (This is the doubling-ratio test of
Sedgewick and Wayne, "Algorithms", 4th edition, section 1.4: the ratio of the times at two sizes estimates the exponent.)

THE MEASUREMENT is made here, not by the caller (`seconds_per_call`), with the standard library's `timeit.Timer` and
by its two rules (both read in the `timeit` module of Python 3.13 on 2026-11-11):
  * a call is repeated in a batch until the batch takes at least `MIN_BATCH_S` (what `Timer.autorange` does, there with
    0.2 s), so a small input is never timed below what the clock and the machine's noise can resolve; `Timer.timeit`
    also keeps the garbage collector off while the clock runs;
  * the batch is run `REPEATS` times and the FASTEST counts, and it is the fastest batch that must reach `MIN_BATCH_S`,
    so a pause of the machine during one batch cannot shorten the batches (the note on `Timer.repeat`: "the lowest value gives a
    lower bound for how fast your machine can run the given code snippet; higher values ... are typically not caused
    by variability in Python's speed, but by other processes interfering with your timing accuracy").

There is NO floor on the small run. An earlier version raised a small run to 4 ms; a fast function was then compared
with a fixed seconds figure and a quadratic cost under that figure was never flagged. A time that is zero or negative
is refused loudly (`ValueError`): a ratio to zero says nothing, and saying "linear" would be a guess."""

from __future__ import annotations

import functools
import math
import time
import timeit
from collections.abc import Callable

PER_SIZE = 3.0
MIN_BATCH_S, REPEATS, MAX_CALLS = 0.02, 3, 1_000_000


def time_limit(t_small: float, small: int, big: int) -> float:
    """The most one call on the big input may take, given the seconds of one call on the small input."""
    if not (math.isfinite(t_small) and t_small > 0):
        raise ValueError(f"the small run took {t_small!r} s: not a time a ratio can be taken of")
    if not 0 < small < big:
        raise ValueError(f"the sizes must be 0 < small < big, got {small} and {big}")
    return PER_SIZE * (big / small) * t_small


def grows_faster_than_size(t_small: float, t_big: float, small: int, big: int) -> bool:
    return t_big > time_limit(t_small, small, big)


def seconds_per_call(
    fn: Callable[[str], object], text: str, clock: Callable[[], float] = time.perf_counter
) -> float:
    """Seconds of ONE `fn(text)`: the fastest of `REPEATS` batches, where even the fastest batch was long enough."""
    batch = timeit.Timer(
        functools.partial(fn, text), timer=clock
    ).timeit  # seconds of N calls, collector off
    calls = 1
    while True:
        best = min(batch(calls) for _ in range(REPEATS))
        if best >= MIN_BATCH_S:
            return best / calls
        if calls >= MAX_CALLS:
            raise ValueError(
                f"{calls} calls took {best!r} s, under {MIN_BATCH_S} s: too fast to time; use a bigger input"
            )
        # aim a fifth over the batch length (a clock that showed no time at all: ten times); at least double
        wanted = math.ceil(calls * 1.2 * MIN_BATCH_S / best) if best > 0 else calls * 10
        calls = min(MAX_CALLS, max(calls * 2, wanted))


def is_superlinear(
    fn: Callable[[str], object],
    unit: str,
    small: int,
    big: int,
    clock: Callable[[], float] = time.perf_counter,
) -> bool:
    """True when `fn` costs more than "linear enough". `fn(text)` is the work itself (it is timed here, its result is
    not used); the texts are `unit` repeated to `small` and `big` characters."""
    t_small, t_big = (
        seconds_per_call(fn, (unit * (n // len(unit) + 1))[:n], clock) for n in (small, big)
    )
    return grows_faster_than_size(t_small, t_big, small, big)
