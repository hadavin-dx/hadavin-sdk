"""The shared linear-time rule (`tests/fixtures/timing.py`) itself, with made-up timings: no clock, so a loaded machine
cannot change the result. The tests that use it with a real clock are marked `perf`."""

from __future__ import annotations

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
