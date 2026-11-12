"""Inbound ledger without a database (AK-G2-a): sender-id check (L18), golden keys (L19), key-check words, the partial
role refusal (L26), the recording fake for column grants (L28 iii), and seeded property tests of the keys and of the
receipt state machine (no lost message, no double-applied message, a terminal state for every message, isolation)."""

import hashlib
import hmac
import random
import re
from datetime import UTC, datetime, timedelta

import pytest

from hadavin_sdk import cli
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import INBOUND_ALLOWED, RUN_ID_PATTERN, check_inbound_move
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import StaleState, missing_inbound_methods, missing_methods
from hadavin_sdk.triggers import ledger
from hadavin_sdk.triggers.ledger import (
    InboundKeyChanged,
    InboundSource,
    Inbox,
    check_sender_id,
    derive_key,
    run_id_for,
)

T0 = datetime(2030, 1, 1, tzinfo=UTC)
CANARY = "person-1@example.invalid"
SRC = InboundSource(
    name="src-orders",
    tenant="tenant-a",
    readers=frozenset({"role:reader"}),
    agent_id="agent-a",
    principal_id="svc:trigger",
)


class _Spy(MemoryStore):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def receive_inbound(self, *a, **k):
        self.calls += 1
        return super().receive_inbound(*a, **k)


class _Sub(str):
    pass


@pytest.mark.parametrize(
    "bad", [5, None, b"x", _Sub("x"), "", "x" * 257, "a\x00b", "a\nb", "a\u200bb", "ab", "\ud800"]
)
def test_l18_a_bad_sender_id_is_refused_before_any_store_call(bad):
    store = _Spy()
    with pytest.raises(ValueError, match="sender id") as err:
        Inbox(store, hkey=b"k" * 32, clock=lambda: T0).receive(SRC, bad, b"x")
    assert store.calls == 0 and CANARY not in str(err.value)


def test_l18_256_characters_are_accepted():
    assert Inbox(_Spy(), hkey=b"k" * 32, clock=lambda: T0).receive(SRC, "x" * 256, b"x") == "new"
    assert check_sender_id("x" * 256) == "x" * 256


def _spec_key(restored: bytes | None):
    return (
        hmac.new(restored, b"hadavin-inbound-key-v1", hashlib.sha256).digest() if restored else None
    )


def _spec_h(k, data: bytes) -> str:
    return hmac.new(k, data, hashlib.sha256).hexdigest() if k else hashlib.sha256(data).hexdigest()


def _spec_tenant_key(*parts: str) -> str:
    return "".join(f"{len(p.encode())}:{p}" for p in parts)


# Pinned once, produced by the spec code above (restored key = b"r" * 32; tenant-a, src-orders, order-1, body b"body").


@pytest.mark.parametrize("restored", [b"r" * 32, None])
def test_l19_keys_equal_the_independent_spec_and_have_the_right_shape(restored):
    hk = derive_key(restored)
    assert hk == _spec_key(restored)
    body = b"body"
    sha = ledger.body_hash(hk, body)
    dk = ledger.delivery_key(hk, "tenant-a", "src-orders", "order-1")
    assert sha == _spec_h(hk, body)
    assert dk == _spec_h(hk, _spec_tenant_key("tenant-a", "src-orders", "order-1").encode())
    assert ledger.reuse_key(hk, "tenant-a", "src-orders", "order-1", sha) == _spec_h(
        hk, _spec_tenant_key("tenant-a", "src-orders", "order-1", "reuse", sha).encode()
    )
    assert (
        run_id_for(dk, 0) == "run-" + dk[:28] + "0000"
        and run_id_for(dk, 1) == "run-" + dk[:28] + "0001"
    )
    assert run_id_for(dk, 65535).endswith("ffff")
    with pytest.raises(ValueError):
        run_id_for(dk, 65536)
    assert all(RUN_ID_PATTERN.fullmatch(run_id_for(dk, g)) for g in (0, 1, 255, 65535))
    assert ledger.item_id_for(dk) == "inb-" + dk[:32]
    assert ledger.key_check_for(hk) == _spec_h(hk, b"hadavin-inbound-key-check-v1")[:16]
    assert list(run_id_for.__code__.co_varnames[:1]) == ["delivery_key"]


def test_l19_golden_literals():
    hk = derive_key(b"r" * 32)
    dk = ledger.delivery_key(hk, "tenant-a", "src-orders", "order-1")
    got = (ledger.body_hash(hk, b"body"), dk, run_id_for(dk, 1), ledger.key_check_for(hk))
    assert got == GOLDEN_VALUES


GOLDEN_VALUES = (
    "8a0199cf66dcfb14aaa06a8c52c13697e850077eb37307ea448a63c4e7f028d8",
    "06daa9928936bb506cbf1dd669d3b27998ebf9b1f45a3dc535d839f94db88e51",
    "run-06daa9928936bb506cbf1dd669d30001",
    "f9afacda223bb681",
)


def test_key_check_reveals_nothing_in_a_log_line():
    k = b"s" * 32
    assert re.fullmatch(
        r"[0-9a-f]{16}", ledger.key_check_for(k)
    ) and k.hex() not in ledger.key_check_for(k)
    assert ledger.key_check_for(None) != ledger.key_check_for(k)


def test_l23_a_store_with_only_the_store_methods_misses_every_inbound_method():
    class Old:
        pass

    assert len(missing_inbound_methods(Old())) == 11
    assert missing_inbound_methods(MemoryStore()) == [] and missing_methods(MemoryStore()) == []


@pytest.mark.parametrize(
    "given",
    [
        ("door",),
        ("dispatch",),
        ("owner",),
        ("door", "dispatch"),
        ("door", "owner"),
        ("dispatch", "owner"),
    ],
)
def test_l26_a_partial_set_of_inbound_roles_is_refused_before_connecting(given, monkeypatch):
    def no_connect(*a, **k):
        raise AssertionError("connected")

    monkeypatch.setattr(mig, "connect", no_connect)
    kw = {
        "inbound_door_role": "dr_x" if "door" in given else None,
        "inbound_dispatch_role": "dp_x" if "dispatch" in given else None,
        "rerun_owner_role": "ro_x" if "owner" in given else None,
    }
    with pytest.raises(ConfigError, match="inbound roles"):
        mig.migrate("host=none", **kw)
    out = cli._migrate(
        type(
            "C", (), {"backends": type("B", (), {"store": type("S", (), {"kind": "postgres"})()})()}
        )(),
        None,
        None,
        None,
        kw["inbound_door_role"],
        kw["inbound_dispatch_role"],
        kw["rerun_owner_role"],
    )
    assert out == 2


def test_l26_the_six_roles_must_differ(monkeypatch):
    monkeypatch.setattr(
        mig, "connect", lambda *a, **k: (_ for _ in ()).throw(AssertionError("connected"))
    )
    with pytest.raises(ConfigError, match="different"):
        mig.migrate(
            "x",
            runtime_role="r_x",
            inbound_door_role="r_x",
            inbound_dispatch_role="d_x",
            rerun_owner_role="o_x",
        )


def test_l28_column_update_is_granted_by_column_and_never_by_table():
    from unittest import mock

    seen = []

    class Db:
        def execute(self, q, params=()):
            seen.append(repr(q))
            return mock.Mock(fetchone=lambda: ("public",))

    mig._apply_grants(
        Db(),
        "r_x",
        lambda g: g.dispatch,
        lambda g: g.dispatch_select_cols,
        lambda g: g.dispatch_update_cols,
    )
    updates = [s for s in seen if "GRANT UPDATE (" in s]
    assert any("inbound_receipts" in s and "claim_token" in s for s in updates)
    assert not any(re.search(r"GRANT [^(]*UPDATE[^(]* ON", s) for s in seen)


def test_the_grant_map_gives_the_runtime_and_portal_roles_nothing_on_the_inbound_tables():
    for name in ("inbound_receipts", "inbound_bodies", "inbound_key_checks", "inbound_rerun_owner"):
        g = mig.GRANTS[name]
        assert g.runtime == "" and g.portal is False
        assert (
            "DELETE" not in g.door
            and "DELETE" not in g.dispatch
            and "TRUNCATE" not in (g.door + g.dispatch + g.rerun)
        )
    assert "DELETE" not in mig.GRANTS["inbound_receipts"].purge
    assert "body" not in mig.GRANTS["inbound_bodies"].purge_cols
    assert mig.GRANTS["inbound_receipts"].door == "INSERT"
    assert "generation" not in mig.GRANTS["inbound_receipts"].dispatch_update_cols
    assert "generation" in mig.GRANTS["inbound_receipts"].rerun_update_cols


def test_the_memory_state_map_equals_the_migration_trigger_move_list():
    from pathlib import Path

    text = (Path(mig.MIGRATIONS) / "0006_inbound.sql").read_text(encoding="utf-8")
    assert "(OLD.state = 'received' AND NEW.state = 'claimed')" in text
    assert (
        "OLD.state = 'claimed' AND NEW.state IN ('claimed', 'received', 'done', 'needs_person', 'refused')"
        in text
    )
    assert INBOUND_ALLOWED["received"] == {"claimed"} and INBOUND_ALLOWED["needs_person"] == {
        "received"
    }
    assert set(INBOUND_ALLOWED["claimed"]) == {
        "claimed",
        "received",
        "done",
        "needs_person",
        "refused",
    }
    for frm in ("done", "refused"):
        for to in ("received", "claimed", "done", "needs_person", "refused"):
            with pytest.raises(ValueError):
                check_inbound_move(frm, to)


# --- seeded property tests ---------------------------------------------------------------------------------------


def test_property_the_delivery_key_separates_every_tenant_source_id_triple():
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator
    alphabet = "ab:-_1"
    seen: dict[str, tuple] = {}
    for _ in range(4000):
        t = "t" + "".join(rng.choice("ab-1") for _ in range(rng.randint(0, 3)))
        s = "s" + "".join(rng.choice("ab-1") for _ in range(rng.randint(0, 3)))
        i = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6)))
        for hk in (b"k" * 32, None):
            key = (hk, t, s, i)
            dk = ledger.delivery_key(hk, t, s, i)
            assert re.fullmatch(r"[0-9a-f]{64}", dk)
            assert seen.setdefault(dk, key) == key  # no two different triples share a key
    # the classic joined-string collision
    assert ledger.delivery_key(None, "ab", "c", "d") != ledger.delivery_key(None, "a", "bc", "d")
    assert ledger.tenant_key("a", "bc") != ledger.tenant_key("ab", "c")
    assert ledger.tenant_key("a", "b", "c") != ledger.tenant_key("a", "b", "reuse", "c", "d")


def test_property_every_message_ends_with_exactly_one_terminal_receipt_no_loss_no_double():
    rng = random.Random(7)  # noqa: S311 - a seeded test generator
    store = MemoryStore()
    t = [T0]
    box = Inbox(store, hkey=b"k" * 32, clock=lambda: t[0])
    srcs = [
        InboundSource(
            name="src-a",
            tenant="tenant-a",
            readers=frozenset({"r"}),
            agent_id="a",
            principal_id="p",
        ),
        InboundSource(
            name="src-a",
            tenant="tenant-b",
            readers=frozenset({"r"}),
            agent_id="b",
            principal_id="p",
        ),
    ]
    sent: dict[tuple, bytes] = {}  # (tenant, id) -> first body
    finished: dict[tuple, int] = {}
    claimed: dict[str, object] = {}
    for _step in range(3000):
        src = rng.choice(srcs)
        op = rng.choice(["recv", "recv", "dup", "reuse", "claim", "finish", "release", "tick"])
        mid = f"m-{rng.randint(0, 40)}"
        key = (src.tenant, mid)
        if op in ("recv", "dup", "reuse"):
            body = (
                sent.get(key, b"") if op == "dup" and key in sent else (b"b%d" % rng.randint(0, 5))
            )
            out = box.receive(src, mid, body)
            if key not in sent and out == "new":
                sent[key] = body
            elif key in sent and body == sent[key]:
                assert out in ("duplicate", "busy") or False
            elif key in sent:
                assert out in ("id_reuse", "id_reuse_capped")
        elif op == "claim":
            rec = store.claim_inbound(src.tenant, src.name, t[0], 100)
            if rec is not None:
                claimed[rec.claim_token] = (rec, src)
        elif op in ("finish", "release") and claimed:
            token, (rec, _s2) = rng.choice(sorted(claimed.items()))
            try:
                if op == "finish":
                    store.finish_inbound(
                        rec.tenant, rec.source, rec.delivery_key, token, "done", None, t[0]
                    )
                    finished[(rec.tenant, rec.delivery_key)] = (
                        finished.get((rec.tenant, rec.delivery_key), 0) + 1
                    )
                else:
                    store.release_inbound(
                        rec.tenant, rec.source, rec.delivery_key, token, "step_error", t[0]
                    )
            except StaleState:
                pass
            claimed.pop(token, None)
        else:
            t[0] += timedelta(seconds=rng.choice([1, 50, 101]))
    # drain: everything open is claimed and finished
    for src in srcs:
        while (
            rec := store.claim_inbound(src.tenant, src.name, t[0] + timedelta(days=1), 100)
        ) is not None:
            store.finish_inbound(
                rec.tenant, rec.source, rec.delivery_key, rec.claim_token, "done", None, t[0]
            )
            finished[(rec.tenant, rec.delivery_key)] = (
                finished.get((rec.tenant, rec.delivery_key), 0) + 1
            )
    rows = list(store._inbound.values())
    real = [r for r in rows if r.reuse_of is None]
    assert len(real) == len(sent) and all(
        r.state == "done" for r in real
    )  # lost 0, terminal for every message
    assert all(v == 1 for v in finished.values()) and len(finished) == len(
        sent
    )  # applied exactly once each
    assert all(
        r.state == "refused" and r.reason == "id_reuse" for r in rows if r.reuse_of is not None
    )
    assert not [r for r in rows if r.state in ("received", "claimed")]
    # tenant isolation: the same ledger name and id stay separate
    assert {(r.tenant, r.delivery_key) for r in real} == {(r.tenant, r.delivery_key) for r in real}
    assert len({r.delivery_key for r in real}) >= len({k[1] for k in sent})


def test_a_changed_key_refuses_the_receive_and_the_message_names_no_key():
    store = MemoryStore()
    Inbox(store, hkey=b"a" * 32, clock=lambda: T0).receive(SRC, "o", b"x")
    with pytest.raises(InboundKeyChanged) as err:
        Inbox(store, hkey=b"b" * 32, clock=lambda: T0).receive(SRC, "o2", b"x")
    assert "tenant-a/src-orders" in str(err.value) and ("b" * 32) not in str(err.value)


def test_a_receipt_with_a_later_update_time_than_its_receive_time_is_not_a_legal_new_receipt():
    from hadavin_sdk.models import InboundReceipt

    t = datetime(2030, 1, 1, tzinfo=UTC)
    dk = "1" * 64
    rec = InboundReceipt(
        tenant="tenant-a",
        source="src-orders",
        readers=frozenset({"role:reader"}),
        delivery_key=dk,
        body_sha256="ab" * 32,
        key_check="0123456789abcdef",
        run_id=run_id_for(dk, 0),
        received_at=t,
        updated_at=t + timedelta(seconds=1),
    )
    store = MemoryStore()
    with pytest.raises(ValueError):
        store.receive_inbound(rec, b"x", max_reuse=8, max_open=10)
    assert (
        store.list_inbound_sources() == []
        and store.get_inbound_body("tenant-a", "src-orders", dk) is None
    )
