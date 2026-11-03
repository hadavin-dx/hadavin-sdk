"""Generic controls promoted from a demo's review 8 and hardened by four reviews of PR #50: read-only config view, stop gate over the
audited durable stop, row store, capped audit, one text fold, output check, mutation judge and runner. No demo import; look-alikes are
built with chr(). No wall-clock assertions: ordering is made with Events."""

import asyncio
import copy
import datetime as dt
import decimal
import enum
import inspect
import json
import pathlib
import pickle
import random
import re
import threading
import unicodedata
import uuid
from pathlib import Path

import pytest
from tools.mutation_runner import Mutant, run_mutants

from hadavin_sdk.audit.capped import CappedAudit, sink_append
from hadavin_sdk.audit.local_dir import LocalDirSink
from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.guard import egress_text, textnorm
from hadavin_sdk.guard.egress_text import LeakPolicy, Violation
from hadavin_sdk.guard.textnorm import (
    LOOKALIKES,
    AllowVerdict,
    allow_equal,
    fold,
    has_mixed_script,
    names_equal,
    same_person,
    squeeze,
)
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch as StoredKillSwitch
from hadavin_sdk.runtime.config_view import (
    ConfigConflict,
    ConfigHolder,
    FrozenDict,
    FrozenList,
    freeze,
    thaw,
)
from hadavin_sdk.runtime.rowstore import (
    DuplicateKey,
    KeyPending,
    RowStore,
    StoreFull,
    copy_row,
    json_keys_ok,
)
from hadavin_sdk.runtime.stop_gate import EffectBlocked, StopGate, StopGateBusy
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.testing.contracts import check_rowstore_contract
from hadavin_sdk.testing.mutation import Verdict, first_failure, first_failure_junit, judge

FIX = Path(__file__).parent / "fixtures"
P = LeakPolicy.payments()


def check_text(text, protected=(), allowed=(), **kw):
    """The module under test needs ``policy=``; these tests default it to the strict payments profile."""
    return egress_text.check_text(text, protected, allowed, **{"policy": P, **kw})


def text_leaks(text, protected=(), allowed=(), **kw):
    return egress_text.text_leaks(text, protected, allowed, **{"policy": P, **kw})


def pol():
    return {"limits": {"cap": 5}, "types": ["a", "b"], "tags": {"x", "y"}}


def directory():
    return {"u1": {"roles": ["clerk"], "employee_id": "e1"}}


# ---- read-only views --------------------------------------------------------------------------------------------------------------------
def test_frozen_views_refuse_every_in_place_edit_at_every_depth():
    h = ConfigHolder(pol(), directory())
    edits = [
        lambda: h.pol["limits"].update(cap=1),
        lambda: h.pol["limits"].__ior__({"cap": 1}),
        lambda: h.pol["types"].append("c"),
        lambda: h.pol["types"].__iadd__(["c"]),
        lambda: h.pol["types"].__imul__(2),
        lambda: h.pol["types"].sort(),
        lambda: h.pol.pop("limits"),
        lambda: h.pol["limits"].__init__({"cap": 9}),
        lambda: h.pol["types"].__init__(["z"]),
        lambda: h.directory["u1"]["roles"].append("controller"),
        lambda: h.directory.__setitem__("evil", {}),
        lambda: h.pol["tags"].add("z"),
    ]
    for e in edits:
        with pytest.raises((TypeError, AttributeError)):
            e()
    assert h.pol["limits"]["cap"] == 5 and h.pol["tags"] == frozenset({"x", "y"})


def test_freeze_copies_deeply_and_rejects_unknown_mutable_types():
    src = pol()
    h = ConfigHolder(src, directory())
    src["limits"]["cap"] = 99
    src["tags"].add("zzz")
    assert h.pol["limits"]["cap"] == 5 and "zzz" not in h.pol["tags"]
    for bad in (bytearray(b"x"), object(), {"a": object()}, [bytearray(1)]):
        with pytest.raises(TypeError):
            freeze(bad)
    assert thaw(freeze({"a": [1, {"b": {2}}]})) == {"a": [1, {"b": {2}}]}


class Colour(enum.Enum):
    RED = 1


def test_freeze_holds_real_configs_tuples_stay_tuples_and_depth_is_a_type_error():
    cfg = {
        "budget": decimal.Decimal("12.50"), "at": dt.datetime(2026, 11, 2, tzinfo=dt.UTC), "day": dt.date(2026, 11, 2), "c": Colour.RED,
        "id": uuid.UUID(int=7), "p": pathlib.PurePosixPath("/x"), "years": (2000, 2099), "pairs": [("a", 1)], "t": dt.timedelta(1),
    }  # fmt: skip
    f = freeze(cfg)
    assert (
        f["years"] == (2000, 2099)
        and type(f["years"]) is tuple
        and f["budget"] == decimal.Decimal("12.50")
    )
    assert thaw(f) == cfg and type(thaw(f)["pairs"][0]) is tuple
    deep: dict = {}
    cur = deep
    for _ in range(200):
        cur["n"] = {}
        cur = cur["n"]
    with pytest.raises(TypeError):
        freeze(deep)  # never a RecursionError
    loop: list = []
    loop.append(loop)
    with pytest.raises(TypeError):
        freeze(loop)
    with pytest.raises(TypeError):
        freeze(
            {("a", ({"k": 1},))}
        )  # a set member that cannot be hashed once frozen is a typed refusal
    pytest.importorskip("pydantic")
    from hadavin_sdk.models import KillSwitch

    with pytest.raises(TypeError):
        freeze({"m": KillSwitch(on=True)})  # a pydantic model could be edited in place


def test_frozen_views_behave_like_plain_json_pickle_and_deepcopy():
    f = freeze({"a": [1, {"b": 2}]})
    assert (
        isinstance(f, FrozenDict)
        and isinstance(f["a"], FrozenList)
        and json.loads(json.dumps(f)) == f
    )
    back = pickle.loads(pickle.dumps(f))  # noqa: S301 - our own bytes
    assert back == f and isinstance(back, FrozenDict)
    d = copy.deepcopy(f)  # by design the editable copy a change is prepared from
    assert type(d) is dict and type(d["a"]) is list
    d["a"].append(3)
    assert f["a"] == [1, {"b": 2}]


def test_the_holder_view_is_one_immutable_pair_and_swap_is_compare_and_set():
    h = ConfigHolder({"n": 0}, {"n": 0})
    v0 = h.view()
    assert (
        v0 is h.view() and v0.pol is h.pol and v0.directory is h.directory
    )  # one object: the pair cannot be torn
    v1 = h.swap({"n": 1}, {"n": 1})
    assert (
        v0.pol["n"] == 0 and v1.version == v0.version + 1 and h.view() is v1
    )  # the old view is unchanged
    with pytest.raises(ConfigConflict):
        h.swap({"n": 2}, {"n": 2}, expect=v0.version)  # another administrator swapped first
    assert h.swap({"n": 2}, {"n": 2}, expect=v1.version).version == 2
    with pytest.raises(TypeError):
        h.swap({"n": object()}, {"n": 1})
    assert h.view().version == 2


def test_readers_never_see_a_torn_pair_across_swaps():
    h = ConfigHolder({"n": 0}, {"n": 0})
    stop, bad = threading.Event(), []

    def reader():
        while not stop.is_set():
            v = h.view()
            if v.pol["n"] != v.directory["n"]:
                bad.append((v.pol["n"], v.directory["n"]))

    ts = [threading.Thread(target=reader) for _ in range(4)]
    [t.start() for t in ts]
    for i in range(1, 501):
        h.swap({"n": i}, {"n": i})
    stop.set()
    [t.join() for t in ts]
    assert bad == []


# ---- stop gate over the audited durable stop ----------------------------------------------------------------------------------------
class FakeStore:
    def __init__(self):
        self.ks = StoredKillSwitch(on=False)
        self.down = False

    def get_kill_switch(self):
        if self.down:
            raise OSError("store down")
        return self.ks

    def set_kill_switch(self, ks):
        if self.down:
            raise OSError("store down")
        self.ks = ks


class FakeLimits:
    """The surface of hadavin_sdk.limits.Limits that the gate uses: audit, stop(by, source), reset(by, source), is_stopped()."""

    def __init__(self, store=None, audit_down=False):
        self.store, self.audit_down, self.log = store or FakeStore(), audit_down, []
        self.audit = RecordingSink()
        self.during_reset = None  # called inside reset, like a slow store write

    def stop(self, by, source="cli"):
        self.store.set_kill_switch(
            StoredKillSwitch(on=True, by=by)
        )  # switch first, then audit (the outbox)
        self.log.append(("stop", by))

    def reset(self, by, source="cli"):
        if self.audit_down:
            raise AuditUnavailable("audit down")  # audit first: a failed audit leaves the switch on
        if self.during_reset:
            self.during_reset()
        self.log.append(("reset", by))
        self.store.set_kill_switch(StoredKillSwitch(on=False, by=by))

    def is_stopped(self):
        return bool(self.store.get_kill_switch().on)


def test_the_fake_limits_matches_the_real_surface():
    for name in ("stop", "reset"):
        assert list(inspect.signature(getattr(Limits, name)).parameters) == ["self", "by", "source"]
        assert list(inspect.signature(getattr(FakeLimits, name)).parameters) == [
            "self",
            "by",
            "source",
        ]
    assert list(inspect.signature(Limits.is_stopped).parameters) == ["self"]


def test_engage_goes_through_limits_and_two_instances_share_the_durable_switch():
    lim = FakeLimits()
    a, b = StopGate(lim), StopGate(lim)
    assert not a.blocked() and not b.blocked()
    res = a.engage(list, lambda k: "x", by="u-ctl-01")
    assert (
        lim.log == [("stop", "u-ctl-01")]
        and lim.store.ks.on
        and res.durable
        and res.store_error is None
    )
    assert b.blocked() and not b.engaged  # the other instance sees it without being engaged
    with pytest.raises(EffectBlocked), b.effect():
        raise AssertionError("an effect must not start")
    a.release(by="u-ctl-01")
    assert not b.blocked() and lim.log[-1] == ("reset", "u-ctl-01")
    assert StopGate(None).blocked() is False


def test_engage_fails_closed_when_the_store_is_down():
    lim = FakeLimits()
    g = StopGate(lim)
    lim.store.down = True
    res = g.engage(list, lambda k: "x", by="u1")
    assert (
        res.durable is False and "OSError" in (res.store_error or "") and g.engaged
    )  # engaged anyway
    with pytest.raises(EffectBlocked), g.effect():
        raise AssertionError("an effect must not start while the store is down")
    assert StopGate(lim).blocked()  # an unreadable store reads as engaged


def test_release_is_audit_first_and_leaves_the_switch_on_if_the_audit_fails():
    lim = FakeLimits()
    g = StopGate(lim)
    g.engage(list, lambda k: "x", by="u1")
    lim.audit_down = True
    with pytest.raises(AuditUnavailable):
        g.release(by="u1")
    assert g.engaged and lim.store.ks.on and g.blocked()  # nothing was removed
    lim.audit_down = False
    g.release(by="u1")
    assert not g.engaged and not lim.store.ks.on


def test_a_port_that_checks_outside_the_lock_cannot_escape_the_gate():
    g = StopGate()
    checked, go, started = threading.Event(), threading.Event(), []

    def port():
        if not g.blocked():  # the racy convention: check ...
            checked.set()
            go.wait(5)
            try:
                with g.effect():  # ... then act: the barrier re-checks atomically
                    started.append(1)
            except EffectBlocked:
                started.append(0)

    t = threading.Thread(target=port)
    t.start()
    assert checked.wait(5)
    g.engage(list, lambda k: "x", by="u1", timeout=1)
    go.set()
    t.join(5)
    assert started == [0]


def test_engage_waits_for_effects_in_flight_with_a_timeout_and_sweeps_after():
    g = StopGate()
    entered, release = threading.Event(), threading.Event()
    swept = []

    def effect():
        with g.effect():
            entered.set()
            release.wait(5)

    t = threading.Thread(target=effect)
    t.start()
    assert entered.wait(5)
    res = g.engage(lambda: ["k1"], lambda k: swept.append(k) or "dequeued", by="u1", timeout=0.05)
    assert res.complete is False and res.in_flight_at_timeout == 1 and swept == []
    out, started = [], threading.Event()

    def second():
        started.set()
        out.append(
            g.engage(lambda: ["k1"], lambda k: swept.append(k) or "dequeued", by="u1", timeout=30)
        )

    t2 = threading.Thread(target=second)
    t2.start()
    started.wait(5)
    release.set()
    t.join(5)
    t2.join(5)
    assert swept == ["k1"] and out[0].complete and out[0].results == [("k1", "dequeued")]


def test_an_incomplete_sweep_runs_nothing_and_a_second_engage_completes_it():
    g, swept = StopGate(), []
    entered, release = threading.Event(), threading.Event()

    def effect():
        with g.effect():
            entered.set()
            release.wait(5)

    t = threading.Thread(target=effect)
    t.start()
    assert entered.wait(5)
    first = g.engage(lambda: ["k"], lambda k: swept.append(k) or "ok", by="u", timeout=0.01)
    assert first.complete is False and swept == []
    release.set()
    t.join(5)
    assert g.engage(
        lambda: ["k"], lambda k: swept.append(k) or "ok", by="u", timeout=5
    ).complete and swept == ["k"]


def test_engage_inside_an_effect_does_not_wait_for_itself():
    g = StopGate()
    with g.effect():
        res = g.engage(
            lambda: ["k"], lambda k: "ok", by="u1", timeout=30
        )  # would hang for 30 s if it counted its own effect
    assert res.complete and res.results == [("k", "ok")]


def test_a_second_engage_runs_no_undo_and_release_during_a_sweep_is_refused():
    g = StopGate()
    inside, go, calls, second = threading.Event(), threading.Event(), [], []

    def undo(k):
        calls.append(k)
        inside.set()
        go.wait(5)
        return "ok"

    t = threading.Thread(target=lambda: g.engage(lambda: ["k1"], undo, by="u1"))
    t.start()
    assert inside.wait(5)
    second.append(g.engage(lambda: ["k1"], undo, by="u2"))
    with pytest.raises(StopGateBusy):
        g.release(by="u1")
    go.set()
    t.join(5)
    assert second[0].already_sweeping and calls == ["k1"]  # undone once


def test_one_failing_undo_does_not_stop_the_sweep_and_an_interrupt_keeps_the_partial_result():
    g = StopGate()

    def undo(k):
        if k == "bad":
            raise RuntimeError("x")
        return "ok"

    assert g.engage(lambda: ["bad", "good"], undo, by="u").results == [
        ("bad", "error:RuntimeError"),
        ("good", "ok"),
    ]
    g2 = StopGate()

    def undo2(k):
        if k == "b":
            raise KeyboardInterrupt
        return "ok"

    with pytest.raises(KeyboardInterrupt):
        g2.engage(lambda: ["a", "b", "c"], undo2, by="u")
    assert g2.last.results == [("a", "ok"), ("b", "interrupted")] and g2.last.complete is False
    lim = FakeLimits()
    StopGate(lim).engage(list, lambda k: "", by="bad\nlabel; DROP")
    assert lim.log == [("stop", "?")]  # a free-text label is never stored raw
    StopGate(lim).engage(list, lambda k: "", by="alice smith")
    assert lim.log[-1] == ("stop", "alice smith")  # a real name keeps its attribution


def test_async_effects_and_aengage():
    async def scenario():
        g = StopGate(FakeLimits())
        entered, release = asyncio.Event(), asyncio.Event()
        order = []

        async def work():
            async with g.aeffect():
                entered.set()
                await release.wait()
            order.append("effect done")

        task = asyncio.create_task(work())
        await entered.wait()
        eng = asyncio.create_task(
            g.aengage(lambda: ["k"], lambda k: order.append("undo") or "ok", by="u1", timeout=30)
        )
        for _ in range(50):
            await asyncio.sleep(0)
        assert (
            order == []
        )  # the sweep waits while the async effect is in flight; the event loop stays free
        release.set()
        await task
        res = await eng
        assert order == ["effect done", "undo"] and res.complete
        with pytest.raises(EffectBlocked):
            async with g.aeffect():
                raise AssertionError("an effect must not start")
        await g.arelease("u1")
        async with g.aeffect():
            pass

    asyncio.run(scenario())


def test_restore_sets_the_flag_without_a_store_write_and_the_ttl_cache_is_honoured():
    lim = FakeLimits()
    g = StopGate(lim)
    g.restore(True)
    assert g.engaged and lim.log == []
    g.restore(False)
    g2 = StopGate(lim, cache_ttl=1000.0)
    assert not g2.durable_on()
    lim.store.ks = StoredKillSwitch(on=True)
    assert (
        not g2.durable_on() and StopGate(lim).durable_on()
    )  # cached for the TTL; a fresh gate reads the store


# ---- row store --------------------------------------------------------------------------------------------------------------------------
def test_the_row_store_meets_the_contract():
    check_rowstore_contract(RowStore)


def test_a_bad_row_fails_before_the_audit_and_a_failed_audit_inserts_nothing():
    rs, audited = RowStore(), []
    for bad in (
        {"a": float("nan")},
        {1: "x"},
        {"a": {(1, 2): 1}},
        {"a": {1}},
        {"a": object()},
        {"a": float("inf")},
    ):
        with pytest.raises(ValueError):
            rs.put_audited(lambda kind, **f: audited.append(kind), "k", "r", bad)
    deep: dict = {}
    cur = deep
    for _ in range(2000):
        cur["n"] = {}
        cur = cur["n"]
    with pytest.raises(ValueError):
        rs.put_audited(
            lambda *a, **k: audited.append(1), "k", "r", deep
        )  # a RecursionError is a typed refusal
    assert audited == [] and rs.keys() == []

    def boom(*a, **k):
        raise OSError("down")

    with pytest.raises(OSError):
        rs.put_audited(boom, "k", "r", {"a": 1})
    assert rs.keys() == []
    rs.put_audited(lambda *a, **k: None, "k", "r", {"a": 1})
    with pytest.raises(DuplicateKey):
        rs.put_audited(lambda *a, **k: None, "k", "r", {"a": 2})


def test_a_key_behind_a_failing_audit_is_pending_not_duplicate():
    rs = RowStore()
    entered, go = threading.Event(), threading.Event()
    errs = []

    def failing(kind, **f):
        entered.set()
        go.wait(5)
        raise OSError("down")

    t = threading.Thread(
        target=lambda: errs.append(_try(lambda: rs.put_audited(failing, "k", "r", {})))
    )
    t.start()
    assert entered.wait(5)
    with pytest.raises(KeyPending) as e:
        rs.put_audited(lambda *a, **k: None, "k", "r", {})
    assert not isinstance(
        e.value, DuplicateKey
    )  # a sibling: the caller must retry, not conclude the row exists
    go.set()
    t.join(5)
    assert isinstance(errs[0], OSError) and rs.keys() == []
    rs.put_audited(lambda *a, **k: None, "k", "r", {})  # the retry succeeds


def _try(fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        return e
    return None


def test_update_delete_and_the_row_limit():
    rs, log = RowStore(max_rows=2), []
    ap = lambda kind, **f: log.append((kind, f["key"]))
    rs.put_audited(ap, "put", "h1", {"state": "held"})
    rs.update_audited(ap, "release", "h1", {"state": "released"})
    assert rs.get("h1") == {"state": "released"}
    with pytest.raises(KeyError):
        rs.update_audited(ap, "release", "nope", {})
    rs.put_audited(ap, "put", "h2", {})
    with pytest.raises(StoreFull):
        rs.put_audited(ap, "put", "h3", {})
    rs.delete_audited(ap, "drop", "h2")
    assert rs.keys() == ["h1"] and log[-1] == ("drop", "h2")

    def boom(*a, **k):
        raise OSError

    with pytest.raises(OSError):
        rs.delete_audited(boom, "drop", "h1")
    assert rs.keys() == ["h1"]  # audit first: a failed audit deletes nothing


def test_an_audit_callback_can_read_the_store_and_a_slow_audit_does_not_block_readers():
    rs = RowStore()
    rs.put_audited(lambda *a, **k: None, "k", "one", {"n": 1})
    seen = []
    rs.put_audited(lambda kind, **f: seen.append(rs.snapshot()), "k", "two", {"n": 2})
    assert seen == [{"one": {"n": 1}}]
    started, done = threading.Event(), threading.Event()

    def slow(kind, **f):
        started.set()
        done.wait(5)

    t = threading.Thread(target=lambda: rs.put_audited(slow, "k", "three", {"n": 3}))
    t.start()
    assert started.wait(5)
    assert sorted(rs.snapshot()) == [
        "one",
        "two",
    ]  # a reader is not blocked by an audit write in progress
    done.set()
    t.join(5)
    assert "three" in rs.snapshot()


def test_snapshot_copies_and_the_rows_are_private():
    rs = RowStore()
    rs.put_audited(lambda *a, **k: None, "k", "a", {"n": [1]})
    snap = rs.snapshot()
    snap["a"]["n"].append(2)
    assert rs.get("a") == {"n": [1]} and not hasattr(rs, "rows")
    assert json_keys_ok({"a": [{"b": 1}]}) and not json_keys_ok({7: 1})
    with pytest.raises(ValueError):
        copy_row({"a": float("nan")})


# ---- capped audit -----------------------------------------------------------------------------------------------------------------------
def test_capped_audit_is_per_tenant_per_bucket_and_visible():
    rows = []
    ca = CappedAudit(lambda kind, **f: rows.append((kind, f["tenant"])), cap=2)
    for _ in range(6):
        ca.deny("t1", "denied", "2026-11-02")
    ca.deny("t2", "denied", "2026-11-02")
    assert [r for r in rows if r[1] == "t1"] == [
        ("denied", "t1"),
        ("denied", "t1"),
        ("audit_suppressed", "t1"),
    ]
    assert (
        ("denied", "t2") in rows
        and ca.suppressed("t1", "denied") == 4
        and ca.suppressed("t1", "denied", "2026-11-03") == 0
    )
    ca.deny("t1", "denied", "2026-11-03")
    assert ca.suppressed("t1", "denied") == 0
    for bad in (0, True, 1.5):
        with pytest.raises(ValueError):
            CappedAudit(lambda *a, **k: None, cap=bad)


def test_the_marker_is_written_once_under_a_race_and_retried_with_back_off():
    rows, barrier = [], threading.Barrier(8)
    ca = CappedAudit(lambda kind, **f: rows.append(kind), cap=1)
    ca.deny("t", "d", "b")

    def hit():
        barrier.wait()
        ca.deny("t", "d", "b")

    ts = [threading.Thread(target=hit) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert rows.count("audit_suppressed") == 1  # not eight
    state = {"fail": True, "tries": 0}

    def append(kind, **f):
        if kind == "audit_suppressed":
            state["tries"] += 1
            if state["fail"]:
                raise OSError("down")

    cb = CappedAudit(append, cap=1)
    for _ in range(40):
        cb.deny("t", "d", "b")
    assert (
        state["tries"] < 10
    )  # a failing marker is not retried on every suppressed event (back-off), and deny never raised
    state["fail"] = False
    for _ in range(2000):
        cb.deny("t", "d", "b")
    assert state["tries"] > 1


def test_capped_audit_memory_is_bounded_by_max_keys_with_an_overflow_counter():
    rows = []
    ca = CappedAudit(lambda kind, **f: rows.append((kind, f.get("tenant"))), cap=1, max_keys=3)
    for i in range(100):
        ca.deny(f"tenant-{i}", "denied", "b")  # an outsider picking tenant names
    assert len(ca._n) <= 4  # three keys plus the shared overflow counter
    assert all(len(k[0] or "") <= 64 for k in ca._n)
    assert (
        ca.suppressed("tenant-99", "denied") == 0
    )  # no counter of its own: not the overflow counter's number
    assert ca.overflow_suppressed("denied") > 0
    ca.deny("x" * 500, "denied", "b")
    assert all(len(t or "") <= 64 for _, t in rows)
    wide = CappedAudit(lambda kind, **f: None, cap=1, max_keys=50)
    wide.deny("x" * 64 + "a", "denied", "b")
    wide.deny(
        "x" * 64 + "b", "denied", "b"
    )  # same first 64 characters: one tenant key, so the second is over the cap
    assert wide.suppressed("x" * 64, "denied") > 0 and all(len(k[0] or "") <= 64 for k in wide._n)
    with pytest.raises(ValueError):
        CappedAudit(lambda *a, **k: None, cap=1, max_keys=0)


def test_tenant_and_kind_in_the_fields_do_not_collide():
    rows = []
    ca = CappedAudit(lambda kind, **f: rows.append((kind, f)), cap=5)
    ca.append(
        "t1", "denied", "b", kind="x", tenant="other", key="k"
    )  # the caller's own 'kind'/'tenant' fields
    assert (
        rows[0][0] == "denied"
        and rows[0][1]["tenant"] == "t1"
        and rows[0][1]["field_kind"] == "x"
        and rows[0][1]["field_tenant"] == "other"
    )


class RecordingSink:
    def __init__(self):
        self.events, self.intents = [], []

    def write_outcome(self, ev):
        self.events.append(ev)

    def write_intent(self, ev):
        self.intents.append(ev)
        if getattr(self, "down", False):
            raise AuditUnavailable("down")
        return "ref"


def test_sink_append_keeps_tenant_kind_and_bucket_and_never_leaks_fields():
    sink = RecordingSink()
    ca = CappedAudit(sink_append(sink, "run1", "dom"), cap=1)
    ca.append("t9", "refused", "2026-11-02", secret_body="do not store", key="k1")  # noqa: S106
    ca.deny("t9", "refused", "2026-11-02", key="k2")
    ca.deny("t9", "refused", "2026-11-02", key="k3")
    first, marker = sink.events[0], sink.events[1]
    assert (
        first.object_ref == "t9|k1"
        and first.operation == "refused"
        and "do not store" not in first.model_dump_json()
    )
    assert (
        marker.operation == "audit_suppressed"
        and marker.object_ref.startswith("t9|")
        and marker.error_code == "refused@2026-11-02"
    )
    assert first.decision == "deny" and first.result == "refused"
    hold = sink_append(sink, "run1", "dom", decision="allow", result="held")
    hold("hold_created", tenant="t9", key="h1")
    assert sink.events[-1].decision == "allow" and sink.events[-1].result == "held"


def test_intent_mode_uses_write_intent_and_raises_when_the_audit_is_down():
    sink = RecordingSink()
    app = sink_append(sink, "run1", "dom", intent=True)
    app("hold_created", tenant="t", key="h1")
    assert len(sink.intents) == 1 and sink.events == []
    sink.down = True
    rs = RowStore()
    with pytest.raises(AuditUnavailable):
        rs.put_audited(app, "hold_created", "h1", {})
    assert rs.keys() == []  # with the intent writer, "a failed audit inserts nothing" holds


# ---- one text fold ----------------------------------------------------------------------------------------------------------------------
def test_fold_is_stable_under_combining_marks_format_unassigned_and_tag_characters():
    rnd = random.Random(7)  # noqa: S311
    marks = [chr(0x301), chr(0x300), chr(0x200B), chr(0xFE0F), chr(0x3164), chr(0x202E), chr(0xAD), chr(0xE000), chr(0xE0002), chr(0xE0000),
             chr(0x2065), chr(0xFFF0)]  # fmt: skip
    for _ in range(300):
        x = "".join(rnd.choice("abcXYZ019 -.") for _ in range(rnd.randint(0, 12)))
        for m in marks:
            assert fold(x + m) == fold(x) == fold(m + x)
    assert fold("admin" + chr(0xE0002)) == fold("admin")  # the same-looking name is the same person


def test_fold_covers_the_listed_look_alikes_and_all_map_to_ascii():
    listed = {0x405: "S", 0x406: "I", 0x408: "J", 0x423: "Y", 0x41E: "O", 0x455: "s", 0x3B9: "i", 0x3BA: "k", 0x3C1: "p", 0x3C4: "t",
              0x3C5: "u", 0x3C7: "x", 0x501: "d", 0x131: "i", 0x130: "I", 0x585: "o", 0x57D: "u", 0x555: "O", 0x54D: "U", 0x3BF: "o",
              0x433: "r", 0x3B7: "n", 0x3B3: "y", 0x3BC: "u", 0x3C9: "w", 0x461: "w", 0x581: "g", 0x251: "a", 0xF8: "o", 0x142: "l", 0x111: "d",
              0x1D0F: "o", 0x1D21: "w", 0x417: "3", 0x437: "3", 0x3B5: "e", 0x261: "g"}  # fmt: skip
    for cp, latin in listed.items():
        assert fold(chr(cp)) == latin, hex(cp)
    assert all(re.fullmatch("[A-Za-z0-9]+", v) and v.isascii() for v in LOOKALIKES.values())
    assert fold(chr(0x661) + chr(0x662) + chr(0xFF13)) == "123" and fold("a\nb\tc") == "a b c"
    for sp in (0x85, 0x1C, 0x1F, 0x2028, 0x2029, 0xA0, 0x3000, 0x2003):
        assert fold("ab" + chr(sp) + "cd") == "ab cd", hex(sp)
    assert (
        squeeze("AB-12 3" + chr(0x200B) + "4") == squeeze("ab1234")
        and squeeze("O0Il1", loose=True) == "00111"
    )
    assert not any(
        unicodedata.category(c) in ("Cc", "Cf") for c in fold("x" + chr(0x200B) + chr(0x202E))
    )


def test_the_digit_table_is_complete_at_import():
    assert (
        len(textnorm._DIGITS) > 400 and textnorm._DIGITS[0x661] == "1"
    )  # built once at import: no lazy fill to race on


def test_allow_decisions_are_exact_and_a_look_alike_is_reported_as_one():
    real, spoof = "alice@bank.example", "alice@bank.ex" + chr(0x430) + "mple"
    assert fold(real) == fold(spoof)  # DENY direction: the same person
    assert allow_equal(real, real) is AllowVerdict.EQUAL
    assert allow_equal(real, spoof) is AllowVerdict.LOOKALIKE  # ALLOW direction: refuse
    assert allow_equal("alice", "bob") is AllowVerdict.DIFFERENT
    # every pair that NFKC + casefold + whitespace used to call equal is NOT equal for an ALLOW
    pairs = [
        (chr(0xFF20), "@"),  # fullwidth at-sign
        ("stra" + chr(0xDF) + "e.de", "strasse.de"),  # sharp s versus ss: two different domains
        (chr(0xFB01) + "le", "file"),  # fi ligature
        (" alice@bank.example", "alice@bank.example"),
        ("alice@bank.example ", "alice@bank.example"),
        ("Alice@Bank.example", "alice@bank.example"),
        ("a  b", "a b"),
    ]
    for x, y in pairs:
        assert allow_equal(x, y) is AllowVerdict.VARIANT, (x, y)  # refused, but not a spoof alarm
        assert same_person(x, y), (x, y)  # and the same person for a DENY
        assert names_equal(x, y), (x, y)  # the name comparison stays tolerant, and is not an ALLOW
    assert not names_equal("alice", "bob") and not same_person("alice", "bob")
    assert same_person(real, spoof) and not names_equal(
        real, spoof
    )  # a DENY sees the spoof; the name comparison does not
    with pytest.raises(TypeError):
        bool(
            allow_equal(real, real)
        )  # 'if allow_equal(a, b):' would always be true: it is refused instead
    with pytest.raises(TypeError):
        _ = not allow_equal(real, spoof)
    assert (
        allow_equal("a" + chr(0x200B), "a") is AllowVerdict.LOOKALIKE
    )  # an invisible character is a spoof, not a variant
    assert (
        allow_equal("alice@bank.example", spoof) is not AllowVerdict.EQUAL
        and allow_equal("", "") is AllowVerdict.EQUAL
    )


def test_mixed_script_is_a_fail_closed_deny_signal():
    assert (
        has_mixed_script("al" + chr(0x456) + "ce")
        and has_mixed_script("bank" + chr(0x3B7) + "x")
        and has_mixed_script("a" + chr(0x581))
    )
    assert (
        not has_mixed_script("alice")
        and not has_mixed_script(chr(0x430) + chr(0x43B) + chr(0x438))
        and not has_mixed_script("INV-2026 " + chr(0x65E5))
    )


def test_one_invisible_character_cannot_split_a_mixed_script_word():
    cher_a = chr(0x13AA)
    for invisible in (
        chr(0x200B),
        chr(0x301),
        chr(0xAD),
        chr(0x2060),
        chr(0xE0002),
        chr(0x3164),
        chr(0xFE0F),
    ):
        assert has_mixed_script("b" + invisible + cher_a + invisible + "nk"), hex(ord(invisible))
    assert has_mixed_script("b" + cher_a + "nk")
    assert not has_mixed_script(cher_a + chr(0x13A0))  # one script


def test_the_micro_and_ohm_signs_are_unit_symbols_not_a_mixed_script():
    assert not has_mixed_script(
        "5 " + chr(0xB5) + "s and 50 k" + chr(0x2126) + " and 3 " + chr(0xB5) + "g"
    )
    assert check_text("the delay is 5 " + chr(0xB5) + "s and 2 " + chr(0xB5) + "m") is None
    assert has_mixed_script(
        "m" + chr(0x3BC) + "s"
    )  # a Greek mu typed as a letter inside Latin text is still flagged


def test_the_table_is_generated_from_the_unicode_data_and_every_value_is_ascii():
    from hadavin_sdk.guard import _confusables

    sys_path = Path(__file__).resolve().parents[1] / "tools" / "gen_confusables.py"
    src = sys_path.read_text(encoding="utf-8")
    assert _confusables.DATA_SHA256 in src, (
        "the generator pins the same sha256 as the generated file"
    )
    assert _confusables.ENTRIES == len(_confusables.TABLE) >= 600
    for cp, v in _confusables.TABLE.items():
        assert v.isascii() and re.fullmatch("[A-Za-z0-9]+", v), (hex(cp), v)
        assert cp >= 0x80 and unicodedata.normalize("NFKC", chr(cp)) == chr(cp), hex(
            cp
        )  # only code points the fold can see
    assert textnorm._TABLE == _confusables.TABLE and len(LOOKALIKES) == len(_confusables.TABLE)
    # whole-script and rare look-alikes the first, curated table missed
    named = {0x13AA: "A", 0x13A0: "D", 0x10E7: "y", 0x5D5: "l", 0xA4D0: "B", 0x2C82: "B", 0x269: "i", 0x1C0: "l", 0x237: "j", 0x192: "f",
             0x1D00: "A", 0x299: "B", 0x1D05: "D", 0x1D07: "E", 0xA730: "F", 0x262: "G", 0x29C: "H", 0x1D0A: "J", 0x1D0B: "K", 0x29F: "L",
             0x1D0D: "M", 0x274: "N", 0x1D18: "P", 0x280: "R", 0x1D1B: "T"}  # fmt: skip
    for cp, latin in named.items():
        assert fold(chr(cp)) == latin, hex(cp)
    assert (
        fold("".join(map(chr, (0x13A0, 0x13AA, 0x13A2)))) == "DAT"
    )  # a name written entirely in Cherokee folds to Latin letters
    assert (
        fold(chr(0x406)) == "I" and fold(chr(0x399)) == "I"
    )  # upper-case sources whose prototype is l read as I


def test_the_generator_refuses_an_unpinned_file_and_is_deterministic(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gen_confusables", Path(__file__).resolve().parents[1] / "tools" / "gen_confusables.py"
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    bad = tmp_path / "confusables.txt"
    bad.write_text("0430 ;\t0061 ;\tMA\t# x\n", encoding="utf-8")
    assert gen.main(["gen", str(bad)]) == 1  # not the pinned file
    tab, nl = chr(9), chr(10)
    assert (
        gen.build("0406 ;" + tab + "006C ;" + tab + "MA" + nl)[0x406] == "I"
    )  # an upper-case source with prototype l reads as I
    assert gen.build("0456 ;" + tab + "0069 ;" + tab + "MA" + nl)[0x456] == "i"
    table = gen.build(
        "0430 ;\t0061 ;\tMA\t# x\n13AA ;\t0041 ;\tMA\t# y\n0021 ;\t0049 ;\tMA\t# ascii source\n05AD ;\t0021 ;\tMA\t# punctuation target\n"
    )
    assert (
        table[0x430] == "a" and table[0x13AA] == "A" and 0x21 not in table and 0x1D00 in table
    )  # data, name rule, no ASCII source


def test_the_gate_views_use_the_shared_fold_and_skip_huge_text():
    from hadavin_sdk.approvals import gate

    spoofed = "AK" + chr(0x406) + "A" + chr(0x406) + "OSFODNN7EXAMPLE"
    assert "AKIAIOSFODNN7EXAMPLE" in gate._views(spoofed)
    old = gate._FOLD_MAX
    gate._FOLD_MAX = 10
    try:
        assert "AKIAIOSFODNN7EXAMPLE" not in gate._views(
            spoofed
        )  # beyond the bound the fold is skipped (the other views still ran)
    finally:
        gate._FOLD_MAX = old


def decode(s):
    return re.sub(r"\{U\+([0-9A-Fa-f]{4,6})\}", lambda m: chr(int(m[1], 16)), s)


VECTORS = json.loads((FIX / "textnorm_vectors.json").read_text(encoding="utf-8"))


def test_vectors_ids_with_homoglyphs_fold_to_the_real_id():
    for case in VECTORS["identities"]:
        real = fold(case["id"], casefold=True, collapse_ws=True)
        for variant in case["variants"]:
            assert fold(decode(variant), casefold=True, collapse_ws=True) == real, (
                case["id"],
                variant,
            )
        for other in case.get("different", []):
            assert fold(decode(other), casefold=True, collapse_ws=True) != real, (case["id"], other)


def test_vectors_domains_with_cyrillic_and_greek_letters_fold_to_the_ascii_domain_but_are_lookalikes():
    for case in VECTORS["domains"]:
        for variant in case["variants"]:
            v = decode(variant)
            assert fold(v, casefold=True) == case["domain"], (case["domain"], variant)
            assert allow_equal(v, case["domain"]) is AllowVerdict.LOOKALIKE, (
                variant
            )  # the ALLOW check refuses every one of them


# ---- output check -----------------------------------------------------------------------------------------------------------------------
SEPS = [" ", "_", ":", "|", "ab", " ab ", chr(0xA0), chr(0x200B), chr(0x301), chr(0x2013), chr(0xE9), chr(0x65E5), chr(0x405), chr(0x43E), chr(0x4AE),
        ".", ",", "-", "/", chr(0xE0002)]  # fmt: skip


def test_digit_budget_beats_separators_letters_scripts_and_punctuation():
    rnd = random.Random(1)  # noqa: S311
    for _ in range(400):
        digs = "".join(
            chr(rnd.choice((0x30, 0xFF10, 0x660, 0x966)) + rnd.randrange(10))
            for _ in range(rnd.randint(8, 18))
        )
        text = "acct " + "".join(d + (rnd.choice(SEPS) if rnd.random() < 0.7 else "") for d in digs)
        assert check_text(text) is not None, text
    assert (
        text_leaks("1234 ab 5678 ab 9012") and text_leaks("1234-12-12") and text_leaks("1999-12-12")
    )


def test_exempt_tokens_are_not_a_free_pass_for_a_card_number_or_an_account():
    for text in (
        "$4111111.11 $1111111.11 1111",
        "$1,234,567.89 $1,234,567.89",
        "2026-11-01 2026-11-02 2026-11-03 2026-11-04",
        " and ".join(f"${i}.50" for i in range(1, 8)),
        "total $41,111,111.11 and $11,111.11",  # 13 digits behind two amounts, a word between them
        "USD 1234567.89 ref USD 1234567.89",
        "12345678.9 USD then 87654321.9 USD",
    ):
        assert check_text(text) in (Violation.EXEMPT_TOKENS, Violation.DIGIT_BUDGET), text
    assert (
        check_text("$4111111.11 $1111111.11") == Violation.EXEMPT_TOKENS
        and check_text("total $41,111,111.11 and $11,111.11") == Violation.EXEMPT_TOKENS
    )
    for text in (
        "1,234 ab 5,678 ab 9,012",
        "2.8 and 5.6 and 7.9 and 1.2 and 3.4",
        "4111111.11 1111111.11 1111",
        "12,345.67 AND 12,345.67",
        "9999999.99 XYZ",
    ):
        assert check_text(text) == Violation.DIGIT_BUDGET, text  # AND and XYZ are not currencies
    assert (
        check_text("dated 2026-11-01, total 15,000 USD") is None
        and check_text("total $1,500.00 due 2026-11-30") is None
    )
    assert (
        check_text(" and ".join(f"${i}.50" for i in range(1, 8))) == Violation.EXEMPT_TOKENS
    )  # token count on its own
    assert (
        check_text("on 2026-11-01 and 2026-11-02 and 2026-11-03 and 2026-11-04")
        == Violation.EXEMPT_TOKENS
    )  # more dates than max_dates
    assert check_text("tax 1,345.67", policy=LeakPolicy(amounts_need_currency=False)) is None
    assert (
        check_text("$1.50 $2.50") == Violation.EXEMPT_TOKENS
    )  # side by side: adjacency alone, few digits
    word = re.compile("ref")
    assert (
        check_text(" x ".join(["ref"] * 7), allowed_patterns=[word]) == Violation.EXEMPT_TOKENS
    )  # token count alone: no digits, not adjacent
    assert check_text(" x ".join(["ref"] * 6), allowed_patterns=[word]) is None
    assert (
        check_text("pay 1500 XTS", policy=LeakPolicy(currencies=frozenset({"XTS"}))) is None
    )  # a configurable currency set


def test_us_and_day_first_dates_are_both_dates():
    assert check_text("paid 03/25/2026 and due 25/03/2026") is None  # two dates
    assert text_leaks(
        "on 13/45/2026 and 99/99/2026 and 11 22 33"
    )  # an impossible date is plain digits


def test_digit_like_letters_count_when_chained_to_digits():
    assert (
        check_text("8 O 1 l 5 S 7 B 3") == Violation.DIGIT_BUDGET
        and check_text("8-O-1-l-5-S-7-B-3") == Violation.DIGIT_BUDGET
    )
    assert (
        check_text("8 L 1 G 5 Q 7 B 3") == Violation.DIGIT_BUDGET
    )  # L, G and Q are in the key fold and now in the budget
    assert check_text("order of 3 small boxes and one big sale") is None
    assert (
        check_text("OlISBZGQ") == Violation.DIGIT_BUDGET
        and check_text("O l I S B Z G Q") == Violation.DIGIT_BUDGET
    )  # fully letter-encoded
    assert (
        check_text("BLISS and a GLOSS finish on the SOIL") is None
    )  # ordinary words made of such letters stay free


def test_a_protected_number_is_found_through_junk_look_alikes_and_exempt_tokens():
    acct = "123456789"
    for text in (
        "Remit 12345.67 and 89.00",
        "pay 123 abc 456 xyz 789",
        "pay 12 3S 4 5B 6 7Z 89",
        "pay I23 4S6 789",
        "pay 1" + chr(0xE0002) + "23456789",
    ):
        assert check_text(text, [acct]) is not None, text
    assert check_text("PO-1234 and 56 nearby", ["987654321"]) is None
    assert check_text("pay 123 abc 4567", ["1234567"]) == Violation.PROTECTED_VALUE
    assert (
        check_text("pin 12 abc 345 ok", ["12345"]) == Violation.PROTECTED_VALUE
    )  # a 5-digit PIN with junk in the middle
    assert squeeze("SBZGQ", loose=True) == "58269" and squeeze("O I L", loose=True) == "011"


def test_non_latin_and_short_protected_values_are_matched_as_words():
    assert (
        check_text(
            "customer " + chr(0x65E5) + chr(0x672C) + chr(0x592A) + chr(0x90CE) + " paid",
            [chr(0x65E5) + chr(0x672C) + chr(0x592A) + chr(0x90CE)],
        )
        == Violation.PROTECTED_VALUE
    )
    cyr = chr(0x418) + chr(0x432) + chr(0x430) + chr(0x43D)
    assert check_text("Dear " + cyr + ", hello", [cyr]) == Violation.PROTECTED_VALUE
    assert (
        check_text("Li paid the bill", ["Li"]) == Violation.PROTECTED_VALUE
        and check_text("Lia paid the bill", ["Li"]) is None
    )
    assert (
        check_text("nothing here", ["Li", cyr]) is None
    )  # a short value no longer takes the whole check down
    with pytest.raises(ValueError):
        check_text("x", ["Li"], policy=LeakPolicy(on_short="raise"))
    for empty in (
        chr(0x200B),
        chr(0xE0002),
        "",
        None,
    ):  # an empty or missing value is an error, not a silent skip
        with pytest.raises(ValueError):
            check_text("x", [empty])  # a value that folds to nothing is always an error


def test_mixed_script_words_and_look_alike_pairs_are_refused():
    assert check_text("pay al" + chr(0x456) + "ce now") == Violation.MIXED_SCRIPT
    assert (
        check_text("alice." + chr(0x3B7) + "g") == Violation.MIXED_SCRIPT
        and check_text("bank" + chr(0x581) + "x") == Violation.MIXED_SCRIPT
    )
    assert (
        check_text("pay al" + chr(0x456) + "ce now", policy=LeakPolicy(deny_mixed_script=False))
        is None
    )


def test_allowed_references_need_a_boundary_and_ignore_case():
    assert check_text("acct 1 2 3 4 5 6 7 8 9", allowed=["1"]) is not None
    assert check_text("!" * 10, allowed=[chr(0x200B)]) is None
    assert (
        check_text("ref ABC-26-0482 ok", allowed=["ABC-26-0482"]) is None
        and check_text("ref abc-26-0482 ok", allowed=["ABC-26-0482"]) is None
    )
    assert check_text("ABC-26-0482 and 123456 ok") is not None  # not allowed: the digits count
    assert (
        check_text("ref abc-26-0482 and 1234 ok", allowed=["ABC-26-0482"]) is None
    )  # the case does not matter; its 6 digits are set aside
    assert check_text("XABC-26-04829999 ok", allowed=["ABC-26-0482"]) is not None


def test_the_length_is_bounded_first_and_types_are_typed():
    assert (
        check_text(None) == Violation.TEXT_NOT_STRING
        and check_text(b"x") == Violation.TEXT_NOT_STRING
    )
    assert check_text("x" * (P.max_len + 1)) == Violation.TEXT_TOO_LONG
    folded = []
    real = textnorm.fold

    import hadavin_sdk.guard.egress_text as eg

    eg.fold = lambda *a, **k: folded.append(1) or real(*a, **k)
    try:
        assert (
            check_text("x " * 600_000) == Violation.TEXT_TOO_LONG and folded == []
        )  # refused before any fold (no cost to the attacker's megabyte)
    finally:
        eg.fold = real


def test_thresholds_come_from_a_validated_policy_and_the_defaults_table_is_documented():
    p = LeakPolicy.from_mapping(
        {"profile": "payments", "max_digits": 12, "date_years": [1990, 2100], "currencies": ["XTS"]}
    )
    assert check_text("id 1234 5678 901", policy=LeakPolicy(max_digits=13)) is None
    assert (
        check_text("id 1234 5678 901", policy=LeakPolicy(max_digits=11)) == Violation.DIGIT_BUDGET
    )
    assert check_text("1995-05-05", policy=p) is None
    for bad in ({"max_digits": 0}, {"max_len": -1}, {"max_len": 10**9}, {"date_years": [2100, 2000]}, {"nope": 1}, {"max_digits": "8"}, {"on_short": "skip"},
                {"max_exempt_digits": 99}, {"currencies": ["usd"]}, {"account_min_len": 2}):  # fmt: skip
        with pytest.raises(ValueError):
            LeakPolicy.from_mapping({"profile": "payments", **bad})
    docs = (Path(__file__).resolve().parents[1] / "docs" / "promoted-controls.md").read_text(
        encoding="utf-8"
    )
    assert all(f"`{name}`" in docs for name in LeakPolicy.__dataclass_fields__), (
        "every LeakPolicy field is in the defaults table"
    )
    for field_name in LeakPolicy.__dataclass_fields__:
        if field_name != "currencies":
            row = next(ln for ln in docs.splitlines() if ln.startswith(f"| `{field_name}`"))
            shown = str(getattr(LeakPolicy.payments(), field_name)).replace("'", '"')
            assert shown in row, (
                field_name,
                row,
            )  # the documented default is the real payments default


def test_account_shapes_and_the_account_length_come_from_the_policy():
    assert check_text("ref AB123456789CD ok") == Violation.ACCOUNT_SHAPED
    assert (
        check_text("ref AB123456789CD ok", policy=LeakPolicy(account_min_len=20, max_digits=20))
        is None
    )


# ---- mutation judge and runner --------------------------------------------------------------------------------------------------------
def test_mutation_judge_verdicts():
    a = "E   AssertionError: assert 1 == 2"
    assert judge(1, "t.py::a", a) == Verdict.KILLED and judge(0, "t.py::a", a) == Verdict.SURVIVED
    assert judge(5, "t.py::a", a) == Verdict.NO_TESTS and judge(2, "t.py::a", a) == Verdict.ERROR
    assert (
        judge(1, "t.py::test_aaaa", a, expect="test_aaaa") == Verdict.KILLED
        and judge(1, "t.py::a", a, expect="zzzz") == Verdict.WRONG_REASON
    )
    with pytest.raises(ValueError):
        judge(1, "t.py::a", a, expect="a")  # a one-letter fragment matches almost anything
    assert judge(1, "t.py::a", a, pinned="t.py::b") == Verdict.OTHER_TEST
    for line in (
        "E   KeyError: 'x'",
        "E   TypeError: boom",
        "E   RuntimeError: x",
        "E   ImportError: no",
        "E   demo.fakes.AuditWriteError: audit write failed",
        "E   Failed: custom",
    ):
        assert judge(1, "t.py::a", line) == Verdict.CRASH, line
    assert judge(1, "t.py::a", "E   Failed: DID NOT RAISE <class 'TypeError'>") == Verdict.KILLED
    internal = "E   AssertionError: assert 'denied:internal_error' == 'queued'"
    assert judge(1, "t.py::a", internal) == Verdict.KILLED
    assert (
        judge(
            1, "t.py::a", internal, crash_markers=[re.compile(r"assert 'denied:internal_error' ==")]
        )
        == Verdict.CRASH
    )
    out = "FAILED tests/t.py::test_x[1] - assert 1\nE   AssertionError: assert 1 == 2\n"
    assert first_failure(out) == ("tests/t.py::test_x[1]", "E   AssertionError: assert 1 == 2")
    xml = (
        '<testsuite><testcase classname="tests.t" name="test_ok"/><testcase classname="tests.t" name="test_x[a - b | c]">'
        '<failure message="boom">def f():\nE   AssertionError: assert 1 == 2\n</failure></testcase></testsuite>'
    )
    assert first_failure_junit(xml) == (
        "tests/t::test_x[a - b | c]",
        "E   AssertionError: assert 1 == 2",
    )  # ids with ' - ' and ' | ' are intact


def test_the_contract_check_raises_assertion_error_not_assert():
    class Broken(RowStore):
        def get(self, key):
            return self._rows[key]  # a live row: breaks copy-on-read

    with pytest.raises(AssertionError, match="copy"):
        check_rowstore_contract(Broken)
    assert "assert " not in "\n".join(
        ln
        for ln in inspect.getsource(check_rowstore_contract.__globals__["_check"]).splitlines()
        if ln.strip().startswith("assert ")
    )


def test_the_runner_kills_a_mutant_of_a_tiny_package(tmp_path):
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__init__.py").write_text(
        "def guard(x):\n    if x < 0:\n        raise ValueError('negative')\n    return x\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_g.py").write_text(
        "import pytest\nfrom pkg import guard\n\ndef test_guard_refuses_negative():\n    with pytest.raises(ValueError):\n        guard(-1)\n",
        encoding="utf-8",
    )
    res = run_mutants(
        tmp_path,
        [Mutant("guard removed", "src/pkg/__init__.py", "if x < 0:", "if False:", "test_guard_refuses_negative"),
         Mutant("no-op mutant", "src/pkg/__init__.py", "return x", "return x  # same", "test_guard_refuses_negative"),
         Mutant("crash mutant", "src/pkg/__init__.py", "if x < 0:", "if 1 / 0:", "test_guard_refuses_negative"),
         Mutant("missing snippet", "src/pkg/__init__.py", "nope", "x", "test_guard")],
        ["tests/test_g.py"],
    )  # fmt: skip
    by = {n: (v, good) for n, v, _, good in res}
    assert (
        by["guard removed"] == (Verdict.KILLED, True)
        and by["no-op mutant"][1] is False
        and by["missing snippet"][1] is False
    )
    assert by["crash mutant"] == (Verdict.CRASH, False)  # an exception is not an assertion kill


# ---- review round 3: digit budget that adds up, CJK, presets, no default policy ---------------------------------------------------------
def test_the_plain_and_the_set_aside_digits_add_up():
    for text in (
        "ref 4111111 total $1,111,111.11 USD",  # 7 plain + 9 in an amount: a 16-digit card
        "4111111 $1,111,111.11",
        "4111111 $1,111.11",  # 7 plain + 6 in an amount: the exempt budget alone allows it, the sum does not
        "411111 $11,111.11 on 2026-03-01",  # 6 + 7 + a date
        "4111 2026-03-01 2026-03-02 2026-03-03",  # a card as dates: more dates than allowed
    ):
        assert check_text(text) is not None, text
    assert check_text("4111111 $1,111.11") == Violation.DIGIT_BUDGET
    assert (
        check_text("pay $1,250.00 for order 12345") is None
        and check_text("due 2026-03-01 for $1,250.00") is None
    )
    assert check_text("a 2026-03-01 and 2026-03-02 and nothing else") is None  # 2 dates: 10 of 14
    assert (
        check_text("4111111 for 2026-03-01 and 2026-03-02") == Violation.DIGIT_BUDGET
    )  # 7 + 10 of 14
    for bad in (
        {"max_exempt_digits": 8},
        {"max_total_digits": 13},
        {"max_total_digits": 0},
        {"max_digits": 6, "max_exempt_digits": 2, "max_total_digits": 11},
    ):
        with pytest.raises(ValueError):
            LeakPolicy(
                **bad
            )  # exempt digits must stay below max_digits; the total below 2 x max_digits - 1


def test_there_is_no_default_policy_and_the_presets_are_named():
    with pytest.raises(TypeError):
        egress_text.check_text("hello")  # the policy is required
    assert not hasattr(egress_text, "DEFAULT_POLICY")
    pay, gen = LeakPolicy.payments(), LeakPolicy.general()
    assert pay.max_digits == 8 and pay.max_total_digits == 12
    ten_digit_phone = "phone 0123456789 thanks"
    assert egress_text.check_text(ten_digit_phone, policy=pay) is not None
    assert egress_text.check_text(ten_digit_phone, policy=gen) is None
    assert (
        egress_text.check_text("4111 1111 1111 1111", policy=gen) == Violation.DIGIT_BUDGET
    )  # a card in one piece is still refused
    assert (
        LeakPolicy.from_mapping({"profile": "payments"}) == pay
        and LeakPolicy.from_mapping({"profile": "general"}) == gen
    )
    for no_profile in ({}, None, {"max_digits": 9}, {"profile": "strict"}):
        with pytest.raises(ValueError):
            LeakPolicy.from_mapping(no_profile)  # a config must name its profile


def test_a_protected_value_in_unspaced_text_and_glued_to_digits_is_found():
    zhang = chr(0x5F20) + chr(0x4F1F)
    for text in (
        chr(0x8054) + chr(0x7CFB) + zhang + chr(0x5427),  # CJK inside CJK, no spaces
        "Bob123 paid",
        "Bob_7 paid",
        "x" + chr(0xE00) + chr(0xE01),  # unrelated Thai: no hit expected below
    ):
        hit = check_text(text, [zhang, "Bob"])
        assert (hit == Violation.PROTECTED_VALUE) == (chr(0xE00) not in text), text
    thai = chr(0xE2A) + chr(0xE21) + chr(0xE0A) + chr(0xE32) + chr(0xE22)
    assert (
        check_text(chr(0xE04) + chr(0xE38) + chr(0xE13) + thai + chr(0xE19) + chr(0xE30), [thai])
        == Violation.PROTECTED_VALUE
    )
    assert (
        check_text("Bobby paid", ["Bob"]) is None
        and check_text("Bob paid", ["Bob"]) == Violation.PROTECTED_VALUE
    )
    assert (
        check_text("no 42x here", ["42"]) is None
        and check_text("code 42 here", ["42"]) == Violation.PROTECTED_VALUE
    )


def test_a_look_alike_name_in_a_single_script_is_folded_to_the_protected_latin_value():
    cherokee_name = "".join(map(chr, (0x13A0, 0x13AA)))  # D A
    assert (
        check_text("contact " + cherokee_name + " now", ["DA"], policy=LeakPolicy(on_short="token"))
        == Violation.PROTECTED_VALUE
    )


# ---- review round 3: stop gate over the real Limits ---------------------------------------------------------------------------------------
def real_limits(tmp_path, store=None, sink=None):
    return Limits(store or MemoryStore(), sink or LocalDirSink(tmp_path), None)


def test_stopgate_over_real_limits(tmp_path):
    lim = real_limits(tmp_path)
    g, other = StopGate(lim), StopGate(lim)
    res = g.engage(list, lambda k: "x", by="u-ctl-01")
    assert res.durable and lim.store.get_kill_switch().on
    ev = lim.audit.events()
    assert [(e.operation, e.principal, e.result, e.source) for e in ev] == [
        ("stop", "u-ctl-01", "on", "gate")
    ]
    with pytest.raises(EffectBlocked), g.effect():
        raise AssertionError("an effect must not start")
    assert other.blocked() and not other.engaged  # a second gate sees the durable switch
    g.release(by="u-ctl-01")
    assert not lim.store.get_kill_switch().on and not g.blocked()
    assert [(e.operation, e.result, e.source) for e in lim.audit.events()] == [
        ("stop", "on", "gate"),
        ("reset", "off", "gate"),
    ]
    lim.stop("op")  # the CLI path keeps its source
    assert lim.audit.events()[-1].source == "cli" and lim.is_stopped()


def test_release_over_real_limits_with_the_audit_down_keeps_the_switch_on(tmp_path):
    class Down(LocalDirSink):
        down = False

        def write_intent(self, ev):
            if self.down:
                raise AuditUnavailable("down")
            return super().write_intent(ev)

    sink = Down(tmp_path)
    lim = real_limits(tmp_path, sink=sink)
    g = StopGate(lim)
    g.engage(list, lambda k: "x", by="u1")
    sink.down = True
    with pytest.raises(AuditUnavailable):
        g.release(by="u1")
    assert lim.store.get_kill_switch().on and g.engaged and g.blocked()
    sink.down = False
    g.release(by="u1")
    assert not g.engaged and not lim.is_stopped()


def test_engage_over_real_limits_with_the_store_down_still_blocks_and_leaves_an_audit_row(tmp_path):
    class Bad(MemoryStore):
        down = False

        def set_kill_switch(self, ks):
            if self.down:
                raise OSError("store down")
            return super().set_kill_switch(ks)

        def get_kill_switch(self):
            if self.down:
                raise OSError("store down")
            return super().get_kill_switch()

    store = Bad()
    lim = real_limits(tmp_path, store=store)
    store.down = True
    g = StopGate(lim)
    res = g.engage(list, lambda k: "x", by="u-ctl-01")
    assert (
        res.durable is False and "OSError" in (res.store_error or "") and g.engaged and g.blocked()
    )
    with pytest.raises(EffectBlocked), g.effect():
        raise AssertionError("an effect must not start")
    ev = lim.audit.events()
    assert [(e.operation, e.principal, e.result, e.source) for e in ev] == [
        ("stop", "u-ctl-01", "on", "gate")
    ]
    assert (ev[0].error_code or "").startswith(
        "durable_write_failed:OSError"
    )  # the emergency stop is on record, marked not durable


def test_a_late_release_cannot_undo_a_newer_engage():
    lim = FakeLimits()
    g = StopGate(lim)
    g.engage(list, lambda k: "x", by="u1")
    lim.during_reset = lambda: g.engage(
        list, lambda k: "x", by="u2"
    )  # an engage lands while release is in its slow reset
    with pytest.raises(StopGateBusy):
        g.release(by="u1")
    assert (
        g.engaged and lim.store.ks.on and g.blocked()
    )  # neither the flag nor the durable switch was cleared
    lim.during_reset = None
    g.release(by="u1")
    assert not g.engaged and not lim.store.ks.on


def test_a_late_release_in_a_thread_cannot_undo_an_engage_from_another_thread():
    lim = FakeLimits()
    g = StopGate(lim)
    g.engage(list, lambda k: "x", by="u1")
    inside, go = threading.Event(), threading.Event()
    errors = []

    def slow():
        inside.set()
        go.wait(5)

    lim.during_reset = slow

    def rel():
        try:
            g.release(by="u1")
        except StopGateBusy as e:
            errors.append(e)

    t = threading.Thread(target=rel)
    t.start()
    assert inside.wait(5)
    lim.during_reset = None
    g.engage(list, lambda k: "x", by="u2")
    go.set()
    t.join(5)
    assert errors and g.engaged and lim.store.ks.on


def test_aengage_inside_an_aeffect_does_not_wait_for_its_own_effect():
    async def scenario():
        g = StopGate(FakeLimits())
        async with g.aeffect():
            res = await g.aengage(lambda: ["k"], lambda k: "ok", by="u1", timeout=5)
        assert res.complete and res.in_flight_at_timeout == 0 and res.results == [("k", "ok")]
        # an effect opened by ANOTHER task is still waited for
        g2 = StopGate(FakeLimits())
        started, done = asyncio.Event(), asyncio.Event()

        async def other():
            async with g2.aeffect():
                started.set()
                await done.wait()

        task = asyncio.create_task(other())
        await started.wait()
        res2 = await g2.aengage(lambda: ["k"], lambda k: "ok", by="u1", timeout=0.05)
        assert res2.complete is False and res2.in_flight_at_timeout == 1
        done.set()
        await task

    asyncio.run(scenario())


def test_engaged_is_the_flag_blocked_reads_the_store_and_the_second_engage_says_it_wrote_nothing():
    lim = FakeLimits()
    g = StopGate(lim)
    lim.store.ks = StoredKillSwitch(on=True)
    assert (
        g.engaged is False and g.blocked() is True and g.durable_on() is True
    )  # engaged is the process flag only
    gate2, inside, go, results = StopGate(FakeLimits()), threading.Event(), threading.Event(), []
    t = threading.Thread(
        target=lambda: gate2.engage(
            lambda: ["k"], lambda k: (inside.set(), go.wait(5), "ok")[2], by="u"
        )
    )
    t.start()
    assert inside.wait(5)
    results.append(gate2.engage(list, lambda k: "x", by="u2"))
    go.set()
    t.join(5)
    assert results[0].already_sweeping and results[0].durable is None
    g3 = StopGate(lim, cache_ttl=1000.0)
    lim.store.ks = StoredKillSwitch(on=False)
    assert not g3.blocked()
    lim.store.ks = StoredKillSwitch(on=True)
    assert (
        not g3.blocked()
    )  # the stale-allow window: a cached off hides an operator's stop for up to cache_ttl
    g3.engage(list, lambda k: "x", by="u")
    assert g3.blocked() and g3._cached is None  # engage clears the cache


# ---- review round 3: the mutation runner stays inside its tree, and stops a hanging mutant --------------------------------------------------
def test_the_runner_refuses_paths_that_leave_its_tree(tmp_path):
    from tools import mutation_runner as mr

    for bad in (
        "../x.py",
        "a/../../x.py",
        "/etc/passwd",
        "C:\\x.py",
        "\\\\host\\share\\x.py",
        "",
        "..\\x.py",
    ):
        with pytest.raises(ValueError):
            Mutant("name", bad, "a", "b", "test_x_assertion")
    outside = tmp_path / "outside.txt"
    with pytest.raises(ValueError):
        mr._inside(tmp_path / "base", "../outside.txt")
    (tmp_path / "base").mkdir()
    assert mr._inside(tmp_path / "base", "src/a.py").is_relative_to((tmp_path / "base").resolve())
    link = tmp_path / "base" / "link"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except (OSError, NotImplementedError):  # no symlink right: a Windows junction needs none
        import subprocess

        subprocess.run(  # noqa: S603
            ["cmd", "/c", "mklink", "/J", str(link), str(tmp_path)],  # noqa: S607
            capture_output=True,
            check=False,
        )
    assert link.exists(), "the test could not create a link out of the tree"
    with pytest.raises(ValueError):
        mr._inside(tmp_path / "base", "link/outside.txt")  # a link out of the tree is refused too
    (tmp_path / "real.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        mr._locate(
            tmp_path / "base", "link/real.txt"
        )  # the listing does not follow the link out of the tree
    with pytest.raises(ValueError):
        Mutant("name", "a.py", "a", "b", "abc")  # expect shorter than 4 characters
    victim = tmp_path / "victim.txt"
    victim.write_text("before", encoding="utf-8")
    forged = Mutant("forged", "src/a.py", "before", "after", "test_x_assertion")
    object.__setattr__(
        forged, "file", str(victim)
    )  # a Mutant built around __post_init__: the runner checks again
    pkg = tmp_path / "pkg0"
    (pkg / "src").mkdir(parents=True)
    (pkg / "tests").mkdir()
    (pkg / "tests" / "test_a.py").write_text(
        "def test_a():" + chr(10) + "    assert True" + chr(10), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        run_mutants(pkg, [forged], ["tests/test_a.py"], extra_dirs=())
    assert victim.read_text(encoding="utf-8") == "before"
    assert not outside.exists()
    root = tmp_path / "pkg"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    for tests, extra in (
        (["../x.py"], ()),
        (["tests/test_a.py"], ("../x",)),
        (["/abs/test.py"], ()),
    ):
        with pytest.raises(ValueError):
            run_mutants(root, [], tests, extra_dirs=extra)


def test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run(tmp_path):
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("FLAG = False\n", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n",
        encoding="utf-8",
    )
    hang = Mutant(
        "hang", "src/pk/core.py", "return flag", "while True:\n        pass", "test_go_is_true"
    )
    out = run_mutants(
        root, [hang], ["tests/test_core.py"], extra_dirs=(), timeout=6, baseline_timeout=180
    )
    assert out == [("hang", Verdict.ERROR, "TIMEOUT", False)]


def test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option(tmp_path):
    from tools import mutation_runner as mr

    (tmp_path / "test_ok.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    assert mr._pytest(tmp_path, ["test_ok.py"], tmp_path / "r2.xml", 60) == 0
    # as a bare option "-x" would collect and pass test_ok.py in the cwd; as an operand it is a missing file
    assert mr._pytest(tmp_path, ["-x"], tmp_path / "r.xml", 60) != 0


def test_capped_audit_clips_the_kind_caps_distinct_kinds_and_purges_once_per_bucket():
    rows = []
    ca = CappedAudit(
        lambda kind, **f: rows.append((kind, f.get("tenant"))), cap=1, max_keys=3, max_kinds=2
    )
    for i in range(50):
        ca.deny("t", f"kind-{i}", "b")  # an outsider picking kind names
    assert len({k[1] for k in ca._n}) <= 3 and len(ca._n) <= 4  # two kinds plus the shared "*"
    long_rows = []
    wide = CappedAudit(lambda kind, **f: long_rows.append(kind), cap=1)
    wide.deny("t", "k" * 500, "b")
    assert (
        all(len(k[1]) <= 64 for k in wide._n)
        and all(len(kind) <= 64 for kind in long_rows)
        and long_rows
    )
    # the stale scan runs when the bucket changes, not on every new key
    scans = []
    cb = CappedAudit(lambda kind, **f: None, cap=1, max_keys=2)
    cb.deny("t0", "d", "same-bucket")  # the first bucket: one purge

    class Counting(dict):
        def items(self):
            scans.append(1)
            return super().items()

    cb._n = Counting(cb._n)
    for i in range(30):
        cb.deny(f"t{i}", "d", "same-bucket")
    assert scans == []  # no scan for the 29 new keys that arrived while the table was full
    cb.deny("t-new", "d", "next-bucket")
    assert scans == [1]


def test_a_tenant_called_star_or_with_a_pipe_cannot_collide_with_the_overflow_counter_or_another_tenant(
    tmp_path,
):
    sink = RecordingSink()
    ca = CappedAudit(sink_append(sink, "r", "d"), cap=1, max_keys=1)
    ca.deny("real", "denied", "b", key="k")  # takes the only counter
    for _ in range(3):
        ca.deny(
            "*", "denied", "b", key="k"
        )  # a tenant literally named "*" overflows like any other
    assert ca.suppressed("*", "denied") == 0 and ca.overflow_suppressed("denied") >= 2
    sink.events.clear()
    for _ in range(3):
        ca.deny("zzz", "other", "b", key="k")
        ca.deny("yyy", "other", "b", key="k")
    marker = next(e for e in sink.events if e.operation == "audit_suppressed")
    assert marker.object_ref.startswith(
        "*|"
    )  # the overflow marker names "*", not the first tenant that overflowed
    sink2 = RecordingSink()
    cc = CappedAudit(sink_append(sink2, "r", "d"), cap=5)
    cc.append("a|b", "denied", "b", key="c")
    cc.append("a", "denied", "b", key="b|c")
    refs = [e.object_ref for e in sink2.events]
    assert (
        refs == ["a%7Cb|c", "a|b|c"] and len(set(refs)) == 2
    )  # the tenant is escaped: no two (tenant, key) pairs give one ref
    assert ca.suppressed("never-seen", "denied") == 0


def test_freeze_has_a_node_budget_and_thaw_a_depth_guard(monkeypatch):
    from hadavin_sdk.runtime import config_view as cv

    shared = {"x": 1}
    node = shared
    for _ in range(21):
        node = {"a": node, "b": node}  # 21 levels, 2**21 paths
    with pytest.raises(TypeError, match="values"):
        freeze(node)
    monkeypatch.setattr(cv, "MAX_NODES", 50)
    with pytest.raises(TypeError, match="values"):
        freeze({"k": list(range(100))})
    monkeypatch.undo()
    deep = cur = []
    for _ in range(200):
        nxt = []
        cur.append(nxt)
        cur = nxt
    with pytest.raises(TypeError):
        thaw(deep)  # not a RecursionError
    cyc = []
    cyc.append(cyc)
    with pytest.raises(TypeError):
        thaw(cyc)


def test_the_row_store_has_a_default_row_limit_and_none_opts_out():
    rs = RowStore()
    assert rs._max_rows == 100_000 and RowStore(max_rows=None)._max_rows is None
    small = RowStore(max_rows=2)
    for i in range(2):
        small.put_audited(lambda *a, **k: None, "k", f"r{i}", {})
    with pytest.raises(StoreFull):
        small.put_audited(lambda *a, **k: None, "k", "r9", {})


def test_redact_masks_a_value_hidden_behind_look_alikes_on_the_line_and_leaves_other_text_alone():
    from hadavin_sdk.guard.redact import redact

    r = redact("mail al" + chr(0x456) + "ce@example.com now")
    assert (
        "alice" not in r.text
        and "<EMAIL_1>" in r.text
        and r.mapping == {"<EMAIL_1>": "alice@example.com"}
    )  # the folded value
    r2 = redact("password=hun" + chr(0x442) + "er2xyz")
    assert "hun" not in r2.text and "<SECRET_1>" in r2.text
    assert (
        redact("caf" + chr(0xE9) + " menu").text == "caf" + chr(0xE9) + " menu"
    )  # no hit: the line is returned unchanged
    assert redact("plain ascii line").text == "plain ascii line"
    multi = redact(
        "first line"
        + chr(10)
        + "mail al"
        + chr(0x456)
        + "ce@example.com"
        + chr(10)
        + "last "
        + chr(0xE9)
    )
    assert multi.text.split(chr(10))[0] == "first line" and multi.text.endswith(
        "last " + chr(0xE9)
    )  # only the hit line changes


# ---- review round 5 (code-4): documented guarantees, newline in the script check, honest docs, process-tree kill -------------------------
def test_general_delivers_ids_up_to_eleven_digits_and_payments_keeps_order_numbers_free():
    general, payments = LeakPolicy.general(), LeakPolicy.payments()
    for text in (
        "id 12345678901 ok",
        "order 1234567890 of 5 orders",
        "id is 12345678901",  # a word BEFORE the digits ends in a lone digit-like letter
        "Total 12345678901",
        "Tel 12345678901",
        "was 12345678901",
        "status 12345678901",
        "Total: 12345678901 shipped",
    ):
        assert egress_text.check_text(text, policy=general) is None, text
        assert egress_text._digitish_count(text, 6) == 11, text
    # two or more digit-like letters in a word still count ("call", "soldiers"); a bare letter still counts
    assert (
        egress_text.check_text("call 12345678901", policy=general) is None
    )  # a word before the id is free
    assert egress_text.check_text("12345678901s", policy=general) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("12345678901ok", policy=general) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("12345678901 O", policy=general) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("Oats Ibex Sand Zeal", policy=payments) is None  # words are free
    assert egress_text.check_text("Order 1234567 shipped", policy=payments) is None
    assert egress_text._digitish_count("id 12345678901 ok", 6) == 11
    assert egress_text._digitish_count("Order 1234567 shipped", 6) == 7
    # a real digit-like run is still counted, in both presets' fail-closed direction
    assert egress_text.check_text("1b5i7g3q", policy=payments) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("OlISBZGq", policy=payments) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("id 12345678901 O l", policy=general) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("12345678901 OS", policy=general) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("8 O 1 l 5 S 7 b 3 i", policy=payments) == Violation.DIGIT_BUDGET


def test_a_newline_or_tab_separates_words_in_the_mixed_script_check():
    ru = "".join(map(chr, (0x43F, 0x440, 0x438, 0x432, 0x435, 0x442)))
    ru_name = chr(0x418) + chr(0x43C) + chr(0x44F)
    for sep in ("\n", "\t", "\r\n", chr(0x2028), "\x0b"):
        assert not has_mixed_script("ab" + sep + ru), repr(sep)
    assert not has_mixed_script("Name\t" + ru_name)
    assert egress_text.check_text("Hello\n" + ru, policy=LeakPolicy.payments()) is None
    # a zero-width space INSIDE a word still does not split it
    assert has_mixed_script("ab" + chr(0x200B) + ru)
    assert has_mixed_script("b" + chr(0x200B) + chr(0x13AA) + "nk")


def test_the_egress_docstring_states_what_the_code_counts():
    doc = egress_text.__doc__
    counted = egress_text._digitish_count
    assert counted("1b5i7g3q", 6) == 8 and counted("OlISBZGq", 6) == 8  # what the sentence claims
    assert "``1b5i7g3q`` is 8" in doc and "MONOTONIC" in doc and "WHAT THIS DOES NOT STOP" in doc
    assert "xl xl xl" in doc and "free text" in doc  # the rule-aware writer is named, not hidden
    fn = counted.__doc__
    for phrase in (
        "MONOTONIC",
        "FREE WORDS",
        "WHOLE TEXT",
        "WHAT THIS DOES NOT STOP",
        "letter-only",
    ):
        assert phrase in fn, phrase
    log = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    if log.exists():
        text = log.read_text(encoding="utf-8")
        assert "refused by `payments()`" in text and "allowed by `general()`" in text
        assert "What this does NOT" in text and "MONOTONIC" in text
    docs = Path(__file__).resolve().parents[1] / "docs" / "promoted-controls.md"
    if docs.exists():
        dtext = docs.read_text(encoding="utf-8")
        assert "what the check does and does NOT stop" in dtext and "`12345678901s`" in dtext
        assert "five pinned files" in dtext and "three text-fold" not in dtext


def test_a_second_engage_is_not_complete():
    gate = StopGate()
    started, hold = threading.Event(), threading.Event()

    def items():
        started.set()
        hold.wait(10)
        return []

    t = threading.Thread(target=lambda: gate.engage(items, lambda k: "x", by="u"))
    t.start()
    assert started.wait(10)
    try:
        second = gate.engage(list, lambda k: "x", by="u")
        assert second.already_sweeping and second.complete is False
    finally:
        hold.set()
        t.join(10)


def _pid_alive(pid):
    import os
    import subprocess

    if os.name == "nt":
        out = subprocess.run(  # noqa: S603
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def test_a_failing_tree_kill_still_kills_the_child(monkeypatch):
    import subprocess
    import sys

    from tools import mutation_runner as mr

    def boom(*a, **k):
        raise FileNotFoundError("taskkill")

    def denied(*a, **k):
        raise PermissionError("killpg")

    monkeypatch.setattr(mr.subprocess, "run", boom)
    monkeypatch.setattr(mr.os, "killpg", denied, raising=False)
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    try:
        mr._kill_tree(proc)
        assert proc.poll() is not None
    finally:
        proc.kill()
        proc.wait()


def test_the_baseline_run_gets_its_own_timeout(tmp_path, monkeypatch):
    from tools import mutation_runner as mr

    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8"
    )
    seen = []

    def fake(cwd, tests, junit, timeout):
        seen.append(timeout)
        return 0 if len(seen) == 1 else mr.TIMED_OUT

    monkeypatch.setattr(mr, "_pytest", fake)
    mut = Mutant("m", "src/pk/core.py", "return flag", "return not flag", "test_a_x")
    out = run_mutants(
        root, [mut], ["tests/test_core.py"], extra_dirs=(), timeout=7, baseline_timeout=111
    )
    assert seen == [111, 7] and out == [("m", Verdict.ERROR, "TIMEOUT", False)]
    seen.clear()
    run_mutants(root, [mut], ["tests/test_core.py"], extra_dirs=(), timeout=9)
    assert seen == [9, 9]  # the baseline falls back to the mutant timeout


def test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout(tmp_path, monkeypatch):
    from tools import mutation_runner as mr

    assert mr.TIMED_OUT != -9 and mr.TIMED_OUT < -64  # no process exit status can equal it
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "core.py").write_text("def go(flag):\n    return flag\n", encoding="utf-8")
    (root / "tests" / "test_core.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    codes = iter([0, -9, mr.TIMED_OUT])  # baseline, a mutant killed by SIGKILL (the OOM killer), a mutant that timed out

    monkeypatch.setattr(mr, "_pytest", lambda cwd, tests, junit, timeout: next(codes))
    muts = [Mutant(f"m{i}", "src/pk/core.py", "return flag", "return not flag", "test_a_x") for i in range(2)]
    seen, finished = [], []
    mr_run = mr.run_mutants

    def on_result(row):
        seen.append(row[0])
        finished.append(len(seen))  # called once per mutant, in order, before the run returns

    out = mr_run(root, muts, ["tests/test_core.py"], extra_dirs=(), on_result=on_result)
    assert seen == ["m0", "m1"] and finished == [1, 2] and [r[0] for r in out] == seen
    assert out[0][1] is Verdict.ERROR and out[0][2] != "TIMEOUT" and out[0][3] is False  # SIGKILL: an error, not a timeout
    assert out[1] == ("m1", Verdict.ERROR, "TIMEOUT", False)


def test_a_timeout_kills_the_whole_process_tree_not_only_pytest(tmp_path):
    import time

    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n",
        encoding="utf-8",
    )
    pidfile = tmp_path / "pid.txt"
    body = (
        "import subprocess, sys, time\n"
        "    c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
        f"    open({str(pidfile)!r}, 'w').write(str(c.pid))\n"
        "    time.sleep(600)"
    )
    spawn = Mutant("spawn", "src/pk/core.py", "return flag", body, "test_go_is_true")
    out = run_mutants(
        root, [spawn], ["tests/test_core.py"], extra_dirs=(), timeout=30, baseline_timeout=180
    )
    assert out == [("spawn", Verdict.ERROR, "TIMEOUT", False)]
    pid = int(pidfile.read_text(encoding="utf-8"))
    for _ in range(50):
        if not _pid_alive(pid):
            break
        time.sleep(0.2)
    assert not _pid_alive(pid), "the grandchild survived the timeout"


def test_the_generator_reproduces_the_checked_in_table_offline(tmp_path):
    import importlib.util
    import unicodedata

    from hadavin_sdk.guard import _confusables

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "gen_confusables2", root / "tools" / "gen_confusables.py"
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    data = (root / "tools" / "data" / "confusables.txt").read_bytes()
    assert (
        gen.DEFAULT_INPUT.read_bytes() == data
    )  # the generator reads the vendored file by default
    import hashlib

    assert (
        hashlib.sha256(data).hexdigest() == gen.PINNED_SHA256 == _confusables.DATA_SHA256
    )  # the vendored file is the pinned one
    if unicodedata.unidata_version != _confusables.DATA_UNICODEDATA:
        pytest.skip(
            "the small-capital rule reads this interpreter's character names: regenerate only on Unicode "
            + _confusables.DATA_UNICODEDATA
        )
    assert gen.build(data.decode("utf-8")) == _confusables.TABLE


def test_check_text_runs_the_card_scan_last(monkeypatch):
    monkeypatch.setattr(egress_text, "_card_run", lambda stream: True)
    assert check_text("hello there") == Violation.CARD_NUMBER
    monkeypatch.setattr(egress_text, "_card_run", lambda stream: False)
    assert check_text("hello there") is None


# ---- review round 6 (code-6): a monotonic count, caps on free words, a whole-text reading ---------------------------------------------
_MONO_TOKENS = [
    "4", "12", "5551234567", "O", "l", "S", "I", "b", "q", "Ib", "Ob", "Sb", "is", "Gq", "Ol", "IS", "BZ", "call", "Hello", "Total", "xl",
    "x", "lllll", "lllllx", "boss", "big", "12345678901s", "1b5i7g3q", "Zeal", "id", "a", "to", "SOS", "oil", "OlISBZGq", "9",
]  # fmt: skip


def test_the_digit_like_count_is_monotonic_under_appended_tokens():
    import random

    rng = random.Random(20261102)  # noqa: S311 - a seeded test generator, not a secret
    for _ in range(3000):
        run_min = rng.choice((3, 6, 6, 6))
        free_run, free_text = rng.choice(((2, 2), (2, 4), (0, 0), (1, 3), (5, 9)))
        text, prev = "", 0
        for _ in range(rng.randint(1, 16)):
            text = (text + rng.choice(" -,.:;/") + rng.choice(_MONO_TOKENS)).strip(" -,.:;/")
            n = egress_text._digitish_count(text, run_min, free_run, free_text)
            assert n >= prev, (text, run_min, free_run, free_text, prev, n)
            prev = n


def test_padding_and_splitting_cannot_hide_a_letter_encoded_number():
    payments, general = LeakPolicy.payments(), LeakPolicy.general()
    refused = (
        "4 " + " ".join(["Ib"] * 15),
        "Ob Ib Sb Zb Bb Lb 5",
        "4 x lllll x lllll x lllll",
        "4 lllllx lllllx lllllx",
        "4 " + " ".join(["Ol"] * 8),
    )
    for text in refused:
        assert egress_text.check_text(text, policy=payments) == Violation.DIGIT_BUDGET, text
        assert egress_text.check_text(text, policy=general) == Violation.DIGIT_BUDGET, text
    assert egress_text.check_text("Ol IS BZ Gq 5", policy=payments) == Violation.DIGIT_BUDGET
    count = egress_text._digitish_count
    assert count("Ol IS BZ Gq 5", 6) >= count("Ol IS BZ Gq", 6) == 8  # a digit never lowers a count
    assert count("Ob Ib Sb Zb Bb Lb 5", 6) >= count("Ob Ib Sb Zb Bb Lb", 6) == 12
    assert count("4 " + " ".join(["Ib"] * 15), 6) > count(" ".join(["Ib"] * 15), 6) - 1
    # prose stays free: no digit, no whole-text reading
    assert egress_text.check_text("BLISS and a GLOSS finish on the SOIL", policy=payments) is None
    assert egress_text.check_text("Oats Ibex Sand Zeal", policy=payments) is None


def test_ordinary_words_before_a_phone_or_an_id_are_free_up_to_the_caps():
    general, payments = LeakPolicy.general(), LeakPolicy.payments()
    for text in (
        "call 5551234567",
        "Hello 5551234567",
        "will 5551234567",
        "tell 5551234567",
        "CALL 5551234567",
        "all 5551234567",
        "still 5551234567",
        "Tel: 5551234567 was",
    ):
        assert egress_text.check_text(text, policy=general) is None, text
    # the documented price: a letter glued to the digits counts, so an 11-digit id with a suffix is refused
    for text in ("12345678901s", "12345678901st"):
        assert egress_text.check_text(text, policy=general) == Violation.DIGIT_BUDGET, text
    # caps: the third and later words in one run count, and a policy can switch the rule off
    many = "is is is 5551234567"
    assert egress_text._digitish_count(many, 6, 2, 9) == 11  # two free, the third counts
    assert egress_text._digitish_count(many, 6, 0, 0) == 13
    two_runs = "is 5551234 x is 5551234"  # the cap over the whole text: the second run gets none
    assert egress_text._digitish_count(two_runs, 6, 2, 1) == 15
    assert egress_text._digitish_count(two_runs, 6, 2, 2) == 14
    off = LeakPolicy.from_mapping({"profile": "general", "max_free_words": 0})
    assert egress_text.check_text("id is 12345678901", policy=off) == Violation.DIGIT_BUDGET
    assert (
        payments.max_free_words_run == 2
        and payments.max_free_words == 2
        and general.max_free_words == 4
    )
    for bad in ({"max_free_words_run": -1}, {"max_free_words": True}, {"max_free_words": 51}):
        with pytest.raises(ValueError):
            LeakPolicy(**bad)


def test_a_store_error_reports_the_class_name_only_and_no_store_reports_nothing_written():
    class Boom:
        audit = None

        def stop(self, by, source="cli"):
            raise OSError("host=db.internal user=svc password=hunter2")

        def reset(self, by, source="cli"):
            pass

        def is_stopped(self):
            return False

    res = StopGate(Boom()).engage(list, lambda k: "x", by="u")
    assert res.durable is False and res.store_error == "OSError"
    assert "hunter2" not in repr(res)
    assert StopGate().engage(list, lambda k: "x", by="u").durable is None


def test_weak_digit_look_alikes_count_inside_a_qualified_run_but_prose_stays_free():
    for text in (
        "OlISBZGq",
        "O l I S B Z G q",
        "OlISBZGi",
        "OlISBZbq",
        "Ol IS BZ Gq",
        "8 O 1 l 5 S 7 b 3 i",
    ):
        assert check_text(text) == Violation.DIGIT_BUDGET, text
    for text in (
        "it is a big issue for the bank, is so big, a big gig",
        "this is big 12345",
        "a big issue for order 12345 and the biggest boss",
        "bigbig gigs quiz is a bliss",
    ):
        assert check_text(text) is None, text
    assert (
        egress_text._digitish_count("OlISBZGq", 6) == 8
        and egress_text._digitish_count("1b5i7g3q", 6) == 8
    )  # the residual, stated


def test_a_card_length_sequence_is_refused_in_every_preset_even_when_split():
    card_splits = (
        "ref 4111111 total $1,111,111.11 USD",
        "4111111 $1,111,111.11",
        "411111 $11,111.11 on 2026-03-01",
        "4111 2026-03-01 2026-03-02 and 1234",
        "41111111 $1,234.56",
        "4111 1111 1111 1111",
        "4111111 $11,111.11",
    )
    for preset in (LeakPolicy.payments(), LeakPolicy.general()):
        for text in card_splits:
            assert egress_text.check_text(text, policy=preset) is not None, (
                text,
                preset.max_digits,
            )
    with pytest.raises(ValueError):
        LeakPolicy(
            max_digits=30, max_total_digits=13
        )  # no policy may allow 13 digits across pieces
    assert egress_text.check_text("phone 0123456789 thanks", policy=LeakPolicy.general()) is None


def test_the_row_store_row_limit_is_validated():
    for bad in (0, -1, True, 1.5, "3", False):
        with pytest.raises(ValueError):
            RowStore(max_rows=bad)
    assert RowStore(max_rows=1)._max_rows == 1


def test_a_luhn_valid_card_across_pieces_is_found_and_dates_are_not_part_of_the_stream():
    card = "4111111111111111"
    assert egress_text._luhn_ok(card) and not egress_text._luhn_ok("4111111111111112")
    mark = egress_text._MARK
    assert (
        egress_text._card_run("pay 4111 1111 $11,111.11 ref 11") is True
    )  # 4111 1111 11111 111 11 -> stream holds the card
    assert (
        egress_text._card_run("4111 1111 " + mark + " 1111 1111") is False
    )  # split at a set-aside date
    assert egress_text._card_run("order 1234567 and 2026") is False  # fewer than 13 digits
    assert egress_text._card_run("x" + card[:7] + "-" + card[7:] + "y") is True
    assert egress_text.check_text(card, policy=LeakPolicy.general()) is not None


def test_weak_letters_glued_to_digits_count_but_a_prose_token_does_not():
    assert (
        egress_text._digitish_count("1b5i7g3q", 6) == 8
        and check_text("1b5i7g3q") == Violation.DIGIT_BUDGET
    )
    assert (
        check_text("this is big 12345") is None
        and egress_text._digitish_count("is big 12345", 6) == 5
    )
    assert check_text("OlISBZGq") == Violation.DIGIT_BUDGET
    # one digit and a weak letter in a token of 1 digit-like character: the weak letter is not counted beside digits
    assert egress_text._digitish_count("1b 2345678", 6) == 8


def test_a_stop_gate_over_a_limits_without_source_fails_at_construction():
    class OldLimits:
        audit = None

        def stop(self, by):
            pass

        def reset(self, by):
            pass

        def is_stopped(self):
            return False

    with pytest.raises(TypeError, match="limits.py"):
        StopGate(OldLimits())
    StopGate(FakeLimits())  # the real surface is fine


def test_a_busy_release_says_whether_the_stop_was_written_again_and_clears_the_cache():
    lim = FakeLimits()
    g = StopGate(lim, cache_ttl=1000.0)
    g.engage(list, lambda k: "x", by="u1")
    lim.during_reset = lambda: g.engage(list, lambda k: "x", by="u2")
    real_stop = lim.stop

    def stop_after_a_read(by, source="cli"):
        g.durable_on()  # a reader fills the cache with the old "off" just before the switch is written
        real_stop(by, source)

    lim.stop = stop_after_a_read
    with pytest.raises(StopGateBusy) as ei:
        g.release(by="u1")
    assert ei.value.durable is True and g._cached is None and g.blocked()
    lim2 = FakeLimits()
    g2 = StopGate(lim2)
    g2.engage(list, lambda k: "x", by="u1")

    def engage_then_break_the_store():
        g2.engage(list, lambda k: "x", by="u2")
        lim2.stop = lambda by, source="cli": (_ for _ in ()).throw(OSError("down"))

    lim2.during_reset = engage_then_break_the_store
    with pytest.raises(StopGateBusy) as ei2:
        g2.release(by="u1")
    assert (
        ei2.value.durable is False and g2.engaged
    )  # the switch may be off, the process stays engaged, and the error says so


def test_redact_leaves_an_existing_placeholder_on_a_non_ascii_line_alone():
    from hadavin_sdk.guard.redact import redact

    r = redact("mail alice@example.com and caf" + chr(0xE9))
    assert r.text == "mail <EMAIL_1> and caf" + chr(0xE9) and list(r.mapping) == ["<EMAIL_1>"]


# ---- review round 7 (code-7): splitting through filler, gluing, boundary constants -------------------------------------------------------
_STRONG_ONLY = ["I", "O", "l", "S", "Z", "B", "o", "s", "z", "Ol", "IS", "BZ", "lll", "OlS", "lllll", "Oslo", "Boss", "OlISBZGQ", "so"]
_FILLER = ["x", "y", "k", "m", "xx", "w", "kmw", "N", "H"]  # no digit-like letter
_SEPS = [" ", "  ", "-", ",", ".", ":", ";", "/", " - "]


def _split_case(rng):
    """A text with a real digit: tokens made only of strong letters, digits and filler, ready to be split through filler."""
    parts = ["4"]
    for _ in range(rng.randint(1, 14)):
        parts.append(rng.choice((*_STRONG_ONLY, *_STRONG_ONLY, "7", "12", *_FILLER)))
    return parts


def _joined(parts, rng):
    return "".join(p + (rng.choice(_SEPS) if i < len(parts) - 1 else "") for i, p in enumerate(parts))


def _splits_cases(count, rng, n_cases):
    """Yield (before, after) for n_cases: a filler token inserted between tokens, or a strong-only token cut in two with a separator or
    a filler token in the cut (the 'split through filler' edit)."""
    for _ in range(n_cases):
        parts = _split_case(rng)
        before = _joined(parts, rng)
        i = rng.randrange(len(parts))
        if rng.random() < 0.5 and len(parts[i]) >= 2 and all(c in "OolISsZzBGQ" for c in parts[i]):
            cut = rng.randint(1, len(parts[i]) - 1)
            parts2 = [*parts[:i], parts[i][:cut], rng.choice(_FILLER), parts[i][cut:], *parts[i + 1 :]]
        else:
            parts2 = [*parts[: i + 1], rng.choice(_FILLER), *parts[i + 1 :]]
        yield before, _joined(parts2, rng)


def _old_count():
    """The count of the previous round (a token of ONE strong letter and a sparse cluster never counted over the whole text): the control."""
    import inspect

    src = inspect.getsource(egress_text._digitish_count)
    new = "elif (ot == 0 and wk == 0) or (ot >= 1 and sg >= 4):"
    assert new in src
    ns = dict(vars(egress_text))
    exec(src.replace(new, "elif (ot == 0 and wk == 0 and n >= 2) or (ot >= 1 and sg >= 4 and 2 * sg > n):").replace("        word =", "        n = len(tok)\n        word ="), ns)  # noqa: S102 - a test-only control built from the module's own source
    return ns["_digitish_count"]


def test_splitting_a_letter_number_through_filler_never_lowers_the_count():
    import random

    rng = random.Random(20261103)  # noqa: S311 - a seeded test generator, not a secret
    count = egress_text._digitish_count
    cases = list(_splits_cases(count, rng, 20000))
    assert len(cases) == 20000
    bad = [(b, a) for b, a in cases if count(a, 6) < count(b, 6)]
    assert not bad, bad[:3]
    # sensitivity control: the same cases make the PREVIOUS rule drop (the generator has teeth), so this test fails on the old code
    old = _old_count()
    dropped = [(b, a) for b, a in cases if old(a, 6) < old(b, 6)]
    assert len(dropped) >= 100, len(dropped)


def test_one_letter_and_filler_split_card_numbers_are_refused():
    payments, general = LeakPolicy.payments(), LeakPolicy.general()
    for text in (
        "4 " + " x ".join(["I"] * 15),
        "4 " + " x ".join(["l"] * 15),
        "4 " + " ".join(["I", "x"] * 15),
        "4 OlSZBxxxxx OlSZBxxxxx OlSZBxxxxx",
        "4 OlSZBxxxxxx OlSZBxxxxxx OlSZBxxxxxx",
        "4 OlSZBy OlSZBy OlSZBy",
    ):
        assert egress_text.check_text(text, policy=payments) == Violation.DIGIT_BUDGET, text
        assert egress_text.check_text(text, policy=general) == Violation.DIGIT_BUDGET, text
    old = _old_count()
    assert old("4 " + " x ".join(["I"] * 15), 6) < 8 and old("4 OlSZBxxxxx OlSZBxxxxx OlSZBxxxxx", 6) < 8  # fail on the old rule


def test_gluing_a_letter_never_lowers_a_cluster_of_four_and_does_lower_a_short_word():
    import random

    rng = random.Random(7)  # noqa: S311 - a seeded test generator, not a secret
    count = egress_text._digitish_count
    big = [t for t in _STRONG_ONLY if sum(c in "OolISsZzBGQ" for c in t) >= 4]
    assert big, "the generator needs clusters of 4 or more strong letters"
    for _ in range(20000):
        parts = _split_case(rng)
        spots = [i for i, p in enumerate(parts) if p in big]
        if not spots:
            continue
        before = _joined(parts, rng)
        i = rng.choice(spots)
        parts[i] += rng.choice("xyk")
        after = _joined(parts, rng)
        assert count(after, 6) >= count(before, 6), (before, after)
    # the limit, stated: a glued letter turns a short strong-only token into a word, so it can lower the count (the same capability
    # as hiding digits inside ordinary-looking words, which is documented as NOT stopped)
    assert count("4 Ol Ol Ol Ol", 6) > count("4 Olx Olx Olx Olx", 6)


def test_the_false_refusals_on_prose_are_the_documented_ones():
    payments, general = LeakPolicy.payments(), LeakPolicy.general()
    for text in ("Boss 1234", "Oslo 1234", "Bill 1234"):
        assert egress_text.check_text(text, policy=payments) == Violation.DIGIT_BUDGET, text
        assert egress_text.check_text(text, policy=general) is None, text
    assert egress_text.check_text("Bill 12345678901", policy=general) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("BLISS GLOSS", policy=payments) == Violation.DIGIT_BUDGET
    assert egress_text.check_text("I paid 1234 for it", policy=payments) is None
    docs = (Path(__file__).resolve().parents[1] / "docs" / "promoted-controls.md").read_text(encoding="utf-8")
    for phrase in ("Boss 1234", "Oslo 1234", "Bill 1234", "BLISS GLOSS", "PIECES"):
        assert phrase in docs, phrase


def test_the_boundary_constants_of_the_whole_text_reading():
    count = egress_text._digitish_count
    assert count("4 I I I I I I I", 6) == 8  # a lone strong letter counts over the whole text (ot == 0 and wk == 0)
    assert count("4 xlll xlll", 6) == 1  # 3 strong letters with filler: a word, not counted (sg >= 4 not met)
    assert count("4 xllll xllll", 6) == 9  # 4 strong letters with filler count whatever the filler (sg >= 4)
    assert count("4 xlllllllllllxxxxxxxxxxxxxxx", 6) >= 12  # a sparse cluster counts (no majority rule)
    assert count("1b 7", 6) == 2  # one digit and a weak letter: the weak letter does not count (d + sg < 2)
    assert count("1b5i7g3q", 6) == 8  # a token with 2 or more digit-like characters: its weak letters count
    assert count("l 1 Zq call 4", 6, 2, 2) == 3  # a bare strong letter is not a free word: `call` keeps its free slot
    assert count("4 IbIb", 6) == 5  # the weak letters of a token with 2+ strong letters count


# last on purpose: a mutation of a pinned file must be judged by the test aimed at it, not by this hash pin
def test_the_manifest_pins_the_files_a_demo_copies():
    import hashlib

    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((FIX / "textnorm_manifest.json").read_text(encoding="utf-8"))
    for rel, sha in manifest["files"].items():
        data = (root / rel).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == sha, (
            rel,
            "changed: re-sync the demos and update the manifest and the CHANGELOG",
        )
    assert set(manifest["files"]) == {
        "src/hadavin_sdk/guard/textnorm.py",
        "src/hadavin_sdk/guard/_confusables.py",
        "src/hadavin_sdk/guard/egress_text.py",
        "src/hadavin_sdk/runtime/stop_gate.py",
        "tests/fixtures/textnorm_vectors.json",
    }
    log = root / "CHANGELOG.md"
    if log.exists():  # the mutation copies do not carry it
        text = log.read_text(encoding="utf-8")
        for rel, sha in manifest["files"].items():
            assert sha in text, rel  # the CHANGELOG re-copy list names every pinned hash
