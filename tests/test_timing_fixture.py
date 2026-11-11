"""The shared linear-time rule (`tests/fixtures/timing.py`) itself, with a made-up clock: no real clock, so a loaded
machine cannot change the result. The tests that use the real clock (waiting work, a child process, ordinary computing)
are marked `perf`; the two that need the processor-time clock are skipped on Windows, where the check is off."""

from __future__ import annotations

import gc
import itertools
import math
import multiprocessing
import sys
import time
import timeit
from concurrent.futures import ProcessPoolExecutor

import pytest

from tests.fixtures import timing

SMALL, BIG, FAR = 1000, 8000, 16000  # a gap of 8 (the smallest allowed) and a gap of 16


class Model:
    """Work whose time is `scale * cost(len(text))` on its own made-up clock.

    `tick` makes the clock coarse (it only shows whole ticks). `pause` seconds are added to batches, as other programs
    taking the machine would: with `spell` 0 to every batch but each fifth one; with `spell` N to N batches in a row,
    then N batches without, and so on."""

    def __init__(self, cost, scale: float, tick: float = 0.0, pause: float = 0.0, spell: int = 0):
        self.cost, self.scale, self.tick, self.pause, self.spell = cost, scale, tick, pause, spell
        self.now, self.calls, self.reads = 0.0, 0, 0
        self.batches: list[tuple[int, int]] = []  # (text length, calls) of every batch, in order
        self.size = 0

    def fn(self, text: str) -> None:
        self.calls += 1
        self.size = len(text)
        self.now += self.scale * self.cost(len(text))

    def clock(self) -> float:
        self.reads += 1
        if self.reads % 2 == 0:  # the read that ends a batch
            done = sum(n for _, n in self.batches)
            self.batches.append((self.size, self.calls - done))
            k = len(self.batches) - 1
            paused = (k // self.spell) % 2 == 0 if self.spell else k % 5 != 0
            if paused:
                self.now += self.pause
        return self.now // self.tick * self.tick if self.tick else self.now

    def is_superlinear(self, small: int = SMALL, big: int = BIG) -> bool:
        return timing.is_superlinear(self.fn, "a", small, big, clock=self.clock)


def power(e: float):
    return lambda n: n**e


def n_log_n(n: int) -> float:
    return n * math.log2(n)


SPEEDS = [
    1e-9,
    1e-8,
    1e-7,
    1e-5,
    1e-3,
]  # seconds per character: one small call takes 1 microsecond to 1 second
GAPS = [(SMALL, BIG), (SMALL, FAR)]
BATCH_CALLS = 20_000  # literal: this many calls of 1 microsecond are one batch of 20 ms


# --- the rule: what passes and what is flagged ------------------------------------------------------------------------


@pytest.mark.parametrize("sizes", GAPS, ids=["gap8", "gap16"])
@pytest.mark.parametrize("scale", SPEEDS)
def test_a_linear_cost_passes_at_any_speed(scale, sizes):
    assert not Model(power(1), scale).is_superlinear(*sizes), "a linear cost was flagged"


@pytest.mark.parametrize("sizes", GAPS, ids=["gap8", "gap16"])
@pytest.mark.parametrize("scale", [1e-10, 1e-9, 1e-7, 1e-5])
def test_an_n_log_n_cost_passes_at_any_speed(scale, sizes):
    # 8x the text: 8 * log(8000)/log(1000) = 10.4x (limit 24x); 16x the text: 22.4x (limit 48x)
    assert not Model(n_log_n, scale).is_superlinear(*sizes), "an n log n cost was flagged"


@pytest.mark.parametrize("sizes", GAPS, ids=["gap8", "gap16"])
@pytest.mark.parametrize("scale", [1e-11, 1e-10, 1e-9, 1e-7, 1e-6, 1e-5])
def test_a_quadratic_cost_is_flagged_at_any_speed(scale, sizes):
    # one small call takes from 10 microseconds to 10 seconds. The three fastest speeds are under the 4 ms an earlier
    # version raised the small run to, where it flagged nothing.
    assert Model(power(2), scale).is_superlinear(*sizes), "a quadratic cost was not flagged"


@pytest.mark.parametrize(
    ("sizes", "passes", "flagged"),
    [((1000, 8000), 1.48, 1.58), ((1000, 16000), 1.35, 1.45), ((1000, 64000), 1.2, 1.3)],
    ids=["gap8", "gap16", "gap64"],
)
def test_the_smallest_exponent_a_gap_flags(sizes, passes, flagged):
    # 1 + log(3) / log(gap): 1.53 for 8, 1.40 for 16, 1.26 for 64. A wider gap sees a gentler growth.
    assert passes < timing.smallest_exponent_flagged(*sizes) < flagged, (
        "the stated exponent is wrong"
    )
    assert not Model(power(passes), 1e-9).is_superlinear(*sizes), (
        "an exponent under the bound was flagged"
    )
    assert Model(power(flagged), 1e-9).is_superlinear(*sizes), (
        "an exponent over the bound was not flagged"
    )


def test_the_limit_is_three_times_the_size_ratio():
    # literal numbers: 8x the size allows 24x the time, 16x allows 48x; nothing else moves the limit
    assert not timing.grows_faster_than_size(1.0, 23.9, 1000, 8000), (
        "23.9x for 8x the size is within the limit"
    )
    assert timing.grows_faster_than_size(1.0, 24.1, 1000, 8000), (
        "24.1x for 8x the size is over the limit"
    )
    assert not timing.grows_faster_than_size(1.0, 47.9, 1000, 16000), (
        "47.9x for 16x the size is within the limit"
    )
    assert timing.grows_faster_than_size(1.0, 48.1, 1000, 16000), (
        "48.1x for 16x the size is over the limit"
    )


def test_exactly_the_limit_passes_and_a_hair_over_is_flagged():
    # 3.0 * 8.0 * 1.0 and 3.0 * 16.0 * 1.0 are exact in floating point: "more than the limit" is strict
    assert not timing.grows_faster_than_size(1.0, 24.0, 1000, 8000), "exactly the limit must pass"
    assert not timing.grows_faster_than_size(1.0, 48.0, 1000, 16000), "exactly the limit must pass"
    assert timing.grows_faster_than_size(1.0, math.nextafter(24.0, 25.0), 1000, 8000), (
        "a hair over the limit must be flagged"
    )


def test_a_fast_small_run_is_not_raised_to_a_floor():
    # 1 ms then 64 ms for 8x the size is quadratic. An earlier version raised the 1 ms to 4 ms and said "linear".
    assert timing.grows_faster_than_size(0.001, 0.064, SMALL, BIG), (
        "a 1 ms small run was raised to a floor"
    )
    assert timing.grows_faster_than_size(1e-7, 64e-7, SMALL, BIG), (
        "a 100 ns small run was raised to a floor"
    )
    assert timing.grows_faster_than_size(0.01, 0.5, SMALL, BIG), (
        "a fast big run was excused by a seconds figure"
    )


def test_what_passes_is_a_small_quadratic_part_and_no_more():
    # the docstring's plain words: at a gap of 16 a quadratic part of about 15 percent of the straight-line part of
    # the small run passes (limit 48x); 17 percent is flagged
    def with_square(q: float):
        return lambda n: n + q * n * n / SMALL

    assert not Model(with_square(0.14), 1e-9).is_superlinear(SMALL, FAR), "14 percent must pass"
    assert Model(with_square(0.17), 1e-9).is_superlinear(SMALL, FAR), "17 percent must be flagged"


def test_a_fixed_cost_per_call_hides_even_a_quadratic_cost_at_a_gap_of_16():
    # the blind spot (a) of the docstring: a fixed cost of 5 times the small run's own work gives 43.5x, under 48x
    small_work = SMALL * SMALL

    def fixed_plus_square(n: int) -> float:
        return 5 * small_work + n * n

    assert not Model(fixed_plus_square, 1e-9).is_superlinear(SMALL, FAR), "the stated blind spot"
    assert Model(lambda n: n * n, 1e-9).is_superlinear(SMALL, FAR), (
        "without the fixed cost it is flagged"
    )


# --- refusals: never "linear" by default --------------------------------------------------------------------------------

NOT_A_TIME = [0.0, -0.001, float("nan"), float("inf"), float("-inf")]


@pytest.mark.parametrize("t_small", NOT_A_TIME)
def test_a_small_run_that_is_not_a_time_is_refused_not_passed(t_small):
    with pytest.raises(ValueError, match="the small run took"):
        timing.grows_faster_than_size(t_small, 1.0, SMALL, BIG)


@pytest.mark.parametrize("t_big", NOT_A_TIME)
def test_a_big_run_that_is_not_a_time_is_refused_not_passed(t_big):
    with pytest.raises(ValueError, match="the big run took"):
        timing.grows_faster_than_size(0.001, t_big, SMALL, BIG)


BAD_SIZES = [(8000, 1000), (1000, 1000), (-5, 1000), (0, 1000), (1000, 7999), (1000, 4000)]


@pytest.mark.parametrize(
    "sizes", BAD_SIZES, ids=["swapped", "equal", "negative", "zero", "just-under-8x", "4x"]
)
def test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work(sizes):
    with pytest.raises(ValueError, match="sizes must be|at least 8 times"):
        timing.time_limit(0.1, *sizes)
    with pytest.raises(ValueError, match="sizes must be|at least 8 times"):
        timing.smallest_exponent_flagged(*sizes)
    model = Model(power(1), 1e-7)
    with pytest.raises(ValueError, match="sizes must be|at least 8 times"):
        model.is_superlinear(*sizes)
    assert model.calls == 0, "the work was run before the sizes were checked"
    assert timing.problems([("case", model.fn, "a")], *sizes, clock=model.clock)[0].startswith(
        "case on 'a': could not be timed: "
    )


def test_a_gap_of_exactly_eight_is_the_smallest_allowed():
    timing.check_sizes(1000, 8000)
    with pytest.raises(timing.Untimeable, match="at least 8 times"):
        timing.check_sizes(1000, 7999)


def test_an_empty_unit_is_refused_before_any_work():
    model = Model(power(1), 1e-7)
    with pytest.raises(ValueError, match="unit to repeat is empty"):
        timing.is_superlinear(model.fn, "", SMALL, BIG, clock=model.clock)
    assert model.calls == 0, "the work was run before the unit was checked"


def test_a_call_too_fast_to_time_is_refused_not_passed(monkeypatch):
    monkeypatch.setattr(
        timing, "MAX_CALLS", 1000
    )  # the real cap is ten million calls: too slow for a unit test
    model = Model(
        power(1), 1e-12
    )  # one call: a nanosecond, so the largest batch allowed is still far too short
    with pytest.raises(ValueError, match="1000 calls took .* too fast to time"):
        timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert max(n for _, n in model.batches) == 1000, "it gave up before trying the largest batch"
    stopped = Model(power(1), 0.0)  # a clock that never moves
    with pytest.raises(ValueError, match="too fast to time"):
        stopped.is_superlinear()


# --- the measurement: batches long enough to time, the fastest of the repeats, the sizes taking turns ---------------


@pytest.mark.parametrize("scale", SPEEDS)
def test_one_call_is_measured_to_its_true_time(scale):
    model = Model(power(1), scale)
    got = timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert got == pytest.approx(scale * SMALL), "the time of one call is wrong"
    both = timing.seconds_per_call_each(model.fn, ["a" * SMALL, "a" * BIG], model.clock)
    assert both == pytest.approx([scale * SMALL, scale * BIG]), (
        "the times of the two sizes are wrong"
    )


def test_a_fast_call_is_batched_to_the_batch_length_and_repeated_five_times():
    model = Model(power(1), 1e-9)  # one call: exactly 1 microsecond
    timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    counted = [n for _, n in model.batches[-5:]]
    assert len(model.batches) > 5, "it must have grown the batch before the repeats"
    assert len(set(counted)) == 1, "the five repeats that count have the same number of calls"
    # literal: BATCH_CALLS calls of 1 microsecond are the batch length; a fifth is aimed over it, never ten times
    assert counted[0] >= BATCH_CALLS, "a batch that counts is shorter than the batch length"
    assert counted[0] <= BATCH_CALLS * 3 // 2, "a batch that counts is needlessly long"


def test_a_pause_while_the_batch_is_sized_cannot_shorten_the_batches_that_count():
    # the first batch (one call of 1 microsecond) is paused for half a second and so looks long enough; the fastest of
    # the repeats shows it is not, and the batch is sized again
    model = Model(power(1), 1e-9, pause=0.5, spell=1)
    got = timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert got == pytest.approx(1e-6), "the time of one call is wrong"
    assert model.batches[0] == (SMALL, 1) and model.batches[1] == (SMALL, 1), (
        "the pause did not hit the sizing"
    )
    counted = [n for _, n in model.batches[-5:]]
    assert min(counted) >= BATCH_CALLS, (
        "a pause while the batch was sized left the batches too short"
    )


def test_a_slow_call_is_run_once_to_size_the_batch_and_once_in_each_of_five_repeats():
    model = Model(power(1), 1e-3)  # one call: 1 second
    timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert model.calls == 6, "one sizing call and five repeats"
    model = Model(power(1), 1e-3)
    model.is_superlinear()
    assert model.calls == 12, "two sizes: two sizing calls and five repeats each"


def test_the_two_sizes_take_turns():
    model = Model(power(1), 1e-3)
    model.is_superlinear()
    order = [size for size, _ in model.batches]
    assert order[:2] == [SMALL, BIG], "each size is sized once first"
    assert order[2:] == [SMALL, BIG] * 5, "the repeats must alternate small, big"


@pytest.mark.parametrize("tick", [0.001, 0.005])
def test_a_coarse_clock_cannot_turn_a_fast_call_into_zero(tick):
    # one small call takes 0.3 ms: read once on these clocks it shows 0 (or one whole tick)
    model = Model(power(1), 3e-7, tick=tick)
    got = timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert got == pytest.approx(3e-7 * SMALL, rel=tick / timing.MIN_BATCH_S), (
        "a coarse clock changed the time"
    )
    assert not Model(power(1), 3e-7, tick=tick).is_superlinear(SMALL, FAR), "linear, coarse clock"
    assert Model(power(2), 3e-10, tick=tick).is_superlinear(SMALL, FAR), "quadratic, coarse clock"


@pytest.mark.parametrize("pause", [0.007, 0.5, 30.0])
def test_a_pause_in_four_of_five_batches_changes_nothing(pause):
    # a pause can only add time: the fastest batch is the one without it (a median of five would count a pause, and
    # so would a single run)
    model = Model(power(1), 1e-7, pause=pause)
    got = timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert got == pytest.approx(1e-7 * SMALL), "a pause was counted as the work's own time"
    for scale in (1e-9, 1e-7, 1e-5):
        assert not Model(power(1), scale, pause=pause).is_superlinear(), "linear, with pauses"
        assert not Model(n_log_n, scale, pause=pause).is_superlinear(SMALL, FAR), (
            "n log n, with pauses"
        )
        assert Model(power(2), scale / 1000, pause=pause).is_superlinear(), "quadratic, with pauses"


@pytest.mark.parametrize("spell", [2, 3, 4, 5])
@pytest.mark.parametrize("pause", [0.5, 30.0])
def test_a_slow_spell_over_several_batches_in_a_row_changes_nothing(spell, pause):
    # up to five batches in a row are slow, then as many are not: the sizes take turns, so each size keeps a clean
    # batch. Timing all the small batches first would lose every one of them to a spell of five.
    for scale in (1e-9, 1e-7, 1e-5):
        linear = Model(power(1), scale, pause=pause, spell=spell)
        assert not linear.is_superlinear(SMALL, FAR), "linear, with a slow spell"
        quadratic = Model(power(2), scale / 1000, pause=pause, spell=spell)
        assert quadratic.is_superlinear(SMALL, FAR), "quadratic, with a slow spell"


def test_timeit_reads_the_clock_exactly_twice_per_batch():
    # the made-up `Model` clock counts two reads per batch (one before, one after): a Python change to `timeit` that
    # breaks that fails here, with this name, and not as a confusing failure in a dozen other tests
    reads = []

    def clock() -> float:
        reads.append(1)
        return 0.0

    timeit.Timer(lambda: None, timer=clock).timeit(3)
    assert len(reads) == 2, "timeit no longer reads the clock exactly twice per batch"


def test_the_collector_is_off_while_the_clock_runs_and_back_on_after():
    was_on = gc.isenabled()
    gc.enable()  # the test sets its own start state: the suite may run with the collector off
    try:
        seen = []
        timing.seconds_per_call(
            lambda _text: seen.append(gc.isenabled()), "a", itertools.count().__next__
        )
        assert len(seen) == 6, "one sizing call and five repeats"
        assert not any(seen), "the collector must be off while the clock runs"
        assert gc.isenabled(), "the collector must be back on after"
    finally:
        if not was_on:
            gc.disable()


@pytest.mark.parametrize("platform", ["linux", "darwin", "cygwin", "freebsd"])
def test_the_clock_is_processor_time_off_windows(platform):
    # processor time does not count the time another program had the processor
    assert timing.pick_clock(platform) is time.process_time, (
        "off Windows the rule must time processor time"
    )


def test_the_clock_is_the_wall_clock_on_windows():
    # on Windows processor time moves in 15.6 ms steps: too coarse for batches of 20 ms
    assert timing.pick_clock("win32") is time.perf_counter, (
        "on Windows the rule must use the wall clock"
    )


def test_the_rules_clock_is_the_one_picked_for_this_platform(monkeypatch):
    assert timing.CLOCK is timing.pick_clock(sys.platform)
    model = Model(power(1), 1e-7)
    monkeypatch.setattr(timing, "CLOCK", model.clock)
    got = timing.seconds_per_call(model.fn, "a" * SMALL)
    assert got == pytest.approx(1e-7 * SMALL), "a call without a clock must use the rule's clock"
    assert not timing.is_superlinear(model.fn, "a", SMALL, BIG), (
        "a call without a clock must use the rule's clock"
    )


def test_the_work_gets_the_unit_repeated_to_exactly_the_two_sizes():
    seen = set()
    model = Model(power(1), 1e-3)
    timing.is_superlinear(
        lambda text: (seen.add(text), model.fn(text)), "abc", 5, 40, clock=model.clock
    )
    assert seen == {"abcab", "abcabcabcabcabcabcabcabcabcabcabcabcabca"}


# --- a sweep: every problem named, none lost ----------------------------------------------------------------------------


def test_a_sweep_names_each_slow_case_and_each_case_it_could_not_time(monkeypatch):
    monkeypatch.setattr(timing, "MAX_CALLS", 1000)
    slow, fine, stopped, late = (
        Model(power(2), 1e-9),
        Model(power(1), 1e-7),
        Model(power(1), 0.0),
        Model(power(2), 1e-9),
    )

    def clock() -> float:  # one clock for the four: only the model that is working moves it
        return slow.clock() + fine.clock() + stopped.clock() + late.clock()

    cases = [("slow", slow.fn, "a"), ("fine", fine.fn, "b"), ("stopped", stopped.fn, "c")]
    cases += [("late", late.fn, "d"), ("empty", fine.fn, "")]
    got = timing.problems(cases, SMALL, BIG, clock=clock)
    assert len(got) == 4, got
    assert got[0].startswith("slow on 'a': grows faster than its input: "), got[0]
    assert "limit 24 times" in got[0], "the line must show the measured ratio and the limit"
    assert (
        got[1].startswith("stopped on 'c': could not be timed: ") and "too fast to time" in got[1]
    )
    assert got[2].startswith("late on 'd': grows faster than its input: "), (
        "a case after a refusal was lost"
    )
    assert got[3] == "empty on '': could not be timed: the unit to repeat is empty"
    assert timing.problems([("fine", fine.fn, "b")], SMALL, BIG, clock=fine.clock) == []


def test_a_failing_line_shows_both_times_the_ratio_and_the_limit():
    # 1 ms at 1000 characters, 64 ms at 8000: 64 times as long for 8 times the text, limit 24 times
    line = str(timing.Growth(0.001, 0.064, SMALL, BIG))
    assert line == (
        "0.001 s at 1000 characters, 0.064 s at 8000: 64.0 times as long for 8 times the text, limit 24 times"
    )
    model = Model(power(2), 1e-9)
    grown = timing.growth(model.fn, "a", SMALL, BIG, clock=model.clock)
    assert grown.ratio > grown.limit, "the measured growth is a quadratic one"


def test_a_case_that_raises_keeps_its_type_and_is_named_with_the_problems_found_before_it():
    slow = Model(power(2), 1e-9)

    def broken(text: str) -> None:
        raise UnicodeEncodeError("ascii", text[:1], 0, 1, "made-up")

    cases = [("slow", slow.fn, "a"), ("broken", broken, "b")]
    with pytest.raises(UnicodeEncodeError) as caught:
        timing.problems(cases, SMALL, BIG, clock=slow.clock)
    notes = "".join(getattr(caught.value, "__notes__", []))
    assert "'broken' on 'b'" in notes, "the note does not name the case that raised"
    assert "slow on 'a': grows faster than its input" in notes, (
        "the note lost the problems found before"
    )


def test_a_case_that_raises_a_value_error_is_not_called_untimeable():
    def broken(text: str) -> None:
        raise ValueError("the case's own error")

    with pytest.raises(ValueError, match="the case's own error") as caught:
        timing.problems([("broken", broken, "b")], SMALL, BIG, clock=Model(power(1), 1e-7).clock)
    assert not isinstance(caught.value, timing.Untimeable)


# --- clocks that are not clocks: a refusal, never a crash with another type or a made-up number ---------------------------------


@pytest.mark.parametrize("took", [5e-324, 1e-300])
def test_a_clock_difference_of_almost_nothing_is_refused_not_an_overflow(took):
    # calls * 1.2 * 0.02 / 5e-324 is infinity: math.ceil(infinity) used to raise OverflowError
    ticks = itertools.cycle([0.0, took])
    with pytest.raises(timing.Untimeable, match="too fast to time"):
        timing.seconds_per_call(lambda _text: None, "a", lambda: next(ticks))


def test_a_clock_that_gives_not_a_number_is_refused_not_returned_as_a_time():
    reads = itertools.cycle([0.0, float("nan")])
    with pytest.raises(timing.Untimeable):
        timing.seconds_per_call(lambda _text: None, "a", lambda: next(reads))


def test_the_sizing_loops_end_by_construction_even_without_the_calls_cap(monkeypatch):
    # defence in depth: a clock stuck at zero and no cap on the calls still ends in a refusal, not a loop
    monkeypatch.setattr(timing, "MAX_CALLS", 10**30)
    monkeypatch.setattr(timing, "MAX_ROUNDS", 5)
    stopped = Model(power(1), 0.0)
    with pytest.raises(timing.Untimeable, match="5 batches in a row stayed under"):
        stopped.is_superlinear()


# --- work that waits: refused, because processor time does not count it -------------------------------------------------------

not_on_windows = pytest.mark.skipif(
    sys.platform == "win32",
    reason="on Windows the rule's clock is the wall clock, so there is no waiting check to test",
)


class WallModel:
    """A made-up processor-time clock and a made-up wall clock that move together by `cost` seconds per call, and a
    list of calls (by number, from 1) after which the wall clock alone jumps by `pause` seconds: a program paused by the
    scheduler while it computes. With `wait` seconds the work also waits that long in every call (the wall moves, the
    processor time does not)."""

    def __init__(self, cost: float, pause: float = 0.0, paused_calls=(), wait: float = 0.0):
        self.cost, self.pause, self.paused, self.wait = cost, pause, set(paused_calls), wait
        self.cpu = self.real = 0.0
        self.calls = 0

    def fn(self, _text: str) -> None:
        self.calls += 1
        self.cpu += self.cost
        self.real += self.cost + self.wait
        if self.calls in self.paused:
            self.real += self.pause

    def cpu_clock(self) -> float:
        return self.cpu

    def wall_clock(self) -> float:
        return self.real

    def seconds(self) -> float:
        return timing.seconds_per_call(self.fn, "a", self.cpu_clock, self.wall_clock)


@pytest.mark.parametrize("calls_paused", [1, 2, 3, 5])
def test_one_pause_inside_a_tiny_batch_is_not_taken_for_waiting(calls_paused):
    # 60 microseconds of work, and the scheduler takes the program away for 8 ms inside the batch: 8 ms is more than 50
    # times 60 microseconds and more than 5 ms, which is what the first version of the check refused at once
    model = WallModel(6e-5, pause=8e-3, paused_calls=[calls_paused])
    assert model.seconds() == pytest.approx(6e-5), "the pause changed the time of one call"


def test_two_pauses_in_a_row_on_the_same_batch_are_still_not_waiting():
    # calls 1 and 2 are the first two tries of the first batch (one call each); the third try is clean
    model = WallModel(6e-5, pause=8e-3, paused_calls=[1, 2])
    assert model.seconds() == pytest.approx(6e-5)


def test_a_pause_on_every_try_of_a_batch_is_what_waiting_looks_like():
    # the made-up work waits 8 ms in every call: every try of the batch looks the same, so it is refused
    model = WallModel(6e-5, wait=8e-3)
    with pytest.raises(timing.Untimeable, match=f"{timing.WAIT_TRIES} times in a row"):
        model.seconds()
    assert model.calls == timing.WAIT_TRIES, (
        "it must refuse after exactly the allowed tries, not run on"
    )


def test_the_waiting_check_is_not_armed_by_a_wall_clock_that_agrees_with_the_processor_clock():
    model = WallModel(6e-5)
    assert model.seconds() == pytest.approx(6e-5)


@not_on_windows
@pytest.mark.perf
def test_work_that_sleeps_is_refused_not_timed_from_a_few_microseconds_of_processor_time(
    monkeypatch,
):
    monkeypatch.setattr(
        timing, "MAX_CALLS", 2
    )  # without the check the run would end at the cap, not after minutes
    started = time.perf_counter()
    with pytest.raises(timing.Untimeable, match="mostly waits"):
        timing.seconds_per_call(lambda _text: time.sleep(0.02), "a")
    assert time.perf_counter() - started < 5, "the refusal came only after a long run"


def _burn_in_the_child(_text: str) -> None:
    started = time.perf_counter()
    while time.perf_counter() - started < 0.4:
        pass


@not_on_windows
@pytest.mark.perf
def test_work_done_in_a_child_process_is_refused_because_processor_time_does_not_count_it(
    monkeypatch,
):
    monkeypatch.setattr(timing, "MAX_CALLS", 2)
    # a "spawn" child (a new interpreter): no fork of a threaded test process, so no fork warning under `-W error`
    with (
        ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn")) as pool,
        pytest.raises(timing.Untimeable, match="child process"),
    ):
        timing.seconds_per_call(lambda text: pool.submit(_burn_in_the_child, text).result(), "a")


@pytest.mark.perf
def test_ordinary_computing_is_not_taken_for_waiting():
    got = timing.seconds_per_call(lambda text: sum(map(ord, text)), "a" * 2000)
    assert 0 < got < 0.01, "a few thousand additions are not waiting"


def test_the_waiting_check_is_for_the_real_clock_only(monkeypatch):
    # with a made-up clock the wall time says nothing about the made-up seconds: no refusal for waiting
    monkeypatch.setattr(timing, "MAX_CALLS", 10)
    with pytest.raises(timing.Untimeable, match="too fast to time"):
        timing.seconds_per_call(lambda _text: time.sleep(0.006), "a", lambda: 0.0)


def test_the_waiting_check_is_off_when_the_rules_clock_is_not_processor_time(monkeypatch):
    # Windows (the wall clock is the clock), or a test that swapped the rule's clock for a made-up one
    monkeypatch.setattr(timing, "CLOCK", time.perf_counter)
    assert timing._wall_for(None, None) is None
    monkeypatch.setattr(timing, "CLOCK", time.process_time)
    assert timing._wall_for(None, None) is time.perf_counter
    assert timing._wall_for(lambda: 0.0, None) is None
    given = lambda: 0.0
    assert timing._wall_for(None, given) is given


@pytest.mark.parametrize("t_small, t_big", [(0.0, 1.0), (1.0, 0.0), (math.nan, 1.0), (1.0, -1.0)])
def test_a_hand_built_growth_with_no_time_is_refused_not_a_division_by_zero(t_small, t_big):
    built = timing.Growth(t_small, t_big, SMALL, BIG)
    with pytest.raises(timing.Untimeable):
        built.ratio  # noqa: B018
    with pytest.raises(timing.Untimeable):
        str(built)


def test_a_resize_times_again_only_the_text_whose_batch_changed():
    # the small text's first guess is short (its first batch is paused, so it looks long enough) and is resized; the big
    # text's batch is right the first time and its five results stand
    model = Model(power(1), 1e-9, pause=0.5, spell=1)
    timing.seconds_per_call_each(model.fn, ["a" * SMALL, "a" * BIG], clock=model.clock)
    sizes = [size for size, _ in model.batches]
    assert sizes.count(BIG) == 2 + 5, (
        "the big text: two sizing batches and five repeats, and no more"
    )
    assert sizes[-5:] == [SMALL] * 5, "after the resize only the small text is timed"
