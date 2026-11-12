"""One rule for the linear-time tests (a test file never imports another test file).

A cost is "linear enough" when growing the input by a factor `g` grows the time by at most `PER_SIZE * g`. The limit is a
RATIO of the two sizes, so it has no fixed seconds figure that a fast or a slow machine could miss: a linear function
grows by about `g`, a quadratic one by about `g * g`, and with `g` of 4 or more the two are far apart from `PER_SIZE * g`.

How a time is measured (`block_seconds`): not one call, but a block of calls, repeated until the block lasts at least
`MIN_BLOCK_S`, divided by the number of calls. The clock is chosen once: process CPU time when its resolution is 0.1 ms or
finer (a busy neighbour takes turns on the CPU but adds nothing to it), with 10 ms blocks; else the monotonic wall clock
(`perf_counter`) with 50 ms blocks, where the best-of-N rule below absorbs the noise. By arithmetic, a clock that ticks
coarsely (15.6 ms on Windows) is off by at most about a third of one block (15.6 / 50); that is shown only with a fake
clock in `tests/test_timing_fixture.py`, no test here has run on a real Windows clock. On a platform without a fine CPU
clock the numbers are wall-clock seconds, so a busy neighbour CAN slow a run there; best-of-N is then the only defence.
A fast CPU cannot leave the small run too short to read, because the block grows until it lasts `MIN_BLOCK_S`.
Every call gets its own text (same length, different last characters), so a cache that keys on the WHOLE text cannot make
the later calls free. A cache that keys on a prefix or a chunk of the text (the first characters are the same in every
variant) still hits: this harness does not defend against that, and a function with such a cache measures its warm cost.

The small run is floored (`MIN_SMALL_S`, 1 ms): a ratio to a time of almost zero says nothing. Floor trade-off: the floor must
stay below the smallest small run a fast CPU can make, or the limit grows and a real quadratic passes
(`test_fast_cpu_simulation_*` pins this: a 2.5 ms small run is flagged at 1 ms and not at 4 ms).

Repeats trade-off: the sweep tests use 2 or 3 repeats per size (`REPEATS` is 5) to keep the `perf` group short (the
`perf` group took 51 s and 58 s in two measured runs on 4 shared cores, not 30 s). With fewer repeats, noise has fewer chances to be dropped: a neighbour that slows
EVERY small run raises the limit and can hide a quadratic (the test `repeats=1` case in `test_timing_fixture.py` shows
it), and one that slows every big run can raise a false red. On a fine CPU clock a neighbour adds almost nothing, so 2 or 3
suffice; on the wall-clock path (Windows) the margin is thinner and a red there is worth one re-run by hand."""

from __future__ import annotations

import itertools
import string
import time
from collections.abc import Callable

PER_SIZE, MIN_SMALL_S = 3.0, 0.001
REPEATS = 5  # runs per size; only the fastest of them counts (see `best_of`); the sweeps pass 2 or 3 (see the header)
COARSE_BLOCK_S, FINE_BLOCK_S = (
    0.05,
    0.01,
)  # a block lasts at least this long: with the wall clock, with a fine CPU clock
MAX_CALLS = 1 << 16  # never time more calls than this in one block (a function that costs nothing)
MAX_BLOCK_BYTES = (
    64 * 1024 * 1024
)  # the texts of one block are made before the clock starts: keep them small
_TAIL = 4  # the last characters that differ between texts


def _choose_clock() -> tuple[Callable[[], float], float]:
    """The clock and the shortest block that suits it, decided once at import: process CPU time if it ticks at 0.1 ms or
    finer (a 10 ms block is then off by 1 percent at most), else the monotonic wall clock, whose noise a 50 ms block and the
    best-of-N rule absorb."""
    try:
        if time.get_clock_info("process_time").resolution <= 1e-4:
            return time.process_time, FINE_BLOCK_S
    except (ValueError, OSError):  # pragma: no cover - a platform without the clock info
        pass
    return time.perf_counter, COARSE_BLOCK_S


CLOCK, MIN_BLOCK_S = _choose_clock()
_FRESH = itertools.count(
    1
)  # one number for every text made in this process (26**4 before the tails repeat)


def _variant(text: str) -> str:
    """The same text with a different tail (same length)."""
    number, tail = next(_FRESH), ""
    for _ in range(_TAIL):
        number, rest = divmod(number, 26)
        tail += string.ascii_lowercase[rest]
    return text[: max(0, len(text) - _TAIL)] + tail[: len(text)]


def time_limit(t_small: float, small: int, big: int) -> float:
    """The most the big run may take."""
    return PER_SIZE * (big / small) * max(t_small, MIN_SMALL_S)


def grows_faster_than_size(t_small: float, t_big: float, small: int, big: int) -> bool:
    return t_big > time_limit(t_small, small, big)


def block_seconds(
    fn: Callable[[str], object],
    text: str,
    min_block: float | None = None,
    clock: Callable[[], float] | None = None,
) -> float:
    """Seconds of ONE call of `fn(text)`: `fn` is called k times (k = 1, 2, 4, ...) on k different texts inside one timed
    block until the block lasts at least `min_block`, and the block time is divided by k. The texts are made before the
    clock starts."""
    clock = clock or CLOCK
    min_block = MIN_BLOCK_S if min_block is None else min_block
    k, k_max = 1, max(1, min(MAX_CALLS, MAX_BLOCK_BYTES // max(1, len(text))))
    while True:
        texts = [_variant(text) for _ in range(k)]
        t0 = clock()
        for t in texts:
            fn(t)
        elapsed = clock() - t0
        if elapsed >= min_block or k >= k_max:
            return elapsed / k
        k = min(k * 2, k_max)


def best_of(samples: list[float]) -> float:
    """Noise (a busy neighbour, a cache miss, a pause) only ever ADDS time, so the fastest run is the closest to the true
    cost; a median of a few runs still moves when most of them are slowed. This is the one estimator the tests use."""
    return min(samples)


def measure_sizes(
    measure: Callable[[str], float], unit: str, small: int, big: int, repeats: int = REPEATS
) -> tuple[float, float]:
    """The fastest `measure(text)` of the small and of the big text. `measure` returns the seconds of one call (use
    `block_seconds`). Small and big are interleaved, and every repeat gets a new text of the same length."""
    texts = [(unit * (n // len(unit) + 1))[:n] for n in (small, big)]
    runs: tuple[list[float], list[float]] = ([], [])
    for _ in range(repeats):
        for samples, text in zip(runs, texts, strict=True):
            samples.append(measure(_variant(text)))
    return best_of(runs[0]), best_of(runs[1])


def is_superlinear(
    measure: Callable[[str], float], unit: str, small: int, big: int, repeats: int = REPEATS
) -> bool:
    """True when the fastest big run is over the limit set by the fastest small run. A load that comes and goes cannot
    slow every small run and leave the big ones alone."""
    return grows_faster_than_size(*measure_sizes(measure, unit, small, big, repeats), small, big)


def quadratic_stand_in(text: str) -> int:
    """A made-up cost that grows with the SQUARE of the text length (a count over every 2nd prefix), for the tests that
    show the harness flags a real quadratic. With 8 KiB and 128 KiB (16x) the big run is about 256x slower against a
    limit of 48x; `tests/test_timing_fixture.py` pins that the small run is at least `MIN_SMALL_S` and the measured
    ratio at least twice the limit. (`tests/test_migration_numbers.py` uses 4 KiB and 64 KiB, the same 16x, to cost less.)"""
    return sum(text.count("a", 0, i) for i in range(0, len(text), 2))
