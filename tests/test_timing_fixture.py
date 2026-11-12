"""The shared linear-time rule (`tests/fixtures/timing.py`) itself, with made-up timings: no clock, so a loaded machine
cannot change the result. The tests that use it with a real clock are marked `perf`."""

from __future__ import annotations

import multiprocessing
import os

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
    # from 0.1 s on the small run up: the big run is 16x, the limit 12x. (Below the 4 ms floor on the small run nothing is
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


def test_the_fastest_run_ignores_one_inflated_small_sample():
    """A busy moment that slows ONE small run must not hide a real quadratic: noise only adds time, so the best of the runs
    stands. With a single run per size (`repeats=1`) the same inflated sample hides it, which shows the test can fail."""

    def measure_with_one_slow_first_small_run():
        calls = {"small": 0}

        def measure(text: str) -> float:
            t = 1e-7 * len(text) ** 2
            if len(text) == SMALL:
                calls["small"] += 1
                if calls["small"] == 1:
                    return t * 50  # the first small run lands on a busy moment
            return t

        return measure

    assert timing.is_superlinear(measure_with_one_slow_first_small_run(), "a", SMALL, BIG)
    assert not timing.is_superlinear(
        measure_with_one_slow_first_small_run(), "a", SMALL, BIG, repeats=1
    )


def test_the_best_of_is_the_minimum():
    assert timing.best_of([0.5, 0.2, 9.0]) == 0.2


def _spin() -> None:
    while True:
        pass


@pytest.fixture
def busy_cpus():
    """One busy-loop process per CPU for the length of the test, always stopped afterwards."""
    workers = [
        multiprocessing.get_context("spawn").Process(target=_spin, daemon=True)
        for _ in range(os.cpu_count() or 1)
    ]
    try:
        for w in workers:
            w.start()
        yield
    finally:
        for w in workers:
            w.terminate()
        for w in workers:
            w.join(timeout=10)


def _linear_stand_in(text: str) -> int:
    return sum(ord(c) for c in text)


@pytest.mark.perf
def test_the_harness_flags_a_real_quadratic_while_every_cpu_is_busy(busy_cpus):
    assert timing.is_superlinear(
        lambda t: timing.cpu_seconds(timing.quadratic_stand_in, t), "a", 16 * 1024, 128 * 1024
    )


@pytest.mark.perf
def test_the_harness_passes_a_linear_cost_while_every_cpu_is_busy(busy_cpus):
    assert not timing.is_superlinear(
        lambda t: timing.cpu_seconds(_linear_stand_in, t), "a", 256 * 1024, 2048 * 1024
    )
