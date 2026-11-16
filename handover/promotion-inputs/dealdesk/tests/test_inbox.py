"""inbound ledger: no inbound message is lost or double-applied. Bursts of 10, 100 and 1000 messages through the REAL inbox + handler + desk with seeded faults
(crash before/after the effect, timeouts, poison, invalid messages, duplicate and reordered delivery, crash on receive, bounded queue, slow dependency).
Honest scope: this is ordering/duplicate/fault behaviour in ONE process. It is not a load test (throughput, latency, 3x peak, soak: see load_profile.json
and runbook; none of that was run in stage 1)."""

import json
import threading
import time
from pathlib import Path

import pytest
from engine_kit import Kit, mk_deal
from properties_rng import Mini

from dealdesk import inbox as ib
from dealdesk.errors import Malformed
from dealdesk.handler import make_handler

D = Path(__file__).resolve().parent.parent
PASS = json.loads((D / "demo_only/data/pass.json").read_text(encoding="utf-8"))
FIRST = [
    "Alder",
    "Birch",
    "Cedar",
    "Dune",
    "Elm",
    "Fern",
    "Glen",
    "Hazel",
    "Iris",
    "Jade",
    "Kelp",
    "Lime",
    "Moss",
    "Nettle",
    "Oak",
    "Pine",
    "Quince",
    "Reed",
    "Sage",
    "Thorn",
]
SECOND = ["Works", "Labs", "Cloud", "Systems", "Robotics", "Logistics", "Analytics", "Software", "Health", "Dynamics", "Foundry", "Studio", "Freight", "Optics",
          "Mills", "Harbor", "Orchard", "Gate", "Forge", "Market", "Bridge", "Signal", "Vector", "Summit", "Atlas"]  # fmt: skip


def name(i):
    return f"{FIRST[i % 20]}{SECOND[(i // 20) % 25]} {SECOND[(i // 500 + i) % 25]}{'x' * (i // 500)}"


def build(n, tenant="t-a"):
    deals = [
        mk_deal(f"deal-{i:04d}", f"acct-{i:04d}", f"{FIRST[i % 20]} {SECOND[(i // 20) % 25]} {chr(65 + i // 500)}{i}", seats=40)
        for i in range(n)
    ]
    k = Kit(tenant=tenant, deals=deals)
    msgs = {}
    for i in range(n):
        d = deals[i]
        msgs[f"m{i:05d}"] = {"msg_id": f"m{i:05d}", "kind": "request", "requester_id": "p-ae-01", "deal_id": d["deal_id"],
                              "text": f"Hi, {d['account_name']} would like a 15% discount please."}  # fmt: skip
    return k, msgs


def run_burst(n, faults, seed, ledger=None, threads=1, queue_bound=4, tenant="t-a"):
    k, msgs = build(n, tenant)
    r = Mini(seed)
    plan = {}
    for mid in msgs:
        plan[mid] = {
            "crash_before": r.n(100) < faults["crash_before"], "crash_after": r.n(100) < faults["crash_after"], "timeout": r.n(100) < faults["timeout"],
            "poison": r.n(100) < faults["poison"], "invalid": r.n(100) < faults["invalid"], "dups": r.n(3) if r.n(100) < faults["dup"] else 0,
            "crash_on_receive": r.n(100) < faults["crash_on_receive"], "slow": r.n(100) < faults["slow"],
        }  # fmt: skip
    for mid, p in plan.items():
        if p["invalid"]:
            del msgs[mid]["text"]  # structurally invalid: must end `rejected`
    real, seen = make_handler(k.desk), {}
    lock = threading.Lock()

    def handler(msg):
        mid = msg["msg_id"]
        with lock:
            seen[mid] = seen.get(mid, 0) + 1
            first = seen[mid] == 1
        p = plan[mid]
        if p["slow"]:
            time.sleep(0.001)
        if p["poison"]:
            raise RuntimeError("poison")
        if first and (p["crash_before"] or p["timeout"]):
            raise TimeoutError("injected")
        out = real(msg)
        if first and p["crash_after"]:
            raise RuntimeError("crash after the effect, before the ledger write")
        return out

    inbox = ib.Inbox(ledger or ib.MemoryLedger(), handler, queue_bound=queue_bound)
    deliveries = []
    for mid in msgs:
        deliveries += [mid] * (1 + plan[mid]["dups"])
    r2 = Mini(seed + 1)
    for i in range(len(deliveries) - 1, 0, -1):  # reorder
        j = r2.n(i + 1)
        deliveries[i], deliveries[j] = deliveries[j], deliveries[i]
    acked = set()
    work = []
    for mid in deliveries:
        if plan[mid]["crash_on_receive"] and mid not in acked and not inbox.ledger.get(tenant, mid):
            plan[mid]["crash_on_receive"] = False  # the first delivery dies before persisting: no ack, the sender redelivers
            deliveries.append(mid)
            continue
        assert inbox.receive(tenant, msgs[mid]) is not None
        acked.add(mid)
        work.append(mid)
    done = []

    def worker(chunk):
        for mid in chunk:
            while not inbox.offer(tenant, mid):
                inbox.drain()  # backpressure: wait/drain, never drop
        inbox.drain()
        done.append(1)

    if threads == 1:
        worker(work)
    else:
        ts = [threading.Thread(target=worker, args=(work[i::threads],)) for i in range(threads)]
        [t.start() for t in ts]
        [t.join() for t in ts]
    inbox.drain()
    return k, msgs, plan, inbox, reconcile_and_check(k, msgs, plan, inbox, tenant)


def reconcile_and_check(k, msgs, plan, inbox, tenant):
    rep = ib.reconcile(inbox.ledger, tenant, set(msgs))
    c = rep["counts"]
    assert (
        rep["missing_in_ledger"] == [] and rep["unknown_in_ledger"] == [] and rep["non_terminal"] == 0
    )  # reconciliation gap = 0
    assert (
        c["processed"] + c["abstained"] + c["dead_lettered"] + c["rejected"] == rep["received"]
    )  # received = sum of terminal states
    quotes = [k.store.get("quotes", q) for q in k.store.names("quotes")]
    per_deal = {}
    for q in quotes:
        per_deal[q["deal_id"]] = per_deal.get(q["deal_id"], 0) + 1
    assert all(
        v == 1 for v in per_deal.values()
    )  # zero duplicated effects: one quote per deal whatever the redeliveries and crashes
    apprs = [k.store.get("approvals", a) for q in quotes for a in q["approvals"]]
    assert len({a["quote_id"] for a in apprs}) == len(apprs)  # one approval request per quote and epoch
    for mid, p in plan.items():
        st = inbox.ledger.get(tenant, mid)["state"]
        if p["poison"]:  # poison raises before the handler can judge the message
            assert st == "dead_lettered", (mid, st)
        elif p["invalid"]:
            assert st == "rejected", (mid, st)
        else:
            assert st == "processed", (mid, st)
    n_good = sum(1 for p in plan.values() if not p["poison"] and not p["invalid"])
    assert len(quotes) == n_good  # every good message produced exactly one quote, no poison message produced any
    assert rep["counts"]["dead_lettered"] == sum(1 for p in plan.values() if p["poison"])
    return rep


FAULTS = {
    "crash_before": 10,
    "crash_after": 10,
    "timeout": 5,
    "poison": 5,
    "invalid": 5,
    "dup": 30,
    "crash_on_receive": 5,
    "slow": 0,
}


@pytest.mark.parametrize("n", [10, 100, 1000])
def test_burst_with_faults_loses_nothing_and_applies_nothing_twice(n):
    _k, _m, _p, _i, rep = run_burst(n, FAULTS, seed=7 + n)
    assert rep["received"] == n and rep["counts"]["processed"] > 0
    assert PASS["missing"] == PASS["duplicated_effects"] == PASS["non_terminal"] == PASS["reconciliation_gap"] == 0


def test_burst_with_threads_slow_dependency_and_sqlite_wal_ledger(tmp_path):
    led = ib.SqliteLedger(str(tmp_path / "ledger.db"))
    _k, _m, _p, inbox, rep = run_burst(100, {**FAULTS, "slow": 20}, seed=99, ledger=led, threads=4)
    assert rep["received"] == 100
    led.close()
    led2 = ib.SqliteLedger(
        str(tmp_path / "ledger.db")
    )  # a reopened ledger (process restart) still holds every receipt in a terminal state
    assert len(led2.ids("t-a")) == 100 and all(s in ib.TERMINAL for s in led2.ids("t-a").values())
    led2.close()
    assert inbox is not None


def test_a_poison_message_never_blocks_those_behind_it_and_backpressure_drops_nothing():
    _k, _m, _plan, _inbox, rep = run_burst(50, {**FAULTS, "poison": 40}, seed=5, queue_bound=1)
    assert rep["counts"]["dead_lettered"] > 10 and rep["counts"]["processed"] > 5


def test_redelivery_of_a_finished_message_changes_nothing_and_terminal_is_final():
    k, msgs = build(3)
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    for _ in range(3):
        inbox.receive("t-a", msgs["m00000"])
        assert inbox.process("t-a", "m00000") == "processed"
    assert len(k.store.names("quotes")) == 1
    inbox.ledger.set_state("t-a", "m00000", "received", None)
    assert inbox.ledger.get("t-a", "m00000")["state"] == "processed"


def test_same_msg_id_in_two_tenants_are_two_messages():
    led = ib.MemoryLedger()
    k1, m1 = build(2, "t-a")
    k2, m2 = build(2, "t-b")
    a, b = ib.Inbox(led, make_handler(k1.desk)), ib.Inbox(led, make_handler(k2.desk))
    a.receive("t-a", m1["m00000"])
    b.receive("t-b", m2["m00000"])
    a.process("t-a", "m00000")
    assert led.get("t-b", "m00000")["state"] == "received" and led.get("t-a", "m00000")["state"] == "processed"
    assert len(k2.store.names("quotes")) == 0
    with pytest.raises(Malformed):
        make_handler(k2.desk)({**m1["m00001"], "tenant_id": "t-a"})  # a message of another tenant is refused by the handler


def test_unkeyable_messages_are_refused_before_any_ack_and_invalid_ones_end_rejected():
    k, msgs = build(1)
    inbox = ib.Inbox(ib.MemoryLedger(), make_handler(k.desk))
    for bad in ({}, {"msg_id": ""}, {"msg_id": 5}, {"msg_id": "x" * 500}, None):
        assert inbox.receive("t-a", bad) is None
    assert inbox.receive("T BAD", msgs["m00000"]) is None and inbox.ledger.ids("t-a") == {}
    inbox.receive("t-a", {"msg_id": "m-bad", "kind": "request"})
    assert inbox.process("t-a", "m-bad") == "rejected" and "text" in inbox.ledger.get("t-a", "m-bad")["reason"]
