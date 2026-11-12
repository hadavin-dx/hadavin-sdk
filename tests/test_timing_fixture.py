"""The shared linear-time rule (`tests/fixtures/timing.py`) itself, with made-up timings: no clock, so a loaded machine
cannot change the result. The tests that use it with a real clock are marked `perf`."""

from __future__ import annotations

import contextlib
import multiprocessing
import os
import time

import pytest

from tests.fixtures import timing

SMALL, BIG = 1000, 4000


def _model(power: int, scale: float = 1e-9):
    """A measure whose time is `scale * len(text) ** power`: no clock."""
    return lambda text: scale * len(text) ** power


@pytest.mark.parametrize("scale", [1e-12, 1e-9, 1e-7, 1e-5])
def test_a_linear_cost_passes_at_any_speed(scale):
    assert not timing.is_superlinear(_model(1, scale), "a", SMALL, BIG)


@pytest.mark.parametrize("scale", [1e-7, 1e-6, 1e-5])
def test_a_quadratic_stand_in_is_flagged_at_any_speed(scale):
    # from 0.1 s on the small run up: the big run is 16x, the limit 12x. (Below the 1 ms floor on the small run nothing is
    # flagged: a cost that small is not measured, which is what the floor is for.)
    assert timing.is_superlinear(_model(2, scale), "a", SMALL, BIG)


def test_the_limit_is_a_ratio_of_the_two_sizes():
    assert timing.time_limit(0.1, 1000, 4000) == pytest.approx(timing.PER_SIZE * 4 * 0.1)
    assert timing.time_limit(0.1, 1000, 16000) == pytest.approx(timing.PER_SIZE * 16 * 0.1)
    # a zero small run is floored, never a limit of zero
    assert timing.time_limit(0.0, 1000, 4000) == pytest.approx(
        timing.PER_SIZE * 4 * timing.MIN_SMALL_S
    )


def test_a_larger_size_gap_separates_the_two_shapes_more():
    small, big = 1000, 8000
    assert not timing.grows_faster_than_size(0.01, 0.01 * 8, small, big)
    assert timing.grows_faster_than_size(0.01, 0.01 * 64, small, big)


def test_there_is_no_fixed_seconds_floor_on_the_big_run():
    assert not hasattr(timing, "FLOOR_S")
    # 0.5 s on the big run after 0.01 s on the small run (4x the size) is 50x: flagged, however "fast" 0.5 s is
    assert timing.grows_faster_than_size(0.01, 0.5, 1000, 4000)


def test_the_fastest_run_ignores_inflated_small_samples():
    """A busy moment that slows MOST of the small runs (here the first three of five) must not hide a real quadratic:
    noise only adds time, so the best of the runs stands. A median would read the slowed value; a single run per size
    (`repeats=1`) hides it too, which shows the test can fail."""

    def measure_with_slow_first_small_runs():
        calls = {"small": 0}

        def measure(text: str) -> float:
            t = 1e-7 * len(text) ** 2
            if len(text) == SMALL:
                calls["small"] += 1
                if calls["small"] <= 3:
                    return t * 50  # these small runs land on a busy moment
            return t

        return measure

    assert timing.is_superlinear(measure_with_slow_first_small_runs(), "a", SMALL, BIG, repeats=5)
    assert not timing.is_superlinear(
        measure_with_slow_first_small_runs(), "a", SMALL, BIG, repeats=1
    )


def test_the_best_of_is_the_minimum():
    assert timing.best_of([0.5, 0.2, 9.0]) == 0.2


# --- the block estimator, with a fake clock and fake calls: no real time, so these run in the ordinary suite ---------------


class FakeClock:
    """A clock the fake calls advance by hand. `tick` > 0 makes it read only whole ticks (15.6 ms is the Windows
    process-time tick); 0 is a perfect clock."""

    def __init__(self, tick: float = 0.0):
        self.now, self.tick = 0.0, tick

    def __call__(self) -> float:
        return self.now if not self.tick else (self.now // self.tick) * self.tick

    def call(self, cost: float) -> None:
        self.now += cost


def _fake_measure(clock: FakeClock, cost):
    """A `measure` for `is_superlinear`: block timing of a fake call that costs `cost(len(text))` seconds on `clock`."""
    return lambda text: timing.block_seconds(
        lambda t: clock.call(cost(len(t))), text, min_block=timing.COARSE_BLOCK_S, clock=clock
    )


def _single_call_measure(clock: FakeClock, cost):
    """The estimator before this change: one call, one reading."""

    def measure(text: str) -> float:
        t0 = clock()
        clock.call(cost(len(text)))
        return clock() - t0

    return measure


def test_a_block_is_timed_until_it_lasts_the_minimum_and_divided_by_the_calls():
    clock, calls = FakeClock(), []

    def fn(text: str) -> None:
        calls.append(text)
        clock.call(0.01)

    assert timing.block_seconds(fn, "a" * 100, min_block=0.05, clock=clock) == pytest.approx(0.01)
    assert (
        len(calls) == 1 + 2 + 4 + 8
    )  # 0.01 s per call: the first block to reach 50 ms has 8 calls (80 ms)
    assert len(set(calls[-8:])) == 8, "every call of a block gets its own text"
    assert {len(t) for t in calls} == {100}


def test_the_clock_is_process_time_when_it_ticks_finely_and_the_wall_clock_otherwise(monkeypatch):
    import types

    real = time.get_clock_info

    def info(name):
        return types.SimpleNamespace(resolution=0.0156) if name == "process_time" else real(name)

    assert timing._choose_clock() == (time.process_time, timing.FINE_BLOCK_S) or (
        real("process_time").resolution > 1e-4
    )
    monkeypatch.setattr(time, "get_clock_info", info)
    assert timing._choose_clock() == (time.perf_counter, timing.COARSE_BLOCK_S)


def test_a_call_that_alone_lasts_the_minimum_is_timed_once():
    clock, calls = FakeClock(), []
    assert timing.block_seconds(
        lambda t: (calls.append(t), clock.call(0.2)), "a" * 50, clock=clock
    ) == (pytest.approx(0.2))
    assert len(calls) == 1


def test_a_function_that_costs_nothing_stops_at_the_call_cap():
    calls = []
    clock = FakeClock()
    assert timing.block_seconds(calls.append, "abcdef", clock=clock) == 0.0
    assert len(calls) == 2 * timing.MAX_CALLS - 1  # the blocks of 1, 2, 4 ... MAX_CALLS calls


def test_a_cap_on_the_bytes_of_one_block_stops_the_doubling_for_a_huge_text():
    calls = []
    clock = FakeClock()
    timing.block_seconds(calls.append, "a" * (timing.MAX_BLOCK_BYTES // 4), clock=clock)
    assert (
        len(calls) == 1 + 2 + 4
    )  # at most 4 texts of that size per block: the blocks of 1, 2 and 4


def test_a_text_is_new_every_time_and_keeps_its_length():
    texts = {timing._variant("a" * 20) for _ in range(500)}
    assert len(texts) == 500
    assert {len(t) for t in texts} == {20}
    assert {len(timing._variant(s)) for s in ("", "a", "ab", "abc")} == {0, 1, 2, 3}


FAST, LINEAR_14MS = 1.5e-3, 14e-3


def test_fast_cpu_simulation_a_small_run_of_1_5_ms_still_flags_a_quadratic():
    """Design Major 1: on a fast CPU the small run costs 1.5 ms. With a floor of 4 ms the limit would be 24 x 4 ms = 96 ms
    and the 8x run (64 x 1.5 ms = 96 ms) would pass; block timing reads the 1.5 ms and the floor is below it."""
    clock = FakeClock()
    small, big = 1000, 8000
    quadratic = lambda n: FAST * (n / small) ** 2
    assert timing.is_superlinear(_fake_measure(clock, quadratic), "a", small, big)
    assert not timing.is_superlinear(
        _fake_measure(clock, lambda n: FAST * (n / small)), "a", small, big
    )
    assert FAST > timing.MIN_SMALL_S, "the floor must stay below the simulated small run"


def test_tick_simulation_a_15_6_ms_clock_does_not_flag_a_linear_cost_and_flags_a_quadratic():
    """Codebase Major / design Major 2: Windows process time ticks at 15.6 ms. A 14 ms small run reads 0 on a single
    call, floors, and a linear big run (16 x 14 ms) is flagged; timed in 50 ms blocks the same cost passes."""
    small, big = 1000, 16000
    linear = lambda n: LINEAR_14MS * (n / small)
    quadratic = lambda n: LINEAR_14MS * (n / small) ** 2
    tick = 0.0156
    assert not timing.is_superlinear(_fake_measure(FakeClock(tick), linear), "a", small, big)
    assert timing.is_superlinear(_fake_measure(FakeClock(tick), quadratic), "a", small, big)
    # the contrast that makes the test mean something: one call per reading misjudges the linear cost on this clock
    assert timing.is_superlinear(_single_call_measure(FakeClock(tick), linear), "a", small, big)


def test_a_cached_function_is_still_flagged_because_every_text_is_new():
    """Design 6: a cache in the code under test (here `functools.cache`, an unbounded `lru_cache`) would make runs 2 to N free if the same text came back."""
    import functools

    clock = FakeClock()
    small, big = 1000, 8000

    @functools.cache
    def cached_quadratic(text: str) -> int:
        clock.call(FAST * (len(text) / small) ** 2)
        return len(text)

    assert timing.is_superlinear(
        lambda t: timing.block_seconds(
            cached_quadratic, t, min_block=timing.COARSE_BLOCK_S, clock=clock
        ),
        "a",
        small,
        big,
    )
    assert cached_quadratic.cache_info().hits == 0


# --- the busy neighbours of the load tests: one busy-loop process per CPU (at most 4), each one confirmed running --------


def _spin(ready) -> None:
    ready.set()
    while True:
        pass


def _never_ready(ready) -> None:
    time.sleep(60)


def _cpus_to_load() -> int:
    try:
        return max(1, min(4, len(os.sched_getaffinity(0))))
    except AttributeError:  # a platform without sched_getaffinity
        return max(1, min(4, os.cpu_count() or 1))


@contextlib.contextmanager
def busy_workers(target=_spin, count: int | None = None, ready_timeout: float = 10.0):
    """Start `count` worker processes and wait until each has said it runs; FAIL (never pass) if one does not within
    `ready_timeout`. Stops only the workers that started, and kills one that ignores `terminate`."""
    ctx = multiprocessing.get_context("spawn")
    events = [ctx.Event() for _ in range(count or _cpus_to_load())]
    workers = [ctx.Process(target=target, args=(ev,), daemon=True) for ev in events]
    started = []
    try:
        for w in workers:
            w.start()
            started.append(w)
        deadline = time.monotonic() + ready_timeout
        for ev in events:
            if not ev.wait(max(0.0, deadline - time.monotonic())):
                pytest.fail(
                    f"a busy worker did not start within {ready_timeout} s: the load test would run unloaded"
                )
        yield started
    finally:
        for w in started:
            if w.is_alive():
                w.terminate()
        for w in started:
            w.join(timeout=10)
            if w.is_alive():
                w.kill()
                w.join(timeout=10)


@pytest.fixture
def busy_cpus():
    with busy_workers():
        yield


def test_a_worker_that_never_says_it_runs_fails_the_load_test_instead_of_passing_it():
    with (
        pytest.raises(pytest.fail.Exception, match="did not start"),
        busy_workers(_never_ready, count=1, ready_timeout=0.5),
    ):
        raise AssertionError("the body must not run when a worker is not ready")


def test_the_workers_are_stopped_after_the_body():
    with busy_workers(count=2) as workers:
        assert all(w.is_alive() for w in workers)
    assert not any(w.is_alive() for w in workers)


def test_the_number_of_busy_workers_is_between_one_and_four():
    assert 1 <= _cpus_to_load() <= 4


def _linear_stand_in(text: str) -> int:
    return sum(ord(c) for c in text)


def _measured(measure, unit: str, small: int, big: int) -> tuple[float, float]:
    return timing.measure_sizes(measure, unit, small, big, repeats=2)


@pytest.mark.perf
def test_the_harness_flags_a_real_quadratic_while_every_cpu_is_busy(busy_cpus):
    small, big = 8 * 1024, 128 * 1024
    t_small, t_big = _measured(
        lambda t: timing.block_seconds(timing.quadratic_stand_in, t), "a", small, big
    )
    # the gap is pinned, not claimed: the small run is well above the floor and the big run well above the limit
    assert t_small >= 4 * timing.MIN_SMALL_S, t_small
    assert t_big / t_small >= 2 * timing.PER_SIZE * big / small, (t_small, t_big)
    assert timing.grows_faster_than_size(t_small, t_big, small, big)


@pytest.mark.perf
def test_the_harness_passes_a_linear_cost_while_every_cpu_is_busy(busy_cpus):
    small, big = 256 * 1024, 2048 * 1024
    t_small, t_big = _measured(lambda t: timing.block_seconds(_linear_stand_in, t), "a", small, big)
    assert t_small >= 4 * timing.MIN_SMALL_S, t_small
    assert not timing.grows_faster_than_size(t_small, t_big, small, big), (t_small, t_big)
