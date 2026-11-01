"""K6 measurement: labels, demotion, the override, promotion evidence, the ceiling and the weekly report.

Everything runs on the memory store and fakes (no model spend); `tests/contracts/test_store_measure.py` checks the
same numbers through the postgres views.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
import yaml

from hadavin_sdk import app as app_mod
from hadavin_sdk import cli, deferred, measure
from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.approvals.receiver import handle_slack_action
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.errors import ConfigError as BaseConfigError
from hadavin_sdk.identity import Principal
from hadavin_sdk.limits import Limits
from hadavin_sdk.measure import DEFAULT_POLICY, Ceiling, Measure
from hadavin_sdk.models import (
    ApprovalRequest,
    AuditEvent,
    ChainStep,
    Label,
    LevelEvent,
    Plan,
    Run,
    RunState,
    Target,
    TickState,
    ToolCall,
)
from hadavin_sdk.registry import load_registry
from hadavin_sdk.replay_records import ReplayRecord
from hadavin_sdk.runtime.agent_loop import Hooks
from hadavin_sdk.runtime.tick import run_tick
from hadavin_sdk.store import MemoryStore
from tests.conftest import qualify
from tests.test_k3_pilot import SECRETS, ScriptedLLM, dev_cfg, reply

S = RunState
SECRET = "k6" + "-signing-secret"  # built from parts
CEIL = Ceiling("harmful labels per quarter", 0, 90, "sponsor email, 2026-11-01")
NOW = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)  # a Monday
WEEK = NOW.date() - timedelta(days=7)  # 2026-10-26
ACTION = "restart_service"
PEOPLE = ("u1", "u2", "u3", "u4")


def day(n: int, hh: int = 12) -> datetime:
    """`n` days before NOW, at hour hh (UTC)."""
    return (NOW - timedelta(days=n)).replace(hour=hh)


class World:
    def __init__(
        self, tmp_path: Path, ceiling: Ceiling | None = CEIL, *, store=None, audit=None, **kw
    ) -> None:
        self.cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
        for who, extra in [
            *((f"fake:{p}", {}) for p in PEOPLE),
            ("fake:nobody", {}),
            ("fake:ops", {"admin_rights": ["stop", "reset"]}),
            ("fake:owner", {"admin_rights": ["clear_override", "approve_label_import"]}),
        ]:
            self.edit_principals(
                lambda d, w=who, e=extra: d.append({"id": w, "kind": "person", **e})
            )
        self.reg = load_registry(load_config(self.cfg))
        self.store = store or MemoryStore()
        self.audit = audit or LocalDirSink(self.reg.config.backends.audit.dir)
        self.channel = FakeChannel(SECRET)
        self.box = [NOW]
        # most tests clear at once; the 24 h minimum age has its own tests (policy=DEFAULT_POLICY)
        kw.setdefault("policy", replace(DEFAULT_POLICY, harmful_clear_min_age_h=0))
        self.measure = Measure(
            self.store,
            self.audit,
            self.reg,
            self.channel,
            ceiling=ceiling,
            clock=lambda: self.box[0],
            limits=Limits(self.store, self.audit, self.reg),
            **kw,
        )
        self.n = 0

    def edit_principals(self, fn) -> None:
        path = self.cfg / "principals.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        fn(data)
        path.write_text(yaml.safe_dump(data), encoding="utf-8")

    def run(
        self,
        *,
        action=ACTION,
        created=None,
        state=S.NO_ACTION,
        reason="shadow",
        plan=True,
        rid=None,
        config_hash=None,
    ):
        self.n += 1
        rid = rid or f"run-{self.n:03d}"
        created = created or NOW
        self.store.create_run(
            Run(
                run_id=rid,
                agent_id="test-agent",
                principal_id="svc:test-agent",
                trigger_kind="event",
                trigger_ref=rid,
                created_at=created,
                updated_at=created,
            )
        )
        self.store.transition(rid, S.RECEIVED, state, reason)
        if plan:
            self.store.save_plan(
                Plan(
                    run_id=rid,
                    agent_id="test-agent",
                    action_id=action,
                    action_version=1,
                    risk_class="reversible",
                    inputs={"service": "x"},
                    target=Target(system="ito-prod"),
                    idempotency_key=rid,
                    expected_outcome="healthy",
                    created_at=created + timedelta(seconds=30),
                    config_hash=config_hash or self.reg.config_hash("test-agent"),
                )
            )
        return rid

    def label(self, rid, name, who="u1", when=None, **kw):
        if when is not None:
            self.box[0] = when
        res = self.measure.record_label(f"fake:{who}", rid, name, **kw)
        self.box[0] = NOW
        return res

    def labelled(self, name, count, *, when=None, action=ACTION, who=None, config_hash=None):
        ids = []
        for i in range(count):
            rid = self.run(
                action=action, created=(when or NOW) - timedelta(hours=1), config_hash=config_hash
            )
            assert self.label(rid, name, who=who[i % len(who)] if who else "u1", when=when).ok
            ids.append(rid)
        return ids

    def clear_value(self, agent="test-agent", action=ACTION):
        """The clear button's value: bound to the newest level event (the demotion it was posted for)."""
        events = [
            e
            for e in self.store.list_level_events()
            if (e.agent_id, e.action_id) == (agent, action)
        ]
        return f"clear|{agent}|{action}|{events[-1].seq}"

    def click(self, user, value, *, secret=SECRET, ts=None, team=None, action_ts=None):
        payload = {"user": {"id": user}, "actions": [{"value": value}]}
        if action_ts is not None:
            payload["actions"][0]["action_ts"] = action_ts
        if team is not None:
            payload["team"] = {"id": team}
        body = urlencode({"payload": json.dumps(payload)}).encode()
        ts = int((ts or NOW).timestamp())
        headers = hmac_v0.sign(body, ts, secret, "X-Hadavin")
        approvals = Approvals(
            self.store, self.audit, self.reg, self.channel, lambda *a: None, lambda: self.box[0]
        )
        return handle_slack_action(approvals, headers, body, self.measure)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path)


# --- parsing ---------------------------------------------------------------------------------------------


def test_k6_label_payload_with_pipe_parses_and_colon_is_refused():
    assert measure.parse_action_value("label|run-1|wrong") == measure.ParsedAction(
        "label", ("run-1", "wrong")
    )
    assert measure.parse_action_value("clear|test-agent|restart_service|7") == measure.ParsedAction(
        "clear", ("test-agent", "restart_service", "7")
    )
    assert (
        measure.parse_action_value("clear|test-agent|restart_service") is None
    )  # not bound to a demotion
    assert measure.parse_action_value("label:run-1:wrong") is None  # the colon form is not ours
    for bad in (
        "label|run-1",
        "label|run-1|wrong|extra",
        "label|run-1|WRONG",
        "label|run 1|wrong",
        "label||wrong",
        "clear|a|b|c|d",
        "clear|a",
        "clear|a|b|x",
        "",
    ):
        assert measure.parse_action_value(bad) is None, bad
    assert measure.is_ours(
        "label:run-1:wrong"
    )  # malformed, but still ours: refused here, never an approval
    assert not measure.is_ours("apr-1|abc|0|approve")


# --- labels and demotion ---------------------------------------------------------------------------------


def test_k6_harmful_demotes(w):
    rid = w.run()
    res = w.label(rid, "harmful")
    assert (res.ok, res.demoted) == (True, True)
    assert w.store.current_overrides() == {("test-agent", ACTION): "shadow"}
    assert w.measure.level_override("test-agent", ACTION) == "shadow"
    assert w.measure.level_override("test-agent", "other") is None
    (ev,) = w.store.list_level_events()
    (lab,) = w.store.list_labels(rid)
    assert (ev.kind, ev.reason) == ("demote", f"harmful:{lab.label_id}")  # keyed by the label row
    # The line owner gets a card with the signed Clear button; the demotion is audited.
    (card,) = w.channel.cards
    values = [b["value"] for blk in card.blocks if blk["kind"] == "buttons" for b in blk["buttons"]]
    assert values == [w.clear_value()]  # the button names the demotion it was posted for
    assert any(e.operation == "demote" for e in w.audit.events())


def test_k6_the_effective_level_only_ever_goes_down(w):
    from hadavin_sdk.runtime.agent_loop import Runtime

    agent = SimpleNamespace(id="test-agent", levels={ACTION: "suggest", "b": "shadow"})
    rt = SimpleNamespace(hooks=Hooks(level_override=w.measure.level_override))
    assert Runtime._level(rt, agent, ACTION) == "suggest"  # no override: the config level
    w.label(w.run(), "harmful")
    assert Runtime._level(rt, agent, ACTION) == "shadow"  # demoted
    assert Runtime._level(rt, agent, "b") == "shadow"  # an override never raises a level


def test_k6_label_sets_caught_by_only_for_wrong_and_harmful(w):
    for name in ("agree", "partial", "wrong", "harmful"):
        w.label(w.run(), name)
    caught = {e.decision: e.caught_by for e in w.audit.events() if e.operation == "label"}
    assert caught == {
        "agree": None,
        "partial": None,
        "wrong": "human_label",
        "harmful": "human_label",
    }


def test_k6_three_wrong_in_14_days_demote(w):
    first, second, third = (w.run() for _ in range(3))
    assert not w.label(first, "wrong", when=day(3)).demoted
    assert not w.label(second, "wrong", when=day(2)).demoted
    assert w.store.current_overrides() == {}
    assert w.label(third, "wrong", when=day(1)).demoted
    assert w.store.current_overrides() == {("test-agent", ACTION): "shadow"}


def test_k6_wrong_labels_older_than_14_days_do_not_count(w):
    a, b, c = (w.run() for _ in range(3))
    w.label(a, "wrong", when=day(20))
    w.label(b, "wrong", when=day(2))
    assert not w.label(c, "wrong", when=day(1)).demoted  # the first is 19 days older than the third


def test_k6_a_corrected_label_does_not_count_as_wrong(w):
    a, b, c = (w.run() for _ in range(3))
    w.label(a, "wrong", when=day(3))
    w.label(
        a, "agree", when=day(2)
    )  # the person corrected themselves: the latest label is the label
    w.label(b, "wrong", when=day(2))
    assert not w.label(c, "wrong", when=day(1)).demoted


def test_k6_wrong_labels_of_another_action_do_not_count(w):
    for _ in range(2):
        w.labelled("wrong", 1)
    other = w.run(action="create_draft_record")
    assert not w.label(other, "wrong").demoted


def test_k6_label_refusals(w):
    rid = w.run()
    assert w.label(rid, "agree", who="nobody").ok  # a known person: yes
    assert w.measure.record_label("fake:stranger", rid, "agree").reason == "unknown_principal"
    assert (
        w.measure.record_label("svc:test-agent", rid, "agree").reason == "unknown_principal"
    )  # a service
    assert w.measure.record_label("fake:u1", "run-missing", "agree").reason == "unknown_run"
    assert w.measure.record_label("fake:u1", rid, "abstain_ok").reason == "label_does_not_fit_run"
    silent = w.run(plan=False, state=S.NO_ACTION, reason=None)
    assert w.measure.record_label("fake:u1", silent, "agree").reason == "label_does_not_fit_run"
    assert w.measure.record_label("fake:u1", rid, "bogus").reason == "unknown_label"
    assert len(w.store.list_labels(rid)) == 1  # only the first one was stored


def test_k6_read_failure_is_shadow(w):
    w.store.current_overrides = lambda: (_ for _ in ()).throw(OSError("store down"))
    assert w.measure.level_override("test-agent", ACTION) == "shadow"


def test_k6_insert_failure_refuses_the_label(w):
    rid = w.run()

    def boom(items, *, may_lower_harmful):
        raise OSError("store down")

    w.store.add_labels = boom
    res = w.label(rid, "harmful")
    assert (res.ok, res.status, res.reason) == (False, 503, "store_unavailable")
    assert w.store.list_labels(rid) == [] and w.store.current_overrides() == {}
    # Through the receiver the person sees a non-2xx.
    status, _ = w.click("u1", f"label|{rid}|harmful")
    assert status == 503


def test_k6_store_read_failure_while_labelling_is_a_refusal(w):
    rid = w.run()
    w.store.get_run = lambda run_id: (_ for _ in ()).throw(OSError("store down"))
    assert w.label(rid, "agree").status == 503


# --- the signed channel path -----------------------------------------------------------------------------


def test_k6_signed_label_click_is_recorded_for_the_verified_user(w):
    rid = w.run()
    assert w.click("u2", f"label|{rid}|partial")[0] == 200
    (lab,) = w.store.list_labels(rid)
    assert (lab.label, lab.principal_id, lab.channel) == ("partial", "fake:u2", "chat")


def test_k6_unsigned_or_stale_click_is_401_and_records_nothing(w):
    rid = w.run()
    assert w.click("u1", f"label|{rid}|agree", secret="wrong" + "-secret")[0] == 401
    assert w.click("u1", f"label|{rid}|agree", ts=NOW - timedelta(hours=1))[0] == 401
    assert w.store.list_labels(rid) == []


def test_k6_click_from_an_unknown_user_is_refused_with_200(w):
    rid = w.run()
    assert w.click("stranger", f"label|{rid}|agree")[0] == 200
    assert w.store.list_labels(rid) == []


def test_k6_a_malformed_label_click_is_never_read_as_an_approval(w):
    rid = w.run()
    assert w.click("u1", f"label:{rid}:agree")[0] == 200
    assert w.store.list_labels(rid) == []
    assert w.store.list_approvals({"PENDING", "APPROVED", "REJECTED", "EXPIRED"}) == []


def test_k6_approval_clicks_still_reach_the_approvals(w):
    """Regression: with a measure wired, an approval payload is still handled by the approvals."""
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
    assert w.click("u1", f"{req.approval_id}|h|0|approve")[0] == 200
    assert w.store.get_approval_request(req.approval_id).status == "APPROVED"


def test_k6_reject_is_caught_by_human_reject(w):
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
    w.click("u1", f"{req.approval_id}|h|0|reject")
    decided = [e for e in w.audit.events("run-x") if e.operation == "decide"]
    assert [(e.decision, e.caught_by) for e in decided] == [("reject", "human_reject")]


def test_k6_only_a_line_owner_can_clear_a_demotion(w):
    w.label(w.run(), "harmful")
    value = w.clear_value()
    assert w.click("u1", value)[0] == 200  # a labeller has no admin right
    assert w.store.current_overrides()
    assert [e.result for e in w.audit.events() if e.operation == "clear"] == ["refused"]
    assert w.click("owner", value)[0] == 200
    assert w.store.current_overrides() == {}
    assert [e.kind for e in w.store.list_level_events()] == [
        "demote",
        "clear",
    ]  # nothing is deleted
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "not_demoted")


def test_k6_signed_stop_and_reset_need_their_admin_rights(w):
    assert w.click("u1", "stop")[0] == 200  # a labeller has no admin right
    assert w.click("owner", "stop")[0] == 200  # a line owner holds clear_override, not stop
    assert not w.store.get_kill_switch().on
    assert w.click("ops", "stop")[0] == 200
    assert w.store.get_kill_switch().on and w.store.get_kill_switch().by == "fake:ops"
    assert w.click("u1", "reset")[0] == 200
    assert w.store.get_kill_switch().on  # still stopped
    assert w.click("ops", "reset")[0] == 200
    assert not w.store.get_kill_switch().on
    refused = [e for e in w.audit.events() if e.result == "refused"]
    assert {e.operation for e in refused} == {"stop", "reset"}
    assert (
        measure.parse_action_value("stop|x") is None
        and measure.parse_action_value("reset") is not None
    )


def test_k6_signed_reset_that_cannot_be_audited_does_not_happen(w):
    from hadavin_sdk.audit.protocol import AuditUnavailable

    w.click("ops", "stop")
    w.audit.write_intent = lambda ev: (_ for _ in ()).throw(AuditUnavailable("down"))
    assert w.click("ops", "reset")[0] == 503
    assert w.store.get_kill_switch().on


def test_k6_clear_store_failure_is_a_non_2xx(w):
    w.label(w.run(), "harmful")
    w.store.clear_demotion = lambda ev, seq: (_ for _ in ()).throw(OSError("down"))
    assert w.click("owner", w.clear_value())[0] == 503


# --- abstain labels and the two error rates --------------------------------------------------------------


def test_k6_abstain_label_counted(w):
    rid = w.run(plan=False, state=S.NEEDS_PERSON, reason="tool_error", created=day(7))
    assert w.label(rid, "abstain_ok", when=day(7)).ok
    pw = w.store.pilot_week(WEEK)
    assert (pw.abstain_ok, pw.missed, pw.abstained, pw.labelled) == (1, 0, 1, 1)


def test_k6_missed_counted(w):
    rid = w.run(plan=False, state=S.NO_ACTION, reason=None, created=day(7))
    assert w.label(rid, "missed", when=day(7)).ok
    assert w.store.pilot_week(WEEK).missed == 1
    assert rid in w.store.held_run_ids()  # a miss is held evidence


def test_k6_two_error_rates_reported(w):
    w.labelled("agree", 6, when=day(7))
    w.labelled("wrong", 1, when=day(7))
    for name in ("abstain_ok", "abstain_ok", "abstain_ok", "missed"):
        rid = w.run(plan=False, state=S.NEEDS_PERSON, reason="tool_error", created=day(7))
        w.label(rid, name, when=day(7))
    text = w.measure.render_report(WEEK, NOW)
    wrong_line = next(ln for ln in text.splitlines() if ln.startswith("- Wrong rate on proposals"))
    miss_line = next(ln for ln in text.splitlines() if ln.startswith("- Miss rate on abstentions"))
    assert wrong_line.startswith("- Wrong rate on proposals: 1 of 7 (14%)")
    assert miss_line.startswith("- Miss rate on abstentions: 1 of 4 (25%)")
    assert "accuracy" not in text.lower()  # never blended into one number


# --- csv labels ------------------------------------------------------------------------------------------


def _numbers(w, action=ACTION):
    return measure.numbers_for(
        w.store.list_labels_for("test-agent", action, None),
        w.store.count_proposals("test-agent", action, None),
        NOW,
    )


def test_k6_unapproved_csv_labels_excluded_from_promotion(w):
    ids = [w.run() for _ in range(3)]
    csv_text = "run_id,label\n" + "\n".join(f"{r},agree" for r in ids) + "\n"
    stored, problems = w.measure.import_csv(csv_text, "fake:u1")
    assert (stored, problems) == (3, [])
    assert {x.channel for r in ids for x in w.store.list_labels(r)} == {"csv"}
    assert _numbers(w).labelled == 0  # not evidence yet
    assert w.store.pilot_week(NOW.date() - timedelta(days=NOW.weekday())).labelled == 0
    # The line owner approves: the same file again, now with approved_by.
    stored, problems = w.measure.import_csv(csv_text, "fake:u1", "fake:owner")
    assert (stored, problems) == (3, [])
    assert _numbers(w).labelled == 3 and _numbers(w).agree == 3


def test_k6_csv_import_rules(w):
    ok = w.run()
    assert (
        w.measure.import_csv(f"run_id,label\n{ok},agree\n", "fake:u1", "fake:u2")[0] == 0
    )  # no admin right
    assert (
        "approve_label_import" in w.measure.import_csv("run_id,label\n", "fake:u1", "fake:u2")[1][0]
    )
    assert w.measure.import_csv("run,label\n", "fake:u1")[1] == [
        "the csv header must be exactly: run_id,label"
    ]
    assert w.measure.import_csv("run_id,label\n", "fake:u1")[1] == ["the csv has no rows"]
    # One bad row stores nothing, and every bad row is named.
    stored, problems = w.measure.import_csv(
        f"run_id,label\n{ok},agree\nrun-nope,agree\n{ok},bogus\n", "fake:u1"
    )
    assert stored == 0 and len(problems) == 2 and problems[0].startswith("row 2")
    assert w.store.list_labels(ok) == []
    # Re-importing the same file is not an error and stores nothing twice.
    text = f"run_id,label\n{ok},agree\n"
    assert w.measure.import_csv(text, "fake:u1") == (1, [])
    assert w.measure.import_csv(text, "fake:u1") == (0, [])


def test_k6_a_short_csv_row_is_a_refused_row_not_a_crash(w):
    ok = w.run()
    stored, problems = w.measure.import_csv(f"run_id,label\n{ok}\n,agree\n{ok},agree\n", "fake:u1")
    assert stored == 0 and [p.split(":")[0] for p in problems] == ["row 1", "row 2"]
    assert w.store.list_labels(ok) == []


def test_k6_audit_events_carry_the_measure_clock(w):
    rid = w.run()
    w.label(rid, "wrong", when=day(7))
    (ev,) = [e for e in w.audit.events() if e.operation == "label"]
    assert ev.ts == day(7)  # the report's week of a caught_by count follows the injected clock


def test_k6_a_receiver_on_the_approvals_takes_label_clicks_without_being_told(w):
    rid = w.run()
    approvals = Approvals(w.store, w.audit, w.reg, w.channel, lambda *a: None, lambda: w.box[0])
    body = urlencode(
        {
            "payload": json.dumps(
                {"user": {"id": "u1"}, "actions": [{"value": f"label|{rid}|agree"}]}
            )
        }
    ).encode()
    headers = hmac_v0.sign(body, int(NOW.timestamp()), SECRET, "X-Hadavin")
    assert (
        handle_slack_action(approvals, headers, body)[0] == 401
    )  # no measure wired: not ours to take
    approvals.measure = w.measure  # what app.build does
    assert handle_slack_action(approvals, headers, body)[0] == 200
    assert [x.label for x in w.store.list_labels(rid)] == ["agree"]


def test_k6_csv_labels_can_still_demote(w):
    """A harmful csv label lowers the level at once, approved or not (the safe direction)."""
    rid = w.run()
    assert w.measure.import_csv(f"run_id,label\n{rid},harmful\n", "fake:u1")[0] == 1
    assert w.store.current_overrides() == {("test-agent", ACTION): "shadow"}


# --- promotion evidence ----------------------------------------------------------------------------------


def _replay_record(w, **kw) -> ReplayRecord:
    agent = w.reg.agents["test-agent"]
    rec = ReplayRecord(
        agent_id="test-agent",
        config_hash=w.reg.config_hash("test-agent"),
        model_id=w.reg.config.routes[agent.model_route].model_id,
        prompt_sha256=w.reg.prompt_sha256("test-agent"),
        bundle_sha256="b" * 64,
        k=3,
        pass_k=1.0,
        pass_rate=1.0,
        threshold=0.9,
        green=True,
        ts=day(10),
        **kw,
    )
    with (w.reg.config.root / "replay-records.jsonl").open("a", encoding="utf-8") as f:
        f.write(rec.model_dump_json() + "\n")
    return rec


def _ready(w, action="create_draft_record", agree=26, partial=3, wrong=1):
    """30 labelled proposals: 26 agree, 3 partial, 1 wrong (the minimum that passes)."""
    for name, n in (("agree", agree), ("partial", partial), ("wrong", wrong)):
        w.labelled(
            name, n, when=day(9), action=action, who=("u1", "u2")
        )  # two people, as 6.1 now requires


def test_k6_promote_check_refuses_below_the_numbers(w):
    _replay_record(w)
    _ready(w, agree=10, partial=2, wrong=0)  # 12 labelled, 83 % agree
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert not res.ok and res.path is None
    assert any("labelled 12 < 30" in p for p in res.problems)
    assert not (w.reg.config.root / "promotions").exists()  # nothing was written


@pytest.mark.parametrize(
    ("agree", "partial", "wrong", "harmful", "expect"),
    [
        (20, 10, 0, 0, "agree 67% < 70%"),
        (25, 3, 2, 0, "wrong + harmful 2 > 1"),
        (27, 2, 0, 1, "1 harmful in the last 28 days"),
    ],
)
def test_k6_each_number_is_enforced(w, agree, partial, wrong, harmful, expect):
    _replay_record(w)
    _ready(w, agree=agree, partial=partial, wrong=wrong)
    w.labelled("harmful", harmful, when=day(9), action="create_draft_record")
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert not res.ok and any(expect in p for p in res.problems), res.problems


def test_k6_coverage_below_80_percent_refuses(w):
    _replay_record(w)
    _ready(w)
    for _ in range(9):  # 9 proposals nobody labelled: 30 of 39 = 77 %
        w.run(action="create_draft_record", created=day(9))
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert any("coverage 77% < 80%" in p for p in res.problems)


def test_k6_harmful_older_than_four_weeks_does_not_block(w):
    _replay_record(w)
    _ready(w, agree=27, partial=2, wrong=0)
    w.labelled(
        "harmful", 1, when=day(35), action="create_draft_record"
    )  # 1 wrong+harmful is allowed
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert not any("harmful in the last" in p for p in res.problems)


def test_k6_promote_check_refuses_without_replay_record(w):
    _ready(w)
    qualify(
        w.reg
    )  # a gate run is not a replay record, and a later gate run never hides or replaces one
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert not res.ok and res.path is None
    assert [p for p in res.problems if "no green replay record" in p]
    assert not (w.reg.config.root / "promotions").exists()
    # A record for another prompt does not count either.
    stale = _replay_record(w)
    path = w.reg.config.root / "replay-records.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(
        "\n".join(ln.replace(stale.prompt_sha256, "0" * 64) for ln in lines) + "\n",
        encoding="utf-8",
    )
    assert not w.measure.promote_check("test-agent", "create_draft_record").ok


def test_k6_promote_check_writes_the_file_and_the_loader_accepts_it(w):
    _replay_record(w)
    _ready(w)
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert res.ok, res.problems
    body = json.loads(res.path.read_text(encoding="utf-8"))
    assert body["numbers"]["labelled"] == 30 and body["numbers"]["agree"] == 26
    assert body["config_hash"] == w.reg.config_hash("test-agent")
    assert body["replay_record"]["bundle_sha256"] == "b" * 64 and re.fullmatch(
        r"[0-9a-f]{64}", body["sha256"]
    )
    assert measure.promotion_problems(w.reg, "test-agent", "create_draft_record") == []


def test_k6_promote_check_file_still_matches_after_a_level_only_flip(w):
    _replay_record(w)
    _ready(w)
    assert w.measure.promote_check("test-agent", "create_draft_record").ok
    agents = w.cfg / "agents.yaml"
    data = yaml.safe_load(agents.read_text(encoding="utf-8"))
    data[0]["levels"] = {"create_draft_record": "suggest"}  # the promotion PR changes only this
    agents.write_text(yaml.safe_dump(data), encoding="utf-8")
    flipped = load_registry(load_config(w.cfg))
    assert flipped.config_hash("test-agent") == w.reg.config_hash("test-agent")
    assert measure.promotion_problems(flipped, "test-agent", "create_draft_record") == []


def test_k6_loader_refuses_a_missing_edited_or_stale_promotion_file(w):
    assert (
        "needs promotions/test-agent.create_draft_record.json"
        in measure.promotion_problems(w.reg, "test-agent", "create_draft_record")[0]
    )
    _replay_record(w)
    _ready(w)
    path = w.measure.promote_check("test-agent", "create_draft_record").path
    good = json.loads(path.read_text(encoding="utf-8"))

    def problems_with(**change):
        body = {**good, **change}
        if "sha256" not in change:
            body["sha256"] = measure._file_sha(
                body
            )  # a file re-sealed by someone with write access
        path.write_text(json.dumps(body), encoding="utf-8")
        return measure.promotion_problems(w.reg, "test-agent", "create_draft_record")

    assert any("edited" in p for p in problems_with(sha256="0" * 64))
    assert any("config_hash does not match" in p for p in problems_with(config_hash="0" * 64))
    assert any("prompt_sha256 does not match" in p for p in problems_with(prompt_sha256="0" * 64))
    assert any(
        "labelled 5 < 30" in p for p in problems_with(numbers={**good["numbers"], "labelled": 5})
    )
    assert any("ceiling breached" in p for p in problems_with(ceiling={"breached": True}))
    path.write_text("not json", encoding="utf-8")
    assert any(
        "not valid JSON" in p
        for p in measure.promotion_problems(w.reg, "test-agent", "create_draft_record")
    )
    path.write_text("[]", encoding="utf-8")
    assert any(
        "not a JSON object" in p
        for p in measure.promotion_problems(w.reg, "test-agent", "create_draft_record")
    )
    assert measure.promotion_problems(w.reg, "../x", "a")[0].endswith(
        "cannot name a promotion file"
    )


def test_k6_promote_check_other_refusals(w):
    assert not w.measure.promote_check("test-agent", "no_such_action").ok
    _replay_record(w)
    _ready(w, action=ACTION)
    res = w.measure.promote_check("test-agent", ACTION)
    assert any(
        "none contract" in p for p in res.problems
    )  # R1: a none contract is never promotable
    _ready(w)
    w.label(w.run(action="create_draft_record"), "harmful")
    assert any(
        "is demoted" in p
        for p in w.measure.promote_check("test-agent", "create_draft_record").problems
    )
    bare = Measure(w.store, w.audit, w.reg, w.channel, ceiling=None)
    with pytest.raises(BaseConfigError, match="baseline.yaml is required"):
        bare.promote_check("test-agent", "create_draft_record")


def test_k6_low_volume_thresholds_are_one_object():
    t = DEFAULT_POLICY.thresholds()
    assert (
        t.min_labelled,
        t.min_agree,
        t.max_wrong_harmful,
        t.harmful_window_days,
        t.min_coverage,
    ) == (
        30,
        0.70,
        1,
        28,
        0.80,
    )


# --- the ceiling -----------------------------------------------------------------------------------------


def test_k6_report_states_ceiling(w):
    w.labelled("agree", 2, when=day(7))
    w.labelled("harmful", 1, when=day(7))
    text = w.measure.render_report(WEEK, NOW)
    assert "ceiling: 1 of 3 in the last 90 days, breached yes" in text
    assert "Promotion is blocked" in text


def test_k6_report_says_no_breach_when_inside(w):
    w.labelled("agree", 4, when=day(7))
    assert "ceiling: 0 of 4 in the last 90 days, breached no" in w.measure.render_report(WEEK, NOW)


def test_k6_ceiling_breach_demotes_what_can_be_demoted_and_tells_the_owner(w):
    _suggest_world(
        w
    )  # only create_draft_record is at suggest: the only thing a breach has to demote
    w.labelled("agree", 2, when=day(7), action="create_draft_record")
    w.labelled("harmful", 1, when=day(5), action="create_draft_record")
    # the harmful label itself triggered the check (no waiting for the tick): the rows are already there
    assert w.measure.enforce(NOW) == []
    rows = [e for e in w.store.list_level_events() if e.reason.startswith("ceiling:")]
    assert {(e.agent_id, e.action_id) for e in rows} == {
        ("test-agent", "create_draft_record")
    }  # not the shadow ones
    assert any(
        who == "fake:owner" and "Ceiling breached: 1 of 3" in text
        for who, text in w.channel.notices
    )
    # Idempotent: a second pass inserts nothing and does not notify again.
    n = len(w.channel.notices)
    assert w.measure.enforce(NOW) == [] and len(w.channel.notices) == n


def test_k6_a_shadow_only_pilot_breaches_without_writing_a_demotion_row(w):
    w.labelled("harmful", 1, when=day(5))  # every action is at shadow: nothing to demote
    assert w.measure.ceiling_status(NOW).breached
    w.measure.enforce(NOW)
    assert [e for e in w.store.list_level_events() if e.reason.startswith("ceiling:")] == []
    assert any(
        "Ceiling breached" in text for _, text in w.channel.notices
    )  # but the owner is told, once
    n = len(w.channel.notices)
    w.measure.enforce(NOW)
    assert len(w.channel.notices) == n


def test_k6_a_ceiling_demotion_cannot_be_cleared_while_the_ceiling_is_breached(w):
    _suggest_world(w)
    w.labelled("harmful", 1, when=day(5), action="create_draft_record")
    w.measure.enforce(NOW)
    pair = ("test-agent", "create_draft_record")
    # "Every action at suggest is shadow" is what the breach notice said, so it must stay true until it is over.
    assert w.measure.clear("fake:owner", *pair) == (200, "ceiling_breached")
    assert pair in w.store.current_overrides()
    assert [
        e.error_code for e in w.audit.events() if e.operation == "clear" and e.result == "refused"
    ] == ["ceiling_breached"]
    # The sponsor raises max in writing: the breach is over; clearing then meets the next guard (the evidence).
    w.measure.ceiling = Ceiling(CEIL.metric, 1, CEIL.window_days, CEIL.source)
    assert w.measure.clear("fake:owner", *pair) == (200, "evidence_below_6_1")


def _suggest_world(w):
    """The config now says suggest for create_draft_record (a level-only change)."""
    agents = w.cfg / "agents.yaml"
    data = yaml.safe_load(agents.read_text(encoding="utf-8"))
    data[0]["levels"] = {"create_draft_record": "suggest"}
    agents.write_text(yaml.safe_dump(data), encoding="utf-8")
    w.measure.registry = load_registry(load_config(w.cfg))


def test_k6_a_suggest_action_is_not_cleared_until_the_numbers_hold_again(w):
    _replay_record(w)
    _ready(w)
    _suggest_world(w)
    w.measure.ceiling = Ceiling(
        CEIL.metric, 5, CEIL.window_days, CEIL.source
    )  # isolate the numbers check
    bad = w.run(action="create_draft_record")
    assert w.label(
        bad, "harmful"
    ).demoted  # 30 earned labels, then one harmful: wrong + harmful is now 2
    assert w.measure.clear("fake:owner", "test-agent", "create_draft_record") == (
        200,
        "evidence_below_6_1",
    )
    assert w.measure.promotion_store_problems()  # and the start-up check says so too
    # The owner corrects the mislabel (audited, and visible in the report); the numbers hold again.
    assert w.label(bad, "agree", who="owner", when=NOW + timedelta(seconds=1)).ok
    assert w.measure.clear("fake:owner", "test-agent", "create_draft_record") == (200, "cleared")


def test_k6_ceiling_window_rolling(w):
    """A breach 91 days ago does not count; a shadow-only breach blocks promote-check and changes no level."""
    w.labelled("harmful", 1, when=day(91))
    old = w.measure.ceiling_status(NOW)
    assert (old.harmful, old.breached) == (0, False)
    assert w.measure.enforce(NOW) == []
    w.labelled("harmful", 1, when=day(89))
    now_in = w.measure.ceiling_status(NOW)
    assert (now_in.harmful, now_in.breached) == (1, True)
    # Shadow-only pilot: every action is already shadow, so nothing changes in effect; promotion is blocked.
    assert w.measure.level_override("test-agent", ACTION) == "shadow"
    _replay_record(w)
    _ready(w)
    res = w.measure.promote_check("test-agent", "create_draft_record")
    assert any("ceiling breached" in p for p in res.problems) and res.path is None
    # The window moves on: 91 days later the breach no longer counts.
    later = NOW + timedelta(days=2)
    assert w.measure.ceiling_status(later).breached is False


def test_k6_sponsor_raising_max_unblocks(w):
    w.labelled("harmful", 1, when=day(5))
    assert w.measure.ceiling_status(NOW).breached
    w.measure.ceiling = Ceiling(
        CEIL.metric, 1, CEIL.window_days, CEIL.source
    )  # in writing, then copied
    assert not w.measure.ceiling_status(NOW).breached


def test_k6_enforce_catches_three_wrong_that_raced(w):
    """Two labels that each saw two wrongs stored a third unseen: the tick re-check demotes."""
    ids = [w.run() for _ in range(3)]
    for rid in ids:  # bypass the label-time check, as a race would
        w.store.add_labels([(measure_label(rid, "wrong", NOW), None)], may_lower_harmful=True)
    assert w.store.current_overrides() == {}
    assert len(w.measure.enforce(NOW)) == 1
    assert w.store.current_overrides() == {("test-agent", ACTION): "shadow"}
    assert w.measure.enforce(NOW) == []


def measure_label(rid, name, when):

    return Label(run_id=rid, label=name, principal_id="fake:u1", channel="chat", created_at=when)


# --- baseline.yaml ---------------------------------------------------------------------------------------


def _baseline(tmp_path, text):
    (tmp_path / "baseline.yaml").write_text(text, encoding="utf-8")
    return tmp_path


def _ceiling(**over):
    fields = {
        "metric": "m",
        "counts": "[harmful]",
        "max": "2",
        "window_days": "30",
        "source": "s",
        **over,
    }
    return "ceiling:\n" + "".join(f"  {k}: {v}\n" for k, v in fields.items() if v is not None)


def test_k6_baseline_loads_a_filled_ceiling(tmp_path):
    root = _baseline(tmp_path, _ceiling())
    assert measure.load_baseline(root) == Ceiling("m", 2, 30, "s", ("harmful",))
    root = _baseline(tmp_path, _ceiling(counts="[harmful, wrong, harmful]"))
    assert measure.load_baseline(root).counts == ("harmful", "wrong")


@pytest.mark.parametrize(
    ("text", "error"),
    [
        (None, "does not exist"),
        ("project: x\n", "`ceiling` is required"),
        ("ceiling: yes\n", "`ceiling` is required"),
        (_ceiling(metric="<ceiling metric>"), "ceiling.metric"),
        (_ceiling(max="<ceiling max>"), "ceiling.max"),
        (_ceiling(source=""), "ceiling.source"),
        (_ceiling(window_days=None), "ceiling.window_days is missing"),  # no default window
        (_ceiling(window_days="<ceiling window days>"), "ceiling.window_days"),
        (_ceiling(counts=None), "ceiling.counts is required"),  # no default counts
        (_ceiling(counts="[]"), "ceiling.counts is required"),
        (_ceiling(counts="harmful"), "ceiling.counts is required"),  # a list, not a bare word
        (_ceiling(counts="<ceiling counts>"), "ceiling.counts is required"),
        (_ceiling(counts="[wrong]"), "must include harmful"),
        (_ceiling(counts="[harmful, nonsense]"), "unknown labels: nonsense"),
        (_ceiling(max="lots"), "whole numbers"),
        (_ceiling(max="-1"), ">= 0"),
        (_ceiling(window_days="0"), ">= 0 and window_days >= 1"),
        (": : :\n  - [", "cannot be read"),
    ],
)
def test_k6_baseline_refusals(tmp_path, text, error):
    if text is not None:
        _baseline(tmp_path, text)
    with pytest.raises(BaseConfigError, match=re.escape(error)):
        measure.load_baseline(tmp_path)


def test_k6_the_refusal_points_at_scoping_md(tmp_path):
    _baseline(tmp_path, _ceiling(counts=None))
    with pytest.raises(BaseConfigError, match=r"scoping\.md `## Success metric and ceiling`"):
        measure.load_baseline(tmp_path)


def _subsets(items):
    for mask in range(1 << len(items)):
        yield [x for i, x in enumerate(items) if mask >> i & 1]


@pytest.mark.parametrize("counts", [c for c in _subsets(list(measure.LABELS)) if c])
def test_k6_any_counts_containing_harmful_loads_and_any_without_it_is_refused(tmp_path, counts):
    _baseline(tmp_path, _ceiling(counts="[" + ", ".join(counts) + "]"))
    if "harmful" in counts:
        assert set(measure.load_baseline(tmp_path).counts) == set(counts)
    else:
        with pytest.raises(BaseConfigError, match="must include harmful"):
            measure.load_baseline(tmp_path)


def test_k6_the_ceiling_counts_exactly_the_configured_classes(w):
    w.labelled("harmful", 1, when=day(5))
    w.labelled("wrong", 2, when=day(5))
    w.labelled("partial", 1, when=day(5))
    silent = w.run(plan=False, state=S.NO_ACTION, reason=None, created=day(5))
    w.label(silent, "missed", when=day(5))
    expected = {
        ("harmful",): 1,
        ("harmful", "wrong"): 3,
        ("harmful", "missed"): 2,
        ("harmful", "wrong", "partial", "missed"): 5,
    }
    for counts, n in expected.items():
        w.measure.ceiling = Ceiling("m", 0, 90, "s", counts)
        status = w.measure.ceiling_status(NOW)
        assert (status.harmful, status.labelled) == (n, 5), counts
        pw = w.store.pilot_week(NOW.date() - timedelta(days=NOW.weekday() + 7))
        assert pw.count_of(counts) == n, counts  # the weekly numbers use the same classes
    text = w.measure.render_report(WEEK, NOW)
    assert "counting: harmful, wrong, partial, missed" in text
    assert "counted by the ceiling this week: 5 (harmful, wrong, partial, missed)" in text


def test_k6_a_wrong_label_breaches_a_ceiling_that_counts_wrong(w):
    w.labelled("wrong", 1, when=day(5))
    assert not w.measure.ceiling_status(NOW).breached  # [harmful] only
    w.measure.ceiling = Ceiling("m", 0, 90, "s", ("harmful", "wrong"))
    assert w.measure.ceiling_status(NOW).breached


def _pilot_build(tmp_path, dsn, *, no_owner=False, drop_baseline=False):
    from tests.test_k3_pilot_env import _spy, pilot_cfg

    cfg = pilot_cfg(tmp_path, no_owner=no_owner)
    if drop_baseline:
        (cfg / "baseline.yaml").unlink()
    qualify(load_registry(load_config(cfg)), "ito-agent")
    return app_mod.build(
        cfg,
        ["ito-agent"],
        secrets=_spy(dsn, []),
        channel=FakeChannel(SECRET),
        llm=ScriptedLLM(),
    )


def test_k6_pilot_build_refuses_without_a_ceiling(tmp_path):
    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        with pytest.raises(BaseConfigError, match="baseline.yaml is required in pilot and prod"):
            _pilot_build(tmp_path, dsn, drop_baseline=True)


def test_k6_pilot_build_refuses_without_a_line_owner(tmp_path):
    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        with pytest.raises(BaseConfigError, match="at least one person must hold .*clear_override"):
            _pilot_build(tmp_path, dsn, no_owner=True)


def test_k6_pilot_build_with_both_starts_and_wires_measure(tmp_path):
    from tests.contracts.kinds.store_postgres import pg_schema

    for dsn in pg_schema():
        app = _pilot_build(tmp_path, dsn)
        assert app.measure.line_owners() == ["slack:UOWNER"]
        assert app.measure.ceiling is not None and app.approvals.measure is app.measure
        app.store._db.close()


# --- the weekly report -----------------------------------------------------------------------------------


def test_k6_report_prints_backlog(w):
    text = w.measure.render_report(WEEK, NOW)
    assert "## Backlog" not in text  # without K4 nothing is printed
    detail = {
        "week": WEEK.isoformat(),
        "max_oldest_received_age_s": 840,
        "late_starts": 2,
        "late_threshold_s": 600,
        "events_received_count": 3,
    }
    w.store.save_tick_state(TickState(step="backlog", last_run_at=NOW, detail=detail))
    text = w.measure.render_report(WEEK, NOW)
    assert "## Backlog" in text
    assert (
        "Maximum oldest_received_age_s: 840" in text
    )  # the weekly maximum K4 recorded, verbatim key
    assert "later than 10 minutes (K4's threshold): 2" in text  # counted against K4's own threshold
    # A row for another week is not this week's: the report says so instead of printing it.
    w.store.save_tick_state(
        TickState(step="backlog", last_run_at=NOW, detail={**detail, "week": "2026-10-19"})
    )
    other = w.measure.render_report(WEEK, NOW)
    assert "were not recorded" in other and "840" not in other
    # A backlog row with no detail prints nothing.
    w.store.save_tick_state(TickState(step="backlog", last_run_at=NOW))
    assert "## Backlog" not in w.measure.render_report(WEEK, NOW)


def test_k6_report_lists_golden_candidates(tmp_path):
    held = {"run-001", "run-003"}
    w = World(tmp_path, has_evidence=lambda rid: rid in held)
    wrong = w.run(created=day(7))
    missed = w.run(plan=False, state=S.NO_ACTION, reason=None, created=day(7))
    no_evidence = w.run(created=day(7))
    fine = w.run(created=day(7))
    w.label(wrong, "wrong", when=day(7))
    w.label(missed, "missed", when=day(7))
    w.label(no_evidence, "wrong", when=day(7))
    w.label(fine, "agree", when=day(7))
    text = w.measure.render_report(WEEK, NOW)
    assert re.search(
        r"test-agent: golden set: \d+ items, version [0-9a-f]{8}, candidates this week: 2", text
    )
    golden = text.split("## Golden set")[1].split("## Held")[0]
    assert "  - run-001" in golden and "  - run-003" in golden  # the wrong one and the missed one
    assert "run-002" not in golden and "run-004" not in golden  # no held evidence / labelled agree


def test_k6_candidates_need_k5_evidence_and_are_zero_before_it(w):
    rid = w.run(created=day(7))
    w.label(rid, "wrong", when=day(7))
    assert (
        w.measure.golden_candidates(day(8), day(0)) == []
    )  # no tool_calls store yet: nothing is held

    class WithCalls(MemoryStore):
        def list_tool_calls(self, run_id):
            return [object()] if run_id == rid else []

    w.store.list_tool_calls = WithCalls().list_tool_calls
    assert w.measure.golden_candidates(day(8), day(0)) == [rid]


def test_k6_hold_run_ids_are_the_wrong_harmful_and_missed_runs(w):
    a, b, c, d = (w.run() for _ in range(4))
    silent = w.run(plan=False, state=S.NO_ACTION, reason=None)
    for rid, name in (
        (a, "wrong"),
        (b, "harmful"),
        (c, "agree"),
        (d, "partial"),
        (silent, "missed"),
    ):
        w.label(rid, name)
    assert w.measure.hold_run_ids() == {a, b, silent}


def test_k6_report_lists_wrong_harmful_holds_and_flags(w):
    w.labelled("agree", 3, when=day(7))
    bad = w.labelled("wrong", 2, when=day(7))
    harmful = w.labelled("harmful", 1, when=day(7))
    text = w.measure.render_report(WEEK, NOW)
    for rid in (*bad, *harmful):
        assert f"- {rid}: " in text
    assert "FLAG: label coverage" not in text  # 6 of 6 proposals labelled
    w.run(created=day(7))
    w.run(created=day(7))  # two unlabelled proposals: 6 of 8 = 75 %
    text = w.measure.render_report(WEEK, NOW)
    assert "FLAG: label coverage 75% is below 80%" in text
    assert "FLAG: wrong labels rose from 0 to 2" in text  # the week before had none
    assert "## Held runs" in text and "purged at the retention maximum" in text  # K5 owns the dates
    assert "test-agent.restart_service: labelled n=6" in text
    assert "UTC /" in text and "IST" in text
    assert "not recorded yet" in text  # K4 failed events and K7 commit SHAs are stated as absent


def test_k6_report_counts_caught_by(w):
    w.label(w.run(created=day(7)), "wrong", when=day(7))
    w.audit.write_outcome(measure_event(day(7), "guard"))
    text = w.measure.render_report(WEEK, NOW)
    assert "- human_label: 1" in text and "- guard: 1" in text


def measure_event(when, caught, run="r"):
    return AuditEvent(
        ts=when,
        run_id=run,
        domain="runtime",
        operation="x",
        principal="p",
        source="s",
        caught_by=caught,
    )


def test_k6_caught_week_twin(w):
    events = [
        measure_event(day(7), "gate", "r1"),
        measure_event(day(7), "gate", "r2"),
        measure_event(day(7), "gate", "r2"),  # the same run caught twice counts once
        measure_event(day(14), "guard"),
    ]
    events.append(measure_event(day(7), None))
    assert measure.caught_week(events, WEEK) == {"gate": 2}


def test_k6_relabelling_a_run_does_not_count_it_caught_twice(w):
    rid = w.run(created=day(7))
    w.label(rid, "wrong", when=day(7))
    w.label(rid, "wrong", who="u2", when=day(7))
    w.label(rid, "harmful", who="u3", when=day(7))
    assert "- human_label: 1" in w.measure.render_report(WEEK, NOW)


def test_k6_weekly_report_writes_once_and_tells_the_line_owner(w):
    w.labelled("agree", 3, when=day(7))
    body = w.measure.weekly_report(NOW)
    assert body and w.store.get_report(WEEK) == body
    (who, text), *rest = w.channel.notices
    assert who == "fake:owner" and not rest
    assert "Pilot report for the week of 2026-10-26" in text and "- Runs: 3" in text
    assert w.measure.weekly_report(NOW + timedelta(hours=3)) is None  # the week has its report
    assert len(w.channel.notices) == 1
    assert (
        w.measure.weekly_report(NOW + timedelta(days=7)) is not None
    )  # the next week gets its own


def test_k6_a_report_nobody_was_told_about_is_not_stored_and_is_retried(w):
    real = w.channel.notify
    w.channel.notify = lambda who, text: (_ for _ in ()).throw(OSError("channel down"))
    with pytest.raises(RuntimeError, match="not announced"):
        w.measure.weekly_report(NOW)
    assert (
        w.store.get_report(WEEK) is None
    )  # the week still has no report, so the next tick tries again
    w.channel.notify = real
    assert w.measure.weekly_report(NOW + timedelta(hours=1))
    assert w.store.get_report(WEEK) and len(w.channel.notices) == 1


def test_k6_a_report_with_no_line_owner_is_an_error_not_a_silent_store(tmp_path):
    w = World(tmp_path)
    w.reg.principals["fake:owner"] = Principal(id="fake:owner", kind="person")
    assert w.measure.line_owners() == []
    with pytest.raises(RuntimeError, match="not announced"):
        w.measure.weekly_report(NOW)
    assert w.store.get_report(WEEK) is None


def test_k6_without_a_ceiling_there_is_no_report(tmp_path):
    w = World(tmp_path, ceiling=None)
    assert w.measure.weekly_report(NOW) is None and w.store.get_report(WEEK) is None
    assert w.measure.ceiling_status() is None


def test_k6_tick_runs_the_report_once_per_week(tmp_path):
    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    (cfg / "baseline.yaml").write_text(
        "ceiling:\n  metric: m\n  counts: [harmful]\n  max: 0\n  window_days: 90\n  source: s\n",
        encoding="utf-8",
    )
    path = cfg / "principals.yaml"
    people = yaml.safe_load(path.read_text(encoding="utf-8"))
    people.append({"id": "fake:owner", "kind": "person", "admin_rights": ["clear_override"]})
    path.write_text(yaml.safe_dump(people), encoding="utf-8")
    reg = load_registry(load_config(cfg))
    qualify(reg)
    channel = FakeChannel(SECRET)
    app = app_mod.build(cfg, ["test-agent"], channel=channel, llm=ScriptedLLM(), secrets=SECRETS)
    assert app.measure is not None and app.measure.ceiling == Ceiling("m", 0, 90, "s")
    assert run_tick(app, NOW) == 0
    assert app.store.get_report(WEEK) is not None and len(channel.notices) == 1
    assert run_tick(app, NOW + timedelta(hours=2)) == 0
    assert len(channel.notices) == 1
    assert {s for s in ("measure_levels", "weekly_report") if app.store.get_tick_state(s)} == {
        "measure_levels",
        "weekly_report",
    }


def test_k6_tick_keeps_a_step_detail_and_saves_a_new_one(tmp_path):
    from hadavin_sdk.runtime.tick import TickStep

    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    qualify(load_registry(load_config(cfg)))
    app = app_mod.build(
        cfg, ["test-agent"], channel=FakeChannel(SECRET), llm=ScriptedLLM(), secrets=SECRETS
    )

    def backlog(ctx):
        ctx.detail["backlog"] = {"oldest_received_age_s": 7}

    assert run_tick(app, NOW, steps=[TickStep("backlog", 0, backlog)]) == 0
    assert app.store.get_tick_state("backlog").detail == {"oldest_received_age_s": 7}
    assert run_tick(app, NOW, steps=[TickStep("backlog", 0, lambda ctx: None)]) == 0
    assert app.store.get_tick_state("backlog").detail == {"oldest_received_age_s": 7}  # kept


# --- wiring ----------------------------------------------------------------------------------------------


def test_k6_build_wires_the_override_and_the_hold_seam(tmp_path, monkeypatch):
    monkeypatch.setattr(Hooks, "hold_run_ids", None, raising=False)  # what K5-core adds
    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    qualify(load_registry(load_config(cfg)))
    app = app_mod.build(
        cfg, ["test-agent"], channel=FakeChannel(SECRET), llm=ScriptedLLM(), secrets=SECRETS
    )
    hooks = app.runtime.hooks
    assert hooks.level_override == app.measure.level_override
    assert hooks.hold_run_ids == app.measure.hold_run_ids  # K5's purge calls this
    assert hooks.hold_run_ids() == set()


def test_k6_build_works_before_k5_has_the_hold_field(tmp_path):
    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    qualify(load_registry(load_config(cfg)))
    app = app_mod.build(
        cfg, ["test-agent"], channel=FakeChannel(SECRET), llm=ScriptedLLM(), secrets=SECRETS
    )
    assert app.measure is not None
    assert (
        app.measure.ceiling is None
    )  # dev without baseline.yaml: the report is off, nothing else is


def test_k6_demoted_action_shadows_a_run_end_to_end(tmp_path):
    """The loop reads the override: a suggest-level action that was demoted ends as a shadow card."""
    cfg = dev_cfg(tmp_path, {"create_draft_record": "suggest"})
    qualify(load_registry(load_config(cfg)))
    propose = ToolCall(name="create_draft_record", input={"title": "Desk", "amount": "9.50"})
    channel = FakeChannel(SECRET)
    app = app_mod.build(
        cfg,
        ["test-agent"],
        channel=channel,
        llm=ScriptedLLM(reply(propose), reply(propose)),
        secrets=SECRETS,
    )
    first = app.runtime.handle("test-agent", "svc:test-agent", b"a")
    assert first.state == S.WAITING_FOR_APPROVAL  # suggest: a person is asked
    assert channel.cards == []
    app.store.add_level_event(
        LevelEvent(
            agent_id="test-agent",
            action_id="create_draft_record",
            kind="demote",
            reason="t",
            by="u",
        )
    )
    second = app.runtime.handle("test-agent", "svc:test-agent", b"b")
    assert (second.state, second.reason_code) == (S.NO_ACTION, "shadow")  # demoted: only a card
    (card,) = channel.cards
    assert card.text.startswith("Agent's view: not checked, do not run")


def test_k6_load_refuses_suggest_in_pilot_without_the_file(tmp_path):
    from tests.test_k3_pilot_env import pilot_cfg

    cfg = pilot_cfg(tmp_path, agent={"levels": {"restart_service": "suggest"}})
    with pytest.raises(ConfigError) as err:
        load_registry(load_config(cfg))
    assert "cannot load before K8" in str(err.value)
    assert "needs promotions/ito-agent.restart_service.json" in str(err.value)
    assert deferred.LIVE == ("pilot", "prod")


# --- independent review: demotion keys, sticky harmful, forged evidence, approvals, report ------------------


def test_k6_harmful_after_a_clear_demotes_again(w):
    rid = w.run()
    assert w.label(rid, "harmful").demoted
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "cleared")
    assert w.label(rid, "agree", who="owner").ok  # only a line owner can lower a harmful label
    assert w.store.current_overrides() == {}
    assert w.label(rid, "harmful").demoted  # a new harmful label is a new fact
    assert ("test-agent", ACTION) in w.store.current_overrides()
    assert [e.kind for e in w.store.list_level_events()] == ["demote", "clear", "demote"]


def test_k6_a_wrong_episode_after_a_clear_demotes_again(w):
    w.labelled("wrong", 3, when=day(2))
    assert ("test-agent", ACTION) in w.store.current_overrides()
    w.measure.clear("fake:owner", "test-agent", ACTION)
    assert w.measure.enforce(NOW) == []  # the same three wrongs do not demote twice
    assert w.label(w.run(), "wrong").demoted  # a newer wrong makes a new episode
    assert [e.kind for e in w.store.list_level_events()] == ["demote", "clear", "demote"]


def test_k6_harmful_is_sticky_and_only_a_line_owner_lowers_it(w):
    rid = w.run()
    w.label(rid, "harmful")
    res = w.label(rid, "agree", who="u2")
    assert (res.ok, res.reason) == (False, "harmful_is_sticky")
    assert [x.label for x in w.store.list_labels(rid)] == ["harmful"]
    assert w.measure.ceiling_status(NOW).harmful == 1  # the refused label changed nothing
    refused = [e for e in w.audit.events() if e.result == "refused" and e.operation == "label"]
    assert [e.error_code for e in refused] == ["harmful_is_sticky"]
    assert w.label(rid, "agree", who="owner", when=NOW + timedelta(seconds=1)).ok
    assert w.measure.ceiling_status(NOW + timedelta(seconds=2)).harmful == 0
    assert any(e.operation == "harmful_lowered" for e in w.audit.events())
    other = w.run()  # a wrong label is not sticky: people may correct themselves
    w.label(other, "wrong")
    assert w.label(other, "agree", who="u2").ok


def test_k6_a_csv_import_cannot_be_approved_by_its_author(w):
    ids = [w.run() for _ in range(3)]
    text = "run_id,label\n" + "".join(f"{r},agree\n" for r in ids)
    assert w.measure.import_csv(text, "fake:owner", "fake:owner")[1] == [
        "an import cannot be approved by the person who made it"
    ]
    assert all(w.store.list_labels(r) == [] for r in ids)


def test_k6_csv_import_is_approved_by_a_signed_click(w):
    ids = [w.run() for _ in range(3)]
    text = "run_id,label\n" + "".join(f"{r},agree\n" for r in ids)
    assert w.measure.import_csv(text, "fake:u1")[0] == 3
    iid = measure.csv_import_id(text)
    (card,) = w.channel.cards
    values = [b["value"] for blk in card.blocks if blk["kind"] == "buttons" for b in blk["buttons"]]
    assert values == [f"approve_import|{iid}"]
    assert _numbers(w).labelled == 0
    assert w.measure.approve_import("fake:u2", iid) == (200, "not_authorised")  # no admin right
    assert (
        w.click("owner", f"approve_import|{iid}")[0] == 200
    )  # signed, and the owner is not the author
    assert _numbers(w).labelled == 3
    assert w.measure.approve_import("fake:owner", "0" * 8) == (200, "unknown_import")
    assert measure.parse_action_value("approve_import|XYZ") is None


def test_k6_nobody_approves_their_own_signed_import(w):
    rid = w.run()
    text = f"run_id,label\n{rid},agree\n"
    w.measure.import_csv(text, "fake:owner")
    assert w.measure.approve_import("fake:owner", measure.csv_import_id(text)) == (
        200,
        "cannot_approve_own_import",
    )
    assert _numbers(w).labelled == 0


def test_k6_admin_rights_need_a_person(w):
    w.reg.principals["svc:bot"] = Principal(
        id="svc:bot",
        kind="service",
        admin_rights=["clear_override", "stop", "approve_label_import"],
    )
    w.label(w.run(), "harmful")
    assert w.measure.clear("svc:bot", "test-agent", ACTION) == (200, "not_authorised")
    assert w.measure.kill_switch("svc:bot", "stop") == (200, "not_authorised")
    assert w.measure.approve_import("svc:bot", "0" * 8) == (200, "not_authorised")
    assert "svc:bot" not in w.measure.line_owners()


def test_k6_the_ceiling_counts_harmful_labels_of_retired_agents(w):
    w.label(w.run(), "harmful", when=day(5))
    agent = w.reg.agents["test-agent"]
    w.reg.agents["test-agent"] = agent.model_copy(update={"status": "retired"})
    assert w.measure._pairs() == []
    status = w.measure.ceiling_status(NOW)
    assert (status.harmful, status.breached) == (1, True)


def test_k6_the_report_lists_only_eligible_latest_wrong_labels(w):
    kept, corrected, unapproved = (w.run(created=day(7)) for _ in range(3))
    w.label(kept, "wrong", when=day(7))
    w.label(corrected, "wrong", when=day(7))
    w.label(corrected, "agree", who="u2", when=day(7, 13))
    w.box[0] = day(7)
    assert w.measure.import_csv(f"run_id,label\n{unapproved},wrong\n", "fake:u1")[0] == 1
    w.box[0] = NOW
    listed = w.measure.render_report(WEEK, NOW).split("## Every wrong and harmful label")[1]
    listed = listed.split("##")[0]
    assert f"- {kept}: wrong" in listed
    assert corrected not in listed and unapproved not in listed


# --- promotion evidence cannot be forged by re-sealing the file ---------------------------------------------


def test_k6_a_promotion_file_with_a_valid_seal_but_no_replay_record_is_refused(w):
    _replay_record(w)
    _ready(w)
    assert w.measure.promote_check("test-agent", "create_draft_record").ok
    records = w.reg.config.root / "replay-records.jsonl"
    saved = records.read_text(encoding="utf-8")
    records.unlink()
    problems = measure.promotion_problems(w.reg, "test-agent", "create_draft_record")
    assert any("names a replay record" in p for p in problems)
    records.write_text(saved, encoding="utf-8")
    assert measure.promotion_problems(w.reg, "test-agent", "create_draft_record") == []
    # A record for the same agent but a different bundle is not the one the file names.
    other = saved.replace("b" * 64, "c" * 64)
    records.write_text(other, encoding="utf-8")
    assert any(
        "names a replay record" in p
        for p in measure.promotion_problems(w.reg, "test-agent", "create_draft_record")
    )


def test_k6_a_resealed_file_with_invented_numbers_is_caught_by_the_store(w):
    _replay_record(w)
    _ready(w)
    path = w.measure.promote_check("test-agent", "create_draft_record").path
    forged = json.loads(path.read_text(encoding="utf-8"))
    forged["action_id"] = "lookup_record"  # an action nobody has labelled
    forged["numbers"] = {**forged["numbers"], "labelled": 90, "proposals": 90}
    forged["sha256"] = measure._file_sha(forged)
    (path.parent / "test-agent.lookup_record.json").write_text(json.dumps(forged), encoding="utf-8")
    agents = w.cfg / "agents.yaml"
    data = yaml.safe_load(agents.read_text(encoding="utf-8"))
    data[0]["levels"] = {"lookup_record": "suggest"}
    agents.write_text(yaml.safe_dump(data), encoding="utf-8")
    w.measure.registry = load_registry(load_config(w.cfg))
    # The file itself passes the loader (seal and replay record are fine)...
    assert measure.promotion_problems(w.measure.registry, "test-agent", "lookup_record") == []
    # ...and the store, asked again at start-up, says the numbers are not there.
    problems = w.measure.promotion_store_problems()
    assert any("the store now says labelled 0 < 30" in p for p in problems), problems


def test_k6_promotion_store_check_passes_for_earned_evidence_and_does_not_skip_demoted(w):
    _replay_record(w)
    _ready(w)
    assert w.measure.promote_check("test-agent", "create_draft_record").ok
    agents = w.cfg / "agents.yaml"
    data = yaml.safe_load(agents.read_text(encoding="utf-8"))
    data[0]["levels"] = {"create_draft_record": "suggest"}
    agents.write_text(yaml.safe_dump(data), encoding="utf-8")
    w.measure.registry = load_registry(load_config(w.cfg))
    assert w.measure.promotion_store_problems() == []
    w.label(
        w.run(action="create_draft_record"), "harmful"
    )  # demoted, but the config still says suggest
    problems = w.measure.promotion_store_problems()
    assert any("wrong + harmful 2 > 1" in p for p in problems), (
        problems
    )  # a demotion does not exempt it


# --- second review: sticky on the latest label, atomic batches, replays, aliases, and more -------------------


def test_k6_a_lowered_harmful_does_not_leave_the_run_stuck_for_others(w):
    rid = w.run()
    w.label(rid, "harmful")
    assert w.label(
        rid, "agree", who="owner", when=NOW + timedelta(seconds=1)
    ).ok  # lowered by a line owner
    # The LATEST eligible label is now agree, so an ordinary labeller may change it again.
    assert w.label(rid, "partial", who="u2", when=NOW + timedelta(seconds=2)).ok
    assert w.label(rid, "wrong", who="u3", when=NOW + timedelta(seconds=3)).ok
    # ... but a harmful that stands (latest) still binds them.
    assert w.label(rid, "harmful", who="u3", when=NOW + timedelta(seconds=4)).ok
    assert (
        w.label(rid, "agree", who="u2", when=NOW + timedelta(seconds=5)).reason
        == "harmful_is_sticky"
    )


def test_k6_an_unapproved_csv_harmful_is_not_a_verdict_to_stick_to(w):
    rid = w.run()
    assert w.measure.import_csv(f"run_id,label\n{rid},harmful\n", "fake:u1")[0] == 1
    assert w.label(
        rid, "agree", who="u2", when=NOW + timedelta(seconds=1)
    ).ok  # it never counted as evidence


def test_k6_a_label_that_fails_the_sticky_rule_in_a_batch_stores_nothing(w):
    ok, stuck = w.run(), w.run()
    w.label(stuck, "harmful", who="u2")
    from hadavin_sdk.store.protocol import HarmfulSticky

    items = [
        (measure_label(ok, "agree", NOW + timedelta(seconds=1)), None),
        (measure_label(stuck, "agree", NOW + timedelta(seconds=2)), None),
    ]
    with pytest.raises(HarmfulSticky):
        w.store.add_labels(items, may_lower_harmful=False)
    assert w.store.list_labels(ok) == []  # the first label went with it
    w.store.add_labels(items, may_lower_harmful=True)  # a line owner may
    assert [x.label for x in w.store.list_labels(stuck)] == ["harmful", "agree"]


def test_k6_a_failing_audit_sink_never_turns_a_committed_label_into_an_error(w):
    w.audit.write_outcome = lambda ev: (_ for _ in ()).throw(OSError("audit down"))
    w.channel.post_card = lambda card: (_ for _ in ()).throw(OSError("channel down"))
    ids = [w.run() for _ in range(3)]
    res = w.measure.record_label("fake:u1", ids[0], "harmful")
    assert (res.ok, res.demoted) == (True, True)  # committed, demoted, the failures only logged
    text = "run_id,label\n" + "".join(f"{r},agree\n" for r in ids[1:])
    assert w.measure.import_csv(text, "fake:u2") == (2, [])  # the loop does not die half way
    assert w.click("u3", f"label|{ids[1]}|partial")[0] == 200  # and the receiver answers


def test_k6_the_receiver_answers_even_when_the_measure_blows_up(w):
    def boom(action):
        raise RuntimeError("bug")

    w.measure.handle_action = boom
    assert w.click("u1", f"label|{w.run()}|agree")[0] == 503


def test_k6_a_csv_import_is_all_or_nothing(w):
    fine, stuck = w.run(), w.run()
    w.label(stuck, "harmful", who="u2")
    text = f"run_id,label\n{fine},agree\n{stuck},agree\n"
    stored, problems = w.measure.import_csv(text, "fake:u1")  # u1 may not lower a harmful verdict
    assert stored == 0 and problems == ["row 2: harmful_is_sticky"]
    assert w.store.list_labels(fine) == []
    assert w.channel.cards == [
        c for c in w.channel.cards if "import" not in c.text
    ]  # no approval card either


def test_k6_approving_an_import_with_a_refused_row_keeps_it_pending_and_says_why(w):
    one, two = w.run(), w.run()
    text = f"run_id,label\n{one},agree\n{two},agree\n"
    assert w.measure.import_csv(text, "fake:u1")[0] == 2
    w.label(
        two, "harmful", who="u2", when=NOW + timedelta(seconds=1)
    )  # now row 2 would lower a harmful verdict
    status, reason = w.measure.approve_import("fake:owner", measure.csv_import_id(text))
    assert (status, reason) == (200, "refused: row 2: harmful_is_sticky")
    assert (
        _numbers(w).agree == 0 and w.store.list_labels(one)[0].approved_by is None
    )  # nothing approved
    assert (
        len(w.store.list_labels(one)) == 1
    )  # still only the pending row, which can be approved later


def test_k6_an_import_that_completes_three_wrongs_demotes(w):
    ids = [w.run() for _ in range(3)]
    text = "run_id,label\n" + "".join(f"{r},wrong\n" for r in ids)
    assert w.measure.import_csv(text, "fake:u1")[0] == 3
    assert (
        "test-agent",
        ACTION,
    ) in w.store.current_overrides()  # no row saw three, the batch re-check did


def test_k6_the_full_digest_names_an_import(w):
    rid = w.run()
    text = f"run_id,label\n{rid},agree\n"
    iid = measure.csv_import_id(text)
    assert len(iid) == 64
    w.measure.import_csv(text, "fake:u1")
    assert [x.label_id for x in w.store.list_csv_import(iid)] == [f"csv-{iid}-1-p"]
    assert w.store.list_csv_import("0" * 64) == []
    assert (
        measure.parse_action_value(f"approve_import|{iid[:8]}") is None
    )  # a short prefix is not an id
    assert measure.parse_action_value(f"approve_import|{iid}") is not None


def test_k6_cli_names_are_refused_in_pilot_and_prod(tmp_path, capsys):
    w = World(tmp_path)
    csv_file = tmp_path / "labels.csv"
    csv_file.write_text(f"run_id,label\n{w.run()},agree\n", encoding="utf-8")
    ns = _args(cmd="label", action="import", file=csv_file, by="fake:u1", approved_by="fake:owner")
    for env in ("pilot", "prod"):
        app = SimpleNamespace(
            measure=w.measure, store=w.store, config=SimpleNamespace(environment=env)
        )
        assert cli.measure_cmd(app, ns) == 2
        assert "only from signed channel clicks" in capsys.readouterr().err
    assert w.store.list_labels("run-001") == []


def test_k6_cli_in_dev_records_the_os_user_and_refuses_one_person_under_two_names(tmp_path):
    import getpass

    w = World(tmp_path)
    rid = w.run()
    csv_file = tmp_path / "labels.csv"
    csv_file.write_text(f"run_id,label\n{rid},agree\n", encoding="utf-8")
    app = SimpleNamespace(
        measure=w.measure, store=w.store, config=SimpleNamespace(environment="dev")
    )
    ns = _args(
        cmd="label", action="import", file=csv_file, by="fake:owner", approved_by="fake:owner"
    )
    assert cli.measure_cmd(app, ns) == 1  # the same person, however it is spelled
    assert w.store.list_labels(rid) == []
    ns.approved_by = None
    assert cli.measure_cmd(app, ns) == 0
    notes = [e for e in w.audit.events() if e.operation == "cli_import"]
    assert len(notes) == 2  # the refused attempt is on record too
    ev = notes[-1]
    assert ev.result == f"os_user:{getpass.getuser()}"


def test_k6_a_replayed_click_is_acted_on_once(w):
    rid = w.run()
    value = f"label|{rid}|agree"
    assert w.click("u1", value)[0] == 200
    assert w.click("u1", value)[0] == 200  # the same signed request again
    assert len(w.store.list_labels(rid)) == 1
    assert any(e.error_code == "replay" for e in w.audit.events())
    # a fresh click (another timestamp) is a new delivery
    assert w.click("u1", f"label|{rid}|partial", ts=NOW + timedelta(seconds=1))[0] == 200
    assert len(w.store.list_labels(rid)) == 2


def test_k6_a_replayed_reset_does_not_lift_a_newer_stop(w):
    assert w.click("ops", "stop", ts=NOW)[0] == 200
    assert w.click("ops", "reset", ts=NOW + timedelta(seconds=1))[0] == 200  # captured by someone
    assert not w.store.get_kill_switch().on
    assert w.click("ops", "stop", ts=NOW + timedelta(seconds=2))[0] == 200  # a new stop
    assert w.store.get_kill_switch().on
    assert (
        w.click("ops", "reset", ts=NOW + timedelta(seconds=1))[0] == 200
    )  # the captured reset, replayed
    assert w.store.get_kill_switch().on  # still stopped
    assert w.click("ops", "stop", ts=NOW)[0] == 200  # a replayed stop changes nothing either


def test_k6_a_replayed_clear_does_not_undo_a_new_demotion(w):
    rid = w.run()
    w.label(rid, "harmful")
    value = w.clear_value()
    w.measure.ceiling = Ceiling(CEIL.metric, 5, CEIL.window_days, CEIL.source)
    assert w.click("owner", value, ts=NOW)[0] == 200
    assert not w.store.current_overrides()
    w.label(w.run(), "harmful", when=NOW + timedelta(seconds=5))
    assert w.store.current_overrides()
    assert w.click("owner", value, ts=NOW)[0] == 200  # replay
    assert w.store.current_overrides()  # the new demotion stands


def test_k6_the_old_abstain_button_value_still_means_missed(w):
    assert measure.parse_action_value("label|run-1|should_have_answered") == measure.ParsedAction(
        "label", ("run-1", "missed")
    )
    rid = w.run(plan=False, state=S.NO_ACTION, reason=None)
    assert w.click("u1", f"label|{rid}|should_have_answered")[0] == 200
    assert [x.label for x in w.store.list_labels(rid)] == ["missed"]


def test_k6_an_unapproved_csv_agree_does_not_hide_a_chat_wrong_from_the_episode(w):
    a, b, c = (w.run() for _ in range(3))
    w.label(a, "wrong", when=day(3))
    assert (
        w.measure.import_csv(f"run_id,label\n{a},agree\n", "fake:u2")[0] == 1
    )  # unapproved: not evidence
    w.label(b, "wrong", when=day(2))
    assert w.label(c, "wrong", when=day(1)).demoted  # run a still counts as wrong


def test_k6_an_unapproved_csv_wrong_counts_towards_the_episode(w):
    a, b, c = (w.run() for _ in range(3))
    w.label(a, "wrong", when=day(3))
    w.label(b, "wrong", when=day(2))
    assert w.measure.import_csv(f"run_id,label\n{c},wrong\n", "fake:u2")[0] == 1
    assert ("test-agent", ACTION) in w.store.current_overrides()  # the safe direction


def test_k6_a_replay_record_that_disagrees_with_itself_is_not_green(w):
    from hadavin_sdk import replay_records

    rec = _replay_record(w)
    assert replay_records.has_green_record(w.reg, "test-agent")
    path = w.reg.config.root / "replay-records.jsonl"
    for change in (
        {"green": False},
        {"pass_rate": 0.5},
        {"threshold": 0.999, "pass_k": 0.99, "green": True},
    ):
        path.write_text(rec.model_copy(update=change).model_dump_json() + "\n", encoding="utf-8")
        assert not replay_records.has_green_record(w.reg, "test-agent"), change


def test_k6_events_waiting_in_the_audit_outbox_are_counted(w):
    pending = [measure_event(day(7), "guard", "r9")]

    class Outbox:
        """An audit whose newest events are still in the outbox until reconcile drains them."""

        def __init__(self):
            self.drained = False

        def reconcile(self):
            self.drained = True
            return len(pending)

        def events(self, run_id=None):
            return list(pending) if self.drained else []

        def write_outcome(self, event):
            return None

    w.measure.audit = Outbox()
    assert "- guard: 1" in w.measure.render_report(WEEK, NOW)


def test_k6_the_report_shows_who_lowered_a_harmful_verdict(w):
    rid = w.run(created=day(7))
    w.label(rid, "harmful", when=day(7))
    w.label(rid, "agree", who="owner", when=day(7, 13))
    text = w.measure.render_report(WEEK, NOW)
    assert "harmful verdicts lowered by a line owner: 1 this week, 1 in all" in text
    assert f"  - {rid}: lowered to agree by fake:owner at" in text
    assert "ceiling: 0 of 1" in text  # it left the count, and the report says how


def test_k6_an_unreachable_owner_is_retried_on_the_next_tick(tmp_path):
    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    (cfg / "baseline.yaml").write_text(
        "ceiling:\n  metric: m\n  counts: [harmful]\n  max: 0\n  window_days: 90\n  source: s\n",
        encoding="utf-8",
    )
    path = cfg / "principals.yaml"
    people = yaml.safe_load(path.read_text(encoding="utf-8"))
    people.append({"id": "fake:owner", "kind": "person", "admin_rights": ["clear_override"]})
    path.write_text(yaml.safe_dump(people), encoding="utf-8")
    qualify(load_registry(load_config(cfg)))
    channel = FakeChannel(SECRET)
    real = channel.notify
    channel.notify = lambda who, text: (_ for _ in ()).throw(OSError("down"))
    app = app_mod.build(cfg, ["test-agent"], channel=channel, llm=ScriptedLLM(), secrets=SECRETS)
    assert run_tick(app, NOW) == 1  # the weekly_report step failed, loudly
    assert app.store.get_report(WEEK) is None
    channel.notify = real
    assert run_tick(app, NOW + timedelta(seconds=45)) == 0  # the very next tick, not an hour later
    assert app.store.get_report(WEEK) is not None


# --- identity and the cli --------------------------------------------------------------------------------


def test_k6_admin_rights_are_a_closed_list_and_default_empty():
    assert Principal(id="p", kind="person").admin_rights == []
    p = Principal(
        id="p",
        kind="person",
        admin_rights=["stop", "reset", "clear_override", "approve_label_import"],
    )
    assert len(p.admin_rights) == 4
    with pytest.raises(ValueError):
        Principal(id="p", kind="person", admin_rights=["root"])
    assert (
        Principal(id="p", kind="person", rights=["x"]).admin_rights == []
    )  # action rights grant no admin right


def _args(**kw):
    return SimpleNamespace(**kw)


def test_k6_cli_label_import_and_report(tmp_path, capsys):
    w = World(tmp_path)
    app = SimpleNamespace(measure=w.measure, store=w.store)
    rid = w.run(created=day(7))
    csv_file = tmp_path / "labels.csv"
    csv_file.write_text(f"run_id,label\n{rid},agree\n", encoding="utf-8")
    ns = _args(cmd="label", action="import", file=csv_file, by="fake:u1", approved_by=None)
    assert cli.measure_cmd(app, ns) == 0
    out = capsys.readouterr().out
    assert "1 labels stored (waiting for a line owner's approval)" in out
    ns.approved_by = "fake:owner"
    assert cli.measure_cmd(app, ns) == 0
    assert "counting as evidence" in capsys.readouterr().out
    csv_file.write_text("run_id,label\nrun-nope,agree\n", encoding="utf-8")
    assert cli.measure_cmd(app, ns) == 1
    assert "REFUSED: row 1: unknown_run" in capsys.readouterr().out
    monday = (NOW - timedelta(days=7)).date().isoformat()
    assert cli.measure_cmd(app, _args(cmd="report", week=monday)) == 0
    captured = capsys.readouterr()
    assert "# Pilot report: week of 2026-10-26" in captured.out and "not stored" in captured.err
    w.store.put_report(WEEK, "stored body")
    assert cli.measure_cmd(app, _args(cmd="report", week=monday)) == 0
    assert capsys.readouterr().out.strip() == "stored body"
    with pytest.raises(BaseConfigError, match="must be a Monday"):
        cli.measure_cmd(app, _args(cmd="report", week="2026-10-27"))
    with pytest.raises(BaseConfigError, match="YYYY-MM-DD"):
        cli.measure_cmd(app, _args(cmd="report", week="soon"))


def test_k6_cli_promote_check_exit_codes(tmp_path, capsys):
    w = World(tmp_path)
    app = SimpleNamespace(measure=w.measure, store=w.store)
    ns = _args(cmd="promote-check", agent="test-agent", action="create_draft_record")
    assert cli.measure_cmd(app, ns) == 1
    out = capsys.readouterr().out
    assert "NOT MET: labelled 0 < 30" in out and "nothing was written" in out
    _replay_record(w)
    _ready(w)
    assert cli.measure_cmd(app, ns) == 0
    assert "promotion evidence written:" in capsys.readouterr().out


def test_k6_cli_refuses_the_memory_store(tmp_path, monkeypatch, capsys):
    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    assert cli.main(["--config", str(cfg), "report"]) == 2
    assert "needs a shared store" in capsys.readouterr().err
    assert cli.main(["--config", str(cfg), "promote-check", "test-agent", ACTION]) == 2
    assert (
        cli.main(["--config", str(cfg), "label", "import", str(tmp_path / "x.csv"), "--by", "p"])
        == 2
    )
