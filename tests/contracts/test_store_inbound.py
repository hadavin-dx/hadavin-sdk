"""Inbound ledger store suite (AK-G2-a rows L1-L11b, L13, L16, L20 (store part), L22, L25 (i)-(iii), L27): the same checks over
the memory store and the Postgres store (the door, dispatch and purge logins of a fresh migrated schema)."""

import threading
from datetime import UTC, datetime, timedelta

import psycopg
import pytest

from hadavin_sdk.models import Run, RunState
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import (
    NotFound,
    RerunRefused,
    StaleState,
    missing_inbound_methods,
    missing_methods,
)
from hadavin_sdk.triggers.ledger import (
    InboundKeyChanged,
    InboundSource,
    Inbox,
    delivery_key,
    key_check_for,
    run_id_for,
)
from tests.contracts.kinds.store_postgres import inbound_postgres_store

T0 = datetime(2030, 1, 1, tzinfo=UTC)
CANARY = "person-1@example.invalid"
KEY = b"k" * 32


class _Clock:
    def __init__(self):
        self.t = T0

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


class _Mem:
    """The memory store with the same helper names as `InboundSplitStore`."""

    kind = "memory"

    def __init__(self):
        self.s = MemoryStore()

    def __getattr__(self, name):
        return getattr(self.s, name)

    def rerun_owner_reopen(self, *a):
        return self.s._rerun_owner_reopen(*a)

    def all_receipts(self):
        return [r.model_dump(mode="json") for r in self.s._inbound.values()]

    def all_bodies(self):
        return list(self.s._inbound_bodies.values())

    def make_run(self, run_id, **kw):
        self.s.create_run(Run(run_id=run_id, **kw))

    def set_run_state(self, run_id, state):
        self.s._runs[run_id].state = state

    def new_dispatch(self):
        return self.s


class _Pg:
    kind = "postgres"

    def __init__(self, split):
        self.sp = split

    def __getattr__(self, name):
        return getattr(self.sp, name)

    def _admin(self):
        return psycopg.connect(self.sp._migrator_dsn, autocommit=True)

    def all_receipts(self):
        with self._admin() as db:
            return [str(r) for r in db.execute("SELECT * FROM inbound_receipts").fetchall()]

    def all_bodies(self):
        with self._admin() as db:
            return [bytes(r[0]) for r in db.execute("SELECT body FROM inbound_bodies").fetchall()]

    def make_run(self, run_id, **kw):
        self.sp.runtime.create_run(Run(run_id=run_id, **kw))

    def set_run_state(self, run_id, state):
        with self._admin() as db:
            db.execute("UPDATE runs SET state = %s WHERE run_id = %s", (state.value, run_id))

    def new_dispatch(self):
        return self.sp.dispatch


@pytest.fixture(params=["memory", "postgres"])
def ibx(request):
    if request.param == "memory":
        yield _Mem()
        return
    gen = inbound_postgres_store()
    split = next(gen)
    yield _Pg(split)
    next(gen, None)


def _src(tenant="tenant-a", name="src-orders", **kw):
    return InboundSource(
        name=name,
        tenant=tenant,
        readers=kw.pop("readers", frozenset({"role:reader"})),
        agent_id=kw.pop("agent_id", "agent-a"),
        principal_id=kw.pop("principal_id", "svc:trigger"),
        **kw,
    )


def _inbox(ibx, clock=None, key=KEY):
    return Inbox(ibx, hkey=key, clock=clock or _Clock())


def _claim(ibx, src, clock, lease_s=300):
    return ibx.claim_inbound(src.tenant, src.name, clock(), lease_s)


def test_l0_the_store_has_every_inbound_method(ibx):
    assert missing_inbound_methods(ibx) == []
    assert missing_inbound_methods(object()) != []
    assert missing_methods(MemoryStore()) == []  # the inbound methods are not part of `Store`


def test_l1_write_ahead_receipt_and_body_are_readable(ibx):
    src, clock = _src(), _Clock()
    assert _inbox(ibx, clock).receive(src, "order-1", b"hello") == "new"
    rec = _claim(ibx, src, clock)
    assert rec is not None and rec.state == "claimed"
    assert rec.readers == frozenset({"role:reader"})
    assert rec.run_id == run_id_for(delivery_key(KEY, "tenant-a", "src-orders", "order-1"), 0)
    assert ibx.get_inbound_body("tenant-a", "src-orders", rec.delivery_key) == b"hello"


def test_l1_a_fault_before_the_body_insert_leaves_neither_row(ibx):
    if ibx.kind != "postgres":
        pytest.skip("the hook is a Postgres seam")

    def boom():
        raise RuntimeError("fault")

    ibx.door._before_body_insert = boom
    with pytest.raises(RuntimeError):
        _inbox(ibx).receive(_src(), "order-1", b"hello")
    assert ibx.all_receipts() == [] and ibx.all_bodies() == []


def test_l2_duplicate_writes_nothing_new(ibx):
    src, ib = _src(), _inbox(ibx)
    assert ib.receive(src, "order-1", b"hello") == "new"
    assert ib.receive(src, "order-1", b"hello") == "duplicate"
    assert len(ibx.all_receipts()) == 1 and ibx.all_bodies() == [b"hello"]


def test_l3_id_reuse_keeps_the_first_and_caps_at_eight(ibx):
    src, ib = _src(), _inbox(ibx)
    assert ib.receive(src, "order-1", b"first") == "new"
    assert ib.receive(src, "order-1", b"second") == "id_reuse"
    assert ib.receive(src, "order-1", b"second") == "id_reuse"  # never `duplicate`
    rows = ibx.all_receipts()
    assert len(rows) == 2 and ibx.all_bodies() == [b"first"]  # the reuse row holds no text
    for i in range(7):  # 7 more distinct reused bodies: 8 reuse rows in all
        assert ib.receive(src, "order-1", b"other-%d" % i) == "id_reuse"
    assert len(ibx.all_receipts()) == 1 + 8
    assert ib.receive(src, "order-1", b"ninth") == "id_reuse_capped"
    assert len(ibx.all_receipts()) == 1 + 8
    reuse = [r for r in ibx.all_receipts() if "id_reuse" in str(r)]
    assert len(reuse) == 8


def test_l4_hashes_only_the_canary_is_in_no_receipt_column(ibx):
    src, ib = _src(), _inbox(ibx)
    ib.receive(src, CANARY, CANARY.encode())
    assert all(CANARY not in str(r) for r in ibx.all_receipts())
    assert ibx.all_bodies() == [CANARY.encode()]


def test_l5_every_receipt_is_claimed_exactly_once_by_8_workers(ibx):
    src, ib, clock = _src(max_open=10_000), _inbox(ibx), _Clock()
    n = 300
    for i in range(n):
        assert ib.receive(src, f"o-{i}", b"x") == "new"
    stores = (
        [ibx.new_dispatch()] if ibx.kind == "memory" else [_dispatch_conn(ibx) for _ in range(8)]
    )
    seen, errors = [], []
    lock = threading.Lock()

    def worker(i):
        st = stores[i % len(stores)]
        try:
            while (rec := st.claim_inbound(src.tenant, src.name, clock(), 300)) is not None:
                with lock:
                    seen.append(rec.delivery_key)
        except Exception as exc:  # noqa: BLE001 - reported below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert errors == [] and len(seen) == n and len(set(seen)) == n


def _dispatch_conn(ibx):
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends.factory import make
    from hadavin_sdk.backends.table import PostgresSettings
    from tests.contracts.kinds.store_postgres import INBOUND

    dsn = next(v["dispatch"] for v in INBOUND.values() if v["migrator"] == ibx.sp._migrator_dsn)
    return make(
        "store",
        PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn"),  # noqa: S106 - a name
        FakeSecretProvider({"pg-dsn": dsn}),
    )


def test_l6_lease_expiry_reclaims_and_counts_one_try(ibx):
    src, ib, clock = _src(), _inbox(ibx), _Clock()
    ib.receive(src, "o-1", b"x")
    first = _claim(ibx, src, clock, lease_s=100)
    assert first.attempts == 0
    assert _claim(ibx, src, clock, lease_s=100) is None
    clock.advance(seconds=100)  # exactly at the lease end: not yet
    assert _claim(ibx, src, clock, lease_s=100) is None
    clock.advance(seconds=1)
    second = _claim(ibx, src, clock, lease_s=100)
    assert second.attempts == 1 and second.claim_token != first.claim_token
    with pytest.raises(StaleState):
        ibx.finish_inbound(
            src.tenant, src.name, first.delivery_key, first.claim_token, "done", None, clock()
        )


def test_l7_finish_is_a_compare_and_set(ibx):
    src, ib, clock = _src(), _inbox(ibx), _Clock()
    ib.receive(src, "o-1", b"x")
    rec = _claim(ibx, src, clock)
    with pytest.raises(StaleState):
        ibx.finish_inbound(
            src.tenant, src.name, rec.delivery_key, "clm-" + "0" * 32, "done", None, clock()
        )
    ibx.finish_inbound(
        src.tenant, src.name, rec.delivery_key, rec.claim_token, "done", None, clock()
    )
    with pytest.raises(StaleState):
        ibx.finish_inbound(
            src.tenant, src.name, rec.delivery_key, rec.claim_token, "done", None, clock()
        )
    with pytest.raises(NotFound):
        ibx.finish_inbound(src.tenant, src.name, "f" * 64, rec.claim_token, "done", None, clock())


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        ("received", None),
        ("claimed", None),
        ("done", "policy"),
        ("refused", "attempts_exhausted"),
        ("needs_person", "id_reuse"),
        ("needs_person", "step_error"),
        ("needs_person", None),
    ],
)
def test_l9_finish_refuses_a_bad_state_or_reason_and_writes_nothing(ibx, state, reason):
    src, ib, clock = _src(), _inbox(ibx), _Clock()
    ib.receive(src, "o-1", b"x")
    rec = _claim(ibx, src, clock)
    with pytest.raises(ValueError):
        ibx.finish_inbound(
            src.tenant, src.name, rec.delivery_key, rec.claim_token, state, reason, clock()
        )
    with pytest.raises(ValueError):
        ibx.release_inbound(
            src.tenant, src.name, rec.delivery_key, rec.claim_token, "policy", clock()
        )
    ibx.release_inbound(
        src.tenant, src.name, rec.delivery_key, rec.claim_token, "step_error", clock()
    )


def test_l9_release_counts_step_error_but_not_audit_unavailable(ibx):
    src, ib, clock = _src(), _inbox(ibx), _Clock()
    ib.receive(src, "o-1", b"x")
    rec = _claim(ibx, src, clock)
    ibx.release_inbound(
        src.tenant, src.name, rec.delivery_key, rec.claim_token, "audit_unavailable", clock()
    )
    rec = _claim(ibx, src, clock)
    assert rec.attempts == 0
    ibx.release_inbound(
        src.tenant, src.name, rec.delivery_key, rec.claim_token, "step_error", clock()
    )
    assert _claim(ibx, src, clock).attempts == 1


def test_l10_two_tenants_with_the_same_ledger_name_and_id_stay_apart(ibx):
    a, b = _src("tenant-a", agent_id="agent-a"), _src("tenant-b", agent_id="agent-b")
    ib, clock = _inbox(ibx), _Clock()
    assert ib.receive(a, "order-1", CANARY.encode()) == "new"
    assert ib.receive(b, "order-1", b"other") == "new"
    ra, rb = _claim(ibx, a, clock), _claim(ibx, b, clock)
    assert (
        ra.tenant == "tenant-a" and rb.tenant == "tenant-b" and ra.delivery_key != rb.delivery_key
    )
    assert ibx.get_inbound_body("tenant-a", "src-orders", rb.delivery_key) is None
    assert ibx.get_inbound_body("tenant-b", "src-orders", rb.delivery_key) == b"other"
    assert _claim(ibx, a, clock) is None and _claim(ibx, b, clock) is None


def test_l11_busy_counts_open_receipts_of_this_address_only(ibx):
    src, ib, clock = _src(max_open=3), _inbox(ibx), _Clock()
    for i in range(3):
        assert ib.receive(src, f"o-{i}", b"x") == "new"
    assert ib.receive(src, "o-new", b"x") == "busy"
    other = _src("tenant-b", agent_id="agent-b")
    assert ib.receive(other, "o-new", b"x") == "new"  # another tenant's count is separate
    a, _b = (
        _claim(ibx, src, clock),
        _claim(ibx, src, clock),
    )  # 2 claimed + 1 received is still 3 open
    assert ib.receive(src, "o-new", b"x") == "busy"
    assert len(ibx.all_receipts()) == 4
    ibx.finish_inbound(src.tenant, src.name, a.delivery_key, a.claim_token, "done", None, clock())
    assert ib.receive(src, "o-new", b"x") == "new"
    assert ib.receive(src, "o-new", b"x") == "duplicate"  # L11b: never busy for an accepted message


def test_l11b_a_retry_of_an_accepted_message_while_full_is_a_duplicate(ibx):
    src, ib = _src(max_open=1), _inbox(ibx)
    assert ib.receive(src, "o-0", b"x") == "new"
    assert ib.receive(src, "o-0", b"x") == "duplicate"
    assert ib.receive(src, "o-1", b"x") == "busy"


def test_l11_racing_receivers_never_pass_open_cap_plus_racers(ibx):
    src, clock = _src(max_open=2), _Clock()
    results, errors = [], []

    def go(i):
        try:
            results.append(Inbox(ibx, hkey=KEY, clock=clock).receive(src, f"r-{i}", b"x"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    ts = [threading.Thread(target=go, args=(i,)) for i in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert errors == [] and results.count("new") <= 2 + 6 - 1 and results.count("new") >= 2
    assert len(ibx.all_receipts()) == results.count("new")


def test_l13_purge_rules(ibx):
    src, ib, clock = _src(max_open=1000), _inbox(ibx), _Clock()
    before, ceiling = (
        T0 - timedelta(days=30) + timedelta(days=100),
        T0 - timedelta(days=400) + timedelta(days=100),
    )
    # received at T0; finished at T0 (all receipts are "31 days old" against `before` = T0 + 70 days)
    names = ("refused", "done_ok", "done_missing", "needs_person", "done_np", "open")
    for name in names:
        ib.receive(src, name, b"body-" + name.encode())
    recs = {}
    for _ in range(6):
        rec = _claim(ibx, src, clock)
        recs[
            next(
                n
                for n in names
                if delivery_key(KEY, "tenant-a", "src-orders", n) == rec.delivery_key
            )
        ] = rec

    def fin(name, state, reason):
        r = recs[name]
        ibx.finish_inbound(
            src.tenant, src.name, r.delivery_key, r.claim_token, state, reason, clock()
        )

    fin("refused", "refused", "forbidden")
    fin("done_ok", "done", None)
    fin("done_missing", "done", None)
    fin("needs_person", "needs_person", "policy")
    fin("done_np", "done", None)
    ibx.make_run(
        recs["done_ok"].run_id,
        agent_id="a",
        principal_id="p",
        trigger_kind="event",
        trigger_ref="inb-x",
    )
    ibx.set_run_state(recs["done_ok"].run_id, RunState.SUCCEEDED)
    ibx.make_run(
        recs["done_np"].run_id,
        agent_id="a",
        principal_id="p",
        trigger_kind="event",
        trigger_ref="inb-x",
    )
    ibx.set_run_state(recs["done_np"].run_id, RunState.NEEDS_PERSON)
    gone = ibx.purge_inbound_bodies(before, ceiling)
    left = ibx.all_bodies()
    assert gone == 3 and sorted(left) == sorted(
        [b"body-needs_person", b"body-done_np", b"body-open"]
    )
    assert len(ibx.all_receipts()) == 6  # receipts are never deleted
    # past the ceiling every final receipt's text goes; an open receipt's never
    assert ibx.purge_inbound_bodies(T0 + timedelta(days=1000), T0 + timedelta(days=1000)) == 2
    assert ibx.all_bodies() == [b"body-open"]


def test_l16_a_final_receipt_cannot_be_finished_or_released_and_reopen_is_refused(ibx):
    src, ib, clock = _src(), _inbox(ibx), _Clock()
    ib.receive(src, "o-1", b"x")
    rec = _claim(ibx, src, clock)
    ibx.finish_inbound(
        src.tenant, src.name, rec.delivery_key, rec.claim_token, "refused", "forbidden", clock()
    )
    with pytest.raises(StaleState):
        ibx.release_inbound(
            src.tenant, src.name, rec.delivery_key, rec.claim_token, "step_error", clock()
        )
    with pytest.raises(RerunRefused):
        ibx.reopen_inbound(src.tenant, src.name, rec.delivery_key, clock())
    with pytest.raises(
        StaleState
    ):  # through the re-run owner: only a `needs_person` receipt can be reopened
        ibx.rerun_owner_reopen(src.tenant, src.name, rec.delivery_key, clock())


def test_l16_reopen_through_the_owner_raises_the_generation_and_gives_a_new_run_id(ibx):
    src, ib, clock = _src(), _inbox(ibx), _Clock()
    ib.receive(src, "o-1", b"x")
    rec = _claim(ibx, src, clock)
    ibx.finish_inbound(
        src.tenant,
        src.name,
        rec.delivery_key,
        rec.claim_token,
        "needs_person",
        "run_interrupted",
        clock(),
    )
    again = ibx.rerun_owner_reopen(src.tenant, src.name, rec.delivery_key, clock())
    assert (
        again.state == "received"
        and again.generation == 1
        and again.attempts == 0
        and again.reason is None
    )
    assert again.run_id == run_id_for(rec.delivery_key, 1) and again.run_id != rec.run_id


def test_l20_key_change_writes_nothing_and_only_dispatch_changes_the_check(ibx):
    src, clock = _src(), _Clock()
    a, b = Inbox(ibx, hkey=b"a" * 32, clock=clock), Inbox(ibx, hkey=b"b" * 32, clock=clock)
    assert a.receive(src, "o-1", b"x") == "new"
    assert ibx.get_inbound_key_check("tenant-a", "src-orders") == a.key_check
    with pytest.raises(InboundKeyChanged) as err:
        b.receive(src, "o-2", b"x")
    assert b"a" * 32 not in str(err.value).encode() and "o-2" not in str(err.value)
    assert len(ibx.all_receipts()) == 1 and ibx.all_bodies() == [b"x"]
    ibx.set_inbound_key_check("tenant-a", "src-orders", a.key_check, b.key_check, clock())
    assert b.receive(src, "o-2", b"x") == "new"
    with pytest.raises(InboundKeyChanged):  # no cache: A is refused at once
        a.receive(src, "o-3", b"x")
    with pytest.raises(StaleState):
        ibx.set_inbound_key_check("tenant-a", "src-orders", a.key_check, b.key_check, clock())
    with pytest.raises(NotFound):
        ibx.set_inbound_key_check("tenant-a", "no-such", a.key_check, b.key_check, clock())
    assert key_check_for(b"b" * 32) == b.key_check


def test_l22_every_written_time_is_the_injected_time(ibx):
    clock = _Clock()
    clock.t = datetime(2001, 1, 1, tzinfo=UTC)
    src, ib = _src(), Inbox(ibx, hkey=KEY, clock=clock)
    ib.receive(src, "o-1", b"x")
    rec = _claim(ibx, src, clock)
    assert rec.received_at == rec.updated_at == clock.t and rec.lease_until == clock.t + timedelta(
        seconds=300
    )
    clock.advance(seconds=5)
    ibx.finish_inbound(
        src.tenant, src.name, rec.delivery_key, rec.claim_token, "done", None, clock()
    )
    assert ibx.list_inbound_sources() == []


def test_l25_eight_receivers_of_one_new_message_give_one_new(ibx):
    src, clock = _src(), _Clock()
    out, errors = [], []

    def go():
        try:
            out.append(Inbox(ibx, hkey=KEY, clock=clock).receive(src, "same", b"x"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    ts = [threading.Thread(target=go) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert errors == [] and sorted(out) == ["duplicate"] * 7 + ["new"]
    assert len(ibx.all_receipts()) == 1


def test_l25_eight_receivers_of_one_reused_body_give_one_reuse_row(ibx):
    src, clock = _src(), _Clock()
    Inbox(ibx, hkey=KEY, clock=clock).receive(src, "same", b"first")
    out, errors = [], []

    def go():
        try:
            out.append(Inbox(ibx, hkey=KEY, clock=clock).receive(src, "same", b"second"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    ts = [threading.Thread(target=go) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert errors == [] and out == ["id_reuse"] * 8 and len(ibx.all_receipts()) == 2


def test_l25_first_receives_of_different_messages_make_one_key_check_row(ibx):
    src, clock = _src(max_open=100), _Clock()
    errors = []

    def go(i):
        try:
            Inbox(ibx, hkey=KEY, clock=clock).receive(src, f"m-{i}", b"x")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    ts = [threading.Thread(target=go, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert errors == [] and len(ibx.all_receipts()) == 8
    assert ibx.get_inbound_key_check("tenant-a", "src-orders") == key_check_for(KEY)


def test_l27_get_inbound_run_is_the_seven_columns_and_a_missing_run_is_not_found(ibx):
    run = Run(agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="inb-1")
    ibx.make_run(
        run.run_id, agent_id="a", principal_id="p", trigger_kind="event", trigger_ref="inb-1"
    )
    view = ibx.get_inbound_run(run.run_id)
    assert (view.agent_id, view.principal_id, view.trigger_ref, view.state) == (
        "a",
        "p",
        "inb-1",
        RunState.RECEIVED,
    )
    with pytest.raises(NotFound):
        ibx.get_inbound_run("run-" + "0" * 32)
