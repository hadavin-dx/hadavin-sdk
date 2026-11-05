"""Named fault tests: FM-21 (stale snapshot) and FM-24 (timeout after apply). failure_modes.md names these tests; a meta-test checks it."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from intake import rules
from intake.adapters.fake_draftstore import FakeDraftStore
from intake.adapters.fake_erp import FakeErp, load_seed
from intake.adapters.port import FaultSchedule, PortFailureError, PortTimeoutError
from intake.tools import Money, draft_from_gold

ROOT = Path(__file__).resolve().parents[1]
POL = rules.load_policy()
SEED = load_seed(ROOT / "demo_only" / "data" / "seed.json")
CASES = [json.loads(line) for sp in ("dev", "test") for line in (ROOT / "demo_only" / "data" / f"{sp}.jsonl").read_text().splitlines()]
GOLD = next(c for c in CASES if c["case_id"] == "intake-e-001")


def _draft(po_suffix: str = "", qty_add: int = 0):
    g = json.loads(json.dumps(GOLD["expected"]["draft"]))
    g["po_number"] += po_suffix
    g["lines"][0]["qty_base"] += qty_add
    return draft_from_gold(g, (), "human", "0" * 64)


# --- FM-21 ---------------------------------------------------------------------------------------------------------------------
def test_stale_snapshot_boundary_and_fault_value():
    assert FakeErp(SEED, snapshot_age_minutes=1440).snapshot_age_minutes() == 1440 and not rules.snapshot_stale(1440, POL)
    assert rules.snapshot_stale(1441, POL)
    assert (
        FakeErp(SEED, faults=FaultSchedule(erp_stale_snapshot_minutes=2880)).snapshot_age_minutes() == 2880
    )  # one source (the case input); the schedule only overrides


def test_stale_snapshot_forces_four_eyes_even_without_credit_hold():
    assert rules.tier_for({"X24"}, Money("100", "USD"), POL) == "four_eyes"
    assert rules.tier_for({"X07", "X24"}, Money("100", "GBP"), POL) == "four_eyes"


def test_stale_snapshot_gold_cases_exist_for_orders_and_invoices():
    stale = [c for c in CASES if c["input"]["snapshot_age_minutes"] > 1440]
    edge = [c for c in CASES if c["input"]["snapshot_age_minutes"] == 1440]
    assert stale and all("X24" in c["expected"]["exceptions"] for c in stale)
    assert any(
        c["kind"] == "supplier_invoice" and c["expected"]["verdict"] == "flag" for c in stale
    )  # a clean-looking invoice may not be 'matched' on stale data
    assert any(c["input"]["snapshot_age_minutes"] == 1441 for c in stale)  # one minute over
    assert edge and all("X24" not in c["expected"]["exceptions"] for c in edge)


def test_erp_read_faults_are_deterministic_by_ordinal():
    erp = FakeErp(SEED, faults=FaultSchedule(erp_read_timeout_on=(2,), erp_read_5xx_on=(3,)))
    erp.as_of()
    with pytest.raises(PortTimeoutError):
        erp.get_stock("L100")
    with pytest.raises(PortFailureError):
        erp.get_stock("L100")
    assert erp.get_stock("L100") > 0


# --- FM-24 ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "fault,exc", [("draft_write_timeout_after_apply_on", PortTimeoutError), ("draft_write_5xx_after_apply_on", PortFailureError)]
)
def test_timeout_after_apply_then_retry_gives_exactly_one_draft(fault, exc):
    store = FakeDraftStore(FaultSchedule(**{fault: (1,)}))
    d = _draft()
    with pytest.raises(exc):
        store.put_draft(d.idempotency_key, d)  # the write landed, the caller cannot tell
    did = store.lookup("tenant-demo", d.idempotency_key)
    assert did is not None and store.count() == 1
    r = store.put_draft(d.idempotency_key, d)
    assert r.outcome == "duplicate_ignored" and r.draft_id == did and store.count() == 1


def test_timeout_after_apply_lookup_may_itself_time_out():
    store = FakeDraftStore(FaultSchedule(draft_write_timeout_after_apply_on=(1,), lookup_timeout_on=(1,)))
    d = _draft()
    with pytest.raises(PortTimeoutError):
        store.put_draft(d.idempotency_key, d)
    with pytest.raises(PortTimeoutError):
        store.lookup("tenant-demo", d.idempotency_key)
    assert store.lookup("tenant-demo", d.idempotency_key) is not None
    assert store.put_draft(d.idempotency_key, d).outcome == "duplicate_ignored" and store.count() == 1


def test_replay_2x_3x_and_concurrent_puts_apply_once():
    store = FakeDraftStore()
    d = _draft()
    assert [store.put_draft(d.idempotency_key, d).outcome for _ in range(3)] == ["applied", "duplicate_ignored", "duplicate_ignored"]
    store2, res = FakeDraftStore(), []
    ts = [threading.Thread(target=lambda: res.append(store2.put_draft(d.idempotency_key, d).outcome)) for _ in range(16)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert res.count("applied") == 1 and res.count("duplicate_ignored") == 15 and store2.count() == 1


def test_edited_resend_is_a_conflict_that_shows_both_payloads_and_never_a_second_draft():
    store = FakeDraftStore()
    a, b = _draft(), _draft(qty_add=5)
    assert a.idempotency_key == b.idempotency_key and a.content_digest != b.content_digest
    assert store.put_draft(a.idempotency_key, a).outcome == "applied"
    r = store.put_draft(b.idempotency_key, b)
    assert r.outcome == "conflict" and store.count() == 1
    assert r.conflict_with is a  # the approver sees the first draft next to the resend


def test_rejected_draft_can_be_redrafted_and_confirm_is_human_only():
    store = FakeDraftStore()
    d = _draft()
    did = store.put_draft(d.idempotency_key, d).draft_id
    store.reject(did, "order_clerk", "clerk-a")
    assert (
        store.put_draft(d.idempotency_key, d).outcome == "applied" and store.count() == 1
    )  # a new open version; the rejected one no longer blocks
    store.confirm(store.lookup("tenant-demo", d.idempotency_key), "order_clerk", "clerk-b")
    assert (
        store.list_open("tenant-demo", d.customer_id) == []
    )  # confirmed drafts are in the ERP's hands; duplicate detection then relies on the ERP orders


def test_recent_counters_are_computed_from_stored_timestamps_for_sender_domain_and_unverified():
    store = FakeDraftStore()
    for i in range(3):
        d = _draft(po_suffix=str(i))
        store.put_draft(d.idempotency_key, d, sender="a@flood.example.net")
    d = _draft(po_suffix="x")
    store.put_draft(d.idempotency_key, d, sender="b@flood.example.net")
    assert store.count_recent("tenant-demo", "a@flood.example.net", "flood.example.net") == (
        3,
        4,
        4,
    )  # rotating the local part still hits the domain counter
    store.advance(3601)
    assert store.count_recent("tenant-demo", "a@flood.example.net", "flood.example.net") == (0, 0, 0)  # 'this hour' really is a window


# --- meta ----------------------------------------------------------------------------------------------------------------------
FM_TESTS = {
    "FM-21": [
        "test_stale_snapshot_boundary_and_fault_value",
        "test_stale_snapshot_forces_four_eyes_even_without_credit_hold",
        "test_stale_snapshot_gold_cases_exist_for_orders_and_invoices",
    ],
    "FM-24": ["test_timeout_after_apply_then_retry_gives_exactly_one_draft", "test_timeout_after_apply_lookup_may_itself_time_out"],
}


def test_failure_modes_name_existing_fault_tests():
    doc = (ROOT / "failure_modes.md").read_text(encoding="utf-8")
    me = globals()
    for fm, names in FM_TESTS.items():
        for n in names:
            assert n in me and callable(me[n]), n
            assert f"tests/test_faults.py::{n}" in doc, (fm, n)
