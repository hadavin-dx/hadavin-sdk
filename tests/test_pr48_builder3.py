"""Money-path behaviour of the spend counters and the billing marks: the day-row lock of a take-back under real
concurrency, a seeded parity fuzz (memory vs Postgres: reserve, settle, release across a month boundary), the month
clamp on a drifted database, the read-only drift check, the per-mark settlement of a failed or successful fallback, the
PostgresStore constructor limits and spend settings, the retry/backoff of a spend transaction, and the maintenance
connect guard (no host, port, user, account or token ever leaves)."""

from __future__ import annotations

import datetime
import functools
import math
import random
import threading
import time
from decimal import Decimal

import pytest

from hadavin_sdk.store.memory import MemoryStore
from tests.contracts.kinds.store_postgres import pg_schema
from tests.helpers_money import (
    ROUTES,
    FreshRaises,
    Stub,
    _fallback_reply,
    _limits,
    _pg_store,
    _unknown_total,
)

D = Decimal
DAY = datetime.date(2026, 3, 9)


def _blocked_by(watch, pid: int, deadline_s: float = 30.0) -> None:
    """Wait (polling the server, never a fixed sleep) until some backend waits on a lock held by ``pid``."""
    end = time.monotonic() + deadline_s
    while True:
        n = watch.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' "
            "AND %s = ANY(pg_blocking_pids(pid))",
            (pid,),
        ).fetchone()[0]
        if n:
            return
        assert time.monotonic() < end, "the take-back never waited on the row lock"
        time.sleep(0.01)


def _all_queued_behind(watch, pid: int, n: int, deadline_s: float = 60.0) -> None:
    """Wait (polling the server, deadline kept) until ``n`` backends are blocked by the transaction of ``pid``, directly
    or through the queue behind it (``pg_blocking_pids`` chain). Only the holder's own waiters count, never other
    sessions of the same database."""
    end = time.monotonic() + deadline_s
    while True:
        queued = watch.execute(
            "WITH RECURSIVE w(pid) AS (SELECT pid FROM pg_stat_activity WHERE %s = ANY(pg_blocking_pids(pid)) "
            "UNION SELECT a.pid FROM pg_stat_activity a JOIN w ON w.pid = ANY(pg_blocking_pids(a.pid))) "
            "SELECT count(*) FROM w",
            (pid,),
        ).fetchone()[0]
        if queued >= n:
            return
        assert time.monotonic() < end, (
            f"only {queued} of {n} take-backs queued behind the row holder"
        )
        time.sleep(0.01)


# --- a take-back reads the day row under FOR UPDATE ------------------------------------------------------------


def test_a_take_back_waits_for_a_concurrent_writer_and_reads_its_committed_total():
    # Deterministic: another transaction has lowered the day to 0.50 and holds the row. A take-back of 1.00 must wait
    # and then take only the 0.50 that is left. Without FOR UPDATE it reads the old 1.00, its UPDATE waits, and after
    # the commit it writes 0.50 - 1.00 = -0.50 (the day goes negative and month no longer equals the sum of its days).
    psycopg = pytest.importorskip("psycopg")
    for dsn in pg_schema():
        store = _pg_store(dsn, LOCK_TIMEOUT_MS=30000)
        try:
            store.settle_spend([("a", DAY, D("1.00"))])
            with (
                psycopg.connect(dsn) as ext,
                psycopg.connect(dsn, autocommit=True) as watch,
            ):
                ext.execute("UPDATE spend SET usd = 0.50 WHERE agent_id = 'a' AND day = %s", (DAY,))
                ext.execute(
                    "UPDATE spend_month SET usd = 0.50 WHERE agent_id = 'a' AND month = %s",
                    (DAY.replace(day=1),),
                )
                errors: list[BaseException] = []

                def take_back(store=store, errors=errors):
                    try:
                        store.settle_spend([("a", DAY, D("-1.00"))])
                    except BaseException as e:  # noqa: BLE001 - reported below
                        errors.append(e)

                t = threading.Thread(target=take_back)
                t.start()
                try:
                    _blocked_by(watch, ext.info.backend_pid)
                finally:
                    ext.commit()
                    t.join(30)
            assert not t.is_alive() and not errors, errors
            assert store.spend_totals("a", DAY) == (D("0"), D("0"))
        finally:
            store.close()


def test_eight_concurrent_take_backs_of_the_whole_day_leave_zero_not_minus_seven():
    # Eight take-backs of the whole day queue behind a transaction that holds the day row, then all run at once.
    # With the row lock each reads the total left by the one before (1.00, then 0): the day ends at 0. Without it
    # every one reads 1.00 before the holder commits and the queued UPDATEs end at 1.00 - 8 x 1.00 = -7.00.
    psycopg = pytest.importorskip("psycopg")
    for dsn in pg_schema():
        store = _pg_store(dsn, LOCK_TIMEOUT_MS=30000)
        try:
            store.settle_spend([("a", DAY, D("1.00"))])
            store.settle_spend([("a", DAY.replace(day=2), D("3.00"))])  # another day, same month
            errors: list[BaseException] = []

            def take_back(store=store, errors=errors):
                try:
                    store.settle_spend([("a", DAY, D("-1.00"))])
                except BaseException as exc:  # noqa: BLE001 - reported below
                    errors.append(exc)

            with (
                psycopg.connect(dsn) as holder,
                psycopg.connect(dsn, autocommit=True) as watch,
            ):
                holder.execute(
                    "SELECT usd FROM spend WHERE agent_id = 'a' AND day = %s FOR UPDATE", (DAY,)
                )
                ts = [threading.Thread(target=take_back) for _ in range(8)]
                for t in ts:
                    t.start()
                try:
                    _all_queued_behind(watch, holder.info.backend_pid, 8)
                finally:
                    holder.commit()
                    for t in ts:
                        t.join(60)
            assert not errors, [type(x).__name__ for x in errors]
            assert store.spend_totals("a", DAY) == (D("0"), D("3.00"))
        finally:
            store.close()


# --- the month clamp on an already drifted database ---------------------------------------------------------


def test_a_take_back_on_a_drifted_month_clamps_the_month_at_zero_and_the_drift_check_sees_it():
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.migrate import spend_drift

    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            store.settle_spend([("a", DAY, D("1.00"))])
            store.settle_spend([("b", DAY, D("2.00"))])  # a clean agent, never reported
            with psycopg.connect(
                dsn, autocommit=True
            ) as db:  # drift left by an older release or raw SQL
                db.execute(
                    "UPDATE spend_month SET usd = 0.50 WHERE agent_id = 'a' AND month = %s",
                    (DAY.replace(day=1),),
                )
                before = db.execute("SELECT agent_id, usd FROM spend_month ORDER BY 1").fetchall()
            assert spend_drift(dsn) == [("a", DAY.replace(day=1), D("0.50"), D("1.00"))]
            with psycopg.connect(dsn, autocommit=True) as db:  # the check wrote nothing
                assert (
                    db.execute("SELECT agent_id, usd FROM spend_month ORDER BY 1").fetchall()
                    == before
                )
            store.settle_spend([("a", DAY, D("-1.00"))])
            assert store.spend_totals("a", DAY) == (
                D("0"),
                D("0"),
            )  # month 0.50 - 1.00 clamps to 0, not -0.50
            assert spend_drift(dsn) == []
        finally:
            store.close()


def test_the_drift_check_fails_closed_by_class_name_only():
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.migrate import spend_drift
    from hadavin_sdk.store.protocol import StoreUnavailable

    for dsn in pg_schema(migrated=False):  # no tables: the query fails, by class name only
        with pytest.raises(StoreUnavailable, match="UndefinedTable") as e:
            spend_drift(dsn)
        assert "spend" not in str(e.value).replace("spend-drift", "")
    bad, host = _bad_dsn()
    with pytest.raises(StoreUnavailable, match=r"^store postgres: cannot connect \(\w+\)$") as e:
        spend_drift(bad)
    assert "leaky" not in str(e.value) and not (host and host in str(e.value))
    assert psycopg  # the driver is present for the cases above


def test_the_spend_drift_cli_reports_and_exits_one(cfg_dir, monkeypatch, capsys):
    import yaml

    from hadavin_sdk import cli

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_CONFIG_DIR", str(cfg_dir))
    monkeypatch.delenv("HADAVIN_MAINTENANCE_DSN", raising=False)
    assert cli.main(["spend-drift"]) == 2
    monkeypatch.setenv("HADAVIN_MAINTENANCE_DSN", "dsn")
    rows = [("a", DAY.replace(day=1), D("0.50"), D("1.00"))]
    monkeypatch.setattr("hadavin_sdk.store.migrate.spend_drift", lambda dsn, **kw: rows)
    assert cli.main(["spend-drift"]) == 1
    out = capsys.readouterr().out
    assert "DRIFT: a 2026-03: month 0.50 below the sum of its days 1.00" in out
    monkeypatch.setattr("hadavin_sdk.store.migrate.spend_drift", lambda dsn, **kw: [])
    assert cli.main(["spend-drift"]) == 0 and "no drift" in capsys.readouterr().out


# --- a committed, seeded parity fuzz across a month boundary --------------------------------------------

FUZZ_DAYS = [
    datetime.date(2026, 10, 30),
    datetime.date(2026, 10, 31),
    datetime.date(2026, 11, 1),
    datetime.date(2026, 11, 2),
]


def _pg_view(pg, keys):
    """Every day and month row of ``keys`` in ONE query (the fuzz checks after every operation)."""
    with pg._lock:
        rows = pg._exec(
            "SELECT agent_id, 'd' AS k, day AS at, usd FROM spend WHERE agent_id = ANY(%s) "
            "UNION ALL SELECT agent_id, 'm', month, usd FROM spend_month WHERE agent_id = ANY(%s)",
            (keys, keys),
        ).fetchall()
    return {(r["agent_id"], r["k"], r["at"]): D(r["usd"]) for r in rows}


def _fuzz_sequence(pg, mem, seed: int, i: int) -> int:
    """One seeded sequence on its own agent and run key; checks both stores after EVERY operation."""
    rng = random.Random(f"{seed}:{i}")  # noqa: S311 - a seeded test generator, one stream per sequence
    agent, run = f"f{i}", f"run:f{i}"
    keys = [agent, run]
    n = rng.randint(3, 9)
    for op in range(n):
        day = rng.choice(FUZZ_DAYS)
        amount = D(rng.randint(1, 400)) / 100
        kind = rng.random()
        where = f"seed={seed} seq={i} op={op}"
        if kind < 0.45:
            caps = (D(rng.randint(1, 12)), D(rng.randint(3, 20)))
            run_kw = (
                {"run_key": run, "run_day": day, "run_cap": D(rng.randint(1, 8))}
                if rng.random() < 0.5
                else {}
            )
            got = [s.reserve_spend(agent, day, amount, *caps, **run_kw) for s in (pg, mem)]
            assert got[0] == got[1], where
        else:
            key = run if rng.random() < 0.2 else agent
            delta = amount if kind < 0.65 else -amount
            for s in (pg, mem):
                s.settle_spend([(key, day, delta)])
        view = _pg_view(pg, keys)
        for key in keys:
            for d in FUZZ_DAYS:
                pg_pair = (
                    view.get((key, "d", d), D(0)),
                    view.get((key, "m", d.replace(day=1)), D(0)),
                )
                assert pg_pair == mem.spend_totals(key, d), (where, key, d)
                days = sum(
                    (view.get((key, "d", x), D(0)) for x in FUZZ_DAYS if x.month == d.month), D(0)
                )
                assert pg_pair[1] >= days and pg_pair[0] >= 0, (where, key, d)
    return n


def test_memory_and_postgres_agree_after_every_operation_of_2000_seeded_sequences():
    # 2000 independent sequences (disjoint keys), 8 at a time so the run stays short; each is reproducible from
    # (seed, sequence number) alone. Reserve with and without a run key, settle and release, across Oct/Nov.
    from concurrent.futures import ThreadPoolExecutor

    from hadavin_sdk.store.migrate import spend_drift

    seed, sequences = 48_309, 2000
    for dsn in pg_schema():
        pg, mem = _pg_store(dsn), MemoryStore()
        try:
            with ThreadPoolExecutor(8) as pool:
                ops = sum(
                    pool.map(functools.partial(_fuzz_sequence, pg, mem, seed), range(sequences))
                )
            assert ops >= sequences * 3
            assert spend_drift(dsn) == []  # and the read-only check agrees on the whole schema
        finally:
            pg.close()


# --- a nested fallback carries one mark per failed primary -------------------------------------------------------


def _carry(outer_lost: int, inner_lost: int):
    from hadavin_sdk.llm.protocol import ProviderExhausted
    from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM

    def primary(lost):  # lost 0: provably sent nothing; lost n: n requests of unknown billing
        return FreshRaises(ProviderExhausted, "x", attempts=lost, refused=0)

    inner = ResilientLLM(
        primary(inner_lost),
        Stub(_fallback_reply()),
        CircuitBreaker(failures=1, reset_after_s=60.0),
        fallback_metered=True,
    )
    outer = ResilientLLM(
        primary(outer_lost),
        inner,
        CircuitBreaker(failures=1, reset_after_s=60.0),
        fallback_metered=True,
    )
    return outer


@pytest.mark.parametrize(
    ("outer_lost", "inner_lost", "marks"),
    [(0, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 2), (3, 0, 1), (3, 2, 2)],
)
def test_a_nested_fallback_carries_one_mark_per_failed_primary(outer_lost, inner_lost, marks):
    reply = _carry(outer_lost, inner_lost).chat([], system="", route="r")
    assert reply.fallback_used and reply.prior_unknown_requests == marks


@pytest.mark.parametrize(
    ("marks", "expected"), [(0, "0.0007"), (1, "0.4007"), (2, "0.8007"), (-1, "0.0007")]
)
def test_the_meter_books_one_reservation_per_mark(marks, expected):
    from hadavin_sdk.llm.protocol import reply_cost_to_settle

    reply = _fallback_reply().model_copy(update={"prior_unknown_requests": marks})
    assert reply_cost_to_settle(reply, D("0.40")) == D(expected)


def test_a_metered_nested_fallback_books_both_primaries_worst_cases(monkeypatch):
    import hadavin_sdk.limits as limits_mod
    from hadavin_sdk.llm.metered import MeteredLLM
    from tests.helpers_money import DAY as RDAY
    from tests.helpers_money import MID

    monkeypatch.setattr(limits_mod, "now", lambda: MID)
    store = MemoryStore()
    MeteredLLM(_carry(1, 1), _limits(store, daily="5"), "a", ROUTES).chat([], system="", route="r")
    worst = _unknown_total(MemoryStore())[0]  # one reservation: the worst case of this call
    assert store.spend_totals("a", RDAY)[0] == 2 * worst + D("0.0007")


# --- the spend settings are validated and reach the store --------------------------------------------------------


def test_postgres_settings_spend_knobs_have_pinned_bounds():
    from pydantic import ValidationError

    from hadavin_sdk.backends.table import PostgresSettings

    def make(**kw):
        return PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn", **kw)  # noqa: S106 - a name

    ok = make(spend_lock_timeout_ms=100, spend_reserve_attempts=10, spend_backoff_s=5)
    assert (ok.spend_lock_timeout_ms, ok.spend_reserve_attempts, ok.spend_backoff_s) == (100, 10, 5)
    assert make(spend_lock_timeout_ms=60000).spend_lock_timeout_ms == 60000
    assert make(spend_reserve_attempts=1).spend_reserve_attempts == 1
    for bad in (
        {"spend_lock_timeout_ms": 0},
        {"spend_lock_timeout_ms": 99},
        {"spend_lock_timeout_ms": 60001},
        {"spend_reserve_attempts": 0},
        {"spend_reserve_attempts": 11},
        {"spend_backoff_s": 0},
        {"spend_backoff_s": math.nan},
        {"spend_backoff_s": 6},
        {"spend_backoff_s": -0.1},
    ):
        with pytest.raises(ValidationError):
            make(**bad)


def test_the_spend_knobs_reach_the_store_from_settings():
    pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    for dsn in pg_schema():
        settings = PostgresSettings(
            kind="postgres",
            dsn_secret_name="pg-dsn",  # noqa: S106 - a name
            spend_lock_timeout_ms=1234,
            spend_reserve_attempts=7,
            spend_backoff_s=0.5,
        )
        store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        try:
            assert (store.LOCK_TIMEOUT_MS, store.RESERVE_ATTEMPTS, store.BACKOFF_S) == (
                1234,
                7,
                0.5,
            )
            seen = []
            store._spend_tx(
                lambda conn, seen=seen: seen.append(conn.execute("SHOW lock_timeout").fetchone()[0])
            )
            assert seen == ["1234ms"]  # applied to the spend transaction, not just stored
        finally:
            store.close()


def test_direct_construction_refuses_wait_forever_and_bad_backoff():
    pytest.importorskip("psycopg")
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store.postgres import PostgresStore

    for bad in (
        {"lock_timeout_ms": 0},
        {"lock_timeout_ms": -5},
        {"lock_timeout_ms": 1.5},
        {"reserve_attempts": 0},
        {"backoff_s": -0.01},
        {"backoff_s": math.nan},
        {"backoff_s": math.inf},
    ):
        with pytest.raises(ConfigError):
            PostgresStore(None, **bad)  # type: ignore[arg-type]
    store = PostgresStore(None, lock_timeout_ms=1, reserve_attempts=1, backoff_s=0)  # type: ignore[arg-type]
    assert (store.LOCK_TIMEOUT_MS, store.RESERVE_ATTEMPTS, store.BACKOFF_S) == (1, 1, 0)


# --- maintenance commands never print the host, port or user of a refused connection ---------------------------


def _bad_dsn() -> tuple[str, str]:
    """The test server with a role that does not exist: refused at once, and the driver's message quotes the host,
    the port and the user (exactly what must never reach the caller)."""
    import os

    dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
    if not dsn:
        pytest.skip("HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)")
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    bad = make_conninfo(dsn, user="leakyuser", dbname="leakydb")
    with pytest.raises(
        psycopg.OperationalError
    ) as raw:  # the raw driver text really carries the details
        psycopg.connect(bad).close()
    assert "leakyuser" in str(raw.value)
    host = conninfo_to_dict(dsn).get("host", "")
    return bad, host


def test_release_reservation_and_prune_refuse_a_dead_dsn_by_class_name_only():
    pytest.importorskip("psycopg")
    from hadavin_sdk.store.migrate import migrate, prune_run_counters, release_reservation
    from hadavin_sdk.store.protocol import StoreUnavailable

    bad, host = _bad_dsn()
    for call in (
        lambda: release_reservation(bad, "a", DAY, D("1")),
        lambda: prune_run_counters(bad),
        lambda: migrate(bad),
    ):
        with pytest.raises(
            StoreUnavailable, match=r"^store postgres: cannot connect \(\w+\)$"
        ) as e:
            call()
        assert e.value.__cause__ is None and e.value.__suppress_context__
        for leak in ("leaky", host, "port"):
            assert not leak or leak not in str(
                e.value
            )  # an empty host (a unix socket) must not make this vacuous


def test_the_release_cli_prints_no_connection_detail_even_with_debug(cfg_dir, monkeypatch, capsys):
    import yaml

    from hadavin_sdk import cli

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_CONFIG_DIR", str(cfg_dir))
    bad, host = _bad_dsn()
    monkeypatch.setenv("HADAVIN_MAINTENANCE_DSN", bad)
    monkeypatch.setenv("HADAVIN_DEBUG", "1")
    for argv in (
        ["release-reservation", "--agent", "a", "--day", "2026-03-15", "--amount", "0.4"],
        ["prune-runs"],
        ["spend-drift"],
    ):
        rc = cli.main(argv)
        out = capsys.readouterr()
        assert rc in (2, 3), (argv, out.err[-300:])  # refused or unavailable, never a crash
        assert "StoreUnavailable" in out.err or "cannot connect" in out.err, (argv, out.err[-300:])
        for leak in ("leaky", host, "port", "connection failed", "FATAL"):
            assert not leak or leak not in out.err + out.out, (argv, leak)
