"""Review 2 (head c3180e0): fail-closed gaps, id-reuse atomicity, the lock cascade, and ack latency on the DURABLE ledger."""

import dataclasses
import threading
import time

import pytest
from engine_kit import Kit, mk_deal

from dealdesk import inbox as ib
from dealdesk.errors import Malformed
from dealdesk.limits import DEFAULT_LIMITS

AG, DW, EX = "agent_runtime", "draft_writer", "commit_executor"


def _k():
    return Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works", seats=40)])


def _approved(k):
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    k.approve_all(q, {"commercial": "p-sm-01"})
    return q


# ---------------------------------------------------------------- M6: id reuse is one write, the marker is reserved, the hash is never cut
@pytest.mark.parametrize("ledger", ["memory", "sqlite"])
def test_an_id_reuse_row_is_rejected_from_its_first_moment_and_recover_never_processes_it(ledger, tmp_path):
    led = ib.MemoryLedger() if ledger == "memory" else ib.SqliteLedger(str(tmp_path / "l.db"))
    seen = []
    inbox = ib.Inbox(led, lambda m: seen.append(m["text"]) or ("processed", None))
    base = {"msg_id": "m1", "kind": "request", "requester_id": "p-ae-01", "deal_id": "d"}
    inbox.receive("t-a", {**base, "text": "first"})
    inbox.receive("t-a", {**base, "text": "second, same id"})
    reuse = [i for i in led.ids("t-a") if "#idreuse-" in i]
    assert len(reuse) == 1
    assert led.get("t-a", reuse[0])["state"] == "rejected" and led.get("t-a", reuse[0])["reason"] == "id_reuse"
    assert reuse[0] not in led.open_ids(
        "t-a"
    )  # never `received`, so a crash right here cannot make recover() process the conflicting body
    inbox.recover("t-a")
    assert seen == ["first"]


def test_the_reserved_marker_is_refused_in_a_sender_id_and_the_hash_keeps_all_16_hex_digits():
    inbox = ib.Inbox(ib.MemoryLedger(), lambda m: ("processed", None))
    assert inbox.receive("t-a", {"msg_id": "x#idreuse-0123456789abcdef", "text": "a"}) is None
    assert inbox.refusals["malformed"] == 1
    long_id = "a" * DEFAULT_LIMITS.max_id_chars
    inbox.receive("t-a", {"msg_id": long_id, "text": "one"})
    inbox.receive("t-a", {"msg_id": long_id, "text": "two"})
    (cid,) = [i for i in inbox.ledger.ids("t-a") if "#idreuse-" in i]
    assert len(cid.split("#idreuse-")[1]) == 16 and cid.startswith(long_id)


# ---------------------------------------------------------------- M3: a handler hung INSIDE the store lock cascades
def test_a_handler_hung_inside_the_store_lock_dead_letters_the_rows_behind_it_and_its_effect_can_land_later():
    """DOCUMENTED LIMIT: the deadline abandons a worker thread, it cannot release a lock that thread holds. Every Desk entry holds `TenantStore.lock`, so a
    handler stuck inside one blocks every later handler of that tenant until it returns; each of those is dead-lettered with reason `deadline`
    (recoverable by re-offering), and the abandoned thread may still finish its effect after its own row says dead_lettered."""
    k = _k()
    release, effects = threading.Event(), []
    lim = dataclasses.replace(DEFAULT_LIMITS, handler_deadline_s=0.3)

    def handler(msg):
        with k.store.lock:
            if msg["text"] == "hang":
                release.wait(20)
            effects.append(msg["text"])
        return "processed", None

    inbox = ib.Inbox(ib.MemoryLedger(), handler, limits=lim)
    for mid, text in (("m1", "hang"), ("m2", "ok-2"), ("m3", "ok-3")):
        inbox.receive("t-a", {"msg_id": mid, "kind": "request", "requester_id": "p-ae-01", "deal_id": "d", "text": text})
    assert [inbox.process("t-a", m) for m in ("m1", "m2", "m3")] == ["dead_lettered"] * 3  # the cascade
    assert inbox.ledger.get("t-a", "m2")["reason"] == "deadline"
    assert effects == []  # nothing has happened yet
    release.set()
    deadline = time.time() + 10
    while time.time() < deadline and "hang" not in effects:
        time.sleep(0.05)
    assert "hang" in effects  # the abandoned thread finished its effect AFTER its row said dead_lettered
    assert inbox.ledger.get("t-a", "m1")["state"] == "dead_lettered"


# ---------------------------------------------------------------- M1: durable ledger ack latency
def test_ack_latency_on_the_durable_sqlite_ledger_wal_synchronous_full(tmp_path):
    led = ib.SqliteLedger(str(tmp_path / "ack.db"))
    inbox = ib.Inbox(led, lambda m: ("processed", None))
    times = []
    for i in range(1000):
        m = {"msg_id": f"m{i:05d}", "kind": "request", "requester_id": "p-ae-01", "deal_id": "d", "text": "15% please"}
        t0 = time.perf_counter()
        assert inbox.receive("t-a", m) is not None
        times.append(time.perf_counter() - t0)
    times.sort()
    p50, p99 = times[len(times) // 2], times[int(0.99 * len(times)) - 1]
    print(f"sqlite ack over 1000 receives: p50 {p50 * 1000:.2f} ms, p99 {p99 * 1000:.2f} ms")
    assert p99 < 1.0  # the 1,000 ms target
    led.close()


# ---------------------------------------------------------------- M8: fail closed
@pytest.mark.parametrize("flag", [0, None, "", "no", 1])
def test_commit_needs_a_real_bool_for_dry_run(flag):
    k = _k()
    q = _approved(k)
    k.desk.draft_quote(DW, q)
    with pytest.raises(TypeError):
        k.ex.commit(EX, q, flag)
    assert k.ex.commit(EX, q)["outcome"] == "dry_run"  # the default is still the dry run


def test_the_authenticated_person_is_required_and_none_is_not_a_person():
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    raw = k.signed(k.open_approval(q), "p-sm-01")
    with pytest.raises(TypeError):
        k.desk.record_decision("approver_commercial", raw)  # no default: a caller cannot skip the check by leaving it out
    assert k.desk.record_decision("approver_commercial", raw, None) == {"status": "decision_not_accepted"}
    assert k.desk.record_decision("approver_commercial", raw, "p-sm-01") == {"status": "accepted"}


def test_an_approver_without_a_usable_mailbox_identity_is_refused_at_decision_time():
    k = _k()
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval(AG, q)
    sm = next(p for p in k.world.directory if p["person_id"] == "p-sm-01")
    sm["email"] = "no-at-sign"
    assert k.decide(k.open_approval(q), "p-sm-01") == {"status": "decision_not_accepted"}


def test_a_mailbox_that_became_unusable_after_the_approval_is_refused_at_draft():
    k = _k()
    q = _approved(k)
    sm = next(p for p in k.world.directory if p["person_id"] == "p-sm-01")
    sm["email"] = None
    out = k.desk.draft_quote(DW, q)
    assert out.get("rule") == "R-DEALDESK-087" and out["status"] == "denied"


def test_a_requester_who_left_the_directory_or_is_inactive_is_refused_at_draft_and_commit():
    for how in ("gone", "inactive"):
        k = _k()
        q = _approved(k)
        req = next(p for p in k.world.directory if p["person_id"] == "p-ae-01")
        if how == "gone":
            k.world.directory.remove(req)
        else:
            req["active"] = False
        assert k.desk.draft_quote(DW, q)["status"] == "denied", how
    k = _k()
    q = _approved(k)
    assert k.desk.draft_quote(DW, q)["status"] == "created"
    req = next(p for p in k.world.directory if p["person_id"] == "p-ae-01")
    k.world.directory.remove(req)
    assert k.ex.commit(EX, q, dry_run=False)["outcome"] == "denied"


def test_a_signing_key_revoked_after_the_approval_voids_the_accepted_step():
    k = _k()
    q = _approved(k)
    k.keys.revoke("p-sm-01", k.device("p-sm-01").key_id)
    out = k.desk.draft_quote(DW, q)
    assert out["status"] == "denied" and out["rule"] == "R-DEALDESK-023" and "revoked" in out["why"]
    assert k.desk.status(AG, q)["state"] == "voided"


def test_commit_key_and_day_totals_are_written_together_and_a_bad_key_writes_neither():
    k = _k()
    q = _approved(k)
    k.desk.draft_quote(DW, q)
    assert k.ex.commit(EX, q, dry_run=False)["outcome"] == "applied"
    day = k.clock.today()
    assert k.store.get("commits", f"day-USD-{day}")["count"] == 1
    before = dict(k.store._d)
    with pytest.raises(Malformed):
        k.store.put_many([("commits", "ok-1", {"a": 1}), ("commits", "bad/name", {"b": 2})])
    assert dict(k.store._d) == before  # all keys are validated BEFORE anything is written
