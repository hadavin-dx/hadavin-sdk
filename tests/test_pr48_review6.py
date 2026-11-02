"""PR #48 review 5 (round 6): privilege matrix, bounded billed_usd, UnusableAnswer contract, fallback carry, small fixes."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.llm.metered import MeteredLLM
from hadavin_sdk.llm.protocol import (
    ProviderError,
    ProviderExhausted,
    UnusableAnswer,
    cost_to_settle,
    unknown_requests,
)
from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
from hadavin_sdk.llm.retry import with_retry
from hadavin_sdk.store.memory import MemoryStore
from tests.contracts.kinds.store_postgres import pg_schema
from tests.test_core_hardening_round2 import (  # noqa: F401 - fixtures are used by name
    DAY,
    MID,
    ROUTES,
    Stub,
    _limits,
    _pg_store,
    clock,
    roles,
)

D = Decimal


class Http(Exception):
    def __init__(self, code):
        super().__init__(f"http {code}")
        self.status_code = code


def _fail(*errors):
    it = iter(errors)

    def call():
        raise next(it)

    return call


# --- M1: the ACTUAL privilege matrix on the spend tables, real Postgres ------------------------------------------------


def test_privilege_matrix_on_the_spend_tables():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate

    denied = psycopg.errors.InsufficientPrivilege
    for dsn in pg_schema():
        rt, mt, pt = (p + uuid.uuid4().hex[:10] for p in ("rt_", "mt_", "pt_"))
        with psycopg.connect(dsn, autocommit=True) as db:
            for n in (rt, mt, pt):
                db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(n)))
        migrate(dsn, runtime_role=rt, maintenance_role=mt, portal_role=pt)
        try:
            for table, key, when in (
                ("spend", "day", "current_date"),
                ("spend_month", "month", "date_trunc('month', current_date)"),
            ):
                ins = f"INSERT INTO {table} (agent_id, {key}, usd) VALUES (%s, {when}, 1)"  # noqa: S608 - table names are literals above
                upd = f"UPDATE {table} SET usd = 2"  # noqa: S608 - table names are literals above
                upk = f"UPDATE {table} SET agent_id = 'z'"  # noqa: S608 - table names are literals above
                dele = f"DELETE FROM {table}"  # noqa: S608 - table names are literals above
                sel = f"SELECT count(*) FROM {table}"  # noqa: S608 - table names are literals above
                with psycopg.connect(make_conninfo(dsn, user=rt), autocommit=True) as db:
                    db.execute(ins, ("r-" + table,))  # runtime: INSERT allowed
                    db.execute(upd)  # runtime: UPDATE of usd allowed (so raw SQL can write any usd)
                    db.execute(sel)
                    with pytest.raises(denied):
                        db.execute(dele)  # runtime: DELETE denied
                with psycopg.connect(make_conninfo(dsn, user=mt), autocommit=True) as db:
                    db.execute(sel)
                    db.execute(upd)  # maintenance: UPDATE (usd) allowed
                    with pytest.raises(denied):
                        db.execute(ins, ("m-" + table,))  # maintenance: INSERT denied
                    with pytest.raises(denied):
                        db.execute(upk)  # maintenance: no other column
                    db.execute(dele)  # maintenance: DELETE allowed
                with psycopg.connect(make_conninfo(dsn, user=pt), autocommit=True) as db:
                    for stmt in (sel, ins, upd, dele):
                        with pytest.raises(denied):
                            db.execute(stmt, ("p-" + table,) if stmt is ins else None)
        finally:
            with psycopg.connect(dsn, autocommit=True) as db:
                for n in (rt, mt, pt):
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(n)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(n)))


# --- M2: billed_usd is bounded by the reservation -------------------------------------------------------------------------


def test_m2_cost_to_settle_never_exceeds_the_reservation():
    R = D("0.40")
    for absurd in ("1e999999", "1e9", "0.4000001"):
        e = UnusableAnswer("x")
        e.billed_usd = D(absurd)
        assert cost_to_settle(e, R) == R
    e = UnusableAnswer("x")
    e.billed_usd = D("0.4")
    assert cost_to_settle(e, R) == R
    e.billed_usd = D("0.01")
    assert cost_to_settle(e, R) == D("0.01")


def _settle_via_metered(store, billed):
    lim = _limits(store, daily="1")
    err = UnusableAnswer("unusable")
    err.billed_usd = billed
    with pytest.raises(UnusableAnswer):
        MeteredLLM(Stub(err), lim, "a", ROUTES).chat([], system="", route="r")
    return store.spend_totals("a", DAY)


def _unknown_total(store):
    lim = _limits(store, daily="1")
    with pytest.raises(ProviderExhausted):
        MeteredLLM(Stub(ProviderExhausted("t")), lim, "a", ROUTES).chat([], system="", route="r")
    return store.spend_totals("a", DAY)


@pytest.mark.parametrize("absurd", ["1e999999", "1e9"])
def test_m2_an_absurd_billed_usd_books_the_worst_case_not_the_absurd_number_memory(absurd, clock):  # noqa: F811
    worst = _unknown_total(MemoryStore())
    assert worst[0] > 0
    assert _settle_via_metered(MemoryStore(), D(absurd)) == worst


@pytest.mark.parametrize("absurd", ["1e999999", "1e9"])
def test_m2_an_absurd_billed_usd_books_the_worst_case_not_the_absurd_number_postgres(
    absurd,
    roles,  # noqa: F811
    clock,  # noqa: F811
):
    store = _pg_store(roles.runtime)
    try:
        worst = _unknown_total(store)
    finally:
        store.close()
    store = _pg_store(roles.runtime)
    try:
        store.prune_spend  # noqa: B018 - the same schema: reset the counters through the owner login
        import psycopg

        with psycopg.connect(roles.owner, autocommit=True) as db:
            db.execute("DELETE FROM spend")
            db.execute("DELETE FROM spend_month")
        assert _settle_via_metered(store, D(absurd)) == worst
    finally:
        store.close()


# --- M3: UnusableAnswer is defined here and a first-attempt unusable answer is never released at zero ----------------


def test_m3_unusable_answer_is_billed_by_class_and_survives_the_retry_layer():
    assert (UnusableAnswer.answered, UnusableAnswer.refused) == (1, 0)
    R = D("0.40")
    # first attempt: stamped attempts=1 by with_retry; answered stays 1; unpriced = the reservation, never zero
    with pytest.raises(UnusableAnswer) as e:
        with_retry(
            _fail(UnusableAnswer("empty body")), label="t", max_attempts=3, sleep=lambda s: None
        )
    assert (e.value.attempts, e.value.answered, e.value.refused) == (1, 1, 0)
    assert cost_to_settle(e.value, R) == R
    # a priced one is booked at its price
    priced = UnusableAnswer("cut off")
    priced.billed_usd = D("0.02")
    with pytest.raises(UnusableAnswer) as e:
        with_retry(_fail(priced), label="t", max_attempts=3, sleep=lambda s: None)
    assert cost_to_settle(e.value, R) == D("0.02")
    # two 5xx first: their billing is unknown, so the whole reservation stays
    with pytest.raises(UnusableAnswer) as e:
        with_retry(
            _fail(Http(503), Http(503), UnusableAnswer("late")),
            label="t",
            max_attempts=3,
            sleep=lambda s: None,
        )
    assert unknown_requests(e.value) == 2 and cost_to_settle(e.value, R) == R


def test_m3_a_metered_first_attempt_unusable_answer_is_not_released(clock):  # noqa: F811
    store = MemoryStore()
    lim = _limits(store, daily="1")
    inner = SimpleNamespace(
        chat=lambda *a, **k: with_retry(
            _fail(UnusableAnswer("empty")), label="t", max_attempts=1, sleep=lambda s: None
        )
    )
    with pytest.raises(UnusableAnswer):
        MeteredLLM(inner, lim, "a", ROUTES).chat([], system="", route="r")
    assert store.spend_totals("a", DAY)[0] > 0  # a billed call is never released at zero


# --- m-a: a failed fallback keeps the primary's unknown request ----------------------------------------------------------


def test_ma_a_failed_fallback_carries_the_primarys_unknown_billing(clock):  # noqa: F811
    primary = Stub(ProviderExhausted("read timeout"))  # unknown billing, trips the breaker
    fb_err = ProviderError("fallback refused the key")  # one request, refused
    fallback = Stub(fb_err)
    llm = ResilientLLM(
        primary, fallback, CircuitBreaker(failures=1, reset_after_s=60.0), fallback_metered=True
    )
    with pytest.raises(ProviderError) as e:
        llm.chat([], system="", route="r")
    assert unknown_requests(e.value) == 1
    assert cost_to_settle(e.value, D("1")) == D("1")
    store = MemoryStore()
    lim = _limits(store, daily="1")
    primary2 = Stub(ProviderExhausted("reset"))
    llm2 = ResilientLLM(
        primary2,
        Stub(ProviderError("no")),
        CircuitBreaker(failures=1, reset_after_s=60.0),
        fallback_metered=True,
    )
    with pytest.raises(ProviderError):
        MeteredLLM(llm2, lim, "a", ROUTES).chat([], system="", route="r")
    assert store.spend_totals("a", DAY)[0] > 0


# --- m-b: a garbage attribute never raises inside the handler ------------------------------------------------------------


@pytest.mark.parametrize("junk", ["x", None, object(), float("nan"), 10**400, -5])
def test_mb_garbage_counts_keep_the_reservation_and_never_raise(junk):
    for attr in ("attempts", "answered", "refused"):
        e = ProviderExhausted("x")
        setattr(e, attr, junk)
        out = cost_to_settle(e, D("0.5"))  # must not raise
        assert out == D("0.5")
    e = ProviderError("x")
    e.attempts = "x"
    assert cost_to_settle(e, D("0.5")) == D("0.5")
    assert unknown_requests(e) == 1


# --- m-e, m-f ------------------------------------------------------------------------------------------------------------


def test_me_the_cli_hints_at_migrate_when_the_maintenance_role_lacks_the_grant(monkeypatch, capsys):
    from hadavin_sdk import cli
    from hadavin_sdk.store import migrate as migrate_mod
    from hadavin_sdk.store import postgres as postgres_mod
    from hadavin_sdk.store.protocol import StoreUnavailable

    def boom(*a, **k):
        raise StoreUnavailable("permission denied")

    store = SimpleNamespace(kind="postgres", iam_auth=False, region=None, sslmode=None)
    cfg = SimpleNamespace(backends=SimpleNamespace(store=store, secrets=None), tenant="")
    monkeypatch.setenv("HADAVIN_MAINTENANCE_DSN", "dsn-for-test")
    monkeypatch.setattr(migrate_mod, "release_reservation", boom)
    monkeypatch.setattr(postgres_mod, "ca_file", lambda *a: None)
    monkeypatch.setattr(cli, "make", lambda *a: SimpleNamespace(get=lambda n: None))
    args = SimpleNamespace(agent="a", day=datetime.date(2026, 3, 15), amount=D("1"), dry_run=False)
    assert cli._release_reservation(cfg, args) == 3
    assert "migrate --maintenance-role" in capsys.readouterr().err


def test_mf_a_non_numeric_amount_is_a_config_error_before_any_connection(monkeypatch):
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store import migrate

    monkeypatch.setattr(
        migrate, "connect", lambda *a, **k: (_ for _ in ()).throw(AssertionError("connected"))
    )
    for junk in ("abc", "", "1,5"):
        with pytest.raises(ConfigError):
            migrate.release_reservation("dsn", "a", datetime.date(2020, 1, 1), junk)
