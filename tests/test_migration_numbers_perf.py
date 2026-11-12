"""The timing tests of `store/migration_numbers.py` (marked `perf`; CI runs them in their own step). They live in a file
of their own so that the mutant run of `tests/migration_numbers_mutants.py` (whose unmutated baseline must pass) does not
depend on how busy the machine is: no mutant of that list is killed by a timing test."""

from __future__ import annotations

import statistics
import time

import pytest

from tests.fixtures import timing


@pytest.fixture
def mn():
    import hadavin_sdk.store.migration_numbers as module

    return module


def _median_time(fn, text: str) -> float:
    runs = []
    for _ in range(3):
        t0 = time.perf_counter()
        fn(text)
        runs.append(time.perf_counter() - t0)
    return statistics.median(runs)


@pytest.mark.perf
def test_lexer_is_linear(mn):
    small, big = 16 * 1024, 256 * 1024
    units = ["'", '"', "$a$", "/*", "--", "E'\\", ";", "$a$ x ", "a$"]
    slow = [
        (fn.__name__, unit)
        for fn in (mn.lex, mn.refused_statements)
        for unit in units
        if timing.is_superlinear(lambda t, f=fn: _median_time(f, t), unit, small, big)
    ]
    assert not slow, slow


@pytest.mark.perf
def test_the_timing_harness_flags_a_quadratic_stand_in():
    def quadratic(t: str) -> float:
        return _median_time(lambda s: sum(s.count("a", 0, i) for i in range(0, len(s), 64)), t)

    assert timing.is_superlinear(quadratic, "a", 16 * 1024, 256 * 1024), (
        "a quadratic function must be flagged"
    )
