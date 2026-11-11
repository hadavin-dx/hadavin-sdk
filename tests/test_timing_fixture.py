"""The shared linear-time rule (`tests/fixtures/timing.py`) itself, with a made-up clock: no real clock, so a loaded
machine cannot change the result. The tests that use the rule with the real clock are marked `perf`."""

from __future__ import annotations

import gc
import itertools
import math
import sys
import time

import pytest

from tests.fixtures import timing

SMALL, BIG, FAR = 1000, 4000, 16000  # a gap of 4 (the smallest allowed) and a gap of 16


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


@pytest.mark.parametrize("sizes", GAPS, ids=["gap4", "gap16"])
@pytest.mark.parametrize("scale", SPEEDS)
def test_a_linear_cost_passes_at_any_speed(scale, sizes):
    assert not Model(power(1), scale).is_superlinear(*sizes), "a linear cost was flagged"


@pytest.mark.parametrize("sizes", GAPS, ids=["gap4", "gap16"])
@pytest.mark.parametrize("scale", [1e-10, 1e-9, 1e-7, 1e-5])
def test_an_n_log_n_cost_passes_at_any_speed(scale, sizes):
    # 4x the text: 4 * log(4000)/log(1000) = 4.8x (limit 12x); 16x the text: 22.4x (limit 48x)
    assert not Model(n_log_n, scale).is_superlinear(*sizes), "an n log n cost was flagged"


@pytest.mark.parametrize("sizes", GAPS, ids=["gap4", "gap16"])
@pytest.mark.parametrize("scale", [1e-11, 1e-10, 1e-9, 1e-7, 1e-6, 1e-5])
def test_a_quadratic_cost_is_flagged_at_any_speed(scale, sizes):
    # one small call takes from 10 microseconds to 10 seconds. The three fastest speeds are under the 4 ms an earlier
    # version raised the small run to, where it flagged nothing.
    assert Model(power(2), scale).is_superlinear(*sizes), "a quadratic cost was not flagged"


@pytest.mark.parametrize(
    ("sizes", "passes", "flagged"),
    [((1000, 4000), 1.75, 1.85), ((1000, 8000), 1.48, 1.58), ((1000, 16000), 1.35, 1.45)],
    ids=["gap4", "gap8", "gap16"],
)
def test_the_smallest_exponent_a_gap_flags(sizes, passes, flagged):
    # 1 + log(3) / log(gap): 1.79 for 4, 1.53 for 8, 1.40 for 16. A wider gap sees a gentler growth.
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
    # literal numbers: 4x the size allows 12x the time, 16x allows 48x; nothing else moves the limit
    assert not timing.grows_faster_than_size(1.0, 11.9, 1000, 4000), (
        "11.9x for 4x the size is within the limit"
    )
    assert timing.grows_faster_than_size(1.0, 12.1, 1000, 4000), (
        "12.1x for 4x the size is over the limit"
    )
    assert not timing.grows_faster_than_size(1.0, 47.9, 1000, 16000), (
        "47.9x for 16x the size is within the limit"
    )
    assert timing.grows_faster_than_size(1.0, 48.1, 1000, 16000), (
        "48.1x for 16x the size is over the limit"
    )


def test_a_fast_small_run_is_not_raised_to_a_floor():
    # 1 ms then 16 ms for 4x the size is quadratic. An earlier version raised the 1 ms to 4 ms and said "linear".
    assert timing.grows_faster_than_size(0.001, 0.016, SMALL, BIG), (
        "a 1 ms small run was raised to a floor"
    )
    assert timing.grows_faster_than_size(1e-7, 16e-7, SMALL, BIG), (
        "a 100 ns small run was raised to a floor"
    )
    assert timing.grows_faster_than_size(0.01, 0.5, SMALL, BIG), (
        "a fast big run was excused by a seconds figure"
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


BAD_SIZES = [(4000, 1000), (1000, 1000), (-5, 1000), (0, 1000), (1000, 3999), (1000, 2000)]


@pytest.mark.parametrize(
    "sizes", BAD_SIZES, ids=["swapped", "equal", "negative", "zero", "just-under-4x", "2x"]
)
def test_sizes_that_cannot_show_a_quadratic_cost_are_refused_before_any_work(sizes):
    with pytest.raises(ValueError, match="sizes must be|at least 4 times"):
        timing.time_limit(0.1, *sizes)
    with pytest.raises(ValueError, match="sizes must be|at least 4 times"):
        timing.smallest_exponent_flagged(*sizes)
    model = Model(power(1), 1e-7)
    with pytest.raises(ValueError, match="sizes must be|at least 4 times"):
        model.is_superlinear(*sizes)
    assert model.calls == 0, "the work was run before the sizes were checked"
    assert timing.problems([("case", model.fn, "a")], *sizes, clock=model.clock)[0].startswith(
        "case on 'a': could not be timed: "
    )


def test_a_gap_of_exactly_four_is_the_smallest_allowed():
    timing.check_sizes(1000, 4000)
    with pytest.raises(ValueError, match="at least 4 times"):
        timing.check_sizes(1000, 3999)


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
    assert not Model(power(1), 3e-7, tick=0.001).is_superlinear(SMALL, FAR), "linear, coarse clock"
    assert Model(power(2), 3e-10, tick=0.001).is_superlinear(SMALL, FAR), "quadratic, coarse clock"


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


def test_the_collector_is_off_while_the_clock_runs_and_back_on_after():
    seen = []
    assert gc.isenabled()
    timing.seconds_per_call(
        lambda _text: seen.append(gc.isenabled()), "a", itertools.count().__next__
    )
    assert len(seen) == 6, "one sizing call and five repeats"
    assert not any(seen), "the collector must be off while the clock runs"
    assert gc.isenabled(), "the collector must be back on after"


def test_the_clock_is_processor_time_except_on_windows(monkeypatch):
    # processor time does not count the time another program had the processor; on Windows it moves in 15.6 ms steps
    wanted = time.perf_counter if sys.platform == "win32" else time.process_time
    assert timing.CLOCK is wanted, (
        "the rule must time processor time (the wall clock only on Windows)"
    )
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
        lambda text: (seen.add(text), model.fn(text)), "abc", 5, 20, clock=model.clock
    )
    assert seen == {"abcab", "abcabcabcabcabcabcab"}


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
    assert got[0] == "slow on 'a': grows faster than its input"
    assert (
        got[1].startswith("stopped on 'c': could not be timed: ") and "too fast to time" in got[1]
    )
    assert got[2] == "late on 'd': grows faster than its input", "a case after a refusal was lost"
    assert got[3] == "empty on '': could not be timed: the unit to repeat is empty"
    assert timing.problems([("fine", fine.fn, "b")], SMALL, BIG, clock=fine.clock) == []
