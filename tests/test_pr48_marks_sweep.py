"""Billing marks on EVERY path that meters a call (PR #48 review 10, class: a mark or a cost is dropped on a path that is
not the one that was tested): an outer fallback chain whose primary is itself a chain, a garbage error count, the judge
(injection screen) success and failure paths, a reused exception, a fallback that is not a ProviderError, the clamp, and
the Postgres stall bounds (statement timeout, idle-in-transaction timeout, a kept pooled connection)."""

# ruff: noqa: B023
from __future__ import annotations

import math
import threading
import time
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.llm.protocol import (
    MAX_MARKS,
    ProviderError,
    ProviderExhausted,
    cost_to_settle,
    reply_cost_to_settle,
)
from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
from hadavin_sdk.models import Reply
from tests.contracts.kinds.store_postgres import pg_schema
from tests.helpers_money import DAY, FreshRaises, Stub, _fallback_reply, _pg_store

D = Decimal
R = D("0.40")


def _breaker():
    return CircuitBreaker(failures=1, reset_after_s=60.0)


def _unknown(msg="x"):
    return FreshRaises(ProviderExhausted, msg, attempts=1, refused=0)


def _chat(llm):
    return llm.chat([], system="", route="r")


def _failure_of(llm):
    with pytest.raises(ProviderError) as e:
        _chat(llm)
    return e.value


# --- MAJOR 1: the PRIMARY is itself a chain ----------------------------------------------------------------------------


def test_an_outer_chain_whose_primary_is_a_chain_books_all_three_possible_bills():
    inner = ResilientLLM(
        _unknown(), _unknown(), _breaker(), fallback_metered=True
    )  # P, F1 both unknown
    outer = ResilientLLM(
        inner, _unknown(), _breaker(), fallback_metered=True
    )  # then F2 unknown too
    err = _failure_of(outer)
    assert err.prior_unknown_requests == 2 and cost_to_settle(err, R) == R * 3


def test_an_outer_chain_whose_primary_chain_failed_and_whose_fallback_succeeds_books_two_marks():
    inner = ResilientLLM(_unknown(), _unknown(), _breaker(), fallback_metered=True)
    outer = ResilientLLM(inner, Stub(_fallback_reply()), _breaker(), fallback_metered=True)
    reply = _chat(outer)
    assert reply.prior_unknown_requests == 2
    assert reply_cost_to_settle(reply, R) == reply.cost_usd + R * 2


def test_an_inner_chain_that_refused_after_an_unknown_primary_still_counts_its_mark():
    # P unknown, F1 refused (own cost 0) inside the inner chain; then F2 refuses: one bill (P) remains.
    inner = ResilientLLM(
        _unknown(), FreshRaises(ProviderError, "no"), _breaker(), fallback_metered=True
    )
    outer = ResilientLLM(inner, FreshRaises(ProviderError, "no"), _breaker(), fallback_metered=True)
    err = _failure_of(outer)
    assert cost_to_settle(err, R) == R


# --- MAJOR 2: garbage counts do not lose good marks --------------------------------------------------------------------


@pytest.mark.parametrize("junk", [None, "x", -5, True, 1.5, math.nan, 10**400])
@pytest.mark.parametrize("attr", ["attempts", "answered", "refused"])
def test_a_garbage_count_keeps_the_reservation_and_the_marks(junk, attr):
    exc = ProviderExhausted("x")
    setattr(exc, attr, junk)
    exc.prior_unknown_requests = 2
    assert (
        cost_to_settle(exc, R) == R * 3
    )  # own: the whole reservation (unknown), plus one per mark


@pytest.mark.parametrize("billed", [None, "abc", math.nan, D("Infinity")])
def test_an_unreadable_billed_usd_keeps_the_reservation_and_the_marks(billed):
    exc = ProviderError("x")
    exc.attempts, exc.answered, exc.refused = 1, 1, 0
    exc.billed_usd = billed
    exc.prior_unknown_requests = 1
    assert cost_to_settle(exc, R) == R * 2


# --- the clamp ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mark", "expected"),
    [
        (0, 0),
        (1, 1),
        (MAX_MARKS, MAX_MARKS),
        (MAX_MARKS + 1, MAX_MARKS),
        (10**6, MAX_MARKS),
        (-1, 0),
    ],
)
def test_a_mark_count_is_clamped_to_the_depth_of_any_chain(mark, expected):
    reply = SimpleNamespace(cost_usd=D("0"), prior_unknown_requests=mark)
    assert reply_cost_to_settle(reply, R) == R * expected
    exc = ProviderError("x")
    exc.prior_unknown_requests = mark
    assert cost_to_settle(exc, R) == R * expected  # a refused error: own cost 0


# --- MINOR 4 and 5: a fallback that is not a ProviderError; a reused exception ----------------------------------------


def test_a_fallback_that_raises_something_else_after_an_unknown_primary_keeps_the_primarys_bill():
    class Bug:
        def chat(self, *a, **k):
            raise KeyError("secret-detail")

    err = _failure_of(ResilientLLM(_unknown(), Bug(), _breaker(), fallback_metered=True))
    assert (
        isinstance(err, ProviderExhausted)
        and "KeyError" in str(err)
        and "secret-detail" not in str(err)
    )
    assert cost_to_settle(err, R) == R * 2  # the fallback's own unknown request plus the primary's


def test_a_fallback_that_raises_something_else_after_a_provably_unsent_primary_passes_unchanged():
    class Bug:
        def chat(self, *a, **k):
            raise KeyError("x")

    primary = FreshRaises(ProviderExhausted, "x", attempts=0, refused=0)
    llm = ResilientLLM(primary, Bug(), _breaker(), fallback_metered=True)
    with pytest.raises(KeyError):
        _chat(llm)


def test_a_reused_exception_instance_does_not_accumulate_marks_across_calls():
    shared = ProviderError("shared")  # one instance a plain fallback raises every time
    llm = ResilientLLM(
        FreshRaises(ProviderExhausted, "x", attempts=1, refused=0),
        Stub(shared),
        CircuitBreaker(failures=1000, reset_after_s=0.001),
        fallback_metered=True,
    )
    for _ in range(5):
        # the breaker trips per call here: each call goes primary (unknown) then the fallback (refused)
        err = _failure_of(llm)
        assert err is shared and err.prior_unknown_requests == 1
        assert cost_to_settle(err, R) == R


def test_a_reused_reply_instance_does_not_accumulate_marks():
    shared = _fallback_reply().model_copy(
        update={"prior_unknown_requests": 7}
    )  # a stale mark from an old call
    llm = ResilientLLM(_unknown(), Stub(shared), _breaker(), fallback_metered=True)
    assert _chat(llm).prior_unknown_requests == 1  # a plain fallback's own mark is not read


# --- MAJOR 3: the judge (injection screen) -----------------------------------------------------------------------------


class _MarkedJudgeModel:
    """A judge model whose reply (or error) carries ``marks`` failed primaries of unknown billing."""

    def __init__(self, marks, fail=False):
        self.marks, self.fail = marks, fail

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        from hadavin_sdk.llm.common import ANSWER_TOOL
        from hadavin_sdk.models import ToolCall

        if self.fail:
            exc = ProviderExhausted("judge: throttled")
            exc.prior_unknown_requests = self.marks
            raise exc
        return Reply(
            tool_calls=[ToolCall(name=ANSWER_TOOL, input={"injection": False, "confidence": 0.1})],
            model_id="judge",
            cost_usd=D("0.001"),
            prior_unknown_requests=self.marks,
        )


def test_a_judge_verdict_carries_the_marks_of_its_reply_and_of_its_error():
    from hadavin_sdk.guard.injection import AnyOf, RegexDetector, injection_check
    from hadavin_sdk.guard.judge import JudgeDetector

    ok = JudgeDetector(_MarkedJudgeModel(2), "screen", 0.7).check("hello", "document")
    assert ok.prior_unknown_requests == 2 and ok.cost_usd == D("0.001")
    failed = injection_check(
        JudgeDetector(_MarkedJudgeModel(3, fail=True), "screen", 0.7), "t", "d"
    )
    assert failed.reason_code == "guard_unavailable" and failed.prior_unknown_requests == 3
    both = AnyOf([RegexDetector(0.5), JudgeDetector(_MarkedJudgeModel(2), "screen", 0.7)]).check(
        "hello", "document"
    )
    assert both.prior_unknown_requests == 2


def _spend_of_a_screened_run(cfg_dir, marks, fail):
    import yaml

    from hadavin_sdk.config import load_config
    from hadavin_sdk.guard.judge import JudgeDetector
    from hadavin_sdk.models import now
    from tests.test_s5_runtime import build

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["routes"]["screen"] = dict(data["routes"]["default"], max_tokens=64)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    rt, cfg = build(cfg_dir)
    rt.detector = JudgeDetector(_MarkedJudgeModel(marks, fail=fail), "screen", 0.7)
    booked: list[Decimal] = []
    real = rt.limits.reserve

    def spy(agent_id, usd, *a, **k):
        booked.append(usd)
        return real(agent_id, usd, *a, **k)

    rt.limits.reserve = spy  # type: ignore[method-assign]
    rt.handle("test-agent", "svc:test-agent", (cfg.inputs_dir / "create.txt").read_bytes())
    assert load_config(cfg_dir)  # the config is still valid
    return rt.store.spend_totals("test-agent", now().date())[0], min(booked)


@pytest.mark.parametrize("fail", [False, True], ids=["judge answered", "judge failed"])
def test_the_agent_loop_books_one_judge_reservation_per_mark_of_the_judge(cfg_dir, fail):
    base, unit = _spend_of_a_screened_run(cfg_dir, 0, fail)
    marked, _ = _spend_of_a_screened_run(cfg_dir, 2, fail)
    assert marked - base == 2 * unit


# --- MINOR 6: an unusable DSN or token provider at build / the pool ----------------------------------------------------


def test_build_and_the_pool_connector_leak_only_a_class_name_for_a_malformed_dsn_or_a_failing_token_provider():
    pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings
    from hadavin_sdk.store.protocol import StoreUnavailable

    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    bad_dsn = "host=127.0.0.1 port=notaport user=leakyuser dbname=secretdb"
    with pytest.raises(StoreUnavailable) as e:
        make("store", settings, FakeSecretProvider({"pg-dsn": bad_dsn}))
    assert all(x not in str(e.value) for x in ("leaky", "secretdb", "notaport"))
    assert e.value.__cause__ is None


def test_the_pool_borrow_turns_a_failing_connector_into_a_class_name_only_error():
    pytest.importorskip("psycopg")
    from hadavin_sdk.store.postgres import PostgresStore
    from hadavin_sdk.store.protocol import StoreUnavailable

    class TokenError(Exception):
        pass

    def connector():
        raise TokenError("account 123456789012 token abc123 host db.internal")

    store = PostgresStore(None, connector, pool_wait_s=1)  # type: ignore[arg-type]
    with (
        pytest.raises(StoreUnavailable, match=r"cannot connect \(TokenError\)") as e,
        store._borrow(),
    ):
        pass
    assert "123456789012" not in str(e.value) and "abc123" not in str(e.value)


# --- the Postgres stall bounds -------------------------------------------------------------------------------------------


def test_a_statement_that_runs_past_the_statement_timeout_is_cancelled_and_frees_its_pool_slot():
    pytest.importorskip("psycopg")
    from hadavin_sdk.store.protocol import StoreUnavailable

    for dsn in pg_schema():
        store = _pg_store(dsn, STATEMENT_TIMEOUT_S=0.2, RESERVE_ATTEMPTS=1)
        try:
            t0 = time.monotonic()
            with pytest.raises(StoreUnavailable, match=r"QueryCanceled"):
                store._spend_tx(lambda conn: conn.execute("SELECT pg_sleep(30)"))
            assert (
                time.monotonic() - t0 < 20
            )  # cancelled by the server, nowhere near the 30 s sleep
            assert store._slots.acquire(timeout=1)  # the pool slot came back
            store._slots.release()
            assert store._spend_tx(lambda conn: conn.execute("SELECT 1").fetchone()[0]) == 1
        finally:
            store.close()


def test_a_session_idle_inside_its_transaction_is_ended_by_the_server():
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.protocol import StoreUnavailable

    for dsn in pg_schema():
        store = _pg_store(dsn, IDLE_IN_TX_TIMEOUT_S=0.2, RESERVE_ATTEMPTS=1)
        try:
            waited = threading.Event()

            def stalled(conn):
                conn.execute("SELECT 1")
                waited.wait(
                    2.0
                )  # the caller stalls inside the open transaction (a black-holed client)
                return conn.execute("SELECT 2").fetchone()

            with pytest.raises(StoreUnavailable):
                store._spend_tx(stalled)
            assert (
                psycopg
            )  # the session was ended by the server: the next call gets a working connection
            assert store._spend_tx(lambda conn: conn.execute("SELECT 3").fetchone()[0]) == 3
        finally:
            store.close()


def test_the_timeout_settings_reach_the_spend_transaction_and_are_validated():
    pytest.importorskip("psycopg")
    from pydantic import ValidationError

    from hadavin_sdk.backends.table import PostgresSettings
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store.postgres import PostgresStore

    for bad in (
        {"spend_statement_timeout_s": 0},
        {"spend_idle_in_tx_timeout_s": -1},
        {"spend_statement_timeout_s": 3601},
    ):
        with pytest.raises(ValidationError):
            PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn", **bad)  # noqa: S106
    for bad in (
        {"statement_timeout_s": 0},
        {"idle_in_tx_timeout_s": math.nan},
        {"statement_timeout_s": True},
    ):
        with pytest.raises(ConfigError):
            PostgresStore(None, **bad)  # type: ignore[arg-type]
    for dsn in pg_schema():
        store = _pg_store(dsn, STATEMENT_TIMEOUT_S=7, IDLE_IN_TX_TIMEOUT_S=9)
        try:
            seen = store._spend_tx(
                lambda conn: (
                    conn.execute("SHOW statement_timeout").fetchone()[0],
                    conn.execute("SHOW idle_in_transaction_session_timeout").fetchone()[0],
                )
            )
            assert seen == ("7s", "9s")
        finally:
            store.close()


def test_a_lock_timeout_retry_keeps_its_pooled_connection():
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.protocol import StoreUnavailable

    for dsn in pg_schema():
        store = _pg_store(dsn, LOCK_TIMEOUT_MS=100, RESERVE_ATTEMPTS=3, BACKOFF_S=0)
        connects: list[int] = []
        real = store._connector
        store._connector = lambda real=real: (connects.append(1), real())[1]  # type: ignore[misc]
        try:
            store.add_spend("a", DAY, D("1.00"))
            n0 = len(connects)
            with psycopg.connect(dsn) as holder:
                holder.execute(
                    "SELECT usd FROM spend WHERE agent_id = 'a' AND day = %s FOR UPDATE", (DAY,)
                )
                with pytest.raises(StoreUnavailable, match="busy"):
                    store.add_spend("a", DAY, D("1.00"))  # three lock timeouts in a row
                holder.rollback()
            assert (
                len(connects) - n0 <= 1
            )  # no reconnect per retry (at most the one connect that built the pool)
        finally:
            store.close()


def test_a_real_connection_error_still_closes_the_pooled_connection():
    psycopg = pytest.importorskip("psycopg")
    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            holder: list = []

            def boom(conn):
                holder.append(conn)
                raise psycopg.errors.InternalError_("broken")

            with pytest.raises(Exception, match="spend operation failed"):
                store._spend_tx(boom)
            assert holder[0].closed
        finally:
            store.close()


def test_a_plain_primary_that_reuses_an_exception_with_a_stale_mark_adds_only_its_own_bill():
    stale = ProviderExhausted("x")
    stale.attempts, stale.refused, stale.prior_unknown_requests = (
        1,
        0,
        5,
    )  # a mark left over from an older call
    llm = ResilientLLM(Stub(stale), Stub(_fallback_reply()), _breaker(), fallback_metered=True)
    assert _chat(llm).prior_unknown_requests == 1  # the primary's one unknown request, not 1 + 5
