"""Money-path behaviour added after the second review of PR #48: one price list for a failed and a successful fallback
(one reservation per failed primary), the guarantees of the read-only drift check, the retry loop of a spend
transaction, ``add_spend`` as a bounded spend transaction, the constructor limits of the pool, the single home of the
spend defaults, and the IAM token fetch inside the connect guard."""

from __future__ import annotations

import math
from decimal import Decimal

import pytest

from hadavin_sdk.store.memory import MemoryStore
from tests.contracts.kinds.store_postgres import pg_schema
from tests.helpers_money import (
    DAY,
    MID,
    ROUTES,
    FreshRaises,
    _fallback_reply,
    _limits,
    _pg_store,
    _unknown_total,
)

D = Decimal


# --- one price list for a failed and a successful fallback: one reservation per failed primary ----------------------------


def _failing_chain(a_lost: int, b_lost: int, *, b_refused: int = 0):
    """Primary A failed with ``a_lost`` requests of unknown billing, then the fallback B FAILED too with ``b_lost``
    unknown requests (``b_refused`` refused ones on top)."""
    from hadavin_sdk.llm.protocol import ProviderExhausted
    from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM

    return ResilientLLM(
        FreshRaises(ProviderExhausted, "a", attempts=a_lost, refused=0),
        FreshRaises(ProviderExhausted, "b", attempts=b_lost + b_refused, refused=b_refused),
        CircuitBreaker(failures=1, reset_after_s=60.0),
        fallback_metered=True,
    )


def _failure_of(llm):
    from hadavin_sdk.llm.protocol import ProviderError

    with pytest.raises(ProviderError) as e:
        llm.chat([], system="", route="r")
    return e.value


@pytest.mark.parametrize(
    ("a_lost", "b_lost", "b_refused", "reservations"),
    [
        (1, 1, 0, 2),  # A unknown, B unknown: two possible bills
        (1, 0, 1, 1),  # A unknown, B refused: only A may have been billed
        (0, 1, 0, 1),  # A provably sent nothing, B unknown
        (0, 0, 1, 0),  # nothing unknown anywhere: released
        (3, 2, 0, 2),  # retries inside one call still count once per call
    ],
)
def test_a_fallback_that_fails_after_an_unknown_primary_books_one_reservation_per_unknown_call(
    a_lost, b_lost, b_refused, reservations
):
    from hadavin_sdk.llm.protocol import cost_to_settle

    err = _failure_of(_failing_chain(a_lost, b_lost, b_refused=b_refused))
    assert (
        err.attempts == b_lost + b_refused
    )  # the fallback's own sent count is no longer rewritten
    assert cost_to_settle(err, D("0.40")) == D("0.40") * reservations


def test_the_failure_path_and_the_success_path_price_the_same_marks():
    from hadavin_sdk.llm.protocol import cost_to_settle, reply_cost_to_settle

    reserved = D("0.40")
    for marks in range(4):
        reply = _fallback_reply().model_copy(update={"prior_unknown_requests": marks})
        exc = _failure_of(_failing_chain(0, 0, b_refused=1))  # a refused error: own cost 0
        exc.prior_unknown_requests = marks
        assert reply_cost_to_settle(reply, reserved) - reply.cost_usd == cost_to_settle(
            exc, reserved
        )


def test_a_three_link_failure_books_three_reservations():
    from hadavin_sdk.llm.protocol import ProviderExhausted, cost_to_settle
    from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM

    def unknown():
        return FreshRaises(ProviderExhausted, "x", attempts=1, refused=0)

    def breaker():
        return CircuitBreaker(failures=1, reset_after_s=60.0)

    inner = ResilientLLM(unknown(), unknown(), breaker(), fallback_metered=True)
    outer = ResilientLLM(unknown(), inner, breaker(), fallback_metered=True)
    assert cost_to_settle(_failure_of(outer), D("0.40")) == D("0.40") * 3


def test_a_metered_double_failure_keeps_both_primaries_reservations(monkeypatch):
    import hadavin_sdk.limits as limits_mod
    from hadavin_sdk.llm.metered import MeteredLLM
    from hadavin_sdk.llm.protocol import ProviderError

    monkeypatch.setattr(limits_mod, "now", lambda: MID)
    worst = _unknown_total(MemoryStore())[0]
    store = MemoryStore()
    with pytest.raises(ProviderError):
        MeteredLLM(_failing_chain(1, 1), _limits(store, daily="5"), "a", ROUTES).chat(
            [], system="", route="r"
        )
    assert store.spend_totals("a", DAY)[0] == 2 * worst


@pytest.mark.parametrize("junk", [None, "2", -3, True, 1.5, math.nan, object(), (1,)])
def test_a_bad_mark_count_on_a_reply_or_an_error_counts_as_no_mark_and_never_raises(junk):
    from types import SimpleNamespace

    from hadavin_sdk.llm.protocol import ProviderError, cost_to_settle, reply_cost_to_settle

    reply = SimpleNamespace(cost_usd=D("0.0007"), prior_unknown_requests=junk)
    assert reply_cost_to_settle(reply, D("0.40")) == D("0.0007")
    exc = ProviderError("x")  # refused: own cost 0
    exc.prior_unknown_requests = junk  # type: ignore[assignment]
    assert cost_to_settle(exc, D("0.40")) == 0


def test_a_mark_count_that_raises_on_read_counts_as_no_mark():
    from hadavin_sdk.llm.protocol import reply_cost_to_settle

    class Bad:
        cost_usd = D("0.0007")

        @property
        def prior_unknown_requests(self):
            raise RuntimeError("boom")

    assert reply_cost_to_settle(Bad(), D("0.40")) == D("0.0007")


# --- the read-only drift check: its guarantees, one by one -----------------------------------------------------------------


def test_the_drift_check_runs_in_a_read_only_transaction(monkeypatch):
    # A write attempted INSIDE the check's own transaction (just before its SELECT) must be refused by the database.
    psycopg = pytest.importorskip("psycopg")
    import hadavin_sdk.store.migrate as migrate_mod

    outcome: list[str] = []
    real_connect = migrate_mod._connect

    class Probe:
        def __init__(self, real):
            self.real = real

        def __getattr__(self, name):
            return getattr(self.real, name)

        def __enter__(self):
            self.real.__enter__()
            return self

        def __exit__(self, *exc):
            return self.real.__exit__(*exc)

        def execute(self, query, *args):
            if str(query).startswith("SELECT s.agent_id"):
                try:
                    with (
                        self.real.transaction()
                    ):  # a savepoint: a refusal leaves the check's transaction usable
                        self.real.execute(
                            "INSERT INTO spend_month (agent_id, month, usd) VALUES ('w', %s, 1)",
                            (DAY,),
                        )
                    outcome.append("wrote")
                except psycopg.errors.ReadOnlySqlTransaction:
                    outcome.append("refused")
            return self.real.execute(query, *args)

    monkeypatch.setattr(migrate_mod, "_connect", lambda dsn_, **kw: Probe(real_connect(dsn_, **kw)))
    for dsn in pg_schema():
        outcome.clear()
        migrate_mod.spend_drift(dsn)
        assert outcome == ["refused"]


def test_a_day_with_no_month_row_is_reported_as_drift():
    # The month row is gone but its day rows remain: the month total is 0 and the check must still list it.
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.migrate import spend_drift

    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            store.settle_spend([("a", DAY, D("1.00"))])
            with psycopg.connect(dsn, autocommit=True) as db:
                db.execute("DELETE FROM spend_month WHERE agent_id = 'a'")
            assert spend_drift(dsn) == [("a", DAY.replace(day=1), D("0"), D("1.00"))]
        finally:
            store.close()


def test_a_take_back_never_adds_to_a_day_row_that_is_already_negative():
    # A day row below zero (raw SQL) takes back nothing: min(amount, day total) is not positive, so nothing is written.
    psycopg = pytest.importorskip("psycopg")
    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            store.settle_spend([("a", DAY, D("1.00"))])
            with psycopg.connect(dsn, autocommit=True) as db:
                db.execute("UPDATE spend SET usd = -0.50 WHERE agent_id = 'a'")
            store.settle_spend([("a", DAY, D("-1.00"))])
            assert store.spend_totals("a", DAY)[0] == D("-0.50")  # unchanged, not -0.50 + 1.00
        finally:
            store.close()


# --- the retry loop of a spend transaction: how many tries, how the wait grows -----------------------------------------------


def _store_with_fake_tx(monkeypatch, outcomes, *, attempts, backoff):
    import hadavin_sdk.store.postgres as pgmod
    from hadavin_sdk.store.postgres import PostgresStore

    store = PostgresStore(None, reserve_attempts=attempts, backoff_s=backoff)  # type: ignore[arg-type]
    sleeps: list[float] = []
    monkeypatch.setattr(pgmod.time, "sleep", sleeps.append)
    calls: list[int] = []

    def fake_run_tx(conn, work):
        calls.append(1)
        out = outcomes[len(calls) - 1]
        if isinstance(out, BaseException):
            raise out
        return out

    store._run_tx = fake_run_tx  # type: ignore[method-assign]
    return store, calls, sleeps


@pytest.mark.parametrize(
    "cls_name", ["SerializationFailure", "DeadlockDetected", "LockNotAvailable"]
)
def test_a_spend_transaction_retries_exactly_the_configured_attempts_with_linear_backoff(
    monkeypatch, cls_name
):
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.protocol import StoreUnavailable

    err = getattr(psycopg.errors, cls_name)
    store, calls, sleeps = _store_with_fake_tx(monkeypatch, [err("x")] * 9, attempts=4, backoff=0.5)
    with pytest.raises(StoreUnavailable, match=rf"busy \({cls_name}\) after 4 attempts"):
        store._spend_tx(lambda conn: None)
    assert len(calls) == 4
    assert sleeps == [0.5, 1.0, 1.5]  # linear growth, none after the last try


def test_a_spend_transaction_that_succeeds_on_a_later_try_stops_retrying(monkeypatch):
    psycopg = pytest.importorskip("psycopg")
    err = psycopg.errors.SerializationFailure("x")
    store, calls, sleeps = _store_with_fake_tx(
        monkeypatch, [err, err, "done"], attempts=5, backoff=0.1
    )
    assert store._spend_tx(lambda conn: None) == "done"
    assert len(calls) == 3 and sleeps == [0.1, 0.2]


def test_another_driver_error_is_not_retried_and_leaks_only_its_class_name(monkeypatch):
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.protocol import StoreUnavailable

    store, calls, sleeps = _store_with_fake_tx(
        monkeypatch, [psycopg.errors.UndefinedTable("secret-table-name")], attempts=4, backoff=0.5
    )
    with pytest.raises(StoreUnavailable, match=r"failed \(UndefinedTable\)") as e:
        store._spend_tx(lambda conn: None)
    assert len(calls) == 1 and sleeps == [] and "secret-table-name" not in str(e.value)


# --- add_spend is a bounded, retried spend transaction like every other spend write ----------------------------------------


def test_add_spend_gives_up_on_a_held_row_by_the_lock_timeout_and_never_holds_the_process_lock():
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.protocol import StoreUnavailable

    for dsn in pg_schema():
        store = _pg_store(dsn, LOCK_TIMEOUT_MS=100, RESERVE_ATTEMPTS=1)
        try:
            store.add_spend("a", DAY, D("1.00"))
            with psycopg.connect(dsn) as holder:
                holder.execute(
                    "SELECT usd FROM spend WHERE agent_id = 'a' AND day = %s FOR UPDATE", (DAY,)
                )
                with pytest.raises(StoreUnavailable, match=r"busy \(LockNotAvailable\)"):
                    store.add_spend("a", DAY, D("1.00"))
                assert store._lock.acquire(
                    blocking=False
                )  # the process-wide lock was not held while waiting
                store._lock.release()
                holder.rollback()
            assert store.add_spend("a", DAY, D("1.00"))[0] == D(
                "2.00"
            )  # and it works once the row is free
        finally:
            store.close()


# --- the PostgresStore constructor also limits the pool, and the defaults have one home ---------------------------------------


def test_the_pool_limits_are_validated_in_the_constructor():
    pytest.importorskip("psycopg")
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store.postgres import PostgresStore

    for bad in (
        {"pool_size": 0},
        {"pool_size": -1},
        {"pool_size": True},
        {"pool_size": 2.0},
        {"pool_wait_s": 0},
        {"pool_wait_s": -1},
        {"pool_wait_s": math.nan},
        {"pool_wait_s": math.inf},
        {"pool_wait_s": True},
        {"pool_wait_s": "5"},
    ):
        with pytest.raises(ConfigError):
            PostgresStore(None, **bad)  # type: ignore[arg-type]
    ok = PostgresStore(None, pool_size=2, pool_wait_s=0.5)  # type: ignore[arg-type]
    assert (ok.POOL_SIZE, ok.POOL_WAIT_S) == (2, 0.5)


def test_the_class_defaults_are_the_settings_defaults():
    pytest.importorskip("psycopg")
    from hadavin_sdk.backends.table import PostgresSettings
    from hadavin_sdk.store.postgres import PostgresStore

    s = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    assert (
        PostgresStore.LOCK_TIMEOUT_MS,
        PostgresStore.RESERVE_ATTEMPTS,
        PostgresStore.POOL_SIZE,
        PostgresStore.POOL_WAIT_S,
        PostgresStore.BACKOFF_S,
    ) == (
        s.spend_lock_timeout_ms,
        s.spend_reserve_attempts,
        s.spend_pool_size,
        s.spend_pool_wait_s,
        s.spend_backoff_s,
    )


# --- the IAM token fetch is inside the connect guard too -------------------------------------------------------------------


def test_a_failing_iam_token_fetch_leaks_only_its_class_name(monkeypatch):
    pytest.importorskip("psycopg")
    import hadavin_sdk.store.postgres as pgmod
    from hadavin_sdk.store.migrate import _connect
    from hadavin_sdk.store.protocol import StoreUnavailable

    class TokenError(Exception):
        pass

    def failing_source(iam_auth, region):
        def password(host, port, user):
            raise TokenError(f"cannot sign for {host} account 123456789012 token abc123")

        return password

    monkeypatch.setattr(pgmod, "password_source", failing_source)
    with pytest.raises(
        StoreUnavailable, match=r"^store postgres: cannot connect \(TokenError\)$"
    ) as e:
        _connect(
            "host=db.internal.example user=svc dbname=x",
            iam_auth=True,
            region="r",
            sslmode="verify-full",
            sslrootcert="ca.pem",
        )
    text = str(e.value)
    assert "db.internal.example" not in text and "123456789012" not in text and "abc123" not in text
    assert e.value.__cause__ is None and e.value.__suppress_context__
