"""The money end state of the crash tests, for the loop that reserves before a model call and settles after
(core-b; `crash_launcher.RESERVES`). Not a test file.

Every crash point has a STATIC expectation, written from the code path and never from a run: how many
reservations of the run are booked at the kill (`reserved`) and how many of those are settled (`settled`).
`reserve_spend` is one store call, `settle_spend` is one, and a hold is open between the two:

  before the first `reserve_spend`           no row, day total 0
  after `reserve_spend`, before `settle_spend`   one OPEN row per model call in flight (reserved_usd > 0),
                                              day total = the sum of the open holds' reserved_usd
  after `settle_spend`                        the row is SETTLED at the real cost (the model doubles price
                                              every call at 0), day total = the sum of the settled costs

A crash leaves an open hold OPEN: the tick steps of these tests do not expire it, and the documented
step-1 limit is "an open hold stays until expiry". After the restart, the tick and the signed retry: a run
that had a row is never run again, so its rows are exactly the ones of the kill (no re-reservation); a run
that had NO row at the kill is run once by the retry and ends with every call reserved AND settled. The day
total always equals what the rows say (it never exceeds their sum).

Limit of the seeding (see crash_launcher.py): the child widens `max_day_skew` and `min_expiry_age`, so none of
this says anything about the real day window or the 3600 s expiry floor.

PostgreSQL is read by plain SQL on a connection of the test's own (tables `spend_reservations`, `spend`);
the memory store by its own reservations dict and `spend_totals`.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from hadavin_sdk.models import now
from tests.triggers.crash_launcher import AGENT

# (status, reserved_usd, settled_usd) per reservation of the run, oldest first
Rows = list[tuple[str, Decimal, Decimal | None]]
Pair = tuple[int, int]  # (reservations booked, of which settled)


def pg_money(dsn: str, run_id: str) -> tuple[Rows, Decimal]:
    import psycopg

    with psycopg.connect(dsn) as db:
        found = db.execute(
            "SELECT status, reserved_usd, settled_usd FROM spend_reservations"
            " WHERE run_id = %s ORDER BY created_at, reservation_id",
            (run_id,),
        ).fetchall()
        total = db.execute("SELECT coalesce(sum(usd), 0) FROM spend WHERE agent_id = %s", (AGENT,))
        return [(r[0], r[1], r[2]) for r in found], total.fetchone()[0]


def memory_money(store, run_id: str) -> tuple[Rows, Decimal]:
    mine = sorted(
        (r for r in store._reservations.values() if r.run_id == run_id),  # noqa: SLF001 - the dict IS the table
        key=lambda r: (r.created_at, r.reservation_id),
    )
    days = {r.day for r in mine} | {now().date(), now().date() - timedelta(days=1)}
    total = sum((store.spend_totals(AGENT, d)[0] for d in days), Decimal(0))
    return [(r.status, r.reserved_usd, r.settled_usd) for r in mine], total


def calls_done(rows, number: int, edge: str) -> Pair:
    """(reserved, settled) at the kill from a table of calls: `rows` yields the call name of each step in
    order, `number` is the 1-based step of the point, `edge` "before" or "after" its call."""
    reserved = settled = 0
    for n, call in enumerate(rows, start=1):
        if n > number or (n == number and edge == "before"):
            break
        reserved += call == "store.reserve_spend"
        settled += call == "store.settle_spend"
    return reserved, settled


def assert_state(rows: Rows, total: Decimal, want: Pair, label: str) -> None:
    reserved, settled = want
    assert [r[0] for r in rows] == ["settled"] * settled + ["open"] * (reserved - settled), (
        label,
        want,
        rows,
    )
    booked = Decimal(0)
    for status, hold, cost in rows:
        assert hold > 0, (label, rows)  # the worst case of a call is never free
        if status == "settled":
            assert cost == 0, (label, rows)  # the double's reply costs nothing: the hold is replaced
            booked += cost
        else:
            assert cost is None, (label, rows)  # stuck-open: still the full worst case, NOT released
            booked += hold
    assert total == booked, (label, total, rows)  # no leak, no double booking, never above the rows


def assert_kill_state(rows: Rows, total: Decimal, allowed: set[Pair], label: str) -> Pair:
    """The state at the kill must be one of `allowed` (two only where a request thread races the loop)."""
    for want in sorted(allowed):
        try:
            assert_state(rows, total, want, label)
        except AssertionError:
            continue
        return want
    raise AssertionError((label, "money state matches none of", sorted(allowed), rows, total))


def assert_end_state(
    rows: Rows, total: Decimal, at_kill: Pair, row_at_kill: str | None, full: int, label: str
) -> None:
    """After restart, tick and the signed retry: no row at the kill means one fresh run (every call booked
    and settled); a row means nothing ran again, so the rows are the ones of the kill (an open hold stays
    open). At most `full` reservations either way."""
    want = (full, full) if row_at_kill is None else at_kill
    assert len(rows) <= full, (label, rows)
    assert_state(rows, total, want, label)
