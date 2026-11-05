"""no-lost-messages (no inbound message lost or double-applied) and tenant-isolation (tenants never affect one another), against the fakes. The in-memory ledger is NOT durable; the SQLite file backend is
(restart test below). load-profile load numbers are in config/policy.json."""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

import pytest

from data import gen
from intake.adapters.fake_draftstore import FakeDraftStore
from intake.adapters.fake_ledger import InboundLedger
from intake.adapters.port import FaultSchedule, OverloadedError, PortFailureError, PortTimeoutError
from intake.tools import business_id, draft_from_gold, idempotency_key

ROOT = Path(__file__).resolve().parents[1]
CASES = [json.loads(x) for x in (ROOT / "demo_only" / "data" / "dev.jsonl").read_text().splitlines()]
GOLD = next(c for c in CASES if c["case_id"] == "intake-e-001")["expected"]["draft"]
POLICY = json.loads((ROOT / "config" / "policy.json").read_text())


@pytest.fixture(params=["memory", "sqlite"])
def make_ledger(request, tmp_path):
    made = []

    def make(capacity=None, name="ledger.db"):
        lg = InboundLedger(":memory:" if request.param == "memory" else str(tmp_path / name), capacity=capacity)
        made.append(lg)
        return lg

    yield make
    for lg in made:
        lg.close()


def draft(tenant: str, po: str = "PO-48211", qty: int = 0, customer: str = "C001"):
    g = json.loads(json.dumps(GOLD))
    g["po_number"], g["customer_id"] = po, customer
    g["lines"][0]["qty_base"] += qty
    return draft_from_gold(g, (), "human", "0" * 64, tenant_id=tenant)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def put_with_retry(store: FakeDraftStore, d, tries: int = 3):
    """The pipeline's rule: on a timeout or 5xx the write may have landed; look the key up first, then re-put (idempotent). At most 2 retries."""
    for _ in range(tries):
        try:
            return store.put_draft(d.idempotency_key, d, sender="orders@x.example.com").outcome
        except (PortTimeoutError, PortFailureError):
            if store.lookup(d.tenant_id, d.idempotency_key) is not None:
                return "applied_before_error"
    return None  # still failing: the receipt stays unresolved and the recovery loop re-drives it


def process(ledger, store, tenant: str, mid: str, crash: bool = False, poison: bool = False):
    """One message: write-ahead receipt, effect, terminal state. `crash` dies after the effect and before the terminal state."""
    rec, is_new = ledger.record_receipt(tenant, mid, sha(mid), verified_sender="orders@x.example.com")
    if not is_new and ledger.state_of(tenant, mid) is not None:
        return "redelivered"
    if poison:
        ledger.set_terminal(rec.receipt_id, "dead_lettered", "unparseable")
        return "dlq"
    d = draft(tenant, po="PO-" + sha(mid)[:10])
    out = put_with_retry(store, d)
    if out is None:
        return "retry_later"
    if crash:
        raise RuntimeError("crash after the effect")
    ledger.set_terminal(rec.receipt_id, "processed", out)
    return out


@pytest.mark.parametrize("burst", [10, 100, 10000])
def test_burst_with_crashes_redelivery_and_poison_loses_and_duplicates_nothing(burst, make_ledger):
    rng = gen.Rng(burst)
    ledger, store = make_ledger(), FakeDraftStore()
    ids = [f"<m{i}@mail.example.com>" for i in range(burst)]
    poison = {i for i in ids if rng.random() < 0.02}
    crashed = set()
    for mid in ids:
        crash = mid not in poison and rng.random() < 0.05
        try:
            process(ledger, store, "t1", mid, crash=crash, poison=mid in poison)
        except RuntimeError:
            crashed.add(mid)
        if rng.random() < 0.3:  # the source redelivers
            process(ledger, store, "t1", mid)
    for rec in ledger.unresolved("t1"):  # recovery loop after the crashes: re-drive from the ledger; the store makes the effect idempotent
        assert rec.message_id in crashed
        process(ledger, store, "t1", rec.message_id)
    c = ledger.counts("t1")
    assert c["received"] == burst and c["unresolved"] == 0
    assert c["processed"] + c["dead_lettered"] + c["rejected"] + c["abstained"] == burst
    assert c["dead_lettered"] == len(poison)
    assert store.count("t1") == c["processed"]
    assert ledger.reconcile("t1", set(ids)) == {"missing": [], "unknown": [], "conflicts": []}


def test_threaded_burst_with_store_timeouts_5xx_crashes_redelivery_and_poison(make_ledger):
    faults = FaultSchedule(
        draft_write_timeout_after_apply_on=tuple(range(5, 6000, 11)), draft_write_5xx_after_apply_on=tuple(range(8, 6000, 17))
    )
    ledger, store = make_ledger(), FakeDraftStore(faults)
    n_threads, per = 8, 250
    ids = [[f"<t{t}m{i}@mail.example.com>" for i in range(per)] for t in range(n_threads)]
    errors = []

    def worker(t: int):
        r = gen.Rng(t + 1)
        try:
            for mid in ids[t]:
                try:
                    process(ledger, store, "t1", mid, crash=r.random() < 0.04, poison=r.random() < 0.02)
                except RuntimeError:
                    pass
                if r.random() < 0.3:
                    process(ledger, store, "t1", mid)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
    [x.start() for x in threads]
    [x.join() for x in threads]
    assert not errors, errors[:2]
    for _ in range(5):  # recovery loop until the ledger is clean (a write may need more than one pass under faults)
        todo = ledger.unresolved("t1")
        if not todo:
            break
        for rec in todo:
            process(ledger, store, "t1", rec.message_id)
    total = n_threads * per
    c = ledger.counts("t1")
    all_ids = {m for row in ids for m in row}
    assert c["received"] == total and c["unresolved"] == 0
    assert c["processed"] + c["dead_lettered"] == total
    assert store.count("t1") == c["processed"], "one stored draft per processed message, despite timeouts, 5xx, crashes and redelivery"
    assert ledger.reconcile("t1", all_ids) == {"missing": [], "unknown": [], "conflicts": []}


def test_backpressure_threaded_producers_retry_nothing_is_dropped(make_ledger):
    ledger = make_ledger(capacity=5)
    ids = [f"<bp{i}@mail.example.com>" for i in range(300)]
    pending = list(ids)
    lock, refused, accepted = threading.Lock(), [0], []

    def producer(chunk):
        for mid in chunk:
            while True:
                try:
                    rec, _ = ledger.record_receipt("t1", mid, sha(mid))
                    accepted.append(rec)
                    break
                except OverloadedError:
                    with lock:
                        refused[0] += 1

    def consumer(stop: threading.Event):
        while not stop.is_set() or ledger.unresolved("t1"):
            for rec in ledger.unresolved("t1"):
                try:
                    ledger.set_terminal(rec.receipt_id, "processed")
                except ValueError:
                    pass

    stop = threading.Event()
    cons = threading.Thread(target=consumer, args=(stop,))
    prods = [threading.Thread(target=producer, args=(pending[i::4],)) for i in range(4)]
    cons.start()
    [p.start() for p in prods]
    [p.join() for p in prods]
    stop.set()
    cons.join()
    assert refused[0] > 0, "the capacity path was never exercised"
    assert ledger.counts("t1")["received"] == len(ids) == len({r.message_id for r in accepted})
    assert ledger.counts("t1")["processed"] == len(ids) and ledger.reconcile("t1", set(ids))["missing"] == []


def test_message_id_poisoning_cannot_reject_the_legitimate_mail(make_ledger):
    ledger = make_ledger()
    legit, new1 = ledger.record_receipt("t1", "<abc@x>", sha("legit order"), verified_sender="orders@harborlane.example.com")
    evil, new2 = ledger.record_receipt("t1", "<abc@x>", sha("attacker mail"))
    assert new1 and new2 and legit.receipt_id != evil.receipt_id
    ledger.set_terminal(legit.receipt_id, "processed")  # the legitimate one still completes
    assert ledger.state_of("t1", "<abc@x>", sha("legit order")) == "processed"
    assert ledger.state_of("t1", "<abc@x>", sha("attacker mail")) == "dead_lettered"
    assert [k for k, _ in ledger.alerts("t1")] == ["message_id_conflict"]
    assert ledger.reconcile("t1", {"<abc@x>"})["conflicts"] == ["<abc@x>"]
    # attacker FIRST: the legitimate mail is dead-lettered with an alert for a person, never silently lost
    other = make_ledger(name="other.db")
    other.record_receipt("t1", "<abc@x>", sha("attacker mail"))
    legit2, _ = other.record_receipt("t1", "<abc@x>", sha("legit order"))
    assert other.state_of("t1", "<abc@x>", sha("legit order")) == "dead_lettered" and other.alerts("t1")


def test_different_content_redelivery_after_the_terminal_state_is_surfaced_not_ignored(make_ledger):
    ledger = make_ledger()
    rec, _ = ledger.record_receipt("t1", "m1", sha("v1"))
    ledger.set_terminal(rec.receipt_id, "processed")
    again, new = ledger.record_receipt("t1", "m1", sha("v2"))
    assert new and ledger.state_of("t1", "m1", sha("v2")) == "dead_lettered" and ledger.alerts("t1")
    same, new_same = ledger.record_receipt("t1", "m1", sha("v1"))
    assert same == rec and not new_same and ledger.deliveries("t1", "m1") == 2


def test_durable_backend_survives_a_restart_and_memory_backend_says_it_does_not(tmp_path):
    p = str(tmp_path / "ledger.db")
    a = InboundLedger(p)
    assert a.durable and not InboundLedger(":memory:").durable
    r1, _ = a.record_receipt("t1", "m1", sha("one"), verified_sender="orders@x.example.com")
    r2, _ = a.record_receipt("t1", "m2", sha("two"))
    a.set_terminal(r1.receipt_id, "processed")
    a.close()  # simulated crash/restart: only what reached the disk survives
    b = InboundLedger(p)
    assert [r.message_id for r in b.unresolved("t1")] == ["m2"]
    assert b.get(r1.receipt_id).verified_sender == "orders@x.example.com"
    assert b.state_of("t1", "m1") == "processed" and b.record_receipt("t1", "m1", sha("one"))[1] is False
    assert b.counts("t1")["received"] == 2
    b.close()


def test_reconciliation_finds_a_gap_the_source_knows_about(make_ledger):
    ledger = make_ledger()
    for m in ("a", "b", "c"):
        ledger.record_receipt("t1", m, "h")
    assert ledger.reconcile("t1", {"a", "b", "c", "d"}) == {"missing": ["d"], "unknown": [], "conflicts": []}
    assert ledger.reconcile("t1", {"a"}) == {"missing": [], "unknown": ["b", "c"], "conflicts": []}


def test_write_ahead_receipt_survives_a_crash_and_a_second_terminal_state_is_refused(make_ledger):
    ledger = make_ledger()
    rec, new = ledger.record_receipt("t1", "m1", "h")
    assert new and [r.message_id for r in ledger.unresolved("t1")] == ["m1"]
    again, new2 = ledger.record_receipt("t1", "m1", "h")
    assert again == rec and not new2 and ledger.deliveries("t1", "m1") == 2
    ledger.set_terminal(rec.receipt_id, "processed")
    ledger.set_terminal(rec.receipt_id, "processed")
    with pytest.raises(ValueError):
        ledger.set_terminal(rec.receipt_id, "abstained")
    fresh, _ = ledger.record_receipt("t1", "m-gone", "h")
    with pytest.raises(ValueError):
        ledger.set_terminal(fresh.receipt_id, "gone")


def test_overload_is_backpressure_not_a_drop(make_ledger):
    ledger = make_ledger(capacity=3)
    recs = [ledger.record_receipt("t1", f"m{i}", "h")[0] for i in range(3)]
    with pytest.raises(OverloadedError):
        ledger.record_receipt("t1", "m3", "h")
    assert ledger.reconcile("t1", {"m0", "m1", "m2", "m3"})["missing"] == ["m3"]
    ledger.set_terminal(recs[0].receipt_id, "processed")
    assert ledger.record_receipt("t1", "m3", "h")[1]


def test_poison_message_does_not_block_the_ones_behind_it(make_ledger):
    ledger, store = make_ledger(), FakeDraftStore()
    out = [process(ledger, store, "t1", m, poison=(m == "m1")) for m in ("m0", "m1", "m2")]
    assert out[1] == "dlq" and out[0] == out[2] == "applied" and ledger.counts("t1")["dead_lettered"] == 1


def test_timeout_after_apply_inside_the_pipeline_still_ends_with_one_effect(make_ledger):
    ledger = make_ledger()
    store = FakeDraftStore(FaultSchedule(draft_write_timeout_after_apply_on=(1,)))
    rec, _ = ledger.record_receipt("t1", "m1", "h")
    d = draft("t1")
    with pytest.raises(PortTimeoutError):
        store.put_draft(d.idempotency_key, d)
    assert store.lookup("t1", d.idempotency_key) is not None
    r = store.put_draft(d.idempotency_key, d)
    ledger.set_terminal(rec.receipt_id, "processed", r.outcome)
    assert r.outcome == "duplicate_ignored" and store.count("t1") == 1


# ---- tenant-isolation tenant isolation -------------------------------------------------------------------------------------------------------
def test_colliding_identifiers_across_tenants_stay_separate_and_canaries_never_cross(make_ledger):
    store, ledger = FakeDraftStore(), make_ledger()
    zw = chr(0x200B)
    tenants = ["acme", "acme" + zw, "ACME", "acme-", "acrne", "acme" + chr(0x2009)]
    rng = gen.Rng(9)
    for t in tenants:
        for _ in range(20):
            po = f"PO-{rng.between(1, 5)}"
            d = draft(t, po=po, qty=len(t))
            store.put_draft(d.idempotency_key, d, sender=f"orders@{t}.example.com")
            ledger.record_receipt(t, f"<m{rng.between(1, 4)}@mail.example.com>", "h-" + t)
    keys = {t: {idempotency_key("create_draft_order", business_id(t, "C001", f"PO-{n}")) for n in range(1, 6)} for t in tenants}
    assert len({k for ks in keys.values() for k in ks}) == 5 * len(tenants)
    for t in tenants:
        opens = store.list_open(t, "C001")
        assert opens and all(o.tenant_id == t for o in opens)
        assert {o.draft_id for o in opens}.isdisjoint({o.draft_id for u in tenants if u != t for o in store.list_open(u, "C001")})
        assert ledger.counts(t)["received"] <= 4
        for k in keys[t]:
            assert all(store.lookup(u, k) is None for u in tenants if u != t)


def test_business_id_cannot_collide_across_tenant_customer_pairs():
    assert business_id("t1|C", "X", "PO-1") != business_id("t1", "C|X", "PO-1")
    assert business_id("a", "bc", "PO-1") != business_id("ab", "c", "PO-1")
    assert business_id("t1", "C001", "PO-48211") == business_id("t1", "C001", "po 48211")


def test_canary_value_of_one_tenant_never_appears_in_another_tenants_reads_or_counters():
    store = FakeDraftStore()
    canary = "CANARY-7f3a91"
    a, b = draft("tenant-a", po="PO-1"), draft("tenant-b", po="PO-1")
    store.put_draft(a.idempotency_key, a, sender=f"{canary}@a.example.com")
    store.put_draft(b.idempotency_key, b, sender="x@b.example.com")
    assert a.idempotency_key != b.idempotency_key
    assert store.count_recent("tenant-b", f"{canary}@a.example.com", "a.example.com") == (0, 0, 1)
    assert canary not in repr(store.list_open("tenant-b", "C001")) and canary not in repr(
        store.list_processed_invoices("tenant-b", "S03", "PO-S-1")
    )
    assert store.count("tenant-a") == 1 == store.count("tenant-b")


def test_every_store_read_requires_a_tenant_id():
    import inspect

    from intake.adapters.port import AgentDraftPort

    for name in ("lookup", "list_open", "list_processed_invoices", "count_recent"):
        assert list(inspect.signature(getattr(AgentDraftPort, name)).parameters)[1] == "tenant_id", name


def test_hard_load_numbers_are_in_config_with_the_three_times_peak_rule():
    lp = POLICY["load_profile"]
    assert lp["test_messages_per_second"] == 3 * lp["peak_messages_per_second"]
    assert lp["spike_messages"] >= 10000 and lp["soak_hours"] >= 4 and lp["burst_sizes"] == [10, 100, 10000]
    assert lp["max_document_chars"] == POLICY["max_document_chars"]


def test_failure_modes_name_the_inbound_and_isolation_tests():
    doc = (ROOT / "failure_modes.md").read_text(encoding="utf-8")
    for n in (
        "test_burst_with_crashes_redelivery_and_poison_loses_and_duplicates_nothing",
        "test_colliding_identifiers_across_tenants_stay_separate_and_canaries_never_cross",
    ):
        assert n in globals() and f"tests/test_inbound_isolation.py::{n}" in doc
