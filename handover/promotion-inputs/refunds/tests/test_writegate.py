"""The governed write path (src/refunds/writegate.py + store.py + approval.py): approvals, tenants, persistence, clock, kill switch, identities, caps."""

import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest
import wgkit as kit

from refunds import identities
from refunds.config import LIMITS
from refunds.store import Store
from refunds.writegate import WriteGate, hash_request

ROOT = Path(__file__).resolve().parents[1]


def run(req=None, people=kit.ONE, clock=None, **kw):
    store, svc, clock_, wg = kit.make(clock=clock)
    req = req or kit.request()
    ap = kit.sign(svc, req, people)
    return store, svc, clock_, wg, req, ap


# ------------------------------------------------------------------------------------------------ approvals (B2): every typed refusal
def test_a_valid_approval_applies_once_and_replays_are_duplicates():
    store, _, _, wg, req, ap = run()
    assert kit.ex(wg, req, ap, "executor", dry_run=False)["outcome"] == "applied"
    again = kit.ex(wg, req, ap, "executor", dry_run=False)
    assert again["outcome"] == "duplicate_ignored" and again["record"]["approval_id"] == ap["approval_id"]
    assert store.count_applied() == 1 and store.audit_chain_ok()


@pytest.mark.parametrize(
    "junk", [None, "", " ", "x", 5, [], {}, {"approval_id": "x"}, {"approval_id": "x", "mac": "y"}, ["ap-1"]]
)
def test_no_approval_object_means_no_money(junk):
    store, _, _, wg, req, _ = run()
    assert kit.ex_safe(wg, req, junk, "executor", dry_run=False) == {"outcome": "denied", "code": "NO_APPROVAL"}
    assert store.count_applied() == 0


def test_a_forged_or_edited_approval_is_refused():
    store, _svc, _, wg, req, ap = run()
    forged = {**ap, "mac": "0" * 64}
    assert kit.ex(wg, req, forged, "executor", dry_run=False)["code"] == "APPROVAL_INVALID"
    edited = {**ap, "tier": "four_eyes"}
    assert kit.ex(wg, req, edited, "executor", dry_run=False)["code"] == "APPROVAL_INVALID"
    other_key = kit.ApprovalIssuer(kit.DIRECTORY, key=b"z" * 32)  # an approval minted by someone without our key
    assert kit.ex(wg, req, kit.sign(other_key, req), "executor", dry_run=False)["code"] == "APPROVAL_INVALID"
    assert store.count_applied() == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"amount_minor": "2501"},
        {"currency": "GBP"},
        {"order_id": "ord-2"},
        {"line_ids": ["l2"]},
        {"action": "reship"},
        {"tenant_id": "t2"},
        {"customer_id": "c9", "cluster": ["c1", "c9"]},
        {"requested_at": "2026-10-20T11:00:00Z"},
        {"beneficiary": "someone.else@example.com"},
        {"cluster": ["c1", "c2"]},
        {"requester": "another-person"},
    ],
    ids=lambda c: "+".join(c),
)
def test_an_approval_covers_exactly_the_approved_action(changes):
    """Every field that any later check reads is inside the hash, including beneficiary, cluster and requester (review 7, M1)."""
    store, _svc, _, wg, req, ap = run()
    if (
        "amount_minor" in changes
    ):  # the signed basis["request"] must equal the amount (else KEY_INVALID), so move both: the hash must still notice
        changes = {**changes, "basis": {**req["basis"], "request": changes["amount_minor"]}}
    assert kit.ex(wg, {**req, **changes}, ap, "executor", dry_run=False)["code"] == "ARGS_HASH_MISMATCH", changes
    assert store.count_applied() == 0


def test_the_cluster_order_does_not_matter_but_its_content_does():
    store, svc, _clock, wg = kit.make()
    req = kit.request(cluster=["c2", "c1"])
    ap = kit.sign(svc, req)
    assert kit.ex(wg, {**req, "cluster": ["c1", "c2"]}, ap, "executor", dry_run=False)["outcome"] == "applied"
    assert store.count_applied() == 1


def test_the_tier_and_basis_are_inside_the_hash_and_a_request_cannot_downgrade_them():
    _store, _svc, _, wg, req, ap = run()
    assert kit.ex(wg, {**req, "tier": "four_eyes"}, ap, "executor", dry_run=False)["code"] == "ARGS_HASH_MISMATCH"
    assert (
        kit.ex(wg, {**req, "basis": {**req["basis"], "captured_minor": "9999999"}}, ap, "executor", dry_run=False)["code"]
        == "ARGS_HASH_MISMATCH"
    )
    assert kit.ex(wg, {**req, "requester": "someone"}, ap, "executor", dry_run=False)["code"] == "ARGS_HASH_MISMATCH"


def test_expiry_uses_the_server_clock_and_the_boundary_is_exact():
    clock = kit.Clock()
    _store, _svc, _, wg, req, ap = run(clock=clock)
    clock.now = "2026-10-21T12:00:00Z"  # exactly 24 h: still valid
    assert kit.ex(wg, req, ap, "executor", dry_run=True)["outcome"] == "dry_run"
    clock.now = "2026-10-21T12:00:01Z"
    assert kit.ex(wg, req, ap, "executor", dry_run=True)["code"] == "EXPIRED"
    _store2, _svc2, _clock2, wg2, req2, ap2 = run(req=kit.request(requested_at="2026-10-20T13:00:00Z"))
    assert kit.ex(wg2, req2, ap2, "executor", dry_run=True)["code"] == "EXPIRED", "an approval from the future is not valid"


def test_the_amount_decides_the_lowest_tier_and_the_signed_tier_cannot_be_lower():
    big = str(LIMITS["USD"].one_approver_max + 1)
    req = kit.request(
        tier="human",
        amount_minor=big,
        basis={
            "captured_minor": "60000",
            "prior_order_minor": "0",
            "prior_customer_30d_minor": "0",
            "prior_refunded_minor": "0",
            "tier_floor": "",
            "request": big,
        },
    )
    store, svc, _, wg, _, _ = run(req=req)
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", dry_run=False)["code"] == "ROLE_NOT_IN_MATRIX"
    req4 = {**req, "tier": "four_eyes"}
    assert kit.ex(wg, req4, kit.sign(svc, req4, kit.ONE), "executor", dry_run=False)["code"] == "ROLE_NOT_IN_MATRIX", (
        "one signature on a four-eyes tier"
    )
    assert kit.ex(wg, req4, kit.sign(svc, req4, kit.TWO), "executor", dry_run=False)["outcome"] == "applied"
    assert store.count_applied() == 1


@pytest.mark.parametrize(
    "people,code",
    [
        ([("staff@desk.example", "janitor")], "ROLE_NOT_IN_MATRIX"),
        ([("nobody@desk.example", "support_lead")], "APPROVER_UNKNOWN"),
        ([("lead@desk.example", "finance_approver")], "APPROVER_UNKNOWN"),
        ([("agent-run", "support_lead")], "REQUESTER_IS_APPROVER"),
        ([("pat@example.com", "support_lead")], "APPROVER_IS_BENEFICIARY"),
        ([], "ROLE_NOT_IN_MATRIX"),
    ],
)
def test_one_approver_tier_refusals(people, code):
    store, svc, _, wg, req, _ = run()
    assert kit.ex(wg, req, kit.sign(svc, req, people), "executor", dry_run=False)["code"] == code
    assert store.count_applied() == 0


@pytest.mark.parametrize(
    "people,code",
    [
        ([("finance@desk.example", "finance_approver"), ("lead@desk.example", "support_lead")], "STEP_ORDER"),
        ([("both@desk.example", "support_lead"), ("both@desk.example", "finance_approver")], "SAME_PERSON"),
        ([("agent-run", "support_lead"), ("finance@desk.example", "finance_approver")], "REQUESTER_IS_APPROVER"),
        ([("lead@desk.example", "support_lead"), ("pat@example.com", "support_lead")], "STEP_ORDER"),
        ([("lead@desk.example", "support_lead")], "ROLE_NOT_IN_MATRIX"),
    ],
)
def test_four_eyes_refusals(people, code):
    req = kit.request(
        tier="four_eyes",
        amount_minor="9000",
        basis={
            "captured_minor": "60000",
            "prior_order_minor": "0",
            "prior_customer_30d_minor": "0",
            "prior_refunded_minor": "0",
            "tier_floor": "",
            "request": "9000",
        },
    )
    store, svc, _, wg, _, _ = run(req=req)
    assert kit.ex(wg, req, kit.sign(svc, req, people), "executor", dry_run=False)["code"] == code
    assert store.count_applied() == 0


def test_the_approver_of_four_eyes_step_two_cannot_be_the_beneficiary():
    req = kit.request(
        tier="four_eyes",
        amount_minor="9000",
        basis={
            "captured_minor": "60000",
            "prior_order_minor": "0",
            "prior_customer_30d_minor": "0",
            "prior_refunded_minor": "0",
            "tier_floor": "",
            "request": "9000",
        },
    )
    _store, svc, _, wg, _, _ = run(req=req)
    svc.directory["pat@example.com"] = frozenset({"support_lead", "finance_approver"})
    ap = kit.sign(svc, req, [("lead@desk.example", "support_lead"), ("pat@example.com", "finance_approver")])
    assert kit.ex(wg, req, ap, "executor", dry_run=False)["code"] == "APPROVER_IS_BENEFICIARY"


def test_one_approval_cannot_pay_under_two_keys():
    store, _svc, _, wg, req, ap = run()
    # a hash binds the key, so a second request cannot reuse the approval...
    req2 = {**req, "order_id": "ord-2", "line_ids": ["l2"]}
    assert kit.ex(wg, req2, ap, "executor", dry_run=False)["code"] == "ARGS_HASH_MISMATCH"
    # ...and if an approval id was already consumed for another key (state recovered from an older store), it still refuses
    kit.consume(store, "t1", ap["approval_id"], "f" * 64)
    assert kit.ex_safe(wg, req, ap, "executor", dry_run=False)["code"] == "APPROVAL_USED"
    assert store.count_applied() == 0


def test_dry_run_is_the_default_and_anything_but_false_is_a_dry_run():
    store, _, _, wg, req, ap = run()
    assert kit.ex(wg, req, ap, "executor")["outcome"] == "dry_run"
    for not_false in (0, None, "False", [], 1):
        assert kit.ex(wg, req, ap, "executor", not_false)["outcome"] == "dry_run", not_false
    assert store.count_applied() == 0 and store.reservations("t1") == [] and store.approval_key("t1", ap["approval_id"]) is None
    assert kit.ex(wg, req, ap, "executor", False)["outcome"] == "applied"


def test_key_reuse_with_other_parameters_is_a_conflict_on_every_leg():
    _store, _, _, _wg, req, _ap = run()
    key = kit.key_of(req)
    base = {"tenant": "t1", "key": key, "action": "refund", "order_id": "ord-1", "line_ids": ["l1"], "amount_minor": 2500, "currency": "USD",
            "customer_id": "c1", "approval_id": "ap-x", "applied_at": kit.START, "day": "2026-10-20"}  # fmt: skip
    for leg, value in (
        ("action", "reship"),
        ("order_id", "ord-2"),
        ("line_ids", ["l9"]),
        ("amount_minor", 2501),
        ("currency", "GBP"),
    ):
        s2, svc2, _, wg2, _, _ = run()
        s2.insert_applied({**base, leg: value})  # a hash collision, simulated: same key, other parameters
        assert kit.ex(wg2, req, kit.sign(svc2, req), "executor", dry_run=False) == {"outcome": "denied", "code": "KEY_REUSED"}, (
            leg
        )
    s3, svc3, _, wg3, _, _ = run()
    s3.insert_applied(base)
    assert kit.ex(wg3, req, kit.sign(svc3, req), "executor", dry_run=False)["outcome"] == "duplicate_ignored"


# ------------------------------------------------------------------------------------------------ tenants (M1)
def test_two_tenants_with_the_same_order_and_lines_each_get_their_own_payment_and_never_the_others_record():
    store, svc, _, wg, _, _ = run()
    r1, r2 = kit.request(tenant_id="t1"), kit.request(tenant_id="t2", customer_id="c1")
    a1, a2 = kit.sign(svc, r1), kit.sign(svc, r2)
    assert kit.key_of(r1) != kit.key_of(r2)
    o1, o2 = kit.ex(wg, r1, a1, "executor", False), kit.ex(wg, r2, a2, "executor", False)
    assert o1["outcome"] == o2["outcome"] == "applied"
    assert o1["record"]["approval_id"] == a1["approval_id"] and o2["record"]["approval_id"] == a2["approval_id"]
    assert o1["record"]["tenant"] == "t1" and o2["record"]["tenant"] == "t2"
    fresh1 = kit.request(tenant_id="t1", order_id="ord-9", line_ids=["l9"])
    fresh2 = kit.request(tenant_id="t2", order_id="ord-9", line_ids=["l9"])
    assert kit.ex(wg, fresh2, kit.sign(svc, fresh1), "executor", False)["code"] == "ARGS_HASH_MISMATCH", (
        "tenant 1's approval cannot pay tenant 2's request"
    )
    assert kit.ex(wg, fresh1, kit.sign(svc, fresh2), "executor", False)["code"] == "ARGS_HASH_MISMATCH"
    assert kit.ex(wg, r1, a2, "executor", False)["record"]["approval_id"] == a1["approval_id"], (
        "a replay answers with the tenant's own record"
    )
    assert store.count_applied("t1") == store.count_applied("t2") == 1


def test_every_write_and_read_path_of_the_store_is_tenant_scoped():
    store, svc, _, wg, _, _ = run()
    kit.raw_reserve(store, "t1", "k" * 64, "c1", "ord-1", 700, "USD", kit.START)
    assert (
        store.reservations("t2") == []
        and store.other_reserved("t2", "USD", "x", "2000-01-01T00:00:00Z") == 0
        and store.other_reserved("t1", "USD", "x", "2000-01-01T00:00:00Z") == 700
    )
    store.release("t2", "k" * 64)
    assert len(store.reservations("t1")) == 1, "t2 cannot release t1's reservation"
    kit.raw_reserve(store, "t2", "k" * 64, "c1", "ord-1", 5, "USD", kit.START)
    assert [r["amount_minor"] for r in store.reservations("t1")] == [700] and [
        r["amount_minor"] for r in store.reservations("t2")
    ] == [5]
    req = kit.request()
    kit.ex(wg, req, kit.sign(svc, req), "executor", False)
    key = kit.key_of(req)
    assert (
        store.get_applied("t2", key) is None
        and store.order_rows("t2", "ord-1") == []
        and store.sum_order("t2", "ord-1", "USD") == 0
    )
    assert (
        store.sum_day("t2", "USD", "2026-10-20") == 0
        and store.sum_customers_since("t2", ["c1"], "USD", "2000-01-01T00:00:00Z") == 0
    )
    assert store.approval_key("t2", "anything") is None and store.compensation_records("t2") == []
    assert len(store.compensation_records("t1")) == 1


def test_tenant_ids_must_be_well_formed_and_a_tenant_is_never_defaulted():
    _, _svc, _, wg, req, ap = run()
    for bad in (None, "", "T1", "t 1", "t|1", 5, ["t1"], {"a": 1}):
        r = {**req, "tenant_id": bad}
        assert kit.ex(wg, r, ap, "executor", False) == {"outcome": "denied", "code": "KEY_INVALID"}, bad
    del req["tenant_id"]
    assert kit.ex(wg, req, ap, "executor", False)["code"] == "KEY_INVALID"


def test_concurrent_interleaved_tenants_never_see_each_others_records():
    store, svc, _, wg, _, _ = run()
    reqs = {t: kit.request(tenant_id=t) for t in ("t1", "t2", "t3")}
    aps = {t: kit.sign(svc, r) for t, r in reqs.items()}
    seen: list[tuple[str, dict]] = []
    lock = threading.Lock()

    def worker(i):
        t = ("t1", "t2", "t3")[i % 3]
        out = kit.ex(wg, reqs[t], aps[t], "executor", False)
        with lock:
            seen.append((t, out))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(60)]
    [x.start() for x in threads]
    [x.join() for x in threads]
    for t, out in seen:
        assert out["record"]["tenant"] == t and out["record"]["approval_id"] == aps[t]["approval_id"], (t, out)
    assert [o["outcome"] for _, o in seen].count("applied") == 3
    assert {t: store.count_applied(t) for t in reqs} == {"t1": 1, "t2": 1, "t3": 1}


# ------------------------------------------------------------------------------------------------ persistence (M1)
def test_a_restart_keeps_the_idempotency_map_the_caps_the_approval_and_the_kill_switch(tmp_path):
    db = str(tmp_path / "desk.sqlite")
    store, svc, clock, wg = kit.make(db)
    req = kit.request()
    ap = kit.sign(svc, req)
    assert kit.ex(wg, req, ap, "executor", False)["outcome"] == "applied"
    assert wg.set_kill_switch("kill_switch_operator", True, "drill")["outcome"] == "ok"
    store.close()
    store2 = Store(db)  # a new process / a second instance
    wg2 = WriteGate(store2, svc.verifier(), clock)
    assert kit.ex(wg2, req, ap, "executor", False)["outcome"] == "duplicate_ignored"
    assert store2.kill_switch() == {"on": True, "operator": "kill_switch_operator", "reason": "drill", "at": kit.START}
    req2 = kit.request(order_id="ord-2", line_ids=["l2"])
    assert kit.ex(wg2, req2, kit.sign(svc, req2), "executor", False)["code"] == "KILL_SWITCH"
    assert store2.count_applied() == 1 and store2.audit_chain_ok()


CHILD = r"""
import json, sys
sys.path[:0] = [sys.argv[1] + "/src", sys.argv[1] + "/tests"]
import wgkit as kit
from refunds.store import Store
from refunds.writegate import WriteGate, hash_request
db, work = sys.argv[2], json.load(open(sys.argv[3]))
svc = kit.ApprovalIssuer(kit.DIRECTORY, key=b"k" * 32)
wg = WriteGate(Store(db), svc.verifier(), kit.Clock())
for i, (req, ap) in enumerate(work):
    print(i, kit.ex(wg, req, ap, "executor", False)["outcome"], flush=True)
while True:  # keep replaying so the kill lands mid-burst
    for req, ap in work:
        kit.ex(wg, req, ap, "executor", False)
"""


def test_kill_mid_burst_restart_replay_leaves_exactly_one_applied_per_request(tmp_path):
    db, work_file, child = str(tmp_path / "burst.sqlite"), tmp_path / "work.json", tmp_path / "child.py"
    store, svc, _clock, _wg = kit.make(db)
    reqs = kit.burst(25)
    for r in reqs:
        kit.raw_reserve(
            store,
            r["tenant_id"],
            kit.key_of(r),
            r["customer_id"],
            r["order_id"],
            int(r["amount_minor"]),
            r["currency"],
            kit.START,
        )
    work = [(r, kit.sign(svc, r)) for r in reqs]
    work_file.write_text(json.dumps(work), encoding="utf-8")
    child.write_text(CHILD, encoding="utf-8")
    store.close()
    p = subprocess.Popen([sys.executable, str(child), str(ROOT), db, str(work_file)], stdout=subprocess.PIPE, text=True)
    for done, _line in enumerate(p.stdout, start=1):
        if done >= 8:
            break
    p.kill()  # no clean shutdown
    p.wait()
    store2 = Store(db)
    wg2 = WriteGate(store2, svc.verifier(), kit.Clock())
    outcomes = [kit.ex(wg2, r, a, "executor", False)["outcome"] for r, a in work]
    assert set(outcomes) <= {"applied", "duplicate_ignored"} and outcomes.count("duplicate_ignored") >= 8
    assert store2.count_applied() == 25, "every request applied exactly once across the crash"
    assert [kit.ex(wg2, r, a, "executor", False)["outcome"] for r, a in work] == ["duplicate_ignored"] * 25
    assert store2.reservations("t1") == [] and store2.audit_chain_ok()
    n = store2._db.execute("SELECT COUNT(*) FROM applied").fetchone()[0]
    assert n == 25


# ------------------------------------------------------------------------------------------------ clock (M4/M5)
@pytest.mark.parametrize(
    "bad",
    [
        None,
        5,
        "",
        "not-a-date",
        "9999-99-99",
        "2026-10-20T12:00:00",
        "0001-01-01T00:00:00+05:00",
        [],
        ("a",),
        "2026-13-01T00:00:00Z",
    ],
)
def test_a_garbage_clock_is_a_typed_deny_never_an_exception_and_never_a_fresh_bucket(bad):
    store, _, clock, wg, req, ap = run()
    clock.now = bad
    assert kit.ex_safe(wg, req, ap, "executor", False) == {"outcome": "denied", "code": "CLOCK_INVALID"}
    assert store.count_applied() == 0


def test_a_raising_clock_is_a_typed_deny():
    store, svc, _, _, req, ap = run()

    def boom():
        raise RuntimeError("clock failure")

    assert WriteGate(store, svc.verifier(), boom).execute(req, ap, "executor", False)["code"] == "CLOCK_INVALID"


def test_the_clock_never_goes_backwards_so_an_old_day_bucket_cannot_be_reopened():
    store, svc, clock, wg = kit.make()
    clock.now = "2026-10-21T00:00:30Z"
    r = kit.request(requested_at="2026-10-21T00:00:30Z")
    assert kit.ex(wg, r, kit.sign(svc, r), "executor", False)["outcome"] == "applied"
    for earlier in (
        "2026-10-20T23:59:59Z",
        "2026-10-19T12:00:00Z",
    ):  # 10-19 has an EMPTY day bucket: a fresh cap if the clock were believed
        clock.now = earlier
        r2 = kit.request(order_id="ord-2", line_ids=["l2"], amount_minor="1000", requested_at=earlier)
        assert kit.ex(wg, r2, kit.sign(svc, r2), "executor", False) == {"outcome": "denied", "code": "CLOCK_BACKWARDS"}, earlier
    assert store.count_applied() == 1 and store.sum_day("t1", "USD", "2026-10-19") == 0


def test_the_day_bucket_is_the_utc_date_whatever_offset_the_clock_string_carries():
    store, svc, clock, wg, _req, _ap = run()
    clock.now = "2026-10-20T20:00:00-05:00"  # = 2026-10-21 01:00 UTC
    r = kit.request(requested_at="2026-10-21T01:00:00Z")
    assert kit.ex(wg, r, kit.sign(svc, r), "executor", False)["record"]["day"] == "2026-10-21"
    assert store.sum_day("t1", "USD", "2026-10-21") == 2500 and store.sum_day("t1", "USD", "2026-10-20") == 0


# ------------------------------------------------------------------------------------------------ garbage in, typed deny out
@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: {**r, "action": ["refund"]},
        lambda r: {**r, "action": {"a": 1}},
        lambda r: {**r, "action": None},
        lambda r: {**r, "action": "bulk_delete"},
        lambda r: {**r, "order_id": ["ord-1"]},
        lambda r: {**r, "order_id": "ORD 1"},
        lambda r: {**r, "line_ids": "l1"},
        lambda r: {**r, "line_ids": [["l1"]]},
        lambda r: {**r, "line_ids": []},
        lambda r: {**r, "amount_minor": 2500},
        lambda r: {**r, "amount_minor": True},
        lambda r: {**r, "amount_minor": "0"},
        lambda r: {**r, "amount_minor": "-5"},
        lambda r: {**r, "amount_minor": "2500.0"},
        lambda r: {**r, "currency": "JPY"},
        lambda r: {**r, "currency": ["USD"]},
        lambda r: {**r, "cluster": "c1"},
        lambda r: {**r, "cluster": [1]},
        lambda r: {**r, "basis": "x"},
        lambda r: {**r, "basis": {"a": float("nan")}},
        lambda r: {**r, "basis": {"a": object()}},
        lambda r: {**r, "customer_id": 5},
        lambda r: {**r, "requested_at": 5},
        lambda r: {**r, "tier": None},
        lambda r: {k: v for k, v in r.items() if k != "basis"},
        lambda r: "not a dict",
        lambda r: None,
        lambda r: [],
    ],
)
def test_garbage_requests_are_typed_denies_never_exceptions_and_never_money(mutation):
    store, _, _, wg, req, ap = run()
    out = kit.ex_safe(wg, mutation(req), ap, "executor", False)
    assert out["outcome"] == "denied" and isinstance(out["code"], str)
    assert store.count_applied() == 0


@pytest.mark.parametrize("who", [None, 5, ["executor"], "", "nobody", "EXECUTOR"])
def test_garbage_identities_are_denied(who):
    store, _, _, wg, req, ap = run()
    assert kit.ex_safe(wg, req, ap, who, False) == {"outcome": "denied", "code": "IDENTITY_DENIED"}
    assert store.count_applied() == 0


# ------------------------------------------------------------------------------------------------ identities enforced at runtime (B3)
@pytest.mark.parametrize("identity", sorted(identities.IDENTITIES))
def test_each_identity_can_do_only_what_the_table_says_at_runtime(identity):
    expected = {
        "execute": identity == "executor",
        "kill_switch": identity == "kill_switch_operator",
        "approve": identity == "approver_human",
    }
    store, svc, _, wg, req, _ = run()
    ap = kit.sign(svc, req)
    out = kit.ex(wg, req, ap, identity, False)
    assert (out["outcome"] == "applied") == expected["execute"], (identity, out)
    if not expected["execute"]:
        assert out["code"] == "IDENTITY_DENIED"
        assert store.count_applied() == 0
    ks = wg.set_kill_switch(identity, False, "check")
    assert (ks["outcome"] == "ok") == expected["kill_switch"], identity
    try:
        kit.sign(svc, kit.request(order_id="ord-9"), identity=identity)
        signed = True
    except Exception as e:  # noqa: BLE001
        signed = False
        assert getattr(e, "code", "") == "IDENTITY_DENIED"
    assert signed == expected["approve"], identity


def test_the_executor_may_run_all_four_money_actions_and_nothing_else_can_run_any():
    for action, ident_action in (
        ("refund", "payments.refund"),
        ("goodwill", "payments.credit"),
        ("cancel", "orders.cancel"),
        ("reship", "orders.reship"),
    ):
        holders = {i for i in identities.IDENTITIES if identities.authorize(i, ident_action)}
        assert holders == {"executor"}, (action, holders)


# ------------------------------------------------------------------------------------------------ kill switch drill (M3)
def test_kill_switch_drill_flip_mid_burst_zero_applies_while_on_clean_resume_afterwards():
    store, svc, _clock, wg = kit.make()
    reqs = kit.burst(30)
    work = [(r, kit.sign(svc, r)) for r in reqs]
    results = []
    for i, (r, a) in enumerate(work):
        if i == 10:
            assert wg.set_kill_switch("kill_switch_operator", True, "drill: card fraud suspected")["outcome"] == "ok"
        if i == 20:
            assert wg.set_kill_switch("kill_switch_operator", False, "drill over")["outcome"] == "ok"
        results.append(kit.ex(wg, r, a, "executor", False)["outcome"])
    assert results[:10] == ["applied"] * 10 and results[10:20] == ["held"] * 10 and results[20:] == ["applied"] * 10
    assert store.count_applied() == 20
    # the ten held ones were never voided: the same approvals resume once the switch is off
    assert [kit.ex(wg, r, a, "executor", False)["outcome"] for r, a in work[10:20]] == ["applied"] * 10
    # a replay of an applied key is answered even while the switch is on
    wg.set_kill_switch("kill_switch_operator", True, "again")
    assert kit.ex(wg, *work[0], "executor", False)["outcome"] == "duplicate_ignored"
    rows = [r for r in store.audit_rows() if r["event"].startswith("kill_switch")]
    assert [r["event"] for r in rows] == ["kill_switch_on", "kill_switch_off", "kill_switch_on"]
    assert json.loads(rows[0]["detail"]) == {"operator": "kill_switch_operator", "reason": "drill: card fraud suspected"}
    assert store.audit_chain_ok()


def test_only_the_operator_flips_the_switch_and_a_reason_is_required():
    _, _, _, wg, _, _ = run()
    assert wg.set_kill_switch("executor", True, "x") == {"outcome": "denied", "code": "IDENTITY_DENIED"}
    for reason in ("", "   ", None, 5):
        assert wg.set_kill_switch("kill_switch_operator", True, reason)["code"] == "KEY_INVALID"
    assert wg.set_kill_switch("kill_switch_operator", "yes", "x")["code"] == "KEY_INVALID"
    assert wg.store.kill_switch()["on"] is False


# ------------------------------------------------------------------------------------------------ caps and ledger against the store (M5)
def _fresh(req, people=kit.ONE):
    store, svc, _clock, wg = kit.make()
    return store, svc, wg, req, kit.sign(svc, req, people)


def test_single_action_cap_boundary_follows_config_limits():
    hard = LIMITS["USD"].hard_cap
    basis = {
        "captured_minor": "999999",
        "prior_order_minor": "0",
        "prior_customer_30d_minor": "0",
        "prior_refunded_minor": "0",
        "tier_floor": "",
        "request": "2500",
    }
    ok = kit.request(tier="four_eyes", amount_minor=str(hard), basis=basis, cluster=["c1"])
    store, _svc, wg, _, ap = _fresh(ok, kit.TWO)
    # at the hard cap the CUSTOMER cap (smaller) is the one that bites, with an exact boundary of its own
    assert kit.ex(wg, ok, ap, "executor", False)["code"] == "CUSTOMER_CAP"
    over = kit.request(tier="four_eyes", amount_minor=str(hard + 1), basis=basis)
    s2, _svc2, wg2, _, ap2 = _fresh(over, kit.TWO)
    assert kit.ex(wg2, over, ap2, "executor", False)["code"] == "OVER_CAP"
    cap = LIMITS["USD"].customer_30d_cap
    at = kit.request(tier="four_eyes", amount_minor=str(cap), basis=basis)
    s3, svc3, wg3, _, ap3 = _fresh(at, kit.TWO)
    assert kit.ex(wg3, at, ap3, "executor", False)["outcome"] == "applied"
    plus = kit.request(order_id="ord-2", line_ids=["l2"], tier="four_eyes", amount_minor="1", basis=basis)
    assert kit.ex(wg3, plus, kit.sign(svc3, plus, kit.TWO), "executor", False)["code"] == "CUSTOMER_CAP", (
        "30000 + 1 > cap for the same cluster"
    )
    other = kit.request(order_id="ord-3", line_ids=["l3"], customer_id="c2", cluster=["c2"], amount_minor="1", basis=basis)
    assert kit.ex(wg3, other, kit.sign(svc3, other), "executor", False)["outcome"] == "applied", "another cluster is unaffected"
    assert s2.count_applied() == 0 and store.count_applied() == 0 and s3.count_applied() == 2


def test_goodwill_cap_order_cap_over_refundable_and_the_ledger_are_checked_against_the_store():
    _store, svc, _clock, wg = kit.make()
    basis = {
        "captured_minor": "6000",
        "prior_order_minor": "0",
        "prior_customer_30d_minor": "0",
        "prior_refunded_minor": "0",
        "tier_floor": "",
        "request": "2500",
    }

    def go(**kw):
        r = kit.request(
            basis=kw.pop("basis", basis), tier="four_eyes", **kw
        )  # the cumulative on one order passes the one-approver limit
        return kit.ex(wg, r, kit.sign(svc, r, kit.TWO), "executor", False)

    assert go(action="goodwill", line_ids=[], amount_minor=str(LIMITS["USD"].goodwill_cap + 1))["code"] == "OVER_CAP"
    assert go(action="goodwill", line_ids=[], amount_minor="1500")["outcome"] == "applied"
    assert go(action="goodwill", line_ids=[], amount_minor="1400")["code"] == "GOODWILL_ALREADY", "one goodwill per order"
    assert go(line_ids=["l1"], amount_minor="2500")["outcome"] == "applied"
    assert go(line_ids=["l1"], amount_minor="2499")["code"] == "LINE_COMPENSATED", "a line is compensated once"
    assert go(action="reship", line_ids=["l1"], amount_minor="2500")["code"] == "LINE_COMPENSATED"
    assert go(line_ids=["l2"], amount_minor="2500")["outcome"] == "applied"
    assert go(line_ids=["l3"], amount_minor="2500")["code"] == "OVER_REFUNDABLE", "1500 + 2500 + 2500 + 2500 > captured 6000"
    assert go(action="cancel", line_ids=[], amount_minor="100")["code"] in {"LINE_COMPENSATED", "OVER_REFUNDABLE"}
    big = {**basis, "prior_order_minor": str(LIMITS["USD"].hard_cap)}
    assert go(order_id="ord-7", line_ids=["l7"], amount_minor="100", basis=big)["code"] == "ORDER_CAP"


def test_cancel_blocks_later_refunds_and_reships_on_the_order():
    _store, svc, _clock, wg = kit.make()
    r = kit.request(action="cancel", line_ids=[], amount_minor="3000")
    assert kit.ex(wg, r, kit.sign(svc, r), "executor", False)["outcome"] == "applied"
    for action, ids in (("refund", ["l1"]), ("reship", ["l1"]), ("cancel", [])):
        r2 = kit.request(action=action, line_ids=ids, amount_minor="500")
        assert kit.ex(wg, r2, kit.sign(svc, r2), "executor", False)["code"] == "LINE_COMPENSATED", action


def test_day_cap_counts_applied_today_plus_other_reservations_in_the_tenant_and_resets_on_a_new_utc_day():
    store, svc, clock, wg = kit.make()
    cap = LIMITS["USD"].store_day_cap
    kit.raw_reserve(store, "t1", "r" * 64, "c9", "ord-9", cap - 2500, "USD", kit.START)
    r = kit.request()
    assert kit.ex(wg, r, kit.sign(svc, r), "executor", False)["outcome"] == "applied", "cap - 2500 reserved + 2500 = cap exactly"
    r2 = kit.request(order_id="ord-2", line_ids=["l2"], customer_id="c2", cluster=["c2"], amount_minor="1")
    assert kit.ex(wg, r2, kit.sign(svc, r2), "executor", False)["code"] == "DAY_CAP"
    kit.raw_reserve(store, "t2", "r" * 64, "c9", "ord-9", cap, "USD", kit.START)
    assert (
        kit.ex(wg, kit.request(tenant_id="t2", order_id="ord-3", line_ids=["l3"], amount_minor="10"), None, "executor", False)[
            "code"
        ]
        == "NO_APPROVAL"
    )
    clock.now = "2026-10-21T00:00:01Z"
    r3 = kit.request(
        order_id="ord-2",
        line_ids=["l2"],
        customer_id="c2",
        cluster=["c2"],
        amount_minor="2501",
        requested_at="2026-10-21T00:00:00Z",
    )
    assert kit.ex(wg, r3, kit.sign(svc, r3), "executor", False)["code"] == "DAY_CAP", (
        "the unapproved reservation still holds today's cap in the new day"
    )
    store.release("t1", "r" * 64)
    assert kit.ex(wg, r3, kit.sign(svc, r3), "executor", False)["outcome"] == "applied"


def test_the_own_reservation_is_converted_not_double_counted_and_a_compensation_record_is_written_not_an_undo():
    store, svc, _clock, wg = kit.make()
    r = kit.request()
    kit.raw_reserve(store, "t1", kit.key_of(r), "c1", "ord-1", 70000, "USD", kit.START)
    assert (
        store.other_reserved("t1", "USD", kit.key_of(r), "2000-01-01T00:00:00Z") == 0
        and store.other_reserved("t1", "USD", "someone-else", "2000-01-01T00:00:00Z") == 70000
    )
    store.release("t1", kit.key_of(r))
    kit.raw_reserve(store, "t1", kit.key_of(r), "c1", "ord-1", 2500, "USD", kit.START)
    assert kit.ex(wg, r, kit.sign(svc, r), "executor", False)["outcome"] == "applied"
    assert store.reservations("t1") == []
    rec = store.compensation_records("t1")
    assert (
        len(rec) == 1
        and rec[0]["kind"] == "compensation_record"
        and "never taken back" in rec[0]["note"]
        and "reverse" not in json.dumps(rec).lower()
    )


def test_the_audit_chain_detects_an_edited_row():
    store, svc, _clock, wg = kit.make()
    r = kit.request()
    kit.ex(wg, r, kit.sign(svc, r), "executor", False)
    kit.ex(wg, kit.request(order_id="ord-5", line_ids=["l5"]), None, "executor", False)
    assert store.audit_chain_ok() and len(store.audit_rows()) >= 3
    store._db.execute("UPDATE audit SET detail='{}' WHERE seq=2")
    assert not store.audit_chain_ok()


def test_the_write_path_never_names_an_undo():
    for path in (ROOT / "src").rglob("*.py"):
        assert "undo" not in path.read_text(encoding="utf-8").lower(), path.name


def test_check_and_apply_is_one_critical_section_under_concurrency():
    """Twenty threads race for a day cap that fits exactly eight 30000 refunds; the store read is slow, so a check-then-act gap cannot hide."""
    store, svc, _clock, wg = kit.make()
    real = store.sum_day
    gather = threading.Barrier(20)

    def slow(*a):
        value = real(*a)
        # every racing thread meets here BEFORE any of them writes, so the value read is stale for all of them unless the check and the write are one
        # critical section (then the first thread waits alone, the barrier breaks after 0.5 s and the rest pass at once). Deterministic, not a sleep.
        try:
            gather.wait(timeout=0.5)
        except threading.BrokenBarrierError:
            pass
        return value

    store.sum_day = slow
    basis = {
        "captured_minor": "99999",
        "prior_order_minor": "0",
        "prior_customer_30d_minor": "0",
        "prior_refunded_minor": "0",
        "tier_floor": "",
        "request": "30000",
    }
    work = []
    for i in range(20):
        r = kit.request(
            order_id=f"ord-{i}",
            line_ids=[f"l{i}"],
            customer_id=f"c{i}",
            cluster=[f"c{i}"],
            amount_minor="30000",
            tier="four_eyes",
            basis=basis,
        )
        work.append((r, kit.sign(svc, r, kit.TWO)))
    out = []

    def go(pair):
        out.append(kit.ex(wg, pair[0], pair[1], "executor", False)["outcome"])

    threads = [threading.Thread(target=go, args=(w,)) for w in work]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert out.count("applied") == 8 and store.sum_day("t1", "USD", "2026-10-20") == 240000, "250000 // 30000 = 8"


def test_applying_consumes_the_approval_under_the_key_it_paid():
    store, svc, _clock, wg = kit.make()
    req = kit.request()
    ap = kit.sign(svc, req)
    assert store.approval_key("t1", ap["approval_id"]) is None
    assert kit.ex(wg, req, ap, "executor", False)["outcome"] == "applied"
    assert store.approval_key("t1", ap["approval_id"]) == kit.key_of(req)
    assert store.approval_key("t2", ap["approval_id"]) is None, "approval ids are tenant scoped"


def test_over_refundable_boundary_is_exact_and_goodwill_does_not_use_up_the_refundable_amount():
    _store, svc, _clock, wg = kit.make()

    def go(**kw):
        r = kit.request(tier="four_eyes", **kw)
        return kit.ex(wg, r, kit.sign(svc, r, kit.TWO), "executor", False)

    assert go(action="goodwill", line_ids=[], amount_minor="1500")["outcome"] == "applied"
    assert go(line_ids=["l1"], amount_minor="2500")["outcome"] == "applied"
    assert go(line_ids=["l2"], amount_minor="2500")["outcome"] == "applied"
    assert go(line_ids=["l3"], amount_minor="1000")["outcome"] == "applied", "5000 + 1000 = captured 6000 exactly: allowed"
    assert go(line_ids=["l4"], amount_minor="1")["code"] == "OVER_REFUNDABLE"


def test_a_store_row_with_the_same_key_in_two_tenants_is_allowed_and_a_failed_transaction_rolls_back():
    store = Store()
    base = {"key": "k" * 64, "action": "refund", "order_id": "ord-1", "line_ids": ["l1"], "amount_minor": 5, "currency": "USD",
            "customer_id": "c1", "approval_id": "ap-1", "applied_at": kit.START, "day": "2026-10-20"}  # fmt: skip

    def attempt(tenant):
        try:
            store.insert_applied({**base, "tenant": tenant})
        except Exception as e:  # noqa: BLE001
            return type(e).__name__
        return "ok"

    assert (attempt("t1"), attempt("t2")) == ("ok", "ok")  # (tenant, key) is the unique pair, not the key alone
    assert attempt("t1") == "IntegrityError", "the same key in the same tenant is refused by the database"
    assert store.count_applied() == 2
    try:
        with store.transaction():
            store.insert_applied({**base, "tenant": "t3"})
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert store.count_applied() == 2 and store.get_applied("t3", "k" * 64) is None, "the half-done transaction was rolled back"


# ------------------------------------------------------------------------------------------------ review 7: bindings, shapes, hostile input
def _basis(**kw):
    return {
        "captured_minor": "6000",
        "prior_order_minor": "0",
        "prior_customer_30d_minor": "0",
        "prior_refunded_minor": "0",
        "tier_floor": "",
        "request": "2500",
        **kw,
    }


@pytest.mark.parametrize(
    "bad", ["-99999999", " 5 ", "1_000", "٥", "05", "1e3", "", "9" * 13, 5, None, ["5"], True], ids=lambda b: repr(b)[:14]
)
@pytest.mark.parametrize("field", ["captured_minor", "prior_order_minor", "prior_customer_30d_minor", "prior_refunded_minor"])
def test_the_signed_basis_must_be_canonical_non_negative_minor_units(field, bad):
    store, _svc, _clock, wg = kit.make()
    req = kit.request(basis=_basis(**{field: bad}))
    # the approval is irrelevant: the request itself is refused before any approval is looked at
    out = kit.ex_safe(wg, req, None, "executor", False)
    want = "AMOUNT_NOT_CANONICAL" if isinstance(bad, str) else "KEY_INVALID"  # a non-text value never reaches the number parser
    assert out == {"outcome": "denied", "code": want}, (field, bad, out)
    assert store.count_applied() == 0 and store.reservations("t1") == []


def test_a_negative_prior_amount_cannot_open_a_cap():
    store, svc, _clock, wg = kit.make()
    big = str(LIMITS["USD"].customer_30d_cap)
    req = kit.request(
        amount_minor=big, tier="four_eyes", basis=_basis(prior_customer_30d_minor="-99999999", captured_minor="99999999")
    )
    assert kit.ex_safe(wg, req, kit.sign(svc, req, kit.TWO), "executor", False)["code"] == "AMOUNT_NOT_CANONICAL"
    ok = kit.request(amount_minor=big, tier="four_eyes", basis=_basis(prior_customer_30d_minor="1", captured_minor="99999999"))
    assert kit.ex_safe(wg, ok, kit.sign(svc, ok, kit.TWO), "executor", False)["code"] == "CUSTOMER_CAP", "30000 + 1 prior > cap"
    assert store.count_applied() == 0


def _deep(n):
    x: object = "x"
    for _ in range(n):
        x = [x]
    return x


HOSTILE_APPROVALS = {
    "extra key in a step": lambda a: {**a, "steps": [{**a["steps"][0], "x": "y"}]},
    "NaN in a step": lambda a: {**a, "steps": [{**a["steps"][0], "x": float("nan")}]},
    "non-string key in a step": lambda a: {**a, "steps": [{1: "a", "person": "p", "role": "r"}]},
    "deep nesting in a step": lambda a: {**a, "steps": [{"person": _deep(5000), "role": "support_lead"}]},
    "deep nesting in the id": lambda a: {**a, "approval_id": _deep(5000)},
    "step is a string": lambda a: {**a, "steps": ["lead"]},
    "too many steps": lambda a: {**a, "steps": a["steps"] * 5},
    "tier not text": lambda a: {**a, "tier": ["human"]},
    "non-ASCII mac": lambda a: {**a, "mac": "é" * 64},
    "mac missing": lambda a: {k: v for k, v in a.items() if k != "mac"},
    "huge id": lambda a: {**a, "approval_id": "a" * 100000},
}


@pytest.mark.parametrize("name", sorted(HOSTILE_APPROVALS))
def test_hostile_approval_objects_are_typed_denies_never_exceptions(name):
    store, svc, _clock, wg = kit.make()
    req = kit.request()
    ap = HOSTILE_APPROVALS[name](kit.sign(svc, req))
    out = kit.ex_safe(wg, req, ap, "executor", False)
    assert out == {"outcome": "denied", "code": "NO_APPROVAL"}, (
        name,
        out,
    )  # the shape check comes before the MAC, so every one of these is NO_APPROVAL
    assert store.count_applied() == 0


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: {**r, "basis": {**r["basis"], "x": _deep(5000)}},
        lambda r: {**r, "basis": {**r["basis"], "x": float("nan")}},
        lambda r: {**r, "basis": {**r["basis"], "extra": "y"}},
        lambda r: {**r, "basis": {**r["basis"], "request": 5}},
        lambda r: {**r, "basis": {**r["basis"], "request": _deep(5000)}},
        lambda r: {**r, "basis": {**r["basis"], 5: "non-string key"}},
        lambda r: {**r, "basis": {**r["basis"], "x": {1, 2}}},
        lambda r: {**r, "line_ids": ["l1"] * 51},
        lambda r: {**r, "line_ids": [f"l{i}" for i in range(10000)]},
        lambda r: {**r, "customer_id": "c" * 100000},
        lambda r: {**r, "customer_id": "c\u200b1"},
        lambda r: {**r, "cluster": ["c1", "c\u200b2"]},
        lambda r: {**r, "cluster": [f"c{i}" for i in range(1, 22)]},
        lambda r: {**r, "cluster": []},
        lambda r: {**r, "cluster": ["c2"]},
        lambda r: {**r, "requester": "x" * 100000},
        lambda r: {**r, "requester": "bidi" + chr(0x202E) + "evil"},
        lambda r: {**r, "requester": ""},
        lambda r: {**r, "requester": "line\nbreak"},
        lambda r: {**r, "beneficiary": "y" * 255},
        lambda r: {**r, "beneficiary": "\u200b"},
        lambda r: {**r, "requested_at": "2026-10-20T12:00:00Z" + "0" * 100},
        lambda r: {**r, "tier": "above"},
        lambda r: {**r, "basis": {**r["basis"], "tier_floor": "blocked"}},
        lambda r: {**r, "basis": {k: v for k, v in r["basis"].items() if k != "tier_floor"}},
    ],
)
def test_request_shapes_and_lengths_are_bounded_and_hostile_values_are_typed_denies(mutate):
    store, svc, _clock, wg = kit.make()
    req = kit.request()
    out = kit.ex_safe(wg, mutate(req), kit.sign(svc, req), "executor", False)
    assert out == {"outcome": "denied", "code": "KEY_INVALID"}, out
    assert store.count_applied() == 0


def test_the_largest_legal_request_is_accepted():
    store, svc, _clock, wg = kit.make()
    ids = [f"l{i}" for i in range(50)]
    req = kit.request(line_ids=ids, cluster=["c1", *[f"c{i}" for i in range(2, 21)]], requester="r" * 254, beneficiary="b" * 254)
    assert kit.ex_safe(wg, req, kit.sign(svc, req), "executor", True)["outcome"] == "dry_run"
    assert store.count_applied() == 0


def test_the_signed_tier_and_request_time_must_equal_the_requests_even_with_a_valid_mac():
    store, svc, _clock, wg = kit.make()
    req = kit.request()
    h = hash_request(req, kit.key_of(req))
    for kw in ({"tier": "four_eyes"}, {"requested_at": "2026-10-20T11:00:00Z"}):
        args = {
            "tenant_id": "t1",
            "args_hash": h,
            "tier": "human",
            "requested_at": req["requested_at"],
            "requester": req["requester"],
            "people": kit.ONE,
        }
        ap = svc.issue("approver_human", **{**args, **kw})
        assert kit.ex(wg, req, ap, "executor", False)["code"] == "ARGS_HASH_MISMATCH", kw
    assert store.count_applied() == 0


def test_the_write_gate_holds_a_verifier_only_and_cannot_issue_an_approval():
    _store, svc, _clock, wg = kit.make()
    assert not hasattr(wg.approvals, "issue") and not hasattr(wg, "issue") and hasattr(svc, "issue")
    assert wg.approvals.directory == svc.directory, "the directory stays live for the verifier"
    with pytest.raises(TypeError):
        wg.approvals.directory["x@desk.example"] = frozenset({"support_lead"})  # the verifier's view is read-only
    svc.directory["new@desk.example"] = frozenset({"support_lead"})
    req = kit.request()
    assert kit.ex(wg, req, kit.sign(svc, req, [("new@desk.example", "support_lead")]), "executor", True)["outcome"] == "dry_run"


# ---- requester and approver comparison is normalised the same way everywhere (M7)
@pytest.mark.parametrize("requester", ["Lead@desk.example", " lead@desk.example ", "LEAD@DESK.EXAMPLE"])
def test_requester_equals_approver_after_nfkc_strip_and_casefold(requester):
    store, svc, _clock, wg = kit.make()
    req = kit.request(requester=requester)
    assert kit.ex(wg, req, kit.sign(svc, req, kit.ONE), "executor", False)["code"] == "REQUESTER_IS_APPROVER"
    assert store.count_applied() == 0


def test_the_same_person_in_two_spellings_is_one_person_and_the_beneficiary_in_any_spelling_cannot_approve():
    req = kit.request(tier="four_eyes", amount_minor="9000", basis=_basis(request="9000", captured_minor="60000"))
    _store, svc, _clock, wg = kit.make()
    svc.directory["both@desk.example"] = frozenset({"support_lead", "finance_approver"})
    ap = kit.sign(svc, req, [("both@desk.example", "support_lead"), ("BOTH@desk.example", "finance_approver")])
    assert kit.ex(wg, req, ap, "executor", False)["code"] == "SAME_PERSON"
    ben = kit.request(beneficiary="Pat@Example.com ")
    assert (
        kit.ex(wg, ben, kit.sign(svc, ben, [("PAT@example.com", "support_lead")]), "executor", False)["code"]
        == "APPROVER_IS_BENEFICIARY"
    )


# ---- the tier is recomputed at execute from the signed basis and the store (M6)
def test_a_one_approver_signature_cannot_cover_a_cumulative_or_risk_floor_that_needs_two():
    store, svc, _clock, wg = kit.make()
    over = kit.request(basis=_basis(prior_order_minor="7000", captured_minor="99999"), amount_minor="1000")
    assert kit.ex(wg, over, kit.sign(svc, over), "executor", False)["code"] == "ROLE_NOT_IN_MATRIX", "7000 + 1000 > 7500"
    over4 = {**over, "tier": "four_eyes"}
    assert kit.ex(wg, over4, kit.sign(svc, over4, kit.TWO), "executor", True)["outcome"] == "dry_run"
    floor = kit.request(basis=_basis(tier_floor="four_eyes"))
    assert kit.ex(wg, floor, kit.sign(svc, floor), "executor", False)["code"] == "ROLE_NOT_IN_MATRIX", (
        "a signed risk floor raises the minimum"
    )
    fl4 = {**floor, "tier": "four_eyes"}
    assert kit.ex(wg, fl4, kit.sign(svc, fl4, kit.TWO), "executor", False)["outcome"] == "applied"
    cust = kit.request(basis=_basis(prior_customer_30d_minor="7000"), amount_minor="1000", order_id="ord-9", line_ids=["l9"])
    assert kit.ex(wg, cust, kit.sign(svc, cust), "executor", False)["code"] == "ROLE_NOT_IN_MATRIX", (
        "the cluster cumulative counts too"
    )
    assert store.count_applied() == 1


def test_what_the_store_applied_since_the_proposal_raises_the_required_tier():
    _store, svc, _clock, wg = kit.make()
    first = kit.request(amount_minor="5000", basis=_basis(captured_minor="99999", request="5000"))
    assert kit.ex(wg, first, kit.sign(svc, first), "executor", False)["outcome"] == "applied"
    second = kit.request(line_ids=["l2"], amount_minor="3000", basis=_basis(captured_minor="99999", request="3000"))
    assert kit.ex(wg, second, kit.sign(svc, second), "executor", False)["code"] == "ROLE_NOT_IN_MATRIX", (
        "5000 applied + 3000 = 8000"
    )
    s4 = {**second, "tier": "four_eyes"}
    assert kit.ex(wg, s4, kit.sign(svc, s4, kit.TWO), "executor", False)["outcome"] == "applied"


# ---- reservations expire (M5)
def test_a_reservation_older_than_the_approval_ttl_no_longer_holds_the_day_cap_and_the_sweeper_removes_it():
    store, svc, _clock, wg = kit.make()
    cap = LIMITS["USD"].store_day_cap
    kit.raw_reserve(
        store, "t1", "r" * 64, "c9", "ord-9", cap - 1000, "USD", "2026-10-19T10:00:00Z"
    )  # 26 hours old at the demo clock
    kit.raw_reserve(store, "t1", "s" * 64, "c9", "ord-8", 5, "USD", "2026-10-20T11:00:00Z")
    req = kit.request(amount_minor="2500")
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", True)["outcome"] == "dry_run", "the stale reservation does not count"
    kit.raw_reserve(store, "t1", "q" * 64, "c9", "ord-7", cap - 1000, "USD", "2026-10-20T11:59:00Z")  # a FRESH one still does
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", True)["code"] == "DAY_CAP"
    assert wg.sweep("executor") == {"outcome": "denied", "code": "IDENTITY_DENIED"}
    assert wg.sweep("sweeper") == {"outcome": "ok", "code": None, "released": 1}
    assert sorted(r["key"][0] for r in store.reservations("t1")) == ["q", "s"]
    assert wg.sweep("reconciler")["released"] == 0
    assert any(r["event"] == "reservations_swept" for r in store.audit_rows())


# ---- identity first, clock window and ratchet (N4, N5)
def test_an_identity_that_may_not_write_learns_nothing_about_the_request():
    _store, _svc, _clock, wg = kit.make()
    for who in ("agent_runtime", "approver_human", "sweeper", "nobody", None, 5):
        assert kit.ex_safe(wg, "not even a request", None, who, False) == {"outcome": "denied", "code": "IDENTITY_DENIED"}, who
    assert kit.ex_safe(wg, "not even a request", None, "executor", False) == {"outcome": "denied", "code": "KEY_INVALID"}


@pytest.mark.parametrize(
    "bad", ["9999-01-01T00:00:00Z", "1999-12-31T23:59:59Z", "2100-01-01T00:00:00Z", "0999-01-01T00:00:00+00:00"]
)
def test_a_clock_outside_the_sane_window_is_refused_and_cannot_brick_the_desk(bad):
    _store, svc, clock, wg = kit.make()
    req = kit.request()
    clock.now = bad
    assert kit.ex_safe(wg, req, kit.sign(svc, req), "executor", False) == {"outcome": "denied", "code": "CLOCK_INVALID"}
    assert wg.set_kill_switch("kill_switch_operator", True, "operator drill")["code"] == "CLOCK_INVALID"
    clock.now = kit.START
    assert kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied"


def test_only_an_applied_payment_or_a_kill_switch_flip_moves_the_clock_ratchet():
    store, svc, clock, wg = kit.make()
    req = kit.request()
    clock.now = "2099-06-01T00:00:00Z"
    future = kit.request(requested_at=clock.now)
    assert kit.ex(wg, future, kit.sign(svc, future), "executor", True)["outcome"] == "dry_run"
    assert kit.ex(wg, future, None, "executor", False)["code"] == "NO_APPROVAL"
    assert store.meta("last_clock") is None, "dry runs and refusals do not move the ratchet"
    clock.now = kit.START
    assert (
        kit.ex(wg, req, kit.sign(svc, req), "executor", False)["outcome"] == "applied" and store.meta("last_clock") == kit.START
    )
    clock.now = "2026-10-20T13:00:00Z"
    assert wg.set_kill_switch("kill_switch_operator", True, "drill")["outcome"] == "ok"
    assert store.meta("last_clock") == "2026-10-20T13:00:00Z"
    clock.now = "2026-10-20T12:30:00Z"
    assert wg.set_kill_switch("kill_switch_operator", False, "back")["code"] == "CLOCK_BACKWARDS", (
        "the switch obeys the same clock rule"
    )


def test_a_failed_commit_rolls_back_instead_of_leaving_the_connection_inside_a_transaction():
    import sqlite3

    store = Store()
    real = store._db

    class Proxy:
        def execute(self, sql, *a):
            if sql == "COMMIT":
                raise sqlite3.OperationalError("disk full")
            return real.execute(sql, *a)

        def __getattr__(self, name):
            return getattr(real, name)

    store._db = Proxy()
    with pytest.raises(sqlite3.OperationalError), store.transaction() as db:
        db.execute("INSERT INTO meta(k, v) VALUES('a', 'b')")
    assert real.in_transaction is False
    store._db = real
    assert store.meta("a") is None, "the half-done write is gone"


def test_the_per_action_identity_check_matters_for_an_identity_that_holds_only_some_money_actions(monkeypatch):
    monkeypatch.setitem(
        identities.IDENTITIES,
        "refund_only",
        {"policy": "test", "allow": frozenset({"payments.refund"}), "why": {"payments.refund": "t"}},
    )
    _store, svc, _clock, wg = kit.make()
    refund, cancel = kit.request(), kit.request(action="cancel", line_ids=[], order_id="ord-2")
    assert kit.ex(wg, refund, kit.sign(svc, refund), "refund_only", True)["outcome"] == "dry_run"
    assert kit.ex(wg, cancel, kit.sign(svc, cancel), "refund_only", True) == {"outcome": "denied", "code": "IDENTITY_DENIED"}


def test_reserving_the_same_key_twice_keeps_the_first_reservation_and_its_age():
    store = Store()
    kit.reserve(store, "t1", "k" * 64, "c1", "ord-1", 5, "USD", "2026-10-20T10:00:00Z")
    store.set_meta("last_clock", "2026-10-20T11:59:00Z")
    kit.reserve(
        store, "t1", "k" * 64, "c1", "ord-1", 9, "USD", "2026-10-20T11:59:00Z"
    )  # a second proposal with the same key shares the reservation
    rows = store.reservations("t1")
    assert [(r["amount_minor"], r["created_at"]) for r in rows] == [(5, "2026-10-20T10:00:00Z")], (
        "the age is not refreshed by a repeat"
    )
