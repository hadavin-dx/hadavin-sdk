"""K6 store suite: the same fixture through every store kind must give the same weekly numbers (the memory store
counts in Python, postgres reads the views), plus labels, level events, reports and the tick detail column."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    ChainStep,
    Label,
    LevelEvent,
    Plan,
    Run,
    RunState,
    Target,
    TickState,
)
from hadavin_sdk.store.protocol import StaleState

S = RunState
WEEK = date(2026, 10, 26)  # a Monday
NEXT = date(2026, 11, 2)


def at(day: int, hh: int = 0, mm: int = 0, ss: int = 0, month: int = 10) -> datetime:
    return datetime(2026, month, day, hh, mm, ss, tzinfo=UTC)


def make_run(store, rid, created, state, reason=None, *, plan_after=None, cost="0", action="fix"):
    store.create_run(
        Run(
            run_id=rid,
            agent_id="agent",
            principal_id="svc:agent",
            trigger_kind="event",
            trigger_ref=rid,
            created_at=created,
            updated_at=created,
        )
    )
    store.transition(rid, S.RECEIVED, state, reason)
    if cost != "0":
        store.add_cost(rid, Decimal(cost))
    if plan_after is not None:
        store.save_plan(
            Plan(
                run_id=rid,
                agent_id="agent",
                action_id=action,
                action_version=1,
                risk_class="reversible",
                inputs={"x": 1},
                target=Target(system="sys"),
                idempotency_key=rid,
                expected_outcome="ok",
                created_at=created + timedelta(seconds=plan_after),
            )
        )


def label(rid, name, when, *, channel="chat", approved_by=None, principal="user:a", lid=None):
    kw = {"label_id": lid} if lid else {}
    return Label(
        run_id=rid,
        label=name,
        principal_id=principal,
        channel=channel,
        approved_by=approved_by,
        created_at=when,
        **kw,
    )


def load_fixture(store):
    make_run(
        store, "r1", at(26), S.NO_ACTION, "shadow", plan_after=40, cost="0.10"
    )  # Monday 00:00:00 exactly
    make_run(
        store, "r2", at(1, 23, 59, 59, month=11), S.NO_ACTION, "shadow", plan_after=20, cost="0.20"
    )  # Sunday last second
    make_run(
        store, "r3", at(2, month=11), S.NO_ACTION, "shadow_undelivered", plan_after=10
    )  # next week
    make_run(store, "r4", at(27), S.NO_ACTION)  # abstained: no plan
    make_run(store, "r5", at(27, 1), S.NEEDS_PERSON, "tool_error")
    make_run(store, "r6", at(27, 2), S.NEEDS_PERSON, "redaction_error")
    make_run(store, "r7", at(27, 3), S.NEEDS_PERSON, "uncited")
    make_run(store, "r8", at(28), S.SUCCEEDED, plan_after=30, cost="0.40")
    store.add_label(label("r1", "agree", at(26, 1)))
    store.add_label(label("r1", "wrong", at(26, 2)))  # the latest label of a run is its label
    store.add_label(label("r2", "harmful", at(28)))
    store.add_label(label("r3", "agree", at(2, 1, month=11)))
    store.add_label(label("r4", "abstain_ok", at(28)))
    store.add_label(label("r5", "missed", at(28)))
    store.add_label(label("r8", "agree", at(28), channel="csv"))  # csv, never approved: not counted
    store.add_label(label("r7", "missed", at(28), channel="csv", approved_by="user:owner"))


def approval(store, aid, created, decided, decision):
    req = ApprovalRequest(
        approval_id=aid,
        run_id="r1",
        plan_hash="h",
        risk_class="reversible",
        chain_id="c",
        steps=[ChainStep(approver_ids=["user:a"], timeout_s=600)],
        step_expires_at=created + timedelta(seconds=600),
        requested_by="svc:agent",
        summary="s",
        created_at=created,
    )
    store.save_approval_request(req)
    store.record_decision(
        ApprovalDecision(
            approval_id=aid,
            plan_hash="h",
            step=0,
            decision=decision,
            approver_id="user:a",
            channel="fake",
            decided_at=decided,
        ),
        req.model_copy(update={"status": "APPROVED" if decision == "approve" else "REJECTED"}),
        "PENDING",
        0,
    )


def test_k6_view_matches_python(store):
    """One fixture, every store kind: the same counts, with UTC week boundaries (Monday 00:00:00 and Sunday
    23:59:59 belong to their own weeks)."""
    load_fixture(store)
    pw = store.pilot_week(WEEK)
    assert (pw.runs, pw.proposals, pw.shadow_cards, pw.cards_not_delivered) == (7, 3, 2, 0)
    assert (pw.labelled, pw.agree, pw.partial, pw.wrong, pw.harmful) == (5, 0, 0, 1, 1)
    assert (pw.abstain_ok, pw.missed, pw.abstained, pw.fixes_verified) == (1, 2, 4, 1)
    assert pw.median_s_to_proposal == pytest.approx(30.0)
    assert float(pw.avg_cost_usd) == pytest.approx(0.1)
    nxt = store.pilot_week(NEXT)
    assert (nxt.runs, nxt.proposals, nxt.cards_not_delivered, nxt.labelled, nxt.agree) == (
        1,
        1,
        1,
        1,
        1,
    )
    assert store.pilot_week(date(2026, 10, 19)).runs == 0  # a week with no runs is all zeros
    assert store.pilot_week(date(2026, 10, 19)).median_s_to_proposal is None


def test_k6_abstained_counts_tool_and_redaction_errors(store):
    """F12: tool_error and redaction_error (and uncited) count as abstentions beside a NO_ACTION with no plan."""
    make_run(store, "t1", at(26), S.NEEDS_PERSON, "tool_error")
    make_run(store, "t2", at(26), S.NEEDS_PERSON, "redaction_error")
    make_run(store, "t3", at(26), S.NEEDS_PERSON, "provider_error")  # not an abstention
    make_run(
        store, "t4", at(26), S.NO_ACTION, "shadow", plan_after=1
    )  # a proposal, not an abstention
    assert store.pilot_week(WEEK).abstained == 2


def test_k6_approval_week(store):
    approval(store, "a1", at(27, 10), at(27, 10, 0, 30), "approve")
    approval(store, "a2", at(28, 10), at(28, 10, 2), "reject")
    approval(store, "a3", at(1, 23, 59, month=11), at(2, 0, 0, 10, month=11), "approve")
    aw = store.approval_week(WEEK)
    assert (aw.decisions, aw.wont_run) == (2, 1)
    assert aw.median_s == pytest.approx(75.0)
    assert store.approval_week(NEXT).decisions == 1


def test_k6_labels_are_appended_once_and_listed(store):
    make_run(store, "r1", at(26), S.NO_ACTION, "shadow", plan_after=1)
    make_run(store, "r9", at(26), S.NO_ACTION, "shadow", plan_after=1, action="other")
    store.add_label(label("r1", "agree", at(26, 1), lid="l1"))
    with pytest.raises(StaleState):
        store.add_label(label("r1", "wrong", at(26, 2), lid="l1"))
    store.add_label(label("r9", "wrong", at(26, 3)))
    assert [x.label for x in store.list_labels("r1")] == ["agree"]
    assert [x.run_id for x in store.list_labels_for("agent", "fix", None)] == ["r1"]
    assert store.list_labels_for("agent", "fix", at(26, 2)) == []  # since filters on the label time
    assert store.count_proposals("agent", "fix", None) == 1
    assert store.count_proposals("agent", "fix", at(27)) == 0
    assert len(store.list_labels_between(at(26), at(27))) == 2
    assert store.list_labels_between(at(27), at(28)) == []


def test_k6_label_and_demotion_are_one_transaction(store):
    """Both stored together; a duplicate label id stores neither the label nor its demotion."""
    make_run(store, "r1", at(26), S.NO_ACTION, "shadow", plan_after=1)
    demote = LevelEvent(
        agent_id="agent", action_id="fix", kind="demote", reason="harmful:r1", by="u", at=at(26, 1)
    )
    store.add_label(label("r1", "harmful", at(26, 1), lid="l1"), demote)
    assert store.current_overrides() == {("agent", "fix"): "shadow"}
    with pytest.raises(StaleState):
        store.add_label(
            label("r1", "harmful", at(26, 2), lid="l1"), demote.model_copy(update={"reason": "dup"})
        )
    assert [e.reason for e in store.list_level_events()] == ["harmful:r1"]


def test_k6_latest_level_event_wins_and_nothing_is_deleted(store):
    ev = lambda kind, why: LevelEvent(
        agent_id="agent", action_id="fix", kind=kind, reason=why, by="u", at=at(26)
    )
    store.add_level_event(ev("demote", "one"))
    store.add_level_event(ev("demote", "two"))
    assert ("agent", "fix") in store.current_overrides()
    store.add_level_event(ev("clear", "owner"))
    assert store.current_overrides() == {}
    store.add_level_event(ev("demote", "three"))
    assert store.current_overrides() == {("agent", "fix"): "shadow"}
    events = store.list_level_events()
    assert [e.reason for e in events] == ["one", "two", "owner", "three"]
    assert [e.seq for e in events] == sorted(e.seq for e in events)


def test_k6_held_run_ids(store):
    for rid in ("a", "b", "c", "d"):
        make_run(store, rid, at(26), S.NO_ACTION, "shadow", plan_after=1)
    for rid, name in (("a", "wrong"), ("b", "harmful"), ("c", "agree"), ("d", "partial")):
        store.add_label(label(rid, name, at(26, 1)))
    store.add_label(label("e", "missed", at(26, 1)))  # a missed run has no plan
    assert store.held_run_ids() == {"a", "b", "e"}


def test_k6_report_is_stored_once_per_week(store):
    assert store.get_report(WEEK) is None
    assert store.put_report(WEEK, "first") is True
    assert store.put_report(WEEK, "second") is False
    assert store.get_report(WEEK) == "first"


def test_k6_tick_state_detail_round_trips(store):
    assert store.get_tick_state("backlog") is None
    state = TickState(
        step="backlog", last_run_at=at(26), detail={"oldest_received_age_s": 840, "n": [1, 2]}
    )
    store.save_tick_state(state)
    assert store.get_tick_state("backlog").detail == {"oldest_received_age_s": 840, "n": [1, 2]}
    store.save_tick_state(TickState(step="backlog", last_run_at=at(27)))
    assert store.get_tick_state("backlog").detail is None
