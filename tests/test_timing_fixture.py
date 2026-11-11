"""The shared linear-time rule (`tests/fixtures/timing.py`) itself, with a made-up clock: no real clock, so a loaded
machine cannot change the result. The tests that use the rule with the real clock are marked `perf`."""

from __future__ import annotations

import gc
import itertools

import pytest

from tests.fixtures import timing

SMALL, BIG = 1000, 4000


class Model:
    """Work whose time is `scale * len(text) ** power` on its own made-up clock. `tick` makes the clock coarse (it only
    shows whole ticks); `pause` is added to every batch but each third one (other programs taking the machine)."""

    def __init__(self, power: int, scale: float, tick: float = 0.0, pause: float = 0.0):
        self.power, self.scale, self.tick, self.pause = power, scale, tick, pause
        self.now, self.calls, self.reads, self.batches = 0.0, 0, 0, []

    def fn(self, text: str) -> None:
        self.calls += 1
        self.now += self.scale * len(text) ** self.power

    def clock(self) -> float:
        self.reads += 1
        if self.reads % 2 == 0:  # the read that ends a batch
            self.batches.append(self.calls)
            if len(self.batches) % 3:
                self.now += self.pause
        return self.now // self.tick * self.tick if self.tick else self.now

    def is_superlinear(self, small: int = SMALL, big: int = BIG) -> bool:
        return timing.is_superlinear(self.fn, "a", small, big, clock=self.clock)


SPEEDS = [
    1e-9,
    1e-8,
    1e-7,
    1e-5,
    1e-3,
]  # seconds per character: one small call takes 1 microsecond to 1 second


@pytest.mark.parametrize("scale", SPEEDS)
def test_a_linear_cost_passes_at_any_speed(scale):
    assert not Model(1, scale).is_superlinear()


@pytest.mark.parametrize("scale", [1e-11, 1e-10, 1e-9, 1e-7, 1e-6, 1e-5])
def test_a_quadratic_stand_in_is_flagged_at_any_speed(scale):
    # one small call takes from 10 microseconds to 10 seconds: the big call is 16x, the limit 12x. The three fastest
    # speeds are under the 4 ms an earlier version raised the small run to, where it flagged nothing.
    assert Model(2, scale).is_superlinear()


def test_a_fast_small_run_is_not_raised_to_a_floor():
    # 1 ms then 16 ms for 4x the size is quadratic. An earlier version raised the 1 ms to 4 ms and said "linear".
    assert timing.grows_faster_than_size(0.001, 0.016, SMALL, BIG)
    assert timing.grows_faster_than_size(1e-7, 16e-7, SMALL, BIG)
    assert not hasattr(timing, "MIN_SMALL_S")


def test_the_limit_is_a_ratio_of_the_two_sizes():
    assert timing.time_limit(0.1, 1000, 4000) == pytest.approx(timing.PER_SIZE * 4 * 0.1)
    assert timing.time_limit(0.1, 1000, 16000) == pytest.approx(timing.PER_SIZE * 16 * 0.1)
    assert timing.time_limit(1e-6, 1000, 4000) == pytest.approx(timing.PER_SIZE * 4 * 1e-6)


@pytest.mark.parametrize("t_small", [0.0, -0.001, float("nan"), float("inf")])
def test_a_small_run_that_is_not_a_time_is_refused_not_passed(t_small):
    with pytest.raises(ValueError, match="small run"):
        timing.grows_faster_than_size(t_small, 1.0, SMALL, BIG)


@pytest.mark.parametrize("sizes", [(4000, 1000), (1000, 1000), (0, 1000), (-5, 1000)])
def test_sizes_that_do_not_grow_are_refused(sizes):
    with pytest.raises(ValueError, match="sizes"):
        timing.time_limit(0.1, *sizes)


def test_a_larger_size_gap_separates_the_two_shapes_more():
    small, big = 1000, 8000
    assert not timing.grows_faster_than_size(0.01, 0.01 * 8, small, big)
    assert timing.grows_faster_than_size(0.01, 0.01 * 64, small, big)


def test_there_is_no_fixed_seconds_floor_on_the_big_run():
    assert not hasattr(timing, "FLOOR_S")
    # 0.5 s on the big run after 0.01 s on the small run (4x the size) is 50x: flagged, however "fast" 0.5 s is
    assert timing.grows_faster_than_size(0.01, 0.5, 1000, 4000)


# --- the measurement: batches long enough to time, the fastest of the repeats ---------------------------------------


@pytest.mark.parametrize("scale", SPEEDS)
def test_one_call_is_measured_to_its_true_time(scale):
    model = Model(1, scale)
    assert timing.seconds_per_call(model.fn, "a" * SMALL, model.clock) == pytest.approx(
        scale * SMALL
    )


def test_a_fast_call_is_repeated_until_the_batch_is_long_enough_to_time():
    model = Model(1, 1e-9)  # one call: 1 microsecond
    timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    sizes = [after - before for before, after in itertools.pairwise([0, *model.batches])]
    assert len(sizes) % timing.REPEATS == 0 and len(sizes) > timing.REPEATS, (
        "it must have grown the batch"
    )
    last = sizes[-timing.REPEATS :]
    assert len(set(last)) == 1, "the repeats that count have the same number of calls"
    assert last[0] * 1e-6 >= timing.MIN_BATCH_S, "every batch that counts is long enough"
    assert last[0] * 1e-6 < 10 * timing.MIN_BATCH_S, "and not needlessly long"


def test_a_slow_call_is_run_once_per_repeat():
    model = Model(1, 1e-3)  # one call: 1 second
    timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert model.calls == timing.REPEATS


@pytest.mark.parametrize("tick", [0.001, 0.0156])  # 15.6 ms: the Windows process clock
def test_a_coarse_clock_cannot_turn_a_fast_call_into_zero(tick):
    # one small call takes 0.3 ms: read once on these clocks it shows 0 (or one whole tick)
    true = 3e-7 * SMALL
    got = timing.seconds_per_call((m := Model(1, 3e-7, tick=tick)).fn, "a" * SMALL, m.clock)
    assert got > 0
    assert got == pytest.approx(true, rel=tick / timing.MIN_BATCH_S)
    assert not Model(1, 3e-7, tick=0.001).is_superlinear(1000, 16000)
    assert Model(2, 3e-10, tick=0.001).is_superlinear(1000, 16000)


@pytest.mark.parametrize("pause", [0.05, 1.0, 30.0])
def test_other_programs_taking_the_machine_in_two_of_three_batches_change_nothing(pause):
    # a pause can only add time: the fastest batch is the one without it (a median of three would count a pause)
    model = Model(1, 1e-7, pause=pause)
    assert timing.seconds_per_call(model.fn, "a" * SMALL, model.clock) == pytest.approx(
        1e-7 * SMALL
    )
    for scale in (1e-9, 1e-7, 1e-5):
        assert not Model(1, scale, pause=pause).is_superlinear()
        assert Model(2, scale / 1000, pause=pause).is_superlinear()


def test_a_call_too_fast_to_time_is_refused_not_passed():
    model = Model(
        1, 1e-12
    )  # one call: a nanosecond, so the largest batch allowed is still far too short
    with pytest.raises(ValueError, match="too fast to time"):
        timing.seconds_per_call(model.fn, "a" * SMALL, model.clock)
    assert model.calls >= timing.MAX_CALLS
    stopped = Model(1, 0.0)  # a clock that never moves
    with pytest.raises(ValueError, match="too fast to time"):
        stopped.is_superlinear()


def test_the_collector_is_off_while_the_clock_runs_and_back_on_after():
    seen = []
    assert gc.isenabled()
    timing.seconds_per_call(
        lambda _text: seen.append(gc.isenabled()), "a", iter(range(10**6)).__next__
    )
    assert seen and not any(seen)
    assert gc.isenabled()


def test_the_work_gets_the_unit_repeated_to_exactly_the_two_sizes():
    seen = set()
    model = Model(1, 1e-3)
    timing.is_superlinear(
        lambda text: (seen.add(text), model.fn(text)), "abc", 7, 20, clock=model.clock
    )
    assert seen == {"abcabca", "abcabcabcabcabcabcab"}
