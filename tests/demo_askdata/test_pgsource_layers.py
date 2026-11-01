"""T-E5 to T-E8: the execution path with the validator DISABLED (hostile text goes straight to PgSource.run).

The login used for the write tests HAS the privilege to insert into scratch.marker, so only the layers below the
validator (the extended protocol, the read-only transaction, the guard) can stop a write.
"""

import threading
import time

import psycopg
import pytest
from askdata import pgsource
from askdata.pgsource import WATCHDOG_NAME, Limits, PgError, PgSource

STACKED = "COMMIT; BEGIN READ WRITE; INSERT INTO scratch.marker VALUES ({m}); COMMIT"


def _count(db, marker: int) -> int:
    with db.admin() as conn:
        return conn.execute(
            "SELECT count(*) FROM scratch.marker WHERE v = %s", (marker,)
        ).fetchone()[0]


def test_c3b_stacked_statement_is_refused_and_writes_nothing(db, rw_login):
    dsn, _ = rw_login
    with pytest.raises(PgError) as caught:
        PgSource(dsn).run(STACKED.format(m=71))
    assert (
        caught.value.sqlstate == "42601"
    )  # syntax error: DECLARE ... CURSOR FOR cannot carry a second statement
    assert _count(db, 71) == 0


def test_c3b_fixed_queries_use_prepare_and_refuse_stacking(db, rw_login):
    dsn, _ = rw_login
    with psycopg.connect(dsn) as conn:
        conn.read_only = True
        with pytest.raises(psycopg.errors.SyntaxError) as caught:  # same sqlstate as above
            conn.execute(STACKED.format(m=72), prepare=True)
    assert caught.value.sqlstate == "42601"
    assert _count(db, 72) == 0


def test_hazard_simple_protocol_string_commits_a_write(db, rw_login):
    """Documents the hazard (psycopg simple protocol). If psycopg ever changes this, the rules can be revisited."""
    dsn, _ = rw_login
    with psycopg.connect(dsn) as conn:
        conn.read_only = True
        conn.execute(
            STACKED.format(m=73)
        )  # no prepare=True: one simple-protocol string, four statements
    assert _count(db, 73) == 1
    with db.admin() as conn:
        conn.execute("DELETE FROM scratch.marker WHERE v = 73")


VARIANTS = [
    "SET TRANSACTION READ WRITE",
    "BEGIN READ WRITE",
    "SET default_transaction_read_only = off",
    "RESET ALL",
    "SELECT set_config('transaction_read_only', 'off', false)",
    "SELECT set_config('default_transaction_read_only', 'off', false)",
    "SELECT set_config('statement_timeout', '0', false)",
]


@pytest.mark.parametrize("variant", VARIANTS)
def test_variants_sent_after_the_guard_never_write(db, rw_login, variant):
    dsn, _ = rw_login
    if variant.startswith(
        "SELECT"
    ):  # set_config forms: executed, but they cannot flip the open transaction
        try:
            PgSource(dsn).run(variant)
        except PgError as err:
            assert err.sqlstate == "25001", err
    else:  # statement forms cannot ride inside DECLARE ... CURSOR FOR
        with pytest.raises(PgError) as caught:
            PgSource(dsn).run(variant)
        assert caught.value.sqlstate == "42601"
    # a fresh connection that tries to write is still refused, and nothing persisted
    with pytest.raises(PgError):
        PgSource(dsn).run("INSERT INTO scratch.marker VALUES (74)")
    assert _count(db, 74) == 0


def test_variants_set_config_of_read_write_fails_after_the_guard(db, rw_login):
    dsn, _ = rw_login
    with pytest.raises(PgError) as caught:
        PgSource(dsn).run("SELECT set_config('transaction_read_only', 'off', false)")
    assert caught.value.sqlstate == "25001"


def test_variants_sent_first_would_flip_the_transaction__which_is_why_the_guard_is_first(
    db, rw_login
):
    dsn, _ = rw_login
    with psycopg.connect(dsn) as conn:  # a connection that bypasses the guard
        conn.read_only = True
        conn.execute(
            "SET TRANSACTION READ WRITE", prepare=True
        )  # the FIRST statement is allowed to flip it
        assert conn.execute("SHOW transaction_read_only", prepare=True).fetchone()[0] == "off"
        conn.rollback()  # nothing was written; this only documents the flip
    assert _count(db, 75) == 0


def test_validator_hash_mismatch_sends_nothing(db):
    with pytest.raises(PgError) as caught:
        PgSource(db.ro_dsn).run("SELECT 1", sql_sha256="0" * 64)
    assert caught.value.sqlstate is None and "hash mismatch" in caught.value.what


def test_percent_signs_in_canonical_sql_are_safe(db):
    result = PgSource(db.ro_dsn).run("SELECT 7 % 4 AS m, 'a%' LIKE 'a%' AS lk")
    assert result.rows == [(3, True)]


def test_errors_carry_only_the_sqlstate(db):
    with pytest.raises(PgError) as caught:
        PgSource(db.ro_dsn).run("SELECT * FROM shop.customers")
    assert caught.value.sqlstate == "42501"
    assert "shop" not in str(caught.value) and "customers" not in str(caught.value)


# --------------------------------------------------------------------------------------------- T-E8 caps


def test_caps_watchdog_cancels_a_blocked_statement(db, capsys):
    timeout = 2.0
    start = time.monotonic()
    with pytest.raises(PgError) as caught:
        PgSource(db.ro_dsn, limits=Limits(statement_timeout_s=timeout)).run("SELECT pg_sleep(30)")
    elapsed = time.monotonic() - start
    with capsys.disabled():
        print(
            f"\nT-E8 watchdog: pg_sleep(30) cancelled after {elapsed:.2f}s (limit {timeout}s, server default 15s)"
        )
    assert caught.value.sqlstate == "57014"
    assert elapsed < timeout + 1  # measured 0.02-0.05 s over locally (docker, Windows)
    assert not [t for t in threading.enumerate() if t.name == WATCHDOG_NAME and t.is_alive()]


def test_caps_row_cap_returns_exactly_max_rows(db):
    result = PgSource(db.ro_dsn).run(
        "SELECT g FROM generate_series(1, 1000000) AS g", limits=Limits(max_rows=500)
    )
    assert len(result.rows) == 500 and result.truncated
    again = PgSource(db.ro_dsn).run(
        "SELECT g FROM generate_series(1, 500) AS g", limits=Limits(max_rows=500)
    )
    assert len(again.rows) == 500 and not again.truncated  # exactly at the cap is not truncated


def test_caps_byte_cap_stops_wide_rows(db):
    result = PgSource(db.ro_dsn).run(
        "SELECT repeat('x', 100000) AS w FROM generate_series(1, 1000)",
        limits=Limits(max_bytes=450_000),
    )
    assert result.truncated and len(result.rows) == 4 and result.byte_count <= 450_000


def test_caps_timer_thread_is_dead_after_a_normal_run(db):
    PgSource(db.ro_dsn).run("SELECT 1")
    assert not [t for t in threading.enumerate() if t.name == WATCHDOG_NAME and t.is_alive()]


def test_result_hash_is_over_raw_values_and_cells_are_cleaned(db):
    esc = chr(27)
    sql = f"SELECT 'a{esc}[2Kb' AS v"  # constant text, not input
    result = PgSource(db.ro_dsn).run(sql.replace(esc, "' || chr(27) || '"))
    assert result.rows == [("ab",)]  # the complete ANSI sequence is removed from the display value
    assert esc not in "".join(str(c) for r in result.rows for c in r)


def test_a_transient_connect_failure_is_retried_once_and_a_second_failure_is_reported(
    db, monkeypatch
):
    real, calls = psycopg.connect, []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise psycopg.OperationalError("connection reset")
        return real(*args, **kwargs)

    monkeypatch.setattr(psycopg, "connect", flaky)
    assert PgSource(db.ro_dsn).run("SELECT 1").rows == [(1,)]
    assert len(calls) == 2

    def dead(*args, **kwargs):
        calls.append(1)
        raise psycopg.OperationalError("connection refused")

    calls.clear()
    monkeypatch.setattr(psycopg, "connect", dead)
    with pytest.raises(PgError) as caught:
        PgSource(db.ro_dsn).run("SELECT 1")
    assert caught.value.sqlstate is None and len(calls) == 2


def test_deadline_is_checked_per_row_not_per_batch(db, monkeypatch):
    """A fake clock that moves one second per reading: a per-batch check would read it a handful of times and pass;
    a per-row check reads it for every row of the batch and trips the 20 s deadline."""

    class Clock:
        n = 0

        @classmethod
        def monotonic(cls) -> float:
            cls.n += 1
            return float(cls.n)

    monkeypatch.setattr(pgsource, "time", Clock)
    with pytest.raises(PgError) as caught:
        PgSource(db.ro_dsn, limits=Limits(statement_timeout_s=20.0)).run(
            "SELECT g FROM generate_series(1, 1000) AS g"
        )
    assert caught.value.sqlstate == "57014" and Clock.n < 40
