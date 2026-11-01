# ruff: noqa: S311  - seeded test randomness; threads are joined inside the loop that defines them
"""K6 class sweeps: each test guards a CLASS of bug that review found more than once, not one example.

* a rule enforced on history instead of the latest state,
* check-then-insert races,
* an asserted name treated as an identity,
* a signed action that can be replayed,
* ids truncated until they can collide.
"""

from __future__ import annotations

import ast
import re
from datetime import timedelta
from pathlib import Path

import pytest

from hadavin_sdk import measure
from hadavin_sdk.models import LevelEvent, RunState
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.postgres import PostgresStore
from tests.test_k6_measure import ACTION, CEIL, NOW, World, day  # noqa: F401 - World and helpers

SRC = Path(__file__).parent.parent / "src" / "hadavin_sdk"


def _calls(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            yield node


# --- identity: a caller-supplied string is not a person ---------------------------------------------------------


def test_class_identity_entry_points_are_called_only_from_where_the_identity_is_verified():
    """`record_label`, `kill_switch`, `approve_import` and a 3-argument `clear` take a principal id as a plain string.
    Outside measure.py they may be called from nowhere (the receiver reaches them through `handle_action`, whose
    user comes from a verified signature); `import_csv` and `note_cli_import` only from the dev-only CLI path."""
    guarded = {"record_label", "kill_switch", "approve_import", "clear"}
    dev_cli = {"import_csv", "note_cli_import"}
    found = []
    for path in SRC.rglob("*.py"):
        if path.name == "measure.py":
            continue
        for call in _calls(ast.parse(path.read_text(encoding="utf-8"))):
            name = call.func.attr
            if name in guarded and not (name == "clear" and len(call.args) < 3):
                found.append(f"{path.relative_to(SRC)}: {name}")
            if name in dev_cli and path.name != "cli.py":
                found.append(f"{path.relative_to(SRC)}: {name}")
    assert found == []


def test_class_cli_limits_reset_is_refused_in_pilot_and_prod_but_stop_and_the_signed_reset_work(
    tmp_path,
):
    import getpass

    from hadavin_sdk import cli
    from hadavin_sdk.models import KillSwitch

    w = World(tmp_path)
    limits = w.measure.limits
    for env in ("pilot", "prod"):
        w.store.set_kill_switch(KillSwitch(on=True, by="someone"))
        assert (
            cli.limits_cmd(limits, "reset", "user:a", env) == 2
        )  # an asserted name cannot lift the kill switch
        assert w.store.get_kill_switch().on
        w.store.set_kill_switch(KillSwitch(on=False))
        assert cli.limits_cmd(limits, "stop", "user:a", env) == 0  # the safe direction stays
        assert w.store.get_kill_switch().on
    # the signed path resets it, with the admin right and once per request
    assert w.click("ops", "reset", ts=NOW)[0] == 200
    assert not w.store.get_kill_switch().on
    assert (
        w.click("owner", "stop", ts=NOW + timedelta(seconds=1))[0] == 200
    )  # a line owner has no stop right
    assert not w.store.get_kill_switch().on
    # dev keeps the CLI for both and audits the operating-system user
    assert cli.limits_cmd(limits, "stop", "user:a", "dev") == 0
    assert cli.limits_cmd(limits, "reset", "user:a", "dev") == 0
    notes = [e for e in w.audit.events() if e.operation.startswith("cli_")]
    assert [(e.operation, e.result) for e in notes] == [
        ("cli_stop", f"os_user:{getpass.getuser()}"),
        ("cli_reset", f"os_user:{getpass.getuser()}"),
    ]


def test_class_cli_dev_import_is_refused_before_it_reads_anything_in_pilot_and_prod():
    cli = (SRC / "cli.py").read_text(encoding="utf-8")
    body = cli[cli.index("def measure_cmd") :]
    assert body.index("in LIVE") < body.index("import_csv(")  # the refusal comes first


# --- ids: a lookup key is never a prefix of someone else's content --------------------------------------------


def test_class_no_truncated_digest_is_used_as_an_id_in_measure():
    text = (SRC / "measure.py").read_text(encoding="utf-8")
    assert not re.search(
        r"hexdigest\(\)\s*\[\s*:", text
    )  # no digest is cut short where it names something


@pytest.mark.parametrize("n", range(25))
def test_class_import_ids_are_full_length_and_differ_for_different_files(n):
    a, b = f"run_id,label\nrun-{n},agree\n", f"run_id,label\nrun-{n},wrong\n"
    ia, ib = measure.csv_import_id(a), measure.csv_import_id(b)
    assert re.fullmatch(r"[0-9a-f]{64}", ia) and ia != ib


# --- one door for labels ----------------------------------------------------------------------------------------


def test_class_a_label_enters_the_store_only_through_add_labels():
    """There is no second, unchecked way in (the old `add_label` skipped the sticky rule)."""
    assert not hasattr(MemoryStore, "add_label") and not hasattr(PostgresStore, "add_label")
    for path in SRC.rglob("*.py"):
        for call in _calls(ast.parse(path.read_text(encoding="utf-8"))):
            assert call.func.attr != "add_label", path


# --- replays: every signed action is acted on once -----------------------------------------------------------------


def test_class_every_signed_measure_action_kind_is_replay_guarded(tmp_path):
    """One nonce check sits in `handle_action`, in front of every kind; this walks all of them."""
    w = World(tmp_path)
    rid = w.run()
    silent = w.run(plan=False, state=RunState.NO_ACTION, reason=None)
    text = f"run_id,label\n{rid},agree\n"
    w.measure.import_csv(text, "fake:u1")
    w.label(w.run(), "harmful")  # something for the clear to act on
    clicks = [
        ("u1", f"label|{rid}|partial"),
        ("u2", f"label|{silent}|missed"),
        ("ops", "stop"),
        ("ops", "reset"),
        ("owner", w.clear_value()),
        ("owner", f"approve_import|{measure.csv_import_id(text)}"),
    ]
    for i, (user, value) in enumerate(clicks):
        ts = NOW + timedelta(seconds=i)
        w.click(user, value, ts=ts)
        before = len(w.store.list_labels(rid)) + len(w.store.list_level_events())
        replays = [e for e in w.audit.events() if e.error_code == "replay"]
        w.click(user, value, ts=ts)  # the same signed request again
        after = len(w.store.list_labels(rid)) + len(w.store.list_level_events())
        assert after == before, value
        assert len([e for e in w.audit.events() if e.error_code == "replay"]) == len(replays) + 1, (
            value
        )


def test_class_a_replayed_approval_click_is_idempotent_by_state(tmp_path):
    """Sibling: the approval buttons are not guarded by the nonce table but by compare-and-set on the request."""
    from hadavin_sdk.models import ApprovalRequest, ChainStep

    w = World(tmp_path)
    req = ApprovalRequest(
        run_id="run-x",
        plan_hash="h",
        risk_class="reversible",
        chain_id="c",
        steps=[ChainStep(approver_ids=["fake:u1"], timeout_s=600)],
        step_expires_at=NOW + timedelta(minutes=10),
        requested_by="svc:test-agent",
        summary="s",
        created_at=NOW,
    )
    w.store.save_approval_request(req)
    value = f"{req.approval_id}|h|0|approve"
    w.click("u1", value, ts=NOW)
    w.click("u1", value, ts=NOW)  # replay
    w.click(
        "u1", f"{req.approval_id}|h|0|reject", ts=NOW + timedelta(seconds=1)
    )  # a different, later click
    assert w.store.get_approval_request(req.approval_id).status == "APPROVED"
    assert w.store.get_approval_decision(req.approval_id).decision == "approve"


# --- check-then-insert: the check and the write are one step --------------------------------------------------------


def test_class_clear_does_not_lift_a_demotion_that_landed_after_it_looked(tmp_path):
    w = World(tmp_path)
    w.label(w.run(), "harmful")
    assert ("test-agent", ACTION) in w.store.current_overrides()
    real = w.measure._clear_blocked

    def look_then_a_new_demotion_lands(agent_id, action_id, last):
        out = real(agent_id, action_id, last)
        w.store.add_level_event(
            LevelEvent(
                agent_id=agent_id, action_id=action_id, kind="demote", reason="harmful:new", by="s"
            )
        )
        return out

    w.measure._clear_blocked = look_then_a_new_demotion_lands
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "changed_meanwhile")
    assert ("test-agent", ACTION) in w.store.current_overrides()
    w.measure._clear_blocked = real
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (
        200,
        "cleared",
    )  # looking again works


def test_class_threads_never_let_a_non_owner_lower_a_harmful_verdict(tmp_path):
    """Many threads label the same runs through the whole Measure path with the real clock; replaying the stored
    order must never show a non-owner lowering a harmful verdict."""
    import threading

    from hadavin_sdk.models import latest_labels

    w = World(tmp_path)
    runs = [w.run() for _ in range(3)]
    people = ["fake:u1", "fake:u2", "fake:u3", "fake:owner"]
    import random

    def work(seed):
        rnd = random.Random(seed)
        for _ in range(40):
            w.box[0] = NOW + timedelta(
                microseconds=rnd.randrange(1000)
            )  # clocks read at different moments
            w.measure.record_label(
                rnd.choice(people),
                rnd.choice(runs),
                rnd.choice(["agree", "wrong", "harmful", "partial"]),
            )

    threads = [threading.Thread(target=work, args=(s,)) for s in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    owners = {p.id for p in w.reg.principals.values() if "clear_override" in p.admin_rights}
    for rid in runs:
        seen = []
        for lab in w.store.list_labels(rid):
            cur = latest_labels(seen).get(rid)
            lowered = cur is not None and cur.label == "harmful" and lab.label != "harmful"
            assert not lowered or lab.principal_id in owners, (rid, lab.label, lab.principal_id)
            seen.append(lab)
