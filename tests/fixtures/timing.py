"""One rule for the linear-time tests (a test file never imports another test file).

THE RULE. A cost is "linear enough" when growing the input by a factor `g` grows the time of one call by at most
`PER_SIZE * g`. The limit is a RATIO of the two sizes, so it has no fixed seconds figure that a fast or a slow machine
could miss: a linear function grows by about `g`, an "n log n" one by a little more than `g`, a quadratic one by about
`g * g`. (This is the doubling-ratio test of Sedgewick and Wayne, "Algorithms", 4th edition, section 1.4: the ratio of
the times at two sizes estimates the exponent of the growth.)

WHAT A SIZE GAP CAN FLAG. A cost that grows as `size ** e` is flagged only when `e` is above
`1 + log(PER_SIZE) / log(g)` (`smallest_exponent_flagged`): 1.79 for a gap of 4, 1.53 for 8, 1.40 for 16. A pure
quadratic cost clears the limit by `g / PER_SIZE`: only 1.33x at a gap of 4, 5.3x at 16. So a gap under `MIN_GROWTH` (4)
is refused (it could never flag a quadratic cost), and a test should use 16 where the input allows it.

THE MEASUREMENT is made here, not by the caller (`seconds_per_call_each`), with the standard library's `timeit.Timer`
and by its rules (read in the `timeit` module of Python 3.13 on 2026-11-11):
  * THE CLOCK (`CLOCK`) is the processor time of this process (`time.process_time`, what `python -m timeit -p`
    uses): time in which another program had the processor is not counted, so a busy machine does not move the result.
    On Windows that clock moves in steps of 15.6 ms, too coarse for these batches, so there the wall clock
    (`time.perf_counter`) is used and the rule is only as steady as the machine is quiet (see below);
  * a call is repeated in a batch until the batch takes at least `MIN_BATCH_S` (what `Timer.autorange` does, there with
    0.2 s), so a small input is never timed below what the clock and the machine's noise can resolve;
  * `Timer.timeit` keeps the garbage collector OFF while the clock runs, so what is timed is the work without collector
    pauses (a cost that exists only in the collector is not seen by this rule);
  * each size's batch is run `REPEATS` times and the FASTEST counts (the note on `Timer.repeat`: "the lowest value gives
    a lower bound for how fast your machine can run the given code snippet; higher values ... are typically not caused
    by variability in Python's speed, but by other processes interfering with your timing accuracy"), and it is the
    fastest batch that must reach `MIN_BATCH_S`, so a pause during one batch cannot shorten the batches;
  * the batches of the two sizes take turns (small, big, small, big, ...), so a slow spell of the machine that lasts
    longer than one batch falls on both sizes and not on all the batches of one of them.

MEASURED on 2026-11-11 (4 processors, Linux, other test runs on the machine; ratio big/small of a linear, an "n log n"
and a quadratic stand-in at a gap of 16, limit 48, 100 samples each, batch length 20 ms; full tables in the changelog):
  * processor time, beside four busy processes of our own (load 7 to 13): linear 14.6 to 16.8, n log n 18.1 to 23.0,
    quadratic 212 to 254; beside eight (load 11 to 13): 15.2 to 16.0, 17.1 to 20.6, 229 to 256. Batches of 20 ms were
    enough; longer ones were not needed.
  * wall clock, same load: linear 2.5 to 26.3, n log n 5.3 to 56.7 (one sample over the limit: a false alarm),
    quadratic 73 to 676. Batches of 50 ms and 100 ms were no steadier on a machine without our own load.

WHAT THE RULE DOES NOT SURVIVE. With processor time: (1) work that WAITS (sleep, input and output, a lock) is not
counted at all, and work in other threads of this process is counted too: the rule is for single-threaded computing.
(2) A slowdown that depends on the size itself and is not the function's own cost: a big text that no longer fits a
processor cache another program is filling looks like faster growth. With the wall clock (Windows): also (3) a machine
with more runnable programs than processors for the whole measurement; at about three runnable programs per processor
one n log n measurement in a hundred was a false alarm. A steady slowdown of everything changes nothing on either clock.

There is NO floor on the small run. An earlier version raised a small run to 4 ms; a fast function was then compared
with a fixed seconds figure and a quadratic cost under that figure was never flagged. A time that is zero, negative or
not a number is refused loudly (`ValueError`), for either size: a ratio with it says nothing, and saying "linear" would
be a guess. "Too fast to time" (`MAX_CALLS` calls in one batch still under `MIN_BATCH_S`) needs a call of a few
nanoseconds: with the real clock only a function that does next to nothing gets there; the tests reach it with a
made-up clock."""

from __future__ import annotations

import functools
import math
import sys
import time
import timeit
from collections.abc import Callable, Iterable, Sequence

PER_SIZE, MIN_GROWTH = 3.0, 4
MIN_BATCH_S, REPEATS, MAX_CALLS = 0.02, 5, 10_000_000

Work = Callable[[str], object]
Clock = Callable[[], float]
CLOCK: Clock = time.perf_counter if sys.platform == "win32" else time.process_time


def check_sizes(small: int, big: int) -> None:
    if not 0 < small < big:
        raise ValueError(f"the sizes must be 0 < small < big, got {small} and {big}")
    if big < MIN_GROWTH * small:
        raise ValueError(
            f"the big size must be at least {MIN_GROWTH} times the small one, got {small} and {big}: "
            "a smaller gap cannot tell a quadratic cost from a linear one"
        )


def _check_time(seconds: float, which: str) -> None:
    if not (math.isfinite(seconds) and seconds > 0):
        raise ValueError(f"the {which} run took {seconds!r} s: not a time a ratio can be taken of")


def smallest_exponent_flagged(small: int, big: int) -> float:
    """A cost growing as `size ** e` is flagged at these two sizes only when `e` is above this."""
    check_sizes(small, big)
    return 1 + math.log(PER_SIZE) / math.log(big / small)


def time_limit(t_small: float, small: int, big: int) -> float:
    """The most one call on the big input may take, given the seconds of one call on the small input."""
    check_sizes(small, big)
    _check_time(t_small, "small")
    return PER_SIZE * (big / small) * t_small


def grows_faster_than_size(t_small: float, t_big: float, small: int, big: int) -> bool:
    _check_time(t_big, "big")
    return t_big > time_limit(t_small, small, big)


def _batch_timer(fn: Work, text: str, clock: Clock) -> Callable[[int], float]:
    """`batch(n)`: the seconds `n` calls of `fn(text)` take, with the garbage collector off."""
    return timeit.Timer(functools.partial(fn, text), timer=clock).timeit


def _more_calls(calls: int, took: float) -> int:
    if calls >= MAX_CALLS:
        raise ValueError(
            f"{calls} calls took {took!r} s, under {MIN_BATCH_S} s: too fast to time; use a bigger input"
        )
    # aim a fifth over the batch length (a clock that showed no time at all: ten times); at least double
    wanted = math.ceil(calls * 1.2 * MIN_BATCH_S / took) if took > 0 else calls * 10
    return min(MAX_CALLS, max(calls * 2, wanted))


def seconds_per_call_each(
    fn: Work, texts: Sequence[str], clock: Clock | None = None
) -> list[float]:
    """Seconds of ONE `fn(text)` for each text: the fastest of `REPEATS` batches per text, the texts taking turns."""
    batches = [_batch_timer(fn, text, clock or CLOCK) for text in texts]
    calls = [1] * len(texts)
    for i, batch in enumerate(batches):  # a first guess at the number of calls a batch needs
        while (took := batch(calls[i])) < MIN_BATCH_S:
            calls[i] = _more_calls(calls[i], took)
    while True:
        runs: list[list[float]] = [[] for _ in texts]
        for _ in range(REPEATS):
            for i, batch in enumerate(batches):
                runs[i].append(batch(calls[i]))
        best = [min(r) for r in runs]
        short = [i for i, seconds in enumerate(best) if seconds < MIN_BATCH_S]
        if not short:
            return [seconds / n for seconds, n in zip(best, calls, strict=True)]
        for i in short:  # the guess was made during a pause: the fastest batch shows the true need
            calls[i] = _more_calls(calls[i], best[i])


def seconds_per_call(fn: Work, text: str, clock: Clock | None = None) -> float:
    return seconds_per_call_each(fn, [text], clock)[0]


def is_superlinear(fn: Work, unit: str, small: int, big: int, clock: Clock | None = None) -> bool:
    """True when `fn` costs more than "linear enough". `fn(text)` is the work itself (it is timed here, its result is
    not used); the texts are `unit` repeated to `small` and `big` characters. Sizes and unit are checked first."""
    check_sizes(small, big)
    if not unit:
        raise ValueError("the unit to repeat is empty")
    texts = [(unit * (n // len(unit) + 1))[:n] for n in (small, big)]
    t_small, t_big = seconds_per_call_each(fn, texts, clock)
    return grows_faster_than_size(t_small, t_big, small, big)


def problems(
    cases: Iterable[tuple[str, Work, str]], small: int, big: int, clock: Clock | None = None
) -> list[str]:
    """For a sweep: one line per case `(name, fn, unit)` that is super-linear OR could not be timed, each naming the
    case. A case that cannot be timed does not stop the sweep, so the cases already found slow are not lost."""
    found = []
    for name, fn, unit in cases:
        try:
            if is_superlinear(fn, unit, small, big, clock):
                found.append(f"{name} on {unit!r}: grows faster than its input")
        except ValueError as refused:
            found.append(f"{name} on {unit!r}: could not be timed: {refused}")
    return found
