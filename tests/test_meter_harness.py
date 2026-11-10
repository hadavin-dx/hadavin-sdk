"""The parallel schedule of ``tests/meter_support.py``, tested on its own with a stub meter (a plain pair of
functions over a counter, no Limits and no store). It must be able to tell a meter that checks and then books
separately (every caller is admitted: the race the real meter has today) from one that books at reserve time
(only as many callers as the cap allows). Without this control a parallel test that passes could mean "the
schedule never overlapped the callers" instead of "the meter is safe".
"""

from __future__ import annotations

import threading

from tests.meter_support import CALLERS, run_parallel

CAP_CALLS = 3  # the stub meter admits this many calls


class StubMeter:
    """A counter with a cap of CAP_CALLS calls. ``check`` and ``book`` are separate steps, as in Limits."""

    def __init__(self) -> None:
        self.booked = 0
        self.gate = threading.Lock()

    def check(self) -> bool:
        return self.booked < CAP_CALLS

    def book(self) -> None:
        with self.gate:
            self.booked += 1

    def check_and_book(self) -> bool:
        with self.gate:
            if self.booked >= CAP_CALLS:
                return False
            self.booked += 1
            return True


def test_the_schedule_forces_the_worst_interleaving_on_a_check_then_book_meter():
    meter = StubMeter()
    admitted = run_parallel(meter.check, meter.book)
    assert admitted == CALLERS, (
        f"only {admitted} of {CALLERS} callers were admitted: the schedule did not hold every caller "
        "at the check until all had decided"
    )
    assert meter.booked == CALLERS, "an admitted caller did not book"


def test_the_schedule_admits_exactly_the_cap_on_a_meter_that_books_at_reserve_time():
    meter = StubMeter()
    admitted = run_parallel(meter.check_and_book, lambda: None)
    assert admitted == CAP_CALLS, f"admitted {admitted} of {CALLERS}, expected {CAP_CALLS}"
    assert meter.booked == CAP_CALLS, f"booked {meter.booked}, expected {CAP_CALLS}"


def test_run_parallel_never_books_for_the_meter():
    """settle is the only place a booking happens: with a no-op settle, nothing is booked by the harness."""
    meter = StubMeter()
    run_parallel(meter.check, lambda: None)
    assert meter.booked == 0, "run_parallel booked a charge itself"
