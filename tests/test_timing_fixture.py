"""The shared linear-time rule (`tests/fixtures/timing.py`) itself. Most tests use made-up timings or a fake clock, so a
loaded machine cannot change the result. Two tests measure a real call with the real clock while every CPU is busy, and
the two tests of the busy workers start real processes (about 1 s); the two real-clock ones are marked `perf`."""

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


# --- the block estimator, with a fake clock and fake calls: no real time passes, so these run in the ordinary suite ---------


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


def test_measure_sizes_gives_every_repeat_a_new_text_of_the_same_length():
    """A repeat that reused the text of an earlier one could be served by a cache inside the code under test."""
    seen: dict[int, list[str]] = {}

    def measure(text: str) -> float:
        seen.setdefault(len(text), []).append(text)
        return 1e-3

    timing.measure_sizes(measure, "ab", 1000, 4000, repeats=6)
    assert set(seen) == {1000, 4000}
    for length, texts in seen.items():
        assert len(texts) == 6, length
        assert len(set(texts)) == 6, f"a text of {length} characters was measured twice"


def test_a_variant_changes_only_the_tail_so_a_cache_keyed_on_a_prefix_is_not_defeated():
    """The stated limit of the harness (see the header of `tests/fixtures/timing.py`): the texts of one run share all but
    their last characters."""
    a, b = timing._variant("x" * 64), timing._variant("x" * 64)
    assert a != b
    assert a[:-4] == b[:-4] == "x" * 60


FAST, LINEAR_14MS = 2.5e-3, 14e-3


def test_fast_cpu_simulation_a_small_run_of_2_5_ms_still_flags_a_quadratic():
    """On a fast CPU the small run costs 2.5 ms. The text is 4x bigger, so a quadratic costs 16 x 2.5 ms = 40 ms against a
    limit of 3 x 4 x 2.5 ms = 30 ms (flagged). With a floor of 4 ms the limit would be 3 x 4 x 4 ms = 48 ms and the quadratic
    would pass (the hand mutant `o267` in `migration_numbers_mutants.py` makes exactly that change). The two sides are 33 %
    apart, so the result does not rest on a float tie."""
    clock = FakeClock()
    small, big = 1000, 4000

    def quadratic(n: int) -> float:
        return FAST * (n / small) ** 2

    def linear(n: int) -> float:
        return FAST * (n / small)

    assert timing.is_superlinear(_fake_measure(clock, quadratic), "a", small, big)
    assert not timing.is_superlinear(_fake_measure(clock, linear), "a", small, big)
    assert FAST > timing.MIN_SMALL_S, "the floor must stay below the simulated small run"


def test_tick_simulation_a_15_6_ms_clock_does_not_flag_a_linear_cost_and_flags_a_quadratic():
    """Codebase Major / design Major 2: Windows process time ticks at 15.6 ms. A 14 ms small run reads 0 on a single
    call, floors, and a linear big run (16 x 14 ms) is flagged; timed in 50 ms blocks the same cost passes."""
    small, big = 1000, 16000

    def linear(n: int) -> float:
        return LINEAR_14MS * (n / small)

    def quadratic(n: int) -> float:
        return LINEAR_14MS * (n / small) ** 2

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
    """One busy worker per CPU THIS process may use (a container or `taskset` can allow fewer than `os.cpu_count()`), 1 to 4."""
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


def test_the_number_of_busy_workers_follows_the_cpus_this_process_may_use(monkeypatch):
    """`os.cpu_count()` says 8 in every case below, so an implementation that ignores `sched_getaffinity` gets 4, not 2 or 1."""
    monkeypatch.setattr(os, "cpu_count", lambda: 8)
    for allowed, expected in (({0}, 1), ({0, 1}, 2), (set(range(3)), 3), (set(range(16)), 4)):
        monkeypatch.setattr(os, "sched_getaffinity", lambda pid, a=allowed: a, raising=False)
        assert _cpus_to_load() == expected, allowed


def test_without_sched_getaffinity_the_cpu_count_is_used_and_never_less_than_one(monkeypatch):
    monkeypatch.delattr(os, "sched_getaffinity", raising=False)
    for count, expected in ((2, 2), (64, 4), (None, 1)):
        monkeypatch.setattr(os, "cpu_count", lambda c=count: c)
        assert _cpus_to_load() == expected, count


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
    # the floor itself, not a multiple of it: a CPU that makes the small run shorter than the floor would make the limit use
    # the floor, and the ratio check below is the real pin. (4x the floor needed a small run of 4 ms; this run is about 6 ms,
    # so a CPU 1.6x faster would have failed on a margin the harness does not need.)
    assert t_small >= timing.MIN_SMALL_S, t_small
    assert t_big / t_small >= 2 * timing.PER_SIZE * big / small, (t_small, t_big)
    assert timing.grows_faster_than_size(t_small, t_big, small, big)


@pytest.mark.perf
def test_the_harness_passes_a_linear_cost_while_every_cpu_is_busy(busy_cpus):
    small, big = 256 * 1024, 2048 * 1024
    t_small, t_big = _measured(lambda t: timing.block_seconds(_linear_stand_in, t), "a", small, big)
    assert t_small >= timing.MIN_SMALL_S, t_small  # the floor itself (see the quadratic test above)
    assert not timing.grows_faster_than_size(t_small, t_big, small, big), (t_small, t_big)
