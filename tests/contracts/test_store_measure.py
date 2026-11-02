# ruff: noqa: S311, B023  - seeded test randomness; threads are joined inside the loop that defines them
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


def put(store, lab, demote=None):
    """Store one label (a line owner's rights: the sticky rule is the Measure tests' business)."""
    store.add_labels([(lab, demote)], may_lower_harmful=True)


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
    put(store, label("r1", "agree", at(26, 1)))
    put(store, label("r1", "wrong", at(26, 2)))  # the latest label of a run is its label
    put(store, label("r2", "harmful", at(28)))
    put(store, label("r3", "agree", at(2, 1, month=11)))
    put(store, label("r4", "abstain_ok", at(28)))
    put(store, label("r5", "missed", at(28)))
    put(store, label("r8", "agree", at(28), channel="csv"))  # csv, never approved: not counted
    put(store, label("r7", "missed", at(28), channel="csv", approved_by="user:owner"))


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
    put(store, label("r1", "agree", at(26, 1), lid="l1"))
    with pytest.raises(StaleState):
        put(store, label("r1", "wrong", at(26, 2), lid="l1"))
    put(store, label("r9", "wrong", at(26, 3)))
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
    put(store, label("r1", "harmful", at(26, 1), lid="l1"), demote)
    assert store.current_overrides() == {("agent", "fix"): "shadow"}
    with pytest.raises(StaleState):
        put(
            store,
            label("r1", "harmful", at(26, 2), lid="l1"),
            demote.model_copy(update={"reason": "dup"}),
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
        put(store, label(rid, name, at(26, 1)))
    put(store, label("e", "missed", at(26, 1)))  # a missed run has no plan
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


def test_k6_add_labels_is_one_transaction_with_the_sticky_rule_inside(store):
    from hadavin_sdk.store.protocol import HarmfulSticky

    make_run(store, "a", at(26), S.NO_ACTION, "shadow", plan_after=1)
    make_run(store, "b", at(26), S.NO_ACTION, "shadow", plan_after=1)
    demote = LevelEvent(
        agent_id="agent", action_id="fix", kind="demote", reason="h", by="u", at=at(26, 1)
    )
    first = [(label("b", "harmful", at(26, 1), lid="b1"), demote)]
    store.add_labels(first, may_lower_harmful=False)
    items = [
        (label("a", "agree", at(26, 2), lid="a1"), None),
        (label("b", "agree", at(26, 3), lid="b2"), None),  # lowers a harmful verdict
    ]
    with pytest.raises(HarmfulSticky):
        store.add_labels(items, may_lower_harmful=False)
    assert store.list_labels("a") == []  # nothing of the batch stayed
    assert [e.reason for e in store.list_level_events()] == ["h"]
    store.add_labels(items, may_lower_harmful=True)
    assert [x.label for x in store.list_labels("b")] == ["harmful", "agree"]
    # The sticky rule reads the LATEST eligible label: b is agree now, so anyone may change it.
    store.add_labels([(label("b", "wrong", at(26, 4), lid="b3"), None)], may_lower_harmful=False)
    # A duplicate id stores nothing, not even the other rows of the batch.
    dup = [
        (label("a", "partial", at(26, 5), lid="a2"), None),
        (label("a", "agree", at(26, 6), lid="a1"), None),
    ]
    with pytest.raises(StaleState):
        store.add_labels(dup, may_lower_harmful=True)
    assert [x.label_id for x in store.list_labels("a")] == ["a1"]


def test_k6_claim_action_accepts_a_nonce_once(store):
    assert store.claim_action("1700000000:v0=abc", at(26)) is True
    assert store.claim_action("1700000000:v0=abc", at(27)) is False
    assert store.claim_action("1700000001:v0=abc", at(27)) is True


def test_k6_csv_import_lookup_is_exact(store):
    make_run(store, "a", at(26), S.NO_ACTION, "shadow", plan_after=1)
    full = "a1" * 32
    put(store, label("a", "agree", at(26, 1), channel="csv", lid=f"csv-{full}-1-p"))
    assert [x.label_id for x in store.list_csv_import(full)] == [f"csv-{full}-1-p"]
    assert store.list_csv_import(full[:8]) == []
    assert store.list_csv_import("b2" * 32) == []


# --- class sweeps: the same rule must hold for every sequence and every interleaving ----------------------------


def _oracle_refuses(accepted, lab, may):
    """The rule, written once and plainly: a non-harmful label is refused when the run's latest ELIGIBLE label is
    harmful and the author may not lower it."""
    from hadavin_sdk.models import latest_labels

    cur = latest_labels([x for x in accepted if x.run_id == lab.run_id]).get(lab.run_id)
    return lab.label != "harmful" and not may and cur is not None and cur.label == "harmful"


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_k6_property_store_sticky_rule_matches_the_oracle_on_random_sequences(store, seed):
    """Random label sequences (any class, chat or csv, approved or not, owner or not): the store accepts and refuses
    exactly what the oracle says, in both store kinds. The stored rows come back in time order, one latest each."""
    import random

    from hadavin_sdk.models import latest_labels
    from hadavin_sdk.store.protocol import HarmfulSticky

    rnd = random.Random(seed)
    names = ["agree", "partial", "wrong", "harmful"]
    accepted = []
    for i in range(120):
        rid = f"p{rnd.randrange(3)}"
        channel = rnd.choice(["chat", "chat", "csv"])
        lab = label(
            rid,
            rnd.choice(names),
            at(1, month=11) + timedelta(seconds=i),
            channel=channel,
            approved_by="user:o" if channel == "csv" and rnd.random() < 0.5 else None,
            lid=f"s{seed}-{i}",
        )
        may = rnd.random() < 0.2
        want_refused = _oracle_refuses(accepted, lab, may)
        try:
            store.add_labels([(lab, None)], may_lower_harmful=may)
            assert not want_refused, (i, lab.label, rid)
            accepted.append(lab)
        except HarmfulSticky:
            assert want_refused, (i, lab.label, rid)
    for rid in {x.run_id for x in accepted}:
        stored = store.list_labels(rid)
        assert [x.label_id for x in stored] == [x.label_id for x in accepted if x.run_id == rid]
        want = latest_labels([x for x in accepted if x.run_id == rid]).get(rid)
        assert latest_labels(stored).get(rid).label_id == want.label_id


def test_k6_add_level_event_says_whether_it_inserted_and_add_labels_returns_the_inserted_demotions(
    store,
):
    ev = LevelEvent(agent_id="a", action_id="x", kind="demote", reason="r1", by="s", at=at(26))
    assert store.add_level_event(ev) is True
    assert store.add_level_event(ev) is False  # already there: nothing to audit or announce
    put(store, label("m", "wrong", at(26, 1)))
    out = store.add_labels(
        [
            (label("n", "wrong", at(26, 2), lid="n1"), ev),  # same demotion again
            (label("o", "wrong", at(26, 3), lid="o1"), ev.model_copy(update={"reason": "r2"})),
        ],
        may_lower_harmful=True,
    )
    assert [e.reason for e in out] == ["r2"]


def test_k6_nonces_can_be_released_and_old_ones_purged(store):
    assert store.claim_action("n1", at(26, 1))
    store.release_action("n1")
    assert store.claim_action("n1", at(26, 1))  # given back, so it can be claimed again
    assert store.claim_action("n2", at(26, 9))
    assert store.purge_actions(at(26, 5)) == 1  # n1 only
    assert store.claim_action("n1", at(27)) is True and store.claim_action("n2", at(27)) is False


def test_k6_two_labels_at_one_instant_are_ordered_by_insertion(store):
    from hadavin_sdk.models import latest_labels

    same = at(26, 1)
    put(store, label("t", "agree", same, lid="zzz"))
    put(store, label("t", "wrong", same, lid="aaa"))  # smaller id, same instant, inserted later
    stored = store.list_labels("t")
    assert [x.label_id for x in stored] == ["zzz", "aaa"]
    assert latest_labels(stored)["t"].label == "wrong"


def test_k6_the_last_inserted_label_is_the_latest_whatever_its_timestamp(store):
    """A label whose clock was read before a later commit is moved just after it: a later commit never sorts earlier."""
    from hadavin_sdk.models import latest_labels

    put(store, label("r", "agree", at(1, 12), lid="first"))
    put(
        store, label("r", "harmful", at(1, 11), lid="second")
    )  # read its clock earlier, committed later
    stored = store.list_labels("r")
    assert [x.label_id for x in stored] == ["first", "second"]
    assert latest_labels(stored)["r"].label == "harmful"  # a non-owner cannot now lower it
    from hadavin_sdk.store.protocol import HarmfulSticky

    with pytest.raises(HarmfulSticky):
        store.add_labels(
            [(label("r", "agree", at(1, 10), lid="third"), None)], may_lower_harmful=False
        )


def test_k6_threads_claim_one_nonce_exactly_once(store):
    import threading

    results = []
    start = threading.Barrier(16)

    def go():
        start.wait()
        results.append(store.claim_action("1:v0=race", at(26)))

    threads = [threading.Thread(target=go) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [False] * 15 + [True]


def test_k6_a_demotion_is_recorded_once_per_reason_even_from_many_threads(store):
    import threading

    ev = LevelEvent(
        agent_id="a", action_id="x", kind="demote", reason="ceiling:t1", by="s", at=at(26)
    )
    start = threading.Barrier(8)

    def go():
        start.wait()
        store.add_level_event(ev)

    threads = [threading.Thread(target=go) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert [e.reason for e in store.list_level_events()] == ["ceiling:t1"]
    # a different reason is a different fact; a clear then the same reason again is still refused (cleared episode)
    store.add_level_event(ev.model_copy(update={"reason": "ceiling:t2"}))
    assert len(store.list_level_events()) == 2


def test_k6_clear_demotion_is_a_compare_and_set(store):
    def demote(reason):
        return LevelEvent(
            agent_id="a", action_id="x", kind="demote", reason=reason, by="s", at=at(26)
        )

    clear = LevelEvent(agent_id="a", action_id="x", kind="clear", reason="owner", by="o", at=at(26))
    store.add_level_event(demote("one"))
    (seen,) = store.list_level_events()
    store.add_level_event(demote("two"))  # lands after the caller looked
    assert store.clear_demotion(clear, seen.seq) is False
    assert store.current_overrides() == {
        ("a", "x"): "shadow"
    }  # the new demotion was not cleared unseen
    newest = store.list_level_events()[-1].seq
    assert store.clear_demotion(clear, newest) is True
    assert store.current_overrides() == {}
    assert store.clear_demotion(clear, newest) is False  # the log moved on (our own clear)


def test_k6_a_clear_racing_new_demotions_never_loses_one(store):
    """Whatever the interleaving, a demotion added while a clear is being decided is still in force after both."""
    import threading

    for i in range(25):
        agent = f"agent{i}"
        base = LevelEvent(
            agent_id=agent, action_id="x", kind="demote", reason="old", by="s", at=at(26)
        )
        store.add_level_event(base)
        seen = store.list_level_events()[-1]
        new = base.model_copy(update={"reason": "new"})
        clear = LevelEvent(
            agent_id=agent, action_id="x", kind="clear", reason="o", by="o", at=at(26)
        )
        start = threading.Barrier(2)

        def do_clear():
            start.wait()
            store.clear_demotion(clear, seen.seq)

        def do_demote():
            start.wait()
            store.add_level_event(new)

        a, b = threading.Thread(target=do_clear), threading.Thread(target=do_demote)
        a.start()
        b.start()
        a.join()
        b.join()
        events = [e for e in store.list_level_events() if e.agent_id == agent]
        newest_demote = max(e.seq for e in events if e.reason == "new")
        cleared_after = [e for e in events if e.kind == "clear" and e.seq > newest_demote]
        assert not cleared_after, i  # no clear may sit after the new demotion it never saw
        assert (agent, "x") in store.current_overrides(), i


def test_k6_claim_action_keeps_the_team_and_the_click_timestamp(store):
    assert store.claim_action("1:v0=t", at(26), "T0TEAM", "1700000000.5") is True
    assert store.get_action("1:v0=t") == ("T0TEAM", "1700000000.5")
    assert store.claim_action("2:v0=t", at(26)) is True
    assert store.get_action("2:v0=t") == ("", "")  # the old two-argument form still works
    assert store.get_action("3:v0=t") is None
    store.release_action("1:v0=t")
    assert store.get_action("1:v0=t") is None
