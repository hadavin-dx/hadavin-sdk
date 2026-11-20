"""Review F6, M1 and M2: a negative, NaN or infinite cost never reaches a counter; a provider's bad token count is
a ProviderError; the PostgreSQL settle delta is computed in our Decimal context; no `-0` is stored."""

from __future__ import annotations

import decimal
import os
import uuid
from datetime import date
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from hadavin_sdk.limits import Budget, Limits
from hadavin_sdk.llm import common
from hadavin_sdk.llm.protocol import ProviderError
from hadavin_sdk.models import Run
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import SpendCapExceeded
from tests.test_limits_reserve import Sink, _registry

DAY = date(2026, 3, 5)
ROUTE = SimpleNamespace(
    model_id="m", input_usd_per_mtok=D(3), output_usd_per_mtok=D(15), max_tokens=10
)
BAD = [D(-100), D("-0.000001"), D("NaN"), D("Infinity"), D("-Infinity"), D("1E+9"), 5, 0.5, "1"]


def _pg_stores():
    dsn = os.environ.get("HADAVIN_TEST_PG_DSN")
    if not dsn:
        return
    psycopg = pytest.importorskip("psycopg")
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate
    from hadavin_sdk.store.postgres import PostgresStore, connect

    schema = "r6_" + uuid.uuid4().hex[:10]
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    scoped = make_conninfo(dsn, options=f"-c search_path={schema}")
    migrate(scoped, no_roles=True)
    try:
        yield PostgresStore(connect(scoped))
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture(params=["memory", "pg"])
def store(request):
    if request.param == "memory":
        yield MemoryStore()
        return
    gen = _pg_stores()
    if gen is None:
        pytest.skip("HADAVIN_TEST_PG_DSN not set")
    yield from gen


def _run(store, run_id="r1"):
    store.create_run(
        Run(run_id=run_id, agent_id="ag", principal_id="p", trigger_kind="user", trigger_ref="t")
    )


@pytest.mark.parametrize("bad", BAD, ids=repr)
def test_add_spend_refuses_bad_amount(store, bad):
    store.reserve_spend("hold1", "ag", DAY, D(4), day_cap=D(5), month_cap=D(50))
    with pytest.raises(ValueError):
        store.add_spend("ag", DAY, bad)
    assert store.spend_totals("ag", DAY) == (D(4), D(4))
    with pytest.raises(SpendCapExceeded):  # the cap still holds
        store.reserve_spend("h2", "ag", DAY, D(2), day_cap=D(5), month_cap=D(50))


@pytest.mark.parametrize("bad", BAD, ids=repr)
def test_add_cost_refuses_bad_amount(store, bad):
    _run(store)
    with pytest.raises(ValueError):
        store.add_cost("r1", bad)
    assert store.get_run("r1").cost_usd == 0


def test_add_spend_and_cost_still_work(store):
    _run(store)
    store.add_cost("r1", D("0.25"))
    assert store.get_run("r1").cost_usd == D("0.25")
    assert store.add_spend("ag", DAY, D("0.25")) == (D("0.25"), D("0.25"))


def _limits():
    store = MemoryStore()
    return store, Limits(store, Sink(), _registry())


@pytest.mark.parametrize("bad", BAD, ids=repr)
def test_limits_charge_refuses_bad_amount(bad):
    _, limits = _limits()
    with pytest.raises(ValueError):
        limits.charge("ag", bad)


@pytest.mark.parametrize("bad", BAD, ids=repr)
def test_budget_charge_refuses_bad_amount(bad):
    budget = Budget(D(5))
    budget.charge(D(1))
    with pytest.raises(ValueError):
        budget.charge(bad)
    assert budget.spent == D(1)


@pytest.mark.parametrize("neg", [-1_000_000_000, -1])
def test_reply_negative_tokens_is_provider_error(neg):
    for tokens in ((neg, 5), (5, neg)):
        with pytest.raises(ProviderError, match="bad_usage"):
            common.reply(ROUTE, text="x", calls=[], tokens=tokens, stop=None, started=0.0, sent="s")


@pytest.mark.parametrize("odd", [1.5, "7", D(2), True])
def test_reply_non_integer_tokens_is_provider_error(odd):
    with pytest.raises(ProviderError, match="bad_usage"):
        common.reply(ROUTE, text="x", calls=[], tokens=(odd, 5), stop=None, started=0.0, sent="s")


def test_reply_missing_or_zero_tokens_still_estimated():
    r = common.reply(ROUTE, text="x", calls=[], tokens=(None, 0), stop=None, started=0.0, sent="s")
    assert r.cost_usd >= 0 and r.input_tokens > 0


def test_reply_cost_with_many_decimals_is_a_valid_amount():
    route = SimpleNamespace(
        model_id="m", input_usd_per_mtok=D("0.1234567"), output_usd_per_mtok=D(1), max_tokens=1
    )
    r = common.reply(route, text="x", calls=[], tokens=(3, 3), stop=None, started=0.0, sent="s")
    from hadavin_sdk.store.protocol import check_spend_amount

    check_spend_amount(r.cost_usd)
    assert r.cost_usd >= D(3) * route.input_usd_per_mtok / D(1_000_000)  # rounded up, never down


def test_fake_llm_negative_usage_is_provider_error(tmp_path):
    import hashlib
    import json

    from hadavin_sdk.llm.fake import FakeLLM

    msgs = [{"role": "user", "content": "hi"}]
    digest = hashlib.sha256(json.dumps(msgs, sort_keys=True).encode()).hexdigest()
    (tmp_path / f"{digest}-1.json").write_text(
        json.dumps(
            {
                "text": "x",
                "input_tokens": -1_000_000_000,
                "output_tokens": 5,
                "stop_reason": "end_turn",
                "tool_calls": [],
                "latency_ms": 1,
            }
        )
    )
    llm = FakeLLM(tmp_path, {"r": ROUTE})
    with pytest.raises(ProviderError, match="bad_usage"):
        llm.chat(msgs, system="", route="r")


def test_pg_settle_delta_in_our_context_prec5():
    gen = _pg_stores()
    if gen is None:
        pytest.skip("HADAVIN_TEST_PG_DSN not set")
    for st in gen:
        st.reserve_spend("x1", "ag", DAY, D("0.5"), day_cap=D(10), month_cap=D(10))
        with decimal.localcontext() as ctx:
            ctx.prec = 5
            st.settle_spend("x1", D("0.123456789012"))
        assert st.spend_totals("ag", DAY) == (D("0.123456789012"), D("0.123456789012"))


def test_memory_settle_prec5_same_result():
    st = MemoryStore()
    st.reserve_spend("x1", "ag", DAY, D("0.5"), day_cap=D(10), month_cap=D(10))
    with decimal.localcontext() as ctx:
        ctx.prec = 5
        st.settle_spend("x1", D("0.123456789012"))
    assert st.spend_totals("ag", DAY) == (D("0.123456789012"), D("0.123456789012"))


def test_negative_zero_is_not_stored(store):
    store.reserve_spend("z", "ag", DAY, D("-0"), day_cap=D(1), month_cap=D(1))
    store.add_spend("ag", DAY, D("-0"))
    for value in store.spend_totals("ag", DAY):
        assert not value.is_signed()
    if isinstance(store, MemoryStore):
        assert not store._reservations["z"].reserved_usd.is_signed()
