"""Spend reservations (step F-store): a reference model and random sequences, over every registered store kind.

Written by a different agent than the builder, from the 13 numbered invariants of the interface text (section 1)
and the ten points of the meter contract, not from the code. The other spend files test one rule per case; this
file tests long mixed sequences, where a wrong counter only shows after several calls.

`Model` is the whole rule set in plain dicts. `_script(seed, n)` is a pure function of the seed: it draws `n`
calls and asks the model what each must return and what every counter must read afterwards. `_replay` makes
the same calls on a store and compares after EVERY call. Every assertion message starts with `seed=… op=…`;
to replay one case run `pytest "tests/contracts/test_store_spend_model.py" -k "seed<N>"`.

No dependency is added: the sequences come from `random.Random(seed)` with the seeds listed in `SEEDS`.
Nothing sleeps. The Protocol has no getter and no clock argument, so three helpers reach behind it, exactly as
tests/contracts/test_store_spend.py does: `_rows` reads the rows, `_older` moves a row's `created_at` back and
`_closed_earlier` its `closed_at`. Ages are whole thousands of seconds against bounds that lie 500 seconds
away from every one of them, and whole tens of days against bounds 5 days away, so the real run time of a test
(seconds) never decides a case.
"""

import random
import threading
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import Run, SpendReservation, now
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import NotFound, SpendCapExceeded, StaleState
from tests.contracts.kinds import KINDS

D = Decimal
# 30 fixed seeds; a failure names its seed and the index of the call
SEEDS = (
    3,
    7,
    11,
    19,
    23,
    42,
    57,
    64,
    101,
    137,
    211,
    256,
    313,
    404,
    512,
    613,
    777,
    919,
    1009,
    1234,
    2024,
    2718,
    3141,
    4096,
    5003,
    6007,
    7919,
    8191,
    9001,
    9973,
)
OPS = 200  # calls per sequence, on both store kinds
AGREE_SEEDS = SEEDS[:8]  # the seeds of the direct memory against PostgreSQL comparison
THREAD_SEED = 20261120
ROWS = 300  # reservations of the threaded case
THREADS = 4
WAIT_S = 120

AGENTS = ("agent-a", "agent-b", "agent-c")
DAY = date(now().year - 1, 1, 31)  # never today, never this month
EVE = DAY - timedelta(days=1)  # the same month
NEXT = DAY + timedelta(days=1)  # the first of February: another day AND another month
DAYS = (EVE, DAY, NEXT)
MICRO = D("0.000001")
BIG = D("1000000")
AMOUNTS = tuple(
    D(a) for a in ("0", "0.000001", "0.25", "0.999999", "1.00", "1.000001", "2.50", "3.00", "5.00")
)
ADDED = tuple(D(a) for a in ("0", "0.000001", "0.25", "1.00", "2.50"))
# a cap is the counter of that moment plus one of these: 0 is "already at the cap", the others are hit exactly
# by one of AMOUNTS and passed by the next one
DAY_ROOM = tuple(D(a) for a in ("0", "0.000001", "1.00", "2.50", "100"))
MONTH_ROOM = tuple(D(a) for a in ("0", "1.00", "3.00", "100"))
BAD = (  # not an amount by invariant 9
    D("-0.01"),
    D("0.0000000000001"),  # 13 decimal places
    D("NaN"),
    D("Infinity"),
    D(10**9),
    1.5,
    1,
    True,
    None,
    "1.00",
)
SHIFT_S = (1000, 2000, 3000)
EXPIRY_AGES = (0, 1500, 2500, 10**6)
SHIFT_DAYS = (10, 20)
PURGE_DAYS = (-1, 5, 15, 400)  # the bound is now minus that many days; -1 is a bound in the future
KIND_WEIGHTS = (("reserve", 40), ("settle", 30), ("add", 16), ("expire", 8), ("purge", 6))


# --- the reference model -------------------------------------------------------------------------------------------


def _is_amount(usd) -> bool:
    """Invariant 9: exactly a Decimal, finite, 0 <= x < 10**9, at most 12 decimal places."""
    return (
        type(usd) is D and usd.is_finite() and 0 <= usd < 10**9 and usd.as_tuple().exponent >= -12
    )


def _month(day):
    return (day.year, day.month)


class Model:
    """The rules, in dicts. Every method returns the outcome the store call must have."""

    def __init__(self, live_runs):
        self.day = defaultdict(D)  # (agent, day) -> booked
        self.month = defaultdict(D)  # (agent, (year, month)) -> booked
        self.cost = {r: D(0) for r in live_runs}  # only runs that exist
        self.rows = {}  # id -> dict(agent, day, run, reserved, settled, status, age_s, closed_days)
        self.added = defaultdict(D)  # add_spend, per (agent, day)
        self.purged = defaultdict(D)  # what purged rows had booked, per (agent, day)

    def _move(self, agent, day, by):
        self.day[(agent, day)] += by
        self.month[(agent, _month(day))] += by

    def reserve(self, rid, agent, day, usd, day_cap, month_cap, run):
        if not _is_amount(usd):
            return ("ValueError",)
        if rid in self.rows:
            return ("StaleState",)
        for which, booked, cap in (
            ("day", self.day[(agent, day)], day_cap),
            ("month", self.month[(agent, _month(day))], month_cap),
        ):
            if booked >= cap or booked + usd > cap:
                return ("SpendCapExceeded", which)
        self._move(agent, day, usd)
        self.rows[rid] = {
            "agent": agent,
            "day": day,
            "run": run,
            "reserved": usd,
            "settled": None,
            "status": "open",
            "age_s": 0,
            "closed_days": 0,
        }
        return ("ok", None)

    def settle(self, rid, actual):
        if not _is_amount(actual):
            return ("ValueError",)
        row = self.rows.get(rid)
        if row is None:
            return ("NotFound",)
        if row["status"] == "settled":
            return ("settled", False, self.view(rid))
        if row["status"] == "open":
            by, stays = actual - row["reserved"], actual
        else:  # expired: only upward
            by, stays = max(D(0), actual - row["reserved"]), max(actual, row["reserved"])
        self._move(row["agent"], row["day"], by)
        if row["run"] in self.cost:
            self.cost[row["run"]] += actual
        row.update(status="settled", settled=stays, closed_days=0)
        return ("settled", True, self.view(rid))

    def expire(self, shifts, older_than_s):
        for rid, secs in shifts:
            self.rows[rid]["age_s"] += secs
        count = 0
        for row in self.rows.values():
            if row["status"] == "open" and row["age_s"] >= older_than_s:
                row.update(status="expired", settled=row["reserved"], closed_days=0)
                count += 1
        return ("count", count)

    def purge(self, shifts, days):
        for rid, by in shifts:
            self.rows[rid]["closed_days"] += by
        gone = [
            rid
            for rid, row in self.rows.items()
            if row["status"] == "settled"
            and row["closed_days"] > days  # E11 M3: expired holds are KEPT
        ]
        for rid in gone:
            row = self.rows.pop(rid)
            self.purged[(row["agent"], row["day"])] += row["settled"]
        return ("count", len(gone))

    def add(self, agent, day, usd):
        self._move(agent, day, usd)
        self.added[(agent, day)] += usd
        return ("totals", self.totals(agent, day))

    def apply(self, op):
        return getattr(self, op[0])(*op[1:])

    def totals(self, agent, day):
        return (self.day[(agent, day)], self.month[(agent, _month(day))])

    def view(self, rid):
        row = self.rows[rid]
        return (
            rid,
            row["agent"],
            row["day"],
            row["run"],
            row["reserved"],
            row["settled"],
            row["status"],
        )

    def snapshot(self):
        return (
            tuple(self.totals(a, d) for a in AGENTS for d in DAYS),
            tuple(self.cost.values()),
            {rid: self.view(rid) for rid in self.rows},
        )


# --- behind the Protocol: rows and row ages ------------------------------------------------------------------------


def _is_memory(store):
    return hasattr(store, "_reservations")


def _rows(store) -> dict[str, SpendReservation]:
    if _is_memory(store):
        with store._lock:
            return dict(store._reservations)
    with store._lock:
        found = store._exec("SELECT * FROM spend_reservations").fetchall()
    return {r["reservation_id"]: SpendReservation.model_validate(r) for r in found}


def _shift(store, rid, column, by):
    """Move `created_at` or `closed_at` of one row back by a timedelta."""
    if _is_memory(store):
        with store._lock:
            row = store._reservations[rid]
            store._reservations[rid] = row.model_copy(update={column: getattr(row, column) - by})
        return
    query = {
        "created_at": "UPDATE spend_reservations SET created_at = created_at - %s WHERE reservation_id = %s",
        "closed_at": "UPDATE spend_reservations SET closed_at = closed_at - %s WHERE reservation_id = %s",
    }[column]
    # 0010 money guard (`spend_reservations_money_guard`) refuses a changed closed_at on a closed row for every login
    # but the SECURITY DEFINER function owner, and the store's login is a non-owner (it cannot ALTER TABLE): this
    # helper ages rows to exercise purge, so it goes through the owner DSN with the guard disabled around the UPDATE.
    import os

    from psycopg import connect
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    options = conninfo_to_dict(store._db.info.dsn).get("options")
    owner = make_conninfo(os.environ["HADAVIN_TEST_PG_DSN"], options=options)
    with store._lock, connect(owner, autocommit=False) as db:
        db.execute("ALTER TABLE spend_reservations DISABLE TRIGGER spend_reservations_money_guard")
        done = db.execute(query, (by, rid)).rowcount
        db.execute("ALTER TABLE spend_reservations ENABLE TRIGGER spend_reservations_money_guard")
    assert done == 1, f"row {rid!r} is not in the table"


def _older(store, rid, seconds):
    _shift(store, rid, "created_at", timedelta(seconds=seconds))


def _closed_earlier(store, rid, days):
    _shift(store, rid, "closed_at", timedelta(days=days))


def _view(row: SpendReservation):
    return (
        row.reservation_id,
        row.agent_id,
        row.day,
        row.run_id,
        row.reserved_usd,
        row.settled_usd,
        row.status,
    )


# --- the script: a pure function of the seed -----------------------------------------------------------------------


def _run_ids(seed):
    """Two runs that get a row and one that never does."""
    return tuple(f"run-{uuid.UUID(int=seed * 16 + k).hex}" for k in range(3))


def _script(seed, n):
    """`n` calls with, for each, the outcome and the state the model demands after it."""
    rng = random.Random(seed)  # noqa: S311 - a test sequence, not a secret
    runs = _run_ids(seed)
    model = Model(runs[:2])
    issued: list[str] = []  # every id ever passed to reserve, also the refused and the purged ones
    steps = []
    kinds, weights = zip(*KIND_WEIGHTS, strict=True)
    for i in range(n):
        kind = rng.choices(kinds, weights)[0]
        if kind == "reserve":
            agent, day = rng.choice(AGENTS), rng.choice(DAYS)
            if issued and rng.random() < 0.08:
                rid = rng.choice(
                    issued
                )  # a duplicate, or the id of a refused or purged reservation
            else:
                rid = f"res-{seed}-{i}"
            usd = rng.choice(BAD) if rng.random() < 0.05 else rng.choice(AMOUNTS)
            booked_day, booked_month = model.totals(agent, day)
            op = (
                "reserve",
                rid,
                agent,
                day,
                usd,
                booked_day + rng.choice(DAY_ROOM),
                booked_month + rng.choice(MONTH_ROOM),
                rng.choice((None, *runs)),
            )
            issued.append(rid)
        elif kind == "settle":
            if not issued or rng.random() < 0.12:
                rid, reserved = f"res-{seed}-unknown-{i}", D("1.00")
            else:
                rid = rng.choice(issued)
                reserved = model.rows[rid]["reserved"] if rid in model.rows else D("1.00")
            if rng.random() < 0.05:
                actual = rng.choice(BAD)
            else:
                actual = rng.choice(
                    (
                        D(0),
                        MICRO,
                        max(D(0), reserved - MICRO),
                        reserved / 2,
                        reserved,
                        reserved + MICRO,
                        reserved * 2 + D("0.25"),
                        D("5.00"),
                    )
                )
            op = ("settle", rid, actual)
        elif kind == "expire":
            open_ids = sorted(r for r, row in model.rows.items() if row["status"] == "open")
            picked = rng.sample(open_ids, min(len(open_ids), rng.randint(0, 3)))
            shifts = tuple((rid, rng.choice(SHIFT_S)) for rid in picked)
            op = ("expire", shifts, rng.choice(EXPIRY_AGES))
        elif kind == "purge":
            closed = sorted(r for r, row in model.rows.items() if row["status"] != "open")
            picked = rng.sample(closed, min(len(closed), rng.randint(0, 3)))
            shifts = tuple((rid, rng.choice(SHIFT_DAYS)) for rid in picked)
            op = ("purge", shifts, rng.choice(PURGE_DAYS))
        else:
            op = ("add", rng.choice(AGENTS), rng.choice(DAYS), rng.choice(ADDED))
        want = model.apply(op)
        steps.append((op, want, model.snapshot()))
    return runs, steps, model


# --- the same calls on a store -------------------------------------------------------------------------------------


def _create_runs(store, runs):
    for run_id in runs[:2]:
        store.create_run(
            Run(
                run_id=run_id,
                agent_id=AGENTS[0],
                principal_id="p",
                trigger_kind="event",
                trigger_ref="t",
            )
        )


def _apply(store, op):
    """Make one call; the result or the exception class, in the model's words."""
    kind = op[0]
    try:
        if kind == "reserve":
            _, rid, agent, day, usd, day_cap, month_cap, run = op
            return (
                "ok",
                store.reserve_spend(
                    rid, agent, day, usd, day_cap=day_cap, month_cap=month_cap, run_id=run
                ),
            )
        if kind == "settle":
            row, applied = store.settle_spend(op[1], op[2])
            return ("settled", applied, _view(row))
        if kind == "expire":
            for rid, secs in op[1]:
                _older(store, rid, secs)
            return ("count", store.expire_spend_reservations(op[2]))
        if kind == "purge":
            for rid, days in op[1]:
                _closed_earlier(store, rid, days)
            return ("count", store.purge_spend_reservations(now() - timedelta(days=op[2])))
        return ("totals", tuple(store.add_spend(op[1], op[2], op[3])))
    except SpendCapExceeded as refused:
        return ("SpendCapExceeded", refused.which)
    except (StaleState, NotFound, ValueError) as raised:
        return (type(raised).__name__,)
    except Exception as raised:  # noqa: BLE001 - reported with its seed and call by the caller
        return ("unexpected", type(raised).__name__, str(raised)[:200])


def _state(store, runs):
    """What the store says after a call: the totals of every (agent, day), the run costs, the rows."""
    rows = _rows(store)
    for row in rows.values():
        assert (row.status == "open") == (row.closed_at is None), row
    return (
        tuple(tuple(store.spend_totals(a, d)) for a in AGENTS for d in DAYS),
        tuple(store.get_run(r).cost_usd for r in runs[:2]),
        {rid: _view(row) for rid, row in rows.items()},
    )


def _diff(got, want):
    """The parts of two states that differ, short enough to read."""
    out = []
    cells = [(a, d.isoformat()) for a in AGENTS for d in DAYS]
    for cell, g, w in zip(cells, got[0], want[0], strict=True):
        if g != w:
            out.append(f"totals{cell}: store={g} model={w}")
    if got[1] != want[1]:
        out.append(f"run costs: store={got[1]} model={want[1]}")
    for rid in sorted(set(got[2]) | set(want[2])):
        if got[2].get(rid) != want[2].get(rid):
            out.append(f"row {rid}: store={got[2].get(rid)} model={want[2].get(rid)}")
    return "; ".join(out)


def _replay(store, seed, runs, steps):
    """Every call of the script on the store, compared with the model after each one."""
    _create_runs(store, runs)
    for i, (op, want, want_state) in enumerate(steps):
        tag = f"seed={seed} op={i} {op!r}"
        got = _apply(store, op)
        assert got == want, f"{tag}: outcome store={got!r} model={want!r}"
        got_state = _state(store, runs)
        assert got_state == want_state, f"{tag}: after the call: {_diff(got_state, want_state)}"


def _trace(store, seed, runs, steps):
    """The calls of the script on the store with no model in the loop: what came back and what stood after."""
    _create_runs(store, runs)
    return [(_apply(store, op), _state(store, runs)) for op, _, _ in steps]


def _conserved(store, added, purged, tag):
    """Counter conservation: for every agent and day, the day counter is exactly the sum over the rows (the
    reserved amount of an open row, the settled amount of a closed one) plus every add_spend amount. A purged
    row is gone from the store, so what it had booked comes from the ledger of the caller."""
    booked = defaultdict(D)
    for row in _rows(store).values():
        assert row.agent_id in AGENTS and row.day in DAYS, f"{tag}: a row nobody reserved: {row}"
        booked[(row.agent_id, row.day)] += (
            row.reserved_usd if row.status == "open" else row.settled_usd
        )
    for a in AGENTS:
        for d in DAYS:
            want = booked[(a, d)] + added[(a, d)] + purged[(a, d)]
            month = sum(
                (
                    booked[(a, x)] + added[(a, x)] + purged[(a, x)]
                    for x in DAYS
                    if _month(x) == _month(d)
                ),
                D(0),
            )
            got = tuple(store.spend_totals(a, d))
            assert got == (want, month), (
                f"{tag}: conservation {a} {d}: counters={got} rows+added+purged={(want, month)}"
            )


# --- 1 to 3: random sequences against the model, and conservation --------------------------------------------------


def test_the_script_is_a_pure_function_of_the_seed_and_covers_every_outcome():
    """Guards the tests below: the same seed gives the same calls, and the 30 scripts together reach every
    outcome the model can give, so a store cannot pass because a rule was never drawn."""
    seen = defaultdict(int)
    for seed in SEEDS:
        runs, steps, _ = _script(seed, OPS)
        again = _script(seed, OPS)
        assert repr((runs, steps)) == repr(again[:2]), f"seed={seed}: the script is not repeatable"
        assert len(steps) >= 200
        for op, want, _ in steps:
            key = (
                (op[0], *want[:2])
                if want[0] in ("SpendCapExceeded", "settled")
                else (op[0], want[0])
            )
            if op[0] in ("expire", "purge"):
                key = (op[0], "some" if want[1] else "none")
            seen[key] += 1
    needed = {
        ("reserve", "ok"),
        ("reserve", "SpendCapExceeded", "day"),
        ("reserve", "SpendCapExceeded", "month"),
        ("reserve", "StaleState"),
        ("reserve", "ValueError"),
        ("settle", "settled", True),
        ("settle", "settled", False),
        ("settle", "NotFound"),
        ("settle", "ValueError"),
        ("expire", "some"),
        ("expire", "none"),
        ("purge", "some"),
        ("purge", "none"),
        ("add", "totals"),
    }
    assert needed <= set(seen), sorted(needed - set(seen))
    assert min(seen[k] for k in needed) >= 30, dict(seen)


@pytest.mark.parametrize("seed", SEEDS, ids=[f"seed{s}" for s in SEEDS])
def test_a_random_sequence_matches_the_model_after_every_call(store, seed):
    """Invariants 2 to 7, 9, 12 and 13 at once: 200 mixed calls, the store compared with the model after each
    (the totals of every agent and day, the run costs, the rows, what the call returned or raised), then
    counter conservation over what is left."""
    runs, steps, model = _script(seed, OPS)
    _replay(store, seed, runs, steps)
    _conserved(store, model.added, model.purged, f"seed={seed} end")
    with pytest.raises(NotFound):  # the run that never got a row was not created by a settle
        store.get_run(runs[2])


# --- 4: the two stores agree ----------------------------------------------------------------------------------------


@pytest.fixture
def both(request, tmp_path):
    """A memory store and a PostgreSQL store (its own fresh schema); skips without HADAVIN_TEST_PG_DSN."""
    made = KINDS["store"]["postgres"](tmp_path)
    postgres = next(made)
    request.addfinalizer(lambda: next(made, None))
    return MemoryStore(), postgres


@pytest.mark.parametrize("seed", AGREE_SEEDS, ids=[f"seed{s}" for s in AGREE_SEEDS])
def test_the_same_seed_gives_the_same_outcomes_on_memory_and_postgres(both, seed):
    """No model in the comparison: the two traces (what every call returned or raised, and every counter, run
    cost and row after it) are compared with each other."""
    memory, postgres = both
    runs, steps, _ = _script(seed, OPS)
    on_memory = _trace(memory, seed, runs, steps)
    on_postgres = _trace(postgres, seed, runs, steps)
    for i, (m, p) in enumerate(zip(on_memory, on_postgres, strict=True)):
        tag = f"seed={seed} op={i} {steps[i][0]!r}"
        assert m[0] == p[0], f"{tag}: outcome memory={m[0]!r} postgres={p[0]!r}"
        assert m[1] == p[1], (
            f"{tag}: after the call (store=memory, model=postgres): {_diff(m[1], p[1])}"
        )


# --- 5a: 300 reservations settled in random order by 4 threads ------------------------------------------------------


def _peers(store, n):
    """`n` callers: the one memory store for all of them, or `n` PostgreSQL connections (the store's own and
    `n - 1` new ones of the same login and schema). Returns the callers and those to close."""
    if _is_memory(store):
        return [store] * n, []
    from hadavin_sdk.store import postgres as postgres_mod

    dsn = store._db.info.dsn
    extra = [postgres_mod.PostgresStore(postgres_mod.connect(dsn)) for _ in range(n - 1)]
    return [store, *extra], extra


def test_300_reservations_settled_in_random_order_by_4_callers_end_at_the_model_totals(store):
    """Every reservation is settled TWICE, with two different amounts, by callers that race; a third of the
    rows expired first. Exactly one of the two settles applies; the model is fed the one that did, and the
    totals, the run costs and conservation must then be exact."""
    rng = random.Random(THREAD_SEED)  # noqa: S311
    runs = _run_ids(THREAD_SEED)
    _create_runs(store, runs)
    model = Model(runs[:2])
    amounts = {}
    for i in range(ROWS):
        rid = f"res-thr-{i}"
        op = (rid, rng.choice(AGENTS), rng.choice(DAYS), rng.choice(AMOUNTS[1:]), BIG, BIG)
        run = rng.choice((None, *runs))
        store.reserve_spend(*op[:4], day_cap=BIG, month_cap=BIG, run_id=run)
        assert model.reserve(*op, run) == ("ok", None)
        low, high = op[3] / 4, op[3] * 3 + MICRO
        amounts[rid] = rng.choice(((low, high), (high, low), (op[3], D(0)), (D(0), high)))
    stale = [f"res-thr-{i}" for i in range(0, ROWS, 3)]
    for rid in stale:
        _older(store, rid, 5000)
    assert store.expire_spend_reservations(2500) == len(stale)
    assert model.expire(tuple((rid, 5000) for rid in stale), 2500) == ("count", len(stale))

    jobs = [(rid, amount) for rid, pair in amounts.items() for amount in pair]
    rng.shuffle(jobs)
    callers, extra = _peers(store, THREADS)
    try:
        if extra:
            pids = {s._db.execute("SELECT pg_backend_pid()").fetchone()[0] for s in callers}
            assert len(pids) == THREADS
            assert {s._db.execute("SELECT current_schema()").fetchone()[0] for s in callers} == {
                store._schema
            }
        start = threading.Barrier(THREADS)
        results: list[list] = [[] for _ in range(THREADS)]

        def work(k):
            start.wait(WAIT_S)
            for rid, amount in jobs[k::THREADS]:
                try:
                    row, applied = callers[k].settle_spend(rid, amount)
                    results[k].append((rid, amount, applied, _view(row)))
                except Exception as raised:  # noqa: BLE001 - asserted below, in the main thread
                    results[k].append((rid, amount, None, repr(raised)))

        threads = [threading.Thread(target=work, args=(k,)) for k in range(THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(WAIT_S)
        assert not any(t.is_alive() for t in threads)
    finally:
        for s in extra:
            s._db.close()

    done = [r for per_thread in results for r in per_thread]
    assert len(done) == 2 * ROWS
    assert [r for r in done if r[2] is None] == []
    winners = {}
    for rid, amount, applied, _ in done:
        if applied:
            assert rid not in winners, f"{rid}: two settles applied"
            winners[rid] = amount
    assert len(winners) == ROWS
    for rid, amount in winners.items():
        assert model.settle(rid, amount)[1] is True
    for rid, _, _, view in done:  # the winner and the loser both got the one stored row
        assert view == model.view(rid), f"{rid}: returned {view}, model {model.view(rid)}"
    got, want = _state(store, runs), model.snapshot()
    assert got == want, _diff(got, want)
    _conserved(store, model.added, model.purged, "threads")


# --- 5b: 12 decimal places through settle ---------------------------------------------------------------------------

TWELVE = [  # (reserved, expire first, settled with, what stays booked)
    ("1.00", False, "0.123456789012", "0.123456789012"),
    ("0.000000000002", False, "0.000000000001", "0.000000000001"),
    ("1.00", False, "999999999.999999999999", "999999999.999999999999"),
    ("0.333333333333", False, "0.333333333334", "0.333333333334"),
    ("0.777777777777", True, "0.777777777778", "0.777777777778"),  # one pico-dollar up after expiry
    ("0.777777777777", True, "0.777777777776", "0.777777777777"),  # one down: the booking stays
]


@pytest.mark.parametrize("reserved,expire,actual,stays", TWELVE, ids=[t[2] for t in TWELVE])
def test_a_settle_amount_with_12_decimal_places_is_booked_and_returned_unrounded(
    store, reserved, expire, actual, stays
):
    runs = _run_ids(12)
    _create_runs(store, runs)
    store.add_spend(AGENTS[0], DAY, D("0.111111111111"))  # the counter starts off the grid too
    store.reserve_spend(
        "res-12",
        AGENTS[0],
        DAY,
        D(reserved),
        day_cap=D(10**10),
        month_cap=D(10**10),
        run_id=runs[0],
    )
    if expire:
        assert store.expire_spend_reservations(0) == 1
    row, applied = store.settle_spend("res-12", D(actual))
    assert applied is True
    assert row.settled_usd == D(stays) and row.reserved_usd == D(reserved)
    assert str(row.settled_usd.normalize()) == str(D(stays).normalize())
    again, applied = store.settle_spend("res-12", D("0.5"))  # another amount: changes nothing
    assert applied is False and again.settled_usd == D(stays)
    assert _rows(store)["res-12"].settled_usd == D(stays)
    want = D("0.111111111111") + D(stays)
    assert tuple(store.spend_totals(AGENTS[0], DAY)) == (want, want)
    assert store.get_run(runs[0]).cost_usd == D(
        actual
    )  # the real amount, also after expiry (invariant 13)


def test_300_pico_dollar_settles_add_up_to_the_exact_sum_on_the_counters_and_the_run(store):
    """Nothing is rounded on the way: 300 amounts with 12 decimal places, summed three ways."""
    rng = random.Random(THREAD_SEED + 1)  # noqa: S311
    runs = _run_ids(13)
    _create_runs(store, runs)
    total = D(0)
    for i in range(ROWS):
        actual = D(rng.randrange(1, 10**15)).scaleb(-12)
        store.reserve_spend(
            f"res-p-{i}",
            AGENTS[1],
            NEXT,
            D("1.00"),
            day_cap=BIG * BIG,
            month_cap=BIG * BIG,
            run_id=runs[1],
        )
        row, applied = store.settle_spend(f"res-p-{i}", actual)
        assert applied and row.settled_usd == actual, f"row {i}: {row.settled_usd} != {actual}"
        total += actual
    assert tuple(store.spend_totals(AGENTS[1], NEXT)) == (total, total)
    assert store.get_run(runs[1]).cost_usd == total
    assert sum((r.settled_usd for r in _rows(store).values()), D(0)) == total


# --- 5c: hostile reservation ids ------------------------------------------------------------------------------------

HOSTILE_IDS = {
    "200_characters": "r" * 200,
    "single_quote": "res-'; DROP TABLE spend_reservations; --",
    "double_quote": 'res-"quoted"',
    "backslash": "res-\\N-\\\\-\\x00",
    "nul": "res-\x00-after",
    "newline": "res-\nline two\r\n",
    "all_of_them": "'\"\\\x00\n" * 40,
}
STORED, REFUSED = "stored and found again", "refused with ValueError"


def _id_outcome(store, rid):
    """Reserve and settle under a hostile id. STORED when the row is booked and the same id finds it again,
    REFUSED when reserve raises ValueError and books nothing, else the name of what was raised."""
    amount, actual = D("1.25"), D("0.75")
    try:
        store.reserve_spend(rid, AGENTS[2], DAY, amount, day_cap=BIG, month_cap=BIG)
    except ValueError:
        assert tuple(store.spend_totals(AGENTS[2], DAY)) == (D(0), D(0))
        assert _rows(store) == {}
        return REFUSED
    except Exception as raised:  # noqa: BLE001 - the outcome under test
        return f"reserve raised {type(raised).__module__}.{type(raised).__name__}"
    try:
        assert set(_rows(store)) == {rid}
        with pytest.raises(StaleState):
            store.reserve_spend(rid, AGENTS[2], DAY, amount, day_cap=BIG, month_cap=BIG)
        with pytest.raises(NotFound):
            store.settle_spend(
                rid[:-1] + ("0" if rid[-1] != "0" else "1"), actual
            )  # same length, unknown
        row, applied = store.settle_spend(rid, actual)
        assert applied is True and row.reservation_id == rid and row.settled_usd == actual
        row, applied = store.settle_spend(rid, amount)
        assert applied is False and row.reservation_id == rid and row.settled_usd == actual
        assert tuple(store.spend_totals(AGENTS[2], DAY)) == (actual, actual)
        assert store.purge_spend_reservations(now() + timedelta(days=1)) == 1
        assert _rows(store) == {}
    except Exception as raised:  # noqa: BLE001 - the outcome under test
        return f"after reserve: {type(raised).__module__}.{type(raised).__name__}"
    return STORED


@pytest.mark.parametrize("name", sorted(HOSTILE_IDS))
def test_a_hostile_reservation_id_is_stored_and_found_again_or_refused_with_value_error(
    store, name
):
    outcome = _id_outcome(store, HOSTILE_IDS[name])
    assert outcome in (STORED, REFUSED), f"{name}: {outcome}"
    # whatever happened, the store still works and nothing is left booked that the caller cannot settle
    store.reserve_spend("res-after", AGENTS[2], NEXT, D("1.00"), day_cap=BIG, month_cap=BIG)
    assert store.settle_spend("res-after", D("0.50"))[1] is True


@pytest.mark.parametrize("name", sorted(HOSTILE_IDS))
def test_a_hostile_reservation_id_has_the_same_outcome_on_memory_and_postgres(both, name):
    memory, postgres = both
    on_memory = _id_outcome(memory, HOSTILE_IDS[name])
    on_postgres = _id_outcome(postgres, HOSTILE_IDS[name])
    assert on_memory == on_postgres, f"{name}: memory={on_memory!r} postgres={on_postgres!r}"
