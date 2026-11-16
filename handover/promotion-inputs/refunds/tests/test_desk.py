"""The thin end-to-end path on the dev data: gate -> reservation -> signed approval -> governed write -> replay (src/refunds/desk.py)."""

import json
from pathlib import Path

from refunds import desk
from refunds.approval import ApprovalIssuer
from refunds.store import Store

DATA = Path(__file__).resolve().parents[1] / "demo_only" / "data"


def _run():
    world = json.loads((DATA / "world.json").read_text(encoding="utf-8"))
    cases = [json.loads(x) for x in (DATA / "dev.jsonl").read_text(encoding="utf-8").splitlines()]
    d = desk.Desk(Store(), ApprovalIssuer(desk.DIRECTORY, key=b"d" * 32), lambda: desk.DEMO_NOW)
    return d, desk.run_five(world, cases, d)


def test_the_five_demo_script_cases_run_end_to_end_with_replay_and_a_kill_switch_hold():
    d, out = _run()
    assert out == [
        ("1 gate", "tier=human"),
        ("1 execute #1", "applied"),
        ("1 execute #2", "duplicate_ignored"),
        ("1 execute #3", "duplicate_ignored"),
        ("2 gate", "tier=four_eyes"),
        ("2 execute (steps swapped)", "STEP_ORDER"),
        ("2 execute (right order)", "applied"),
        ("3 steered turns", "AUTHORITY_MISMATCH,BASIS_NOT_ALLOWED"),
        ("4 gate", "ORDER_AMBIGUOUS"),
        ("5 execute (response lost)", "applied"),
        ("5 retry by key", "duplicate_ignored"),
        ("5 kill switch", "ok"),
        ("5 replay while switched off", "duplicate_ignored"),
    ]
    assert d.store.count_applied() == 3 and d.store.audit_chain_ok()
    assert d.store.kill_switch()["on"] is True and len(d.store.compensation_records("demo")) == 3


def test_a_new_action_is_held_while_the_switch_is_on_and_resumes_when_it_is_lifted():
    d, _ = _run()
    world = json.loads((DATA / "world.json").read_text(encoding="utf-8"))
    cases = [json.loads(x) for x in (DATA / "dev.jsonl").read_text(encoding="utf-8").splitlines()]
    c = next(x for x in cases if x["case_id"] == "refunds-e-003")
    dec = d.propose(c, world, desk.recorded_call(c))
    ap = d.approve(
        dec,
        [("lead@desk.example", "support_lead")]
        if dec.tier == "human"
        else [("lead@desk.example", "support_lead"), ("finance@desk.example", "finance_approver")],
    )
    assert d.execute(dec, ap)["outcome"] == "held"
    assert d.write.set_kill_switch("kill_switch_operator", False, "drill over")["outcome"] == "ok"
    assert d.execute(dec, ap)["outcome"] == "applied"


def test_a_real_person_as_requester_cannot_approve_their_own_request_but_a_colleague_can():
    d, _ = _run()
    world = json.loads((DATA / "world.json").read_text(encoding="utf-8"))
    cases = [json.loads(x) for x in (DATA / "dev.jsonl").read_text(encoding="utf-8").splitlines()]
    c = next(x for x in cases if x["case_id"] == "refunds-e-003")
    dec = d.propose(
        c, world, desk.recorded_call(c), requester="Lead@Desk.example"
    )  # a staff member raised it on the customer's behalf
    assert dec.request["requester"] == "Lead@Desk.example" and dec.tier == "human"
    own = d.approve(dec, [("lead@desk.example", "support_lead")])
    assert d.write.set_kill_switch("kill_switch_operator", False, "lift")["outcome"] == "ok"
    assert d.execute(dec, own)["code"] == "REQUESTER_IS_APPROVER"
    colleague = d.approve(dec, [("lead2@desk.example", "support_lead")])
    assert d.execute(dec, colleague)["outcome"] == "applied"
