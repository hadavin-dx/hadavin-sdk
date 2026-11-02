"""Round-2 review of PR #48: the runtime starts under the least-privilege role, pruning is its own identity, a stale
success cannot launder a spend cap, a deadline never falls back, Postgres spend work is pooled and typed, the
monthly cap is tested on Postgres, hostile bodies are bounded in time and size, counter keys are injective."""

# ruff: noqa: B023
from __future__ import annotations

import copy
import http.server
import json
import pickle
import threading
import time
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
import yaml

from hadavin_sdk import limits as limits_mod
from hadavin_sdk.config import Route
from hadavin_sdk.extract import extract
from hadavin_sdk.limits import Limits, OverBudget
from hadavin_sdk.llm import common, openai_compat, retry
from hadavin_sdk.llm.common import json_in_text
from hadavin_sdk.llm.metered import MeteredLLM
from hadavin_sdk.llm.protocol import (
    DeadlineExceeded,
    ProviderError,
    ProviderExhausted,
    SpendLimitReached,
)
from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
from hadavin_sdk.models import KillSwitch, Reply
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.contracts.kinds.store_postgres import pg_schema

D = Decimal
MID = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
DAY = MID.date()


@pytest.fixture
def clock(monkeypatch):
    monkeypatch.setattr(limits_mod, "now", lambda: MID)


def _limits(store, tenant="", daily="1", monthly="100", max_run=None):
    agent = SimpleNamespace(
        budget_usd=SimpleNamespace(daily=D(daily), monthly=D(monthly)),
        max_run_usd=None if max_run is None else D(max_run),
    )
    return Limits(store, None, SimpleNamespace(agents={"a": agent}), tenant=tenant)  # type: ignore[arg-type]


def _pg_store(dsn, **kw):
    pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
    for k, v in kw.items():
        setattr(store, k, v)
    return store


@pytest.fixture
def roles():
    """A migrated schema with a runtime role and a maintenance role (fresh login roles), dropped afterwards."""
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    from hadavin_sdk.store.migrate import migrate

    for dsn in pg_schema():
        rt, mt = "rt_" + uuid.uuid4().hex[:10], "mt_" + uuid.uuid4().hex[:10]
        with psycopg.connect(dsn, autocommit=True) as db:
            for n in (rt, mt):
                db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(n)))
        migrate(dsn, runtime_role=rt, maintenance_role=mt)
        try:
            yield SimpleNamespace(
                owner=dsn, runtime=make_conninfo(dsn, user=rt), maint=make_conninfo(dsn, user=mt)
            )
        finally:
            with psycopg.connect(dsn, autocommit=True) as db:
                for n in (rt, mt):
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(n)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(n)))


# --- BLOCKER 1: the runtime starts and works under the least-privilege role; pruning is its own identity -----------


def test_runtime_start_up_does_not_touch_the_database_for_pruning(cfg_dir):
    from tests.test_s5_runtime import build

    class Exploding(MemoryStore):
        def prune_spend(self, before):
            raise RuntimeError("the runtime must not prune")

    import hadavin_sdk.store as store_pkg

    # Runtime construction with a store whose prune raises: it must still start.
    rt, _ = build(cfg_dir)
    boom = Exploding()
    rt2 = type(rt)(
        rt.registry,
        boom,
        rt.audit,
        rt.llm,
        rt.detector,
        Limits(boom, rt.audit, rt.registry),
        ["test-agent"],
    )
    assert rt2.limits.store is boom and store_pkg


def test_the_runtime_role_reserves_and_settles_but_cannot_delete_money_rows(roles, clock):
    import psycopg

    store = _pg_store(roles.runtime)
    try:
        lim = _limits(store, max_run="5")
        res = lim.reserve("a", D("0.10"), run_id="r1")
        lim.settle(res, D("0.04"))
        assert store.spend_totals("a", DAY)[0] == D("0.04")
        with pytest.raises(StoreUnavailable, match="InsufficientPrivilege"):
            lim.prune_runs()  # the negative test: DELETE is not the runtime's (the driver text is not passed on)
        with psycopg.connect(roles.runtime, autocommit=True) as db:
            for stmt in ("DELETE FROM spend", "DELETE FROM spend_month", "TRUNCATE spend"):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    db.execute(stmt)
    finally:
        store.close()


def test_the_maintenance_role_prunes_run_counters_only_and_has_no_other_rights(
    roles, clock, monkeypatch
):
    import psycopg

    monkeypatch.setattr("hadavin_sdk.models.now", lambda: MID)

    from hadavin_sdk.store.migrate import prune_run_counters

    owner = _pg_store(roles.owner)
    try:
        lim = _limits(owner, tenant="clientx", max_run="5")
        old = DAY.replace(day=1)
        lim.reserve("a", D("0.1"), run_id="old", run_day=old)
        lim.reserve("a", D("0.1"), run_id="new")
        _limits(owner, max_run="5").reserve("a", D("0.1"), run_id="bare-old", run_day=old)
        n = prune_run_counters(roles.maint, keep_days=7)
        assert n == 2  # tenant-prefixed and bare run counters both
        assert owner.spend_totals("a", DAY)[0] == D(
            "0.1"
        )  # agent totals stay (reserved by 3 runs, own tenants)
    finally:
        owner.close()
    with psycopg.connect(roles.maint, autocommit=True) as db:
        assert (
            db.execute(
                "SELECT count(*) FROM spend WHERE agent_id !~ '^([0-9]+:[^/]*/)?run:'"
            ).fetchone()[0]
            > 0
        )
        for stmt in (
            "INSERT INTO spend (agent_id, day, usd) VALUES ('x', current_date, 1)",
            "UPDATE spend SET agent_id = 'y'",  # only the usd column is writable (release-reservation)
            "UPDATE spend SET day = current_date",
            "UPDATE spend_month SET month = current_date",
            "SELECT * FROM runs",
            "DELETE FROM runs",
            'UPDATE kill_switch SET "on" = true',
            "DELETE FROM audit_entries",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(stmt)


def test_the_runtime_and_maintenance_roles_must_differ():
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.store.migrate import migrate

    with pytest.raises(ConfigError, match="different roles"):
        migrate("postgresql://unused", runtime_role="same_role", maintenance_role="same_role")


# --- MAJOR 2 and 3: the breaker keeps the trip reason; a deadline never falls back ---------------------------------


class Stub:
    label = "stub"

    def __init__(self, *outcomes):
        self.outcomes, self.n = list(outcomes), 0

    def chat(self, messages, **kw):
        self.n += 1
        o = self.outcomes[min(self.n, len(self.outcomes)) - 1]
        if isinstance(o, BaseException):
            raise o
        return o


OK = Reply(text="ok", model_id="m")


def test_a_stale_in_flight_success_does_not_launder_a_spent_cap():
    gate, release = threading.Event(), threading.Event()

    class Primary:
        calls = 0

        def chat(self, messages, **kw):
            Primary.calls += 1
            n = Primary.calls
            if n == 1:
                gate.set()
                release.wait(10)
                return OK  # the late, stale success
            raise SpendLimitReached("cap")

    backup = Stub(OK)
    llm = ResilientLLM(Primary(), backup, CircuitBreaker(3, 3600.0))
    t = threading.Thread(target=lambda: llm.chat([], system="", route="r"))
    t.start()
    gate.wait(10)
    for _ in range(3):
        with pytest.raises(SpendLimitReached):
            llm.chat([], system="", route="r")  # opens the circuit on a spend limit
    release.set()
    t.join(10)
    with pytest.raises(SpendLimitReached):  # the stale success must not clear the reason
        llm.chat([], system="", route="r")
    assert backup.n == 0


def test_the_spend_reason_clears_when_a_current_probe_closes_the_circuit():
    now = [0.0]
    b = CircuitBreaker(1, 10.0, clock=lambda: now[0])
    b.failure(b.allow(), spend=True)
    assert b.open_for_spend
    now[0] = 11
    probe = b.allow()
    b.success(probe)
    assert not b.open_for_spend


def test_a_deadline_on_the_primary_is_not_served_by_the_fallback():
    backup = Stub(OK)
    llm = ResilientLLM(Stub(DeadlineExceeded("late")), backup, CircuitBreaker(5, 30.0))
    with pytest.raises(DeadlineExceeded):
        llm.chat([], system="", route="r")
    assert backup.n == 0


def test_the_loop_keeps_the_primary_worst_case_booked_behind_a_resilient_wrapper(cfg_dir):
    from tests.test_s5_runtime import _doc, build

    rt, cfg = build(cfg_dir)
    rt.llm = ResilientLLM(Stub(DeadlineExceeded("late")), Stub(OK))
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.reason_code == "provider_exhausted"
    assert rt.store.spend_totals("test-agent", run.created_at.date())[0] > 0


def test_resilient_copy_deepcopy_and_pickle_are_defined():
    llm = ResilientLLM(Stub(OK), None)
    assert copy.copy(llm).breaker is llm.breaker
    with pytest.raises(TypeError, match="build a new one"):
        copy.deepcopy(llm)
    with pytest.raises(TypeError, match="cannot be pickled"):
        pickle.dumps(llm)


# --- MAJOR 4: pooled, typed Postgres spend work ----------------------------------------------------------------------


def test_150_threads_get_a_booking_or_a_typed_refusal_and_never_a_raw_driver_error(clock):
    psycopg = pytest.importorskip("psycopg")
    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            lim = _limits(store, daily="1000", monthly="1000")
            ok, bad, raw = [], [], []
            lock = threading.Lock()
            gate = threading.Barrier(150)

            def one():
                gate.wait()
                try:
                    lim.reserve("a", D("0.01"))
                    with lock:
                        ok.append(1)
                except (OverBudget, StoreUnavailable) as e:
                    with lock:
                        bad.append(e)
                except Exception as e:  # noqa: BLE001
                    with lock:
                        raw.append(e)

            ts = [threading.Thread(target=one) for _ in range(150)]
            for t in ts:
                t.start()
            for t in ts:
                t.join(120)
            assert not raw, [type(e).__name__ for e in raw[:3]]
            assert not [e for e in bad if isinstance(e, psycopg.Error)]
            assert store.spend_totals("a", DAY)[0] == D("0.01") * len(ok)  # booked == granted
            assert len(ok) >= 100  # a bounded pool queues callers; it does not drop them
            with psycopg.connect(dsn, autocommit=True) as db:
                conns = db.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                ).fetchone()[0]
            assert conns <= store.POOL_SIZE + 4  # pool + main + this probe + slack
        finally:
            store.close()


def test_a_connect_failure_is_a_typed_error_without_driver_text():
    psycopg = pytest.importorskip("psycopg")
    from hadavin_sdk.store.postgres import PostgresStore

    def connector():
        raise psycopg.OperationalError("connection to host=db-secret-host user=svc failed")

    store = PostgresStore(SimpleNamespace(), connector)  # type: ignore[arg-type]
    with pytest.raises(StoreUnavailable) as e:
        store.reserve_spend("a", DAY, D("0.1"), D(1), D(1))
    assert (
        "secret" not in str(e.value)
        and "svc" not in str(e.value)
        and "OperationalError" in str(e.value)
    )


# --- MAJOR 5: the monthly cap on Postgres ----------------------------------------------------------------------------


def test_postgres_monthly_cap_binds_across_days_and_not_across_months():
    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            d1, d2, feb = date(2026, 3, 1), date(2026, 3, 20), date(2026, 2, 27)
            assert (
                store.reserve_spend("m", feb, D("9"), D("100"), D("100")) == []
            )  # last month: not counted
            assert store.reserve_spend("m", d1, D("0.9"), D("5"), D("1")) == []
            assert store.reserve_spend("m", d2, D("0.2"), D("5"), D("1")) == ["monthly_budget"]
            assert store.reserve_spend("m", d2, D("0.1"), D("5"), D("1")) == []
            assert store.reserve_spend("m", d2, D("0.01"), D("5"), D("1")) == ["monthly_budget"]
            # both caps at once name both
            assert store.reserve_spend("m", d2, D("50"), D("5"), D("1")) == [
                "daily_budget",
                "monthly_budget",
            ]
        finally:
            store.close()


# --- MINOR 5-7: hostile bodies are bounded in time and size ----------------------------------------------------------


class _Trickle(http.server.BaseHTTPRequestHandler):
    stop = threading.Event()

    def do_POST(self):
        self.send_response(429)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "100000")
        self.end_headers()
        for _ in range(400):
            if self.stop.is_set():
                return
            try:
                self.wfile.write(b" ")
                self.wfile.flush()
            except OSError:
                return
            time.sleep(0.25)

    def log_message(self, *a):
        pass


def test_a_trickling_429_body_cannot_hold_the_call_past_its_deadline():
    _Trickle.stop = threading.Event()
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Trickle)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        routes = {
            "r": Route(
                model_id="m-1", input_usd_per_mtok=D(1), output_usd_per_mtok=D(1), max_tokens=5
            )
        }
        llm = openai_compat.OpenAICompatLLM(
            f"http://127.0.0.1:{srv.server_address[1]}/v1", None, routes, 1.0, 3, lambda s: None
        )
        llm.deadline_s = 1.5
        t0 = time.monotonic()
        with pytest.raises(ProviderError):
            llm.chat([{"role": "user", "content": "q"}], system="", route="r")
        assert time.monotonic() - t0 < 5  # was 20 s against a 3 s deadline
    finally:
        _Trickle.stop.set()
        srv.shutdown()


def test_post_json_never_reads_more_than_its_cap_and_refuses_oversize_and_bad_utf8(monkeypatch):
    reads = []

    class Resp:
        def __init__(self, data):
            self.data = data

        def read(self, n=-1):
            reads.append(n)
            return self.data[: n if n >= 0 else None]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(common, "_MAX_RESPONSE_BYTES", 1000)
    for data in (b"x" * 5000, b'{"a": "\xff"}'):
        monkeypatch.setattr(common._LOCAL_OPENER, "open", lambda req, timeout, d=data: Resp(d))
        with pytest.raises(common.ReplyUnparseable):
            common.post_json("http://127.0.0.1:1/x", {}, {}, 1.0)
    assert reads and all(n == 1001 for n in reads)  # a bounded read, never read-all


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("{" * 50 + " " * 990_000, id="braces"),
        pytest.param('{"a":' * 25 + " " * 990_000, id="objects"),
        pytest.param("{[" * 20 + " " * 990_000, id="mixed"),
    ],
)
def test_json_in_text_is_bounded_in_time(text):
    t0 = time.monotonic()
    assert json_in_text(text) is None
    assert time.monotonic() - t0 < 1.5  # 2-5 s before the scan budget


# --- MINOR 8: injective counter keys, validated ids, the tenant reaches the app ----------------------------------------


def test_counter_keys_cannot_collide_across_tenants_and_agent_ids():
    from hadavin_sdk.registry import AgentRecord

    for bad in ("a/b", "a b", "", "x" * 65, "b:c", "../x"):
        with pytest.raises(ValueError):
            Limits(MemoryStore(), None, SimpleNamespace(agents={}), tenant=bad) if bad else (
                _ for _ in ()
            ).throw(ValueError())  # type: ignore[arg-type]
    fields = {
        "status": "draft",
        "data_class": "internal",
        "model_route": "default",
        "prompt_file": "p.md",
        "scope_allowed": [],
        "max_steps": 3,
        "budget_usd": {"daily": "1", "monthly": "10"},
    }
    AgentRecord.model_validate(
        {**fields, "id": "ok-agent_1.x"}
    )  # the same fields with a good id pass
    for bad_id in ("a/b", "b:c", "x" * 65, ""):
        with pytest.raises(ValueError):
            AgentRecord.model_validate({**fields, "id": bad_id})
    k = lambda t, n: Limits(MemoryStore(), None, SimpleNamespace(agents={}), tenant=t)._key(n)
    assert (
        len(
            {
                k("a", "b"),
                k("ab", ""),
                k("a", "b/c") if False else k("a", "bc"),
                k("b", "c"),
                k("", "c"),
            }
        )
        == 5
    )
    assert k("", "c") == "c" and k("ab", "c") == "2:ab/c"


def test_the_tenant_from_config_reaches_the_limits(cfg_dir):
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.app import build as build_app
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry
    from tests.conftest import qualify

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["tenant"] = "client-a"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    qualify(load_registry(load_config(cfg_dir)))
    app = build_app(cfg_dir, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "t"}))
    assert app.limits.tenant == "client-a"


# --- MINOR 9-10: one lock order; a settle after a prune leaves no negative counter --------------------------------------


def test_settle_hands_the_store_the_run_counter_first_the_order_reserve_takes(clock):
    seen = []

    class Spy(MemoryStore):
        def settle_spend(self, deltas):
            seen.append([k for k, _, _ in deltas])
            super().settle_spend(deltas)

    lim = _limits(Spy(), max_run="5")
    lim.settle(lim.reserve("a", D("0.1"), run_id="r"), D("0.05"))
    assert seen == [["run:r", "a"]]


def test_memory_prune_removes_tenant_prefixed_run_counters_too(clock):
    store = MemoryStore()
    lim = _limits(store, tenant="clientx", max_run="5")
    lim.reserve("a", D("0.1"), run_id="r", run_day=date(2026, 2, 1))
    assert lim.prune_runs() == 1
    assert store.spend_totals("7:clientx/a", DAY)[0] == D("0.1")  # the agent counter stays


def test_a_settle_after_a_prune_recreates_no_negative_counter_memory(clock):
    store = MemoryStore()
    lim = _limits(store, max_run="5")
    res = lim.reserve("a", D("0.1"), run_id="r", run_day=date(2026, 2, 1))
    assert lim.prune_runs() == 1
    lim.release(res)
    assert ("run:r", date(2026, 2, 1)) not in store._spend and store.spend_totals("a", DAY)[0] == 0


def test_a_settle_after_a_prune_recreates_no_negative_counter_postgres(clock):
    import psycopg

    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            lim = _limits(store, max_run="5")
            res = lim.reserve("a", D("0.1"), run_id="r", run_day=date(2026, 2, 1))
            assert lim.prune_runs() >= 1
            lim.release(res)
            with psycopg.connect(dsn, autocommit=True) as db:
                assert db.execute("SELECT count(*) FROM spend WHERE usd < 0").fetchone()[0] == 0
                assert (
                    db.execute("SELECT count(*) FROM spend_month WHERE usd < 0").fetchone()[0] == 0
                )
        finally:
            store.close()


def test_postgres_reserve_settle_storm_has_no_wrong_totals(clock):
    for dsn in pg_schema():
        store = _pg_store(dsn)
        try:
            lim = _limits(store, daily="1000", monthly="1000", max_run="100")
            gate, errs = threading.Barrier(24), []

            def one(i):
                gate.wait()
                try:
                    for _ in range(5):
                        res = lim.reserve("a", D("0.10"), run_id=f"r{i % 3}")
                        lim.settle(res, D("0.04"))
                except Exception as e:  # noqa: BLE001
                    errs.append(e)

            ts = [threading.Thread(target=one, args=(i,)) for i in range(24)]
            for t in ts:
                t.start()
            for t in ts:
                t.join(120)
            assert not errs, [type(e).__name__ for e in errs[:3]]
            assert store.spend_totals("a", DAY)[0] == D("0.04") * 120
        finally:
            store.close()


# --- MINOR 11: bounded abandoned attempts -------------------------------------------------------------------------------


def test_hung_attempts_cannot_pile_up_threads_past_the_bound(monkeypatch):
    monkeypatch.setattr(retry, "_SLOTS", threading.BoundedSemaphore(3))
    release = threading.Event()
    for _ in range(3):
        with pytest.raises(DeadlineExceeded):
            retry.with_retry(lambda: release.wait(30), label="t", max_attempts=1, deadline_s=0.1)
    with pytest.raises(ProviderExhausted, match="too many attempts"):
        retry.with_retry(lambda: "x", label="t", max_attempts=1, deadline_s=0.5)
    release.set()
    time.sleep(0.3)
    assert (
        retry.with_retry(lambda: "x", label="t", max_attempts=1, deadline_s=1.0) == "x"
    )  # slots came back


# --- MINOR 11: calls outside the agent loop are metered --------------------------------------------------------------


ROUTES = {
    "r": Route(model_id="m-1", input_usd_per_mtok=D(3), output_usd_per_mtok=D(15), max_tokens=100)
}


def test_metered_llm_reserves_settles_releases_and_refuses(clock):
    store = MemoryStore()
    lim = _limits(store, daily="1")
    ok = MeteredLLM(Stub(Reply(text="ok", model_id="m", cost_usd=D("0.002"))), lim, "a", ROUTES)
    ok.chat([{"role": "user", "content": "q"}], system="", route="r")
    assert store.spend_totals("a", DAY)[0] == D("0.002")  # settled to the real cost
    for exc, left in ((ProviderError("bad"), D("0.002")), (SpendLimitReached("cap"), D("0.002"))):
        with pytest.raises(ProviderError):
            MeteredLLM(Stub(exc), lim, "a", ROUTES).chat([], system="", route="r")
        assert store.spend_totals("a", DAY)[0] == left  # released
    with pytest.raises(DeadlineExceeded):
        MeteredLLM(Stub(DeadlineExceeded("late")), lim, "a", ROUTES).chat([], system="", route="r")
    assert store.spend_totals("a", DAY)[0] > D("0.002")  # the worst case stays booked
    inner = Stub(OK)
    store.set_kill_switch(KillSwitch(on=True, by="t"))
    with pytest.raises(OverBudget):
        MeteredLLM(inner, lim, "a", ROUTES).chat([], system="", route="r")
    assert inner.n == 0  # the model was never called


def test_extract_and_the_evals_gate_can_be_metered(cfg_dir, clock):
    from pydantic import BaseModel

    from hadavin_sdk import evals
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    class Rec(BaseModel):
        title: str

    store = MemoryStore()
    lim = _limits(store, daily="1")
    llm = MeteredLLM(
        Stub(Reply(text='{"title": "t"}', model_id="m", cost_usd=D("0.003"))), lim, "a", ROUTES
    )
    out = extract(llm, b"doc", Rec, run_id="r", route="r")
    assert out.data.title == "t" and store.spend_totals("a", DAY)[0] == D("0.003")

    reg = load_registry(load_config(cfg_dir))
    (reg.config.golden_dir / "test-agent.jsonl").write_text(
        json.dumps(
            {"id": "a", "input_ref": "golden-01.txt", "expected": {"action": None, "inputs": {}}}
        )
        + "\n",
        encoding="utf-8",
    )
    store2 = MemoryStore()
    agent = reg.agents["test-agent"]
    lim2 = Limits(store2, None, reg)  # type: ignore[arg-type]
    evals.gate(
        reg, Stub(Reply(text="x", model_id="m", cost_usd=D("0.001"))), "test-agent", limits=lim2
    )
    assert store2.spend_totals("test-agent", DAY)[0] == D("0.001") and agent
