"""One rule for the linear-time tests (a test file never imports another test file).

THE RULE. A cost is "linear enough" when growing the input by a factor `g` grows the time of one call by at most
`PER_SIZE * g`. The limit is a RATIO of the two sizes, so it has no fixed seconds figure that a fast or a slow machine
could miss: a linear function grows by about `g`, an "n log n" one by a little more than `g`, a quadratic one by about
`g * g`. (This is the doubling-ratio test of Sedgewick and Wayne, "Algorithms", 4th edition, section 1.4: the ratio of
the times at two sizes estimates the exponent of the growth.)

WHAT PASSES, IN PLAIN WORDS. Anything that takes up to 3 times longer at the big size than straight-line growth from
the small size would give. At a gap of 16 (limit 48 times) that lets through, besides a straight line, a quadratic part
that is up to about 15 percent of the straight-line part of the SMALL run (at the big size that part is about 2.5 times
the straight-line part). Two blind spots follow from the same arithmetic: (a) a fixed cost per call that is large next to
the small run (5 times the small run's own work, for example) hides even a pure quadratic cost at a gap of 16 (43.5
times, under the limit of 48), so use input where the fixed cost is small; (b) nothing above the big size is seen.

WHAT A SIZE GAP CAN FLAG. A cost that grows as `size ** e` is flagged only when `e` is above
`1 + log(PER_SIZE) / log(g)` (`smallest_exponent_flagged`): 1.53 for a gap of 8, 1.40 for 16. A pure quadratic cost
clears the limit by `g / PER_SIZE`: 2.7x at a gap of 8, 5.3x at 16. So a gap under `MIN_GROWTH` (8) is refused (every
caller uses 8 or 16; a gap of 4 cleared the limit by only 1.33x), and a test should use 16 where the input allows it.

THE MEASUREMENT is made here, not by the caller (`seconds_per_call_each`), with the standard library's `timeit.Timer`
and by its rules (read in the `timeit` module of Python 3.13 on 2026-11-11):
  * THE CLOCK (`CLOCK`, chosen by `pick_clock`) is the processor time of this process (`time.process_time`, what
    `python -m timeit -p` uses): time in which another program had the processor is not counted, so a busy machine moves
    the result far less (measured: up to about a quarter, see below). On Windows that clock moves in steps of 15.6 ms, too
    coarse for these batches, so there the wall clock (`time.perf_counter`) is used and the rule is only as steady as the
    machine is quiet (see below);
  * a call is repeated in a batch until the batch takes at least `MIN_BATCH_S` (what `Timer.autorange` does, there with
    0.2 s), so a small input is never timed below what the clock and the machine's noise can resolve;
  * `Timer.timeit` keeps the garbage collector OFF while the clock runs, so what is timed is the work without collector
    pauses (a cost that exists only in the collector is not seen by this rule);
  * each size's batch is run `REPEATS` times and the FASTEST counts (the note on `Timer.repeat`: "the lowest value gives
    a lower bound for how fast your machine can run the given code snippet; higher values ... are typically not caused
    by variability in Python's speed, but by other processes interfering with your timing accuracy"), and it is the
    fastest batch that must reach `MIN_BATCH_S`, so a pause during one batch cannot shorten the batches;
  * the batches of the two sizes take turns (small, big, small, big, ...), so a slow spell of the machine that lasts
    longer than one batch falls on both sizes and not on all the batches of one of them;
  * WORK THAT MOSTLY WAITS is refused, not mis-timed: with the real processor-time clock (not on Windows, where the wall
    clock is the clock and the check is off), a batch whose wall time is more than `WAIT_FACTOR` times its processor time
    (and at least `WAIT_MIN_S`) looks like waiting; it is run again, and `Untimeable` is raised when `WAIT_TRIES`
    tries of the same batch in a row all look like it. That covers sleeping, input and output, lock waits and work done in
    a child process (processor time does not count a child: measured 0.0003 s of process time for a child that burned
    1.0 s). ONE look is not enough, because a program that is paused by the scheduler for a few milliseconds inside a batch
    of a few microseconds (the first, tiny sizing batches) would look the same: the machine paused, the work did not
    wait. Work that waits does so in every try; a pause does not repeat in the next try (shown with a made-up wall clock in
    `test_timing_fixture.py`; the same pause with the first version of the check, which judged one look, failed under four
    busy processes, see the changelog).
  * These ceilings count computing only: a regression that sleeps or blocks is NOT caught by a processor-time ceiling; a
    test for that needs a wall-time limit (`test_k5_review.py` abandons a hang at its deadline, `test_pgsource_layers.py`
    uses a database sleep with a watchdog).
  * THE RAW WALL-CLOCK TESTS THAT REMAIN, on purpose (they guard a hang or a wait, which processor time cannot see, with a
    ceiling far above the normal time): `test_k5_classes.py` (a hung tool is abandoned: the child process must finish
    in under 30 s, its tool deadline is 0.3 s), `test_k5_review.py` (the same abandon, in under 3 s against a 0.3 s
    deadline) and `test_scan_repo.py::test_long_word_runs_do_not_hang_the_password_rule` (the scan runs in a child
    process, which processor time does not count: 20 s against a measured 0.09 s). A new ceiling on a computing cost
    goes through this rule, not through a raw clock.
  * Only the doubling-ratio test (`growth`, marked `perf` where it uses the real clock) sees mild super-linear growth (an
    exponent of 1.3 passes a fixed ceiling on seconds); the fixed ceilings catch an exploding cost only.

MEASURED on 2026-11-11 (4 processors, LINUX, other test runs on the machine; ratio big/small of a linear, an "n log n"
and a quadratic stand-in at a gap of 16, limit 48, 100 samples each, batch length 20 ms; full tables in the changelog):
  * processor time, beside four busy processes of our own (load 8 to 13): linear 14.6 to 16.8, n log n 18.1 to 23.0,
    quadratic 212 to 254; beside eight (load 11 to 13): 15.2 to 16.0, 17.1 to 20.6, 229 to 256. Batches of 20 ms were
    enough; longer ones were not needed.
  * the WALL clock on Linux, same load (this is what Windows would use; Windows itself was NOT run): linear 2.5 to 26.3,
    n log n 5.3 to 56.7 (one sample over the limit: a false alarm), quadratic 73 to 676. Batches of 50 ms and 100 ms
    gave narrower ranges in some columns and wider in others, under a different load, so they were not compared further.

WHAT THE RULE DOES NOT SURVIVE. With processor time: (1) work in other threads of this process is counted too: the rule
is for single-threaded computing; (2) a function that remembers its result per text is timed only on the remembered path
(the first real call falls in the sizing batch, which is thrown away); (3) a slowdown that depends on the size itself and
is not the function's own cost: a big text that no longer fits a processor cache another program is filling looks like
faster growth; (4) a collector cost (see above). With the wall clock (Windows): also (5) a machine with more runnable
programs than processors for the whole measurement; at about three runnable programs per processor one n log n
measurement in a hundred was a false alarm, a linear one read as low as 2.5 (a small run inflated about 6.4 times) and a
quadratic one as low as 5.3 times its true ratio would have been missed. A steady slowdown of everything changes nothing
on either clock.

There is NO floor on the small run. An earlier version raised a small run to 4 ms; a fast function was then compared
with a fixed seconds figure and a quadratic cost under that figure was never flagged. A time that is zero, negative or
not a number is refused loudly (`Untimeable`, a `ValueError`), for either size: a ratio with it says nothing, and saying
"linear" would be a guess. "Too fast to time" (`MAX_CALLS` calls in one batch still under `MIN_BATCH_S`) needs a call of
a few nanoseconds: with the real clock only a function that does next to nothing gets there; the tests reach it with a
made-up clock."""

from __future__ import annotations

import functools
import math
import sys
import time
import timeit
from collections.abc import Callable, Iterable, Sequence
from typing import NamedTuple

PER_SIZE, MIN_GROWTH = 3.0, 8
MIN_BATCH_S, REPEATS, MAX_CALLS = 0.02, 5, 10_000_000
MAX_ROUNDS = (
    60  # a bound by construction: every resize at least doubles the calls, so 24 reach MAX_CALLS
)
WAIT_FACTOR, WAIT_MIN_S = (
    50.0,
    0.005,
)  # a batch with 50x more wall time than processor time (and 5 ms or more) looks like waiting ...
WAIT_TRIES = 3  # ... and is refused only when this many tries of the SAME batch in a row all look like waiting

Work = Callable[[str], object]
Clock = Callable[[], float]


class Untimeable(ValueError):
    """The rule refuses to judge: sizes, unit, a time that is not a time, work too fast or mostly waiting."""


def pick_clock(platform: str) -> Clock:
    """Processor time, except on Windows (`win32`), where that clock moves in 15.6 ms steps: the wall clock there."""
    return time.perf_counter if platform == "win32" else time.process_time


CLOCK: Clock = pick_clock(sys.platform)


def check_sizes(small: int, big: int) -> None:
    if not 0 < small < big:
        raise Untimeable(f"the sizes must be 0 < small < big, got {small} and {big}")
    if big < MIN_GROWTH * small:
        raise Untimeable(
            f"the big size must be at least {MIN_GROWTH} times the small one, got {small} and {big}: "
            "a smaller gap clears the limit by too little to tell a quadratic cost from a linear one"
        )


def _check_time(seconds: float, which: str) -> None:
    if not (math.isfinite(seconds) and seconds > 0):
        raise Untimeable(f"the {which} run took {seconds!r} s: not a time a ratio can be taken of")


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


class Growth(NamedTuple):
    """What was measured: seconds of one call at each size. `str(growth)` is the line a failing test prints."""

    t_small: float
    t_big: float
    small: int
    big: int

    @property
    def ratio(self) -> float:
        _check_time(self.t_small, "small")
        _check_time(self.t_big, "big")
        return self.t_big / self.t_small

    @property
    def limit(self) -> float:
        return PER_SIZE * (self.big / self.small)

    @property
    def flagged(self) -> bool:
        return grows_faster_than_size(self.t_small, self.t_big, self.small, self.big)

    def __str__(self) -> str:
        return (
            f"{self.t_small:.3g} s at {self.small} characters, {self.t_big:.3g} s at {self.big}: "
            f"{self.ratio:.1f} times as long for {self.big / self.small:g} times the text, limit {self.limit:g} times"
        )


def _looks_like_waiting(took: float, waited: float) -> bool:
    return waited >= WAIT_MIN_S and waited > WAIT_FACTOR * took


def _batch_timer(fn: Work, text: str, clock: Clock, wall: Clock | None) -> Callable[[int], float]:
    """`batch(n)`: the seconds `n` calls of `fn(text)` take, with the garbage collector off. With `wall` (the real
    processor-time clock only) a batch that mostly waits is refused: a batch that looks like waiting is run again, and
    only `WAIT_TRIES` looks in a row refuse it (a pause by the scheduler is one look, never three), so one pause is
    thrown away and the batch is measured again."""
    timed = timeit.Timer(functools.partial(fn, text), timer=clock).timeit
    if wall is None:
        return timed

    def batch(n: int) -> float:
        for _ in range(WAIT_TRIES):
            started = wall()
            took = timed(n)
            waited = wall() - started
            if not _looks_like_waiting(took, waited):
                return took
        raise Untimeable(
            f"{n} calls took {took:.3g} s of processor time but {waited:.3g} s of real time, {WAIT_TRIES} times in a row: "
            "the work mostly waits (sleep, input and output, a lock) or runs in a child process, which processor time "
            "does not count"
        )

    return batch


def _more_calls(calls: int, took: float) -> int:
    if calls >= MAX_CALLS:
        raise Untimeable(
            f"{calls} calls took {took!r} s, under {MIN_BATCH_S} s: too fast to time; use a bigger input"
        )
    # aim a fifth over the batch length (a clock that showed no time at all, or not a number: ten times); at least double
    wanted = math.ceil(min(calls * 1.2 * MIN_BATCH_S / took, MAX_CALLS)) if took > 0 else calls * 10
    return min(MAX_CALLS, max(calls * 2, wanted))


def _wall_for(clock: Clock | None, wall: Clock | None) -> Clock | None:
    """The wall clock that arms the waiting check: given (a test with a made-up one), or the real one when the real
    processor-time clock is used; none otherwise (a made-up clock, or Windows, where the wall clock is the clock)."""
    if wall is not None:
        return wall
    return time.perf_counter if clock is None and CLOCK is time.process_time else None


def seconds_per_call_each(
    fn: Work, texts: Sequence[str], clock: Clock | None = None, wall: Clock | None = None
) -> list[float]:
    """Seconds of ONE `fn(text)` for each text: the fastest of `REPEATS` batches per text, the texts taking turns."""
    wall = _wall_for(clock, wall)
    batches = [_batch_timer(fn, text, clock or CLOCK, wall) for text in texts]
    calls = [1] * len(texts)
    for i, batch in enumerate(batches):  # a first guess at the number of calls a batch needs
        for _ in range(MAX_ROUNDS):
            if (took := batch(calls[i])) >= MIN_BATCH_S:
                break
            calls[i] = _more_calls(calls[i], took)
        else:
            raise Untimeable(
                f"{MAX_ROUNDS} batches in a row stayed under {MIN_BATCH_S} s: not a time that grows"
            )
    best = [0.0] * len(texts)
    todo = list(
        range(len(texts))
    )  # the texts whose batch size is new: only these are timed again after a resize
    for _ in range(MAX_ROUNDS):
        runs: dict[int, list[float]] = {i: [] for i in todo}
        for _ in range(REPEATS):
            for i in todo:
                runs[i].append(batches[i](calls[i]))
        for i in todo:
            best[i] = min(runs[i])
        todo = [i for i, seconds in enumerate(best) if not seconds >= MIN_BATCH_S]
        if not todo:
            return [seconds / n for seconds, n in zip(best, calls, strict=True)]
        for i in todo:  # the guess was made during a pause: the fastest batch shows the true need
            calls[i] = _more_calls(calls[i], best[i])
    raise Untimeable(
        f"{MAX_ROUNDS} rounds in a row had a batch under {MIN_BATCH_S} s: not a time that grows"
    )


def seconds_per_call(
    fn: Work, text: str, clock: Clock | None = None, wall: Clock | None = None
) -> float:
    return seconds_per_call_each(fn, [text], clock, wall)[0]


def growth(fn: Work, unit: str, small: int, big: int, clock: Clock | None = None) -> Growth:
    """Measure `fn` at the two sizes. `fn(text)` is the work itself (it is timed here, its result is not used); the
    texts are `unit` repeated to `small` and `big` characters. Sizes and unit are checked first."""
    check_sizes(small, big)
    if not unit:
        raise Untimeable("the unit to repeat is empty")
    texts = [(unit * (n // len(unit) + 1))[:n] for n in (small, big)]
    t_small, t_big = seconds_per_call_each(fn, texts, clock)
    return Growth(t_small, t_big, small, big)


def is_superlinear(fn: Work, unit: str, small: int, big: int, clock: Clock | None = None) -> bool:
    """True when `fn` costs more than "linear enough" (see `growth`; a test that wants the numbers uses `growth`)."""
    return growth(fn, unit, small, big, clock).flagged


def problems(
    cases: Iterable[tuple[str, Work, str]], small: int, big: int, clock: Clock | None = None
) -> list[str]:
    """For a sweep: one line per case `(name, fn, unit)` that is super-linear (with the measured times), could not be
    timed, each naming the case. A case that cannot be timed does not stop the sweep, so the cases already found slow
    are not lost. A case whose own function raises ends the sweep with that exception (type and traceback kept), with
    a note naming the case and the problems found before it."""
    found = []
    for name, fn, unit in cases:
        try:
            measured = growth(fn, unit, small, big, clock)
            if measured.flagged:
                found.append(f"{name} on {unit!r}: grows faster than its input: {measured}")
        except Untimeable as refused:
            found.append(f"{name} on {unit!r}: could not be timed: {refused}")
        except Exception as error:
            # the case's own function failed: keep its type and traceback, name the case and what was found so far
            error.add_note(
                f"in the sweep case {name!r} on {unit!r}; problems found before it: {found}"
            )
            raise
    return found
