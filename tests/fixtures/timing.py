"""One rule for the linear-time tests (a test file never imports another test file).

A cost is "linear enough" when growing the input by a factor `g` grows the time by at most `PER_SIZE * g`. The limit is a
RATIO of the two sizes, so it has no fixed seconds figure that a fast or a slow machine could miss: a linear function
grows by about `g`, a quadratic one by about `g * g`, and with `g` of 4 or more the two are far apart from `PER_SIZE * g`.
Only the small run is floored (`MIN_SMALL_S`): a small input can time at zero on a fast machine, and a ratio to zero says
nothing."""

from __future__ import annotations

import time
from collections.abc import Callable

PER_SIZE, MIN_SMALL_S = 3.0, 0.004
REPEATS = 7  # runs per size; only the fastest of them counts (see `best_of`)


def time_limit(t_small: float, small: int, big: int) -> float:
    """The most the big run may take."""
    return PER_SIZE * (big / small) * max(t_small, MIN_SMALL_S)


def grows_faster_than_size(t_small: float, t_big: float, small: int, big: int) -> bool:
    return t_big > time_limit(t_small, small, big)


def cpu_seconds(fn: Callable[[str], object], text: str) -> float:
    """One run of `fn(text)` timed in process CPU time. Another process on the machine takes turns on the CPU but does not
    add to this process's CPU time, so it moves the result far less than wall time does."""
    t0 = time.process_time()
    fn(text)
    return time.process_time() - t0


def best_of(samples: list[float]) -> float:
    """Noise (a busy neighbour, a cache miss, a pause) only ever ADDS time, so the fastest run is the closest to the true
    cost; a median of a few runs still moves when most of them are slowed. This is the one estimator the tests use."""
    return min(samples)


def is_superlinear(
    measure: Callable[[str], float], unit: str, small: int, big: int, repeats: int = REPEATS
) -> bool:
    """`measure(text)` returns the seconds of ONE run (use `cpu_seconds`); the texts are `unit` repeated to `small` and
    `big` characters. Each size is measured `repeats` times, small and big interleaved, and the fastest run of each size is
    compared with the limit: a load that comes and goes cannot slow every small run and leave the big ones alone."""
    texts = [(unit * (n // len(unit) + 1))[:n] for n in (small, big)]
    runs: tuple[list[float], list[float]] = ([], [])
    for _ in range(repeats):
        for samples, text in zip(runs, texts, strict=True):
            samples.append(measure(text))
    return grows_faster_than_size(best_of(runs[0]), best_of(runs[1]), small, big)


def quadratic_stand_in(text: str) -> int:
    """A made-up cost that grows with the SQUARE of the text length (a count over every 8th prefix), for the tests that
    show the harness flags a real quadratic. Sized so the small run (16 KiB) takes about 6 ms, above the `MIN_SMALL_S`
    floor, and the 8x bigger run is about 64x slower against a limit of 24x: a gap of about 2.7x, in about 0.4 s."""
    return sum(text.count("a", 0, i) for i in range(0, len(text), 8))
