"""P4d-a2-ii, Postgres only: the write wrapper (error mapping, retry, timeouts, the budget, the re-entrant lock).
Unit rows use a stub connection and driver error objects built by `drv.make_error`; the rest use a real server."""

import ast
import contextlib
import re
import signal
import threading
import time
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make as make_store_kind
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    ChainStep,
    DeadLetter,
    GateDecision,
    KillSwitch,
    Plan,
    Run,
    RunState,
    Target,
    TickState,
    ToolCallRecord,
    now,
)
from hadavin_sdk.store.postgres import PostgresStore, _writes
from hadavin_sdk.store.protocol import (
    NotFound,
    StaleState,
    StoreBusy,
    StoreUnavailable,
    is_connectivity_error,
)
from tests.contracts.kinds.store_postgres import pg_driver, pg_schema
from tests.contracts.store_support import utc_today

drv = pg_driver(module_level=True)
BASE = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}  # a secret NAME, not a secret
# What a finished call may raise here: a Protocol error, or the refusal of the purge by the runtime login.
EXPECTED = (ValueError, KeyError, RuntimeError, type(drv.make_error("42501")))
SRC = Path(__file__).parents[2] / "src/hadavin_sdk/store/postgres.py"

# The 22 write methods of PostgresStore (18 existing, 4 of P4d-b). ONE list: the scan test below compares it with
# the methods that carry `@_writes`, and the lone-caller row runs every name in it.
WRITE_METHODS = [
    "create_run", "transition", "add_cost", "touch", "save_plan", "save_gate_decision",
    "save_approval_request", "update_approval_request", "record_decision", "save_approval_decision",
    "add_dead_letter", "add_spend", "set_kill_switch", "save_tick_state", "add_tool_call",
    "purge_tool_calls", "put_redaction_map", "purge_redaction_maps",
    "reserve_spend", "settle_spend", "release_spend", "sweep_spend_reservations",
]  # fmt: skip
NO_RETRY = {"add_spend", "add_cost", "add_dead_letter", "touch"}


class _Conn:
    """A stand-in connection: a transaction that lets errors through, and statements that are only recorded."""

    def __init__(self):
        self.sent = []

    @contextlib.contextmanager
    def transaction(self):
        yield

    def execute(self, query, params=()):
        self.sent.append((query, params))


class Probe(PostgresStore):
    """One write wrapped like the others; `plan` runs inside the attempt."""

    @_writes()
    def op(self, plan):
        return plan(self)

    @_writes(retry=False)
    def keyless(self, plan):
        return plan(self)


def _stub(**kw):
    return Probe(_Conn(), **kw)


def _fail_times(code, n, result="ok"):
    state = {"calls": 0}

    def plan(_store):
        state["calls"] += 1
        if state["calls"] <= n:
            raise drv.make_error(code)
        return result

    return plan, state


# --- error mapping (no database) -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("23503", NotFound),
        ("23514", ValueError),
        ("23502", ValueError),
        ("22021", ValueError),
        ("22003", ValueError),
        ("54000", ValueError),
        ("23505", StaleState),
        ("55P03", StoreBusy),
        ("57014", StoreBusy),
    ],
)
def test_driver_errors_become_protocol_errors(code, expected):
    store = _stub()
    plan, state = _fail_times(code, 99)
    with pytest.raises(expected) as caught:
        store.op(plan)
    assert state["calls"] == 1  # none of these is retried
    assert "made-up error" not in str(
        caught.value
    )  # the driver text can carry values: never copied
    assert caught.value.__cause__ is None


@pytest.mark.parametrize("code", ["08006", "42501", "42P01", "40003"])
def test_connection_schema_privilege_and_unknown_outcome_errors_pass_through_unchanged(code):
    store = _stub()
    error = drv.make_error(code)

    def plan(_store):
        raise error

    with pytest.raises(type(error)) as caught:
        store.op(plan)
    assert caught.value is error


# --- retry ------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "times"), [("40P01", 1), ("40001", 1), ("40P01", 2), ("40001", 2)]
)
def test_a_deadlock_or_serialization_failure_is_retried_and_counted(code, times):
    seen = []
    store = _stub(on_retry=lambda sqlstate, attempt: seen.append((sqlstate, attempt)))
    plan, state = _fail_times(code, times)
    assert store.op(plan) == "ok"
    assert state["calls"] == times + 1
    assert seen == [(code, n) for n in range(1, times + 1)]


def test_three_attempts_at_most_then_store_busy():
    seen = []
    store = _stub(on_retry=lambda sqlstate, attempt: seen.append(attempt))
    plan, state = _fail_times("40P01", 99)
    with pytest.raises(StoreBusy):
        store.op(plan)
    assert state["calls"] == 3
    assert seen == [1, 2]


@pytest.mark.parametrize("code", ["40003", "23505", "55P03"])
def test_other_errors_are_never_retried(code):
    seen = []
    store = _stub(on_retry=lambda *a: seen.append(a))
    plan, state = _fail_times(code, 99)
    with contextlib.suppress(Exception):  # the type is checked by the mapping rows
        store.op(plan)
    assert (state["calls"], seen) == (1, [])


@pytest.mark.parametrize("code", ["40P01", "40001"])
def test_a_keyless_write_raises_store_busy_at_once_with_no_retry(code):
    seen = []
    store = _stub(on_retry=lambda *a: seen.append(a))
    plan, state = _fail_times(code, 1)
    with pytest.raises(StoreBusy):
        store.keyless(plan)
    assert (state["calls"], seen) == (1, [])


def test_the_keyless_writes_are_exactly_the_four_named():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PostgresStore")
    keyless = set()
    for fn in cls.body:
        for d in getattr(fn, "decorator_list", []):
            if (
                isinstance(d, ast.Call)
                and getattr(d.func, "id", "") == "_writes"
                and any(k.arg == "retry" and k.value.value is False for k in d.keywords)
            ):
                keyless.add(fn.name)
    assert keyless == NO_RETRY


def test_the_retry_sleep_holds_neither_the_lock_nor_a_transaction():
    """The hook runs between two attempts (where the sleep is). A second thread must get the store's lock then."""
    got = {}

    def hook(_sqlstate, _attempt):
        done = threading.Event()

        def other():
            with store._lock:  # a plain lock held by the sleeping thread would block this forever
                got["lock"] = True
            done.set()

        threading.Thread(target=other, daemon=True).start()
        got["free"] = done.wait(5)

    store = _stub(on_retry=hook)
    plan, _ = _fail_times("40P01", 1)
    assert store.op(plan) == "ok"
    assert got == {"lock": True, "free": True}


def test_a_wrapped_write_called_from_inside_another_joins_its_transaction_and_budget():
    store = _stub()
    seen = []

    def inner(s):
        seen.append(s._deadline)
        return "inner"

    def outer(s):
        before = s._deadline
        assert s.keyless(inner) == "inner"
        assert s._deadline == before  # the nested call must not clear the outer call's deadline
        return "outer"

    assert store.op(outer) == "outer"
    assert len([q for q, _ in store._db.sent if "set_config" in q]) == 1
    assert seen[0] is not None
    assert store._deadline is None


@pytest.mark.parametrize(
    "bad",
    [
        {"lock_timeout_ms": 99},
        {"lock_timeout_ms": 60001},
        {"call_budget_ms": 499},
        {"call_budget_ms": 60001},
    ],
)
def test_the_two_settings_have_ranges(bad):
    with pytest.raises(ValueError):
        PostgresSettings(**BASE, **bad)


def test_build_passes_the_settings_to_the_store(dsn):
    settings = PostgresSettings(**BASE, lock_timeout_ms=123, call_budget_ms=4567)
    store = make_store_kind("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
    try:
        assert (store._lock_timeout_ms, store._call_budget_ms) == (123, 4567)
        defaults = make_store_kind(
            "store",
            PostgresSettings(**BASE),
            FakeSecretProvider({"pg-dsn": dsn}),
        )
        assert (defaults._lock_timeout_ms, defaults._call_budget_ms) == (1000, 5000)
        defaults._db.close()
    finally:
        store._db.close()


def test_a_spent_budget_is_store_busy_before_anything_is_sent():
    store = _stub()
    store._call_budget_ms = (
        0  # the constructor refuses 0 (BN N5); a budget spent in time looks the same
    )
    plan, state = _fail_times("40P01", 0)
    with pytest.raises(StoreBusy):
        store.op(plan)
    assert state["calls"] == 0
    assert store._db.sent == []


def test_a_retry_after_the_budget_ran_out_during_the_back_off_is_store_busy():
    store = _stub(call_budget_ms=500, on_retry=lambda *a: time.sleep(0.6))
    plan, state = _fail_times("40P01", 99)
    with pytest.raises(StoreBusy):
        store.op(plan)
    assert state["calls"] == 1  # the second attempt never started


def test_budget_is_shared_across_retries_and_a_spent_budget_stops_the_loop():
    store = _stub(call_budget_ms=500)
    t0 = time.monotonic()
    plan, state = _fail_times("40P01", 99)
    with pytest.raises(StoreBusy):
        store.op(plan)
    assert time.monotonic() - t0 < 5
    assert state["calls"] == 3


# --- is_connectivity_error -------------------------------------------------------------------------------------


@pytest.mark.parametrize("code", ["40001", "40P01", "55P03", "57014", "42P01", "42501"])
def test_sqlstates_of_an_answering_server_are_not_connectivity(code):
    assert is_connectivity_error(drv.make_error(code)) is False


def test_store_busy_is_not_connectivity_and_real_connection_trouble_is():
    assert is_connectivity_error(StoreBusy("x")) is False
    assert is_connectivity_error(drv.make_error("08006")) is True
    assert is_connectivity_error(StoreUnavailable("x")) is True
    assert is_connectivity_error(ConnectionRefusedError()) is True


# --- the scan: every write method is wrapped, no method sends SQL around `_exec` ----------------------------------


def _class_methods():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PostgresStore")
    return tree, [n for n in cls.body if isinstance(n, ast.FunctionDef)]


def test_the_wrapped_methods_are_exactly_WRITE_METHODS():
    _, methods = _class_methods()
    wrapped = {
        m.name
        for m in methods
        if any(
            (isinstance(d, ast.Call) and getattr(d.func, "id", "") == "_writes")
            for d in m.decorator_list
        )
    }
    assert wrapped == set(WRITE_METHODS)
    assert len(WRITE_METHODS) == len(set(WRITE_METHODS)) == 22


def test_no_public_method_with_a_write_name_lacks_the_wrapper():
    """The sibling check: a write added later under a write-looking name cannot skip the decorator."""
    _, methods = _class_methods()
    pattern = re.compile(
        r"(create_|transition|add_|touch|save_|update_|record_|set_|put_|purge_|reserve_|settle_|release_|sweep_)"
    )
    looks_like_a_write = {
        m.name for m in methods if not m.name.startswith("_") and pattern.match(m.name)
    }
    assert looks_like_a_write == set(WRITE_METHODS)


def test_sql_leaves_only_through_exec_and_the_wrappers_first_statement():
    tree, _ = _class_methods()
    allowed = {"connect", "_exec", "_write", "attempt"}  # `attempt` is inside `_write`
    offenders = []
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name not in allowed:
            for node in ast.walk(fn):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"execute", "executemany", "cursor"}
                ):
                    offenders.append((fn.name, node.lineno))
    assert offenders == []


# --- real server ------------------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _watchdog():
    """A store whose lock is not re-entrant makes a call wait for itself for ever. Turn that into a failure."""

    def stop(_signum, _frame):
        raise AssertionError("the test ran over 60 s: a call is waiting for its own lock")

    old = signal.signal(signal.SIGALRM, stop)
    signal.alarm(60)
    yield
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old)


@pytest.fixture
def dsn():
    yield from pg_schema(runtime=True)


@pytest.fixture
def make(dsn):
    opened = []

    def build(cls=PostgresStore, **kw):
        conn = drv.connect_runtime(dsn)
        opened.append(conn)
        return cls(conn, **kw)

    yield build
    for conn in opened:
        conn.close()


@pytest.fixture
def admin(dsn):
    with drv.connect_admin(dsn, autocommit=False) as conn:
        yield conn


def _new_run(store):
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


def _request(store, approval_id="apr-1"):
    req = ApprovalRequest(
        approval_id=approval_id,
        run_id="run-x",
        plan_hash="h",
        risk_class="reversible",
        chain_id="c",
        steps=[ChainStep(approver_ids=["user:a"], timeout_s=60)],
        status="PENDING",
        step_expires_at=now() + timedelta(minutes=1),
        requested_by="svc:a",
        summary="s",
    )
    store.save_approval_request(req)
    return req


@pytest.mark.parametrize(
    ("settings", "ceiling"),
    [
        ({"lock_timeout_ms": 100, "call_budget_ms": 60000}, 10),
        ({"lock_timeout_ms": 60000, "call_budget_ms": 500}, 10),
    ],
    ids=["T1-lock-timeout-100", "T2-budget-500"],
)
def test_a_lock_that_is_never_released_gives_store_busy_for_three_kinds_of_write(
    make, admin, settings, ceiling
):
    """T1 (the lock timeout alone cuts the wait) and T2 (the lock wait is cut to the remaining budget)."""
    store = make(**settings)
    run = _new_run(store)
    store.add_spend("a", date(2030, 1, 1), Decimal(1))
    req = _request(store)
    probes = {
        "transition": lambda: store.transition(run.run_id, RunState.RECEIVED, RunState.WORKING),
        "add_spend": lambda: store.add_spend("a", date(2030, 1, 1), Decimal(1)),
        "record_decision": lambda: store.record_decision(
            ApprovalDecision(
                approval_id="apr-1",
                plan_hash="h",
                step=0,
                decision="approve",
                approver_id="user:a",
                channel="fake",
            ),
            req.model_copy(update={"status": "APPROVED"}),
            "PENDING",
            0,
        ),
    }
    locks = {
        "transition": "SELECT 1 FROM runs WHERE run_id = %s FOR UPDATE",
        "add_spend": "SELECT 1 FROM spend WHERE agent_id = %s FOR UPDATE",
        "record_decision": "SELECT 1 FROM approval_requests WHERE approval_id = %s FOR UPDATE",
    }
    keys = {"transition": run.run_id, "add_spend": "a", "record_decision": "apr-1"}
    for name, call in probes.items():
        admin.execute(locks[name], (keys[name],))  # held, never released within the call
        t0 = time.monotonic()
        with pytest.raises(StoreBusy):
            call()
        assert time.monotonic() - t0 < ceiling, name
        admin.rollback()
    assert store.get_run(run.run_id).state is RunState.RECEIVED  # nothing half-applied


class _SettingsProbe(PostgresStore):
    seen: list

    @_writes()
    def read_settings(self, fail_first_with=None):
        row = self._exec(
            "SELECT current_setting('lock_timeout') AS l, current_setting('statement_timeout') AS s"
        ).fetchone()
        self.seen.append((_ms(row["l"]), _ms(row["s"])))
        if fail_first_with and len(self.seen) == 1:
            raise drv.make_error(fail_first_with)
        return self.seen[-1]


def _ms(text):
    n = re.fullmatch(r"(\d+)(ms|s|min)?", text)
    return int(n.group(1)) * {"ms": 1, "s": 1000, "min": 60000, None: 1}[n.group(2)]


def test_T3_both_timeouts_are_set_on_the_connection_and_shrink_on_a_retry(make):
    store = make(_SettingsProbe, lock_timeout_ms=100, call_budget_ms=60000)
    store.seen = []
    lock, stmt = store.read_settings()
    assert lock == 100 and 0 < stmt <= 60000
    store = make(
        _SettingsProbe,
        lock_timeout_ms=60000,
        call_budget_ms=500,
        on_retry=lambda *a: time.sleep(0.05),
    )
    store.seen = []
    store.read_settings(fail_first_with="40P01")
    (l1, s1), (l2, s2) = store.seen
    assert 0 < l1 <= 500 and 0 < s1 <= 500
    assert l2 < l1 and s2 < s1  # the retry's values come from the REMAINING budget


class _HeldRows(PostgresStore):
    sent = 0

    @_writes()
    def three_statements(self, x, y):
        for row in (x, y):
            self._exec("SELECT 1 FROM runs WHERE run_id = %s FOR UPDATE", (row,))
            self.sent += 1
        self._exec("SELECT 1")
        self.sent += 1  # reached only when the third statement was sent and answered


def test_T4_a_statement_is_not_sent_after_the_budget_is_spent(make, admin, dsn):
    """Two held rows. A single held row cannot show this: its wait would end at the budget by the lock timeout and
    the call would fail there anyway. Budget 2000 ms: X is released at 1000 ms, Y at 2800 ms; the second wait
    (1800 ms, inside the 2000 ms lock timeout) succeeds at 2800 ms, after the budget, so the third statement
    must not be sent."""
    store = make(_HeldRows, lock_timeout_ms=60000, call_budget_ms=2000)
    x, y = _new_run(store), _new_run(store)
    admin.execute("SELECT 1 FROM runs WHERE run_id = %s FOR UPDATE", (x.run_id,))
    # the second row is locked by another admin connection, released on its own timer
    with drv.connect_admin(dsn, autocommit=False) as admin2:
        admin2.execute("SELECT 1 FROM runs WHERE run_id = %s FOR UPDATE", (y.run_id,))
        timers = [
            threading.Timer(1.0, admin.rollback),
            threading.Timer(2.8, admin2.rollback),
        ]
        t0 = time.monotonic()
        for t in timers:
            t.start()
        try:
            with pytest.raises(StoreBusy):
                store.three_statements(x.run_id, y.run_id)
        finally:
            for t in timers:
                t.join()
        assert time.monotonic() - t0 < 2 * 2.0 + 3
    assert store.sent == 2


# --- a lone caller finishes, for every write method (a plain Lock would make each wait for itself) ----------------


def _calls(store, run):
    day = utc_today(store)
    rid = run.run_id
    store.reserve_spend(
        "res-1",
        "a",
        day,
        Decimal(1),
        day_cap=Decimal(10),
        month_cap=Decimal(10),
        run_cap=None,
    )
    store.reserve_spend(
        "res-2",
        "a",
        day,
        Decimal(1),
        day_cap=Decimal(10),
        month_cap=Decimal(10),
        run_cap=None,
    )
    req = _request(store, "apr-lone")
    plan = Plan(
        run_id=rid, agent_id="a", action_id="act", action_version=1, risk_class="reversible",
        inputs={}, target=Target(system="s", ref="r"), idempotency_key="i", expected_outcome="o",
    )  # fmt: skip
    decision = ApprovalDecision(
        approval_id="apr-lone",
        plan_hash="h",
        step=0,
        decision="approve",
        approver_id="user:a",
        channel="fake",
    )
    return {
        "create_run": lambda: store.create_run(
            Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="t")
        ),
        "transition": lambda: store.transition(rid, RunState.RECEIVED, RunState.WORKING),
        "add_cost": lambda: store.add_cost(rid, Decimal(1)),
        "touch": lambda: store.touch(rid),
        "save_plan": lambda: store.save_plan(plan),
        "save_gate_decision": lambda: store.save_gate_decision(
            GateDecision(run_id=rid, plan_hash="h", outcome="allow", rule_id="r")
        ),
        "save_approval_request": lambda: _request(store, "apr-other"),
        "update_approval_request": lambda: store.update_approval_request(
            req.model_copy(update={"summary": "z"}), "PENDING", 0
        ),
        "record_decision": lambda: store.record_decision(
            decision, req.model_copy(update={"status": "APPROVED"}), "PENDING", 0
        ),
        "save_approval_decision": lambda: store.save_approval_decision(
            decision.model_copy(update={"step": 1})
        ),
        "add_dead_letter": lambda: store.add_dead_letter(
            DeadLetter(run_id=rid, reason="r", errors=[])
        ),
        "add_spend": lambda: store.add_spend("a", day, Decimal(1)),
        "set_kill_switch": lambda: store.set_kill_switch(KillSwitch(on=False, by="user:a")),
        "save_tick_state": lambda: store.save_tick_state(TickState(step="lone", last_run_at=now())),
        "add_tool_call": lambda: store.add_tool_call(
            ToolCallRecord(
                call_id=f"{rid}:1",
                run_id=rid,
                tool="t",
                inputs={},
                output="o",
                output_sha256="a" * 64,
                created_at=now(),
            )
        ),
        "purge_tool_calls": lambda: store.purge_tool_calls(now(), keep_run_ids=frozenset()),
        "put_redaction_map": lambda: store.put_redaction_map(rid, {"a": "b"}),
        "purge_redaction_maps": lambda: store.purge_redaction_maps(now(), keep_run_ids=frozenset()),
        "reserve_spend": lambda: store.reserve_spend(
            "res-3", "a", day, Decimal(1), day_cap=None, month_cap=None, run_cap=None
        ),
        "settle_spend": lambda: store.settle_spend("res-1", Decimal(1)),
        "release_spend": lambda: store.release_spend("res-2"),
        "sweep_spend_reservations": lambda: store.sweep_spend_reservations(3600),
    }


@pytest.mark.parametrize("name", WRITE_METHODS)
def test_a_lone_caller_finishes_for_every_write_method(make, name):
    """The setup runs on the thread too: with a plain Lock even `create_run` would wait for itself."""
    store = make()
    outcome = {}

    def go():
        try:
            run = _new_run(store)
            outcome["setup"] = True
            _calls(store, run)[name]()
        except EXPECTED as exc:
            outcome["error"] = exc

    thread = threading.Thread(target=go, daemon=True)
    thread.start()
    thread.join(10)
    stuck = thread.is_alive()
    if (
        stuck
    ):  # free the server: a stuck transaction would block the schema drop in the fixture's teardown
        store._db.close()
    assert not stuck, f"{name} did not finish: it waits for its own lock"
    error = outcome.get("error")
    # the two purges are refused for the runtime login by design (the purge role owns them): still a finished call
    assert error is None or (name.startswith("purge_") and drv.sqlstate(error) == "42501"), repr(
        error
    )


# --- review round 1 fixes (PR 75) ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "bad"),
    [
        *[("lock_timeout_ms", v) for v in (0, 99, 60001)],
        *[("call_budget_ms", v) for v in (0, 499, 60001)],
        *[
            (n, v)
            for n in ("lock_timeout_ms", "call_budget_ms")
            for v in (-1, True, False, 1.5, "1000", None)
        ],
    ],
    ids=repr,
)
def test_M1_the_constructor_refuses_a_timeout_outside_the_settings_ranges(name, bad):
    """Class: a setting validated at one entry (the settings model) and not at the other (the constructor)."""
    with pytest.raises(ValueError, match=name):
        PostgresStore(_Conn(), **{name: bad})


@pytest.mark.parametrize(
    ("kw", "want"),
    [
        ({}, (1000, 5000)),
        ({"lock_timeout_ms": 100, "call_budget_ms": 500}, (100, 500)),
        ({"lock_timeout_ms": 60000, "call_budget_ms": 60000}, (60000, 60000)),
    ],
    ids=["defaults", "lowest", "highest"],
)
def test_M1_the_edges_of_the_ranges_build(kw, want):
    store = PostgresStore(_Conn(), **kw)
    assert (store._lock_timeout_ms, store._call_budget_ms) == want


def test_M4_the_back_off_is_20_ms_times_2_to_the_n_plus_at_most_20_ms_of_jitter(monkeypatch):
    """Class: a tuning constant nobody pins (tenacity's `wait_exponential_jitter(multiplier=0.02, jitter=0.02)`
    is valid in 9.2.1; a mistaken unit or name would show here). Two sleeps: 0.02 + [0, 0.02] and 0.04 + [0, 0.02]."""
    slept = []
    monkeypatch.setattr(time, "sleep", slept.append)
    for _ in range(
        40
    ):  # the jitter is random: 40 runs cover both ends well enough to catch a wrong constant
        store = _stub()
        plan, _ = _fail_times("40P01", 2)
        assert store.op(plan) == "ok"
    first, second = slept[0::2], slept[1::2]
    assert len(first) == len(second) == 40
    assert all(0.02 <= x <= 0.04 for x in first), (min(first), max(first))
    assert all(0.04 <= x <= 0.06 for x in second), (min(second), max(second))
    assert max(first) - min(first) > 0.002  # a jitter exists (not a fixed delay)


# M2: the kill switch is read in ONE place (get_kill_switch); reserve_spend uses it.


def test_M2_reserve_spend_reads_the_kill_switch_through_get_kill_switch(make):
    class Switched(PostgresStore):
        def get_kill_switch(self):
            return KillSwitch(on=True, by="user:test")

    from hadavin_sdk.store.protocol import KillSwitchOn

    store = make(Switched)
    with pytest.raises(KillSwitchOn):
        store.reserve_spend(
            "res-ks",
            "a",
            utc_today(store),
            Decimal(1),
            day_cap=Decimal(10),
            month_cap=Decimal(10),
            run_cap=None,
        )
    assert store.spend_totals("a", utc_today(store)) == (0, 0)


def test_M2_only_get_kill_switch_and_set_kill_switch_name_the_table():
    """The sibling check: no third place may read or write the kill switch row."""
    _, methods = _class_methods()
    naming = {
        m.name
        for m in methods
        for node in ast.walk(m)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and "kill_switch" in node.value
        and m.name not in {"_select"}
    }
    assert naming == {"get_kill_switch", "set_kill_switch"}
    # and the old second reader is gone
    assert "_kill_switch_row" not in {m.name for m in methods}


# M5: a purge deletes in batches, so one large purge is not one long statement under the 5 s budget.


@pytest.fixture
def purger(dsn):
    """A store on the purge login of the fixture schema (the runtime login cannot delete)."""
    from tests.contracts.kinds.store_postgres import PURGE_DSN

    with drv.connect_admin(
        PURGE_DSN[dsn], autocommit=True
    ) as conn:  # PURGE_DSN is not an owner DSN: used as is
        yield conn


def _old_tool_calls(admin, n):
    admin.execute(
        "INSERT INTO tool_calls (call_id, run_id, tool, inputs, output, output_sha256, created_at) "
        "SELECT 'c' || g, 'run-' || (g %% 7), 't', '{}'::jsonb, 'o', repeat('a', 64), now() - interval '2 days' "
        "FROM generate_series(1, %s) g",
        (n,),
    )
    admin.commit()


def test_M5_a_purge_larger_than_one_batch_deletes_all_of_it(dsn, admin, purger):
    from hadavin_sdk import defaults

    n = defaults.STORE_PURGE_BATCH_ROWS * 2 + 345
    _old_tool_calls(admin, n)
    store = PostgresStore(purger)
    assert store.purge_tool_calls(now(), keep_run_ids=frozenset({"run-3"})) == n - len(
        range(3, n + 1, 7)
    )
    left = admin.execute("SELECT count(*), min(run_id), max(run_id) FROM tool_calls").fetchone()
    assert left[1:] == ("run-3", "run-3")


def test_M5_the_statements_are_batches_of_the_configured_size(dsn, admin, purger, monkeypatch):
    from hadavin_sdk import defaults

    n = defaults.STORE_PURGE_BATCH_ROWS * 2 + 5
    _old_tool_calls(admin, n)
    seen = []
    real = PostgresStore._exec

    def spy(self, query, params=()):
        seen.append(params[-1] if params else None)
        return real(self, query, params)

    monkeypatch.setattr(PostgresStore, "_exec", spy)
    store = PostgresStore(purger)
    assert store.purge_tool_calls(now(), keep_run_ids=frozenset()) == n
    batches = [x for x in seen if x == defaults.STORE_PURGE_BATCH_ROWS]
    assert len(batches) == 3  # 1000 + 1000 + 5 (the short batch ends the loop)


def test_M5_a_nearly_spent_budget_stops_between_batches_and_keeps_what_was_deleted(
    dsn, admin, purger, monkeypatch
):
    from hadavin_sdk import defaults

    n = defaults.STORE_PURGE_BATCH_ROWS * 3
    _old_tool_calls(admin, n)
    store = PostgresStore(purger, call_budget_ms=5000)
    real = PostgresStore._exec
    calls = {"n": 0}

    def slow_second(self, query, params=()):
        calls["n"] += 1
        out = real(self, query, params)
        if params and params[-1] == defaults.STORE_PURGE_BATCH_ROWS:
            # pretend the first batch used the whole budget
            self._deadline = time.monotonic() + 0.001
        return out

    monkeypatch.setattr(PostgresStore, "_exec", slow_second)
    got = store.purge_tool_calls(now(), keep_run_ids=frozenset())
    assert got == defaults.STORE_PURGE_BATCH_ROWS  # one batch, then it stopped
    left = admin.execute("SELECT count(*) FROM tool_calls").fetchone()[0]
    assert left == n - got  # the finished batch was committed, not rolled back
    monkeypatch.undo()
    assert (
        store.purge_tool_calls(now(), keep_run_ids=frozenset()) == left
    )  # a second call finishes it


def test_M5_the_redaction_map_purge_batches_too(dsn, admin, purger):
    from hadavin_sdk import defaults

    n = defaults.STORE_PURGE_BATCH_ROWS + 50
    admin.execute(
        "INSERT INTO redaction_maps (run_id, mapping, updated_at) "
        "SELECT 'r' || g, '{}'::jsonb, now() - interval '3 days' FROM generate_series(1, %s) g",
        (n,),
    )
    admin.commit()
    store = PostgresStore(purger)
    assert store.purge_redaction_maps(now(), keep_run_ids=frozenset({"r1"})) == n - 1
    assert admin.execute("SELECT run_id FROM redaction_maps").fetchall() == [("r1",)]
    assert store.purge_redaction_maps(now(), keep_run_ids=frozenset(), keep_open=False) == 1
