"""K6 after the EGM review (codebase-details, design, implementation-readiness): evidence per config, who may
label and how many people, every downgrade audited and told, a clear bound to its demotion, announcements that are
retried, floors under the policy, the promotion file's own thresholds, the report's new sections, a two-week pilot."""

from __future__ import annotations

import json
from datetime import timedelta
from types import SimpleNamespace

from hadavin_sdk import app as app_mod
from hadavin_sdk import cli, measure
from hadavin_sdk.approvals.channel import FakeChannel
from hadavin_sdk.config import load_config
from hadavin_sdk.measure import DEFAULT_POLICY, Ceiling
from hadavin_sdk.models import RunState, ToolCall
from hadavin_sdk.registry import load_registry
from tests.conftest import qualify
from tests.test_k3_pilot import SECRETS, ScriptedLLM, dev_cfg, reply
from tests.test_k6_measure import (
    ACTION,
    CEIL,
    NOW,
    SECRET,
    WEEK,
    World,
    _ready,
    _replay_record,
    _suggest_world,
    day,
)

S = RunState
CD = "create_draft_record"


def _world(tmp_path, **policy):
    from dataclasses import replace

    w = World(tmp_path)
    w.measure.policy = replace(DEFAULT_POLICY, **policy)
    w.measure.th = w.measure.policy.thresholds()
    return w


# --- B1: promotion evidence belongs to the config that produced it -------------------------------------------------


def test_egm_labels_made_under_an_older_config_do_not_count_for_the_current_one(tmp_path):
    w = World(tmp_path)
    _replay_record(w)
    old = "0" * 64  # the proposals were made under another prompt
    for name, n in (("agree", 26), ("partial", 3), ("wrong", 1)):
        w.labelled(name, n, when=day(9), action=CD, who=("u1", "u2"), config_hash=old)
    res = w.measure.promote_check("test-agent", CD)
    assert not res.ok and any("labelled 0 < 30" in p for p in res.problems), res.problems
    _ready(w)  # the same amount of evidence, now under the current hash
    assert w.measure.promote_check("test-agent", CD).ok


def test_egm_the_runtime_stamps_config_hash_model_and_prompt_on_every_plan(tmp_path):
    cfg = dev_cfg(tmp_path, {ACTION: "shadow"})
    reg = load_registry(load_config(cfg))
    qualify(reg)
    propose = ToolCall(name=ACTION, input={"service": "checkout"})
    app = app_mod.build(
        cfg,
        ["test-agent"],
        channel=FakeChannel(SECRET),
        llm=ScriptedLLM(reply(propose)),
        secrets=SECRETS,
    )
    run = app.runtime.handle("test-agent", "svc:test-agent", b"checkout is down")
    plan = app.store.get_plan(run.run_id)
    agent = reg.agents["test-agent"]
    assert plan.config_hash == reg.config_hash("test-agent")
    assert plan.model_id == reg.config.routes[agent.model_route].model_id
    assert plan.prompt_sha256 == reg.prompt_sha256("test-agent")


def test_egm_a_plan_stored_before_the_stamps_existed_never_counts(tmp_path):
    w = World(tmp_path)
    rid = w.run()
    plan = w.store.get_plan(rid)
    w.store.save_plan(
        plan.model_copy(update={"config_hash": None})
    )  # as stored by an older release
    assert w.store.count_proposals("test-agent", ACTION, None, w.reg.config_hash("test-agent")) == 0


# --- B2: the start-up store leg re-checks what the file only claims -------------------------------------------------------


def _promoted_world(tmp_path):
    w = World(tmp_path)
    _replay_record(w)
    _ready(w)
    assert w.measure.promote_check("test-agent", CD).ok
    _suggest_world(w)
    return w


def test_egm_store_leg_checks_the_replay_the_ceiling_and_the_thresholds(tmp_path):
    w = _promoted_world(tmp_path)
    assert w.measure.promotion_store_problems() == []
    # the replay leg: the record is gone
    records = w.reg.config.root / "replay-records.jsonl"
    saved = records.read_text(encoding="utf-8")
    records.unlink()
    assert any("no green replay record" in p for p in w.measure.promotion_store_problems())
    records.write_text(saved, encoding="utf-8")
    # the ceiling leg: a self-attested "breached: false" is not believed when the store says breached
    w.labelled("harmful", 1, when=day(2), action=ACTION)
    assert any("the ceiling is breached now" in p for p in w.measure.promotion_store_problems())


def test_egm_a_file_written_under_looser_thresholds_than_the_policy_now_in_force_is_refused(
    tmp_path,
):
    from dataclasses import replace

    w = World(tmp_path)
    w.measure.policy = replace(
        DEFAULT_POLICY, promotion_min_labelled=5, allow_weaker_than_spec=True
    )
    w.measure.th = w.measure.policy.thresholds()
    _replay_record(w)
    w.labelled("agree", 6, when=day(9), action=CD, who=("u1", "u2"))
    res = w.measure.promote_check("test-agent", CD)
    assert res.ok, res.problems  # legitimately weaker, signed on purpose
    body = json.loads(res.path.read_text(encoding="utf-8"))
    assert body["weaker_allowed"] is True and body["thresholds"]["min_labelled"] == 5
    assert (
        body["policy"]["allow_weaker_than_spec"] is True
    )  # the effective policy is written into the file
    assert (
        measure.promotion_problems(w.reg, "test-agent", CD) == []
    )  # CB1: the loader reads the FILE's thresholds
    _suggest_world(w)
    w.measure.policy = DEFAULT_POLICY  # the client tightened the policy since
    w.measure.th = DEFAULT_POLICY.thresholds()
    assert any("looser thresholds" in p for p in w.measure.promotion_store_problems())


def test_egm_a_relaxed_policy_writes_a_file_the_loader_accepts_and_a_forged_weak_file_is_refused(
    tmp_path,
):
    w = _promoted_world(tmp_path)
    path = measure.promotion_path(w.reg.config.root, "test-agent", CD)
    body = json.loads(path.read_text(encoding="utf-8"))
    body["thresholds"] = {
        **body["thresholds"],
        "min_labelled": 1,
    }  # weaker than the spec, and not declared
    body["sha256"] = measure._file_sha(body)
    path.write_text(json.dumps(body), encoding="utf-8")
    assert any(
        "weaker than the spec's" in p for p in measure.promotion_problems(w.reg, "test-agent", CD)
    )
    del body["thresholds"]
    body["sha256"] = measure._file_sha(body)
    path.write_text(json.dumps(body), encoding="utf-8")
    assert any(
        "does not record the thresholds" in p
        for p in measure.promotion_problems(w.reg, "test-agent", CD)
    )


# --- D3: who may label, and how many people the evidence rests on ---------------------------------------------------------


def test_egm_promotion_needs_two_distinct_labellers_and_the_report_shows_concentration(tmp_path):
    w = World(tmp_path)
    _replay_record(w)
    for name, n in (("agree", 26), ("partial", 3), ("wrong", 1)):
        w.labelled(name, n, when=day(9), action=CD, who=("u1",))  # one person supplied everything
    res = w.measure.promote_check("test-agent", CD)
    assert not res.ok and any("labelled by 1 distinct people < 2" in p for p in res.problems)
    assert "the busiest gave 100% of the labels" in w.measure.render_report(WEEK, NOW)


def test_egm_who_may_label_which_agent(tmp_path, monkeypatch):
    w = World(tmp_path)
    rid = w.run()
    p = lambda **kw: SimpleNamespace(label_agents=kw.get("agents"))
    m = w.measure
    assert m._may_label(p(agents=["*"]), "test-agent") and m._may_label(
        p(agents=["test-agent"]), "test-agent"
    )
    assert not m._may_label(p(agents=["other-agent"]), "test-agent")
    assert m._may_label(p(), "test-agent")  # not stated: allowed in dev
    object.__setattr__(w.reg.config, "environment", "pilot")  # pilot and prod: a labeller is named
    try:
        assert not m._may_label(p(), "test-agent")
        assert m._may_label(p(agents=["test-agent"]), "test-agent")
    finally:
        object.__setattr__(w.reg.config, "environment", "dev")
    w.reg.principals["fake:u1"] = w.reg.principals["fake:u1"].model_copy(
        update={"label_agents": ["other-agent"]}
    )
    assert w.measure.record_label("fake:u1", rid, "agree").reason == "not_a_labeller_for_this_agent"


def test_egm_only_a_delivered_shadow_card_can_be_labelled(tmp_path):
    w = World(tmp_path)
    rid = w.run(reason="shadow_undelivered")  # the card never reached anyone
    assert w.measure.record_label("fake:u1", rid, "agree").reason == "card_not_delivered"
    assert w.store.list_labels(rid) == []


# --- D4 / D5: downgrades are audited and told; a harmful demotion is not cleared by its author ------------------------


def test_egm_every_downgrade_of_wrong_or_harmful_is_audited_told_and_reported(tmp_path):
    w = World(tmp_path)
    a, b = w.run(created=day(7)), w.run(created=day(7))
    w.label(a, "wrong", when=day(7))
    w.label(a, "agree", who="u2", when=day(7, 13))  # a wrong verdict quietly softened
    w.label(b, "harmful", when=day(7))
    w.label(b, "agree", who="owner", when=day(7, 14))
    ops = [
        (e.operation, e.result, e.decision)
        for e in w.audit.events()
        if e.operation.endswith(("downgraded", "lowered"))
    ]
    assert ("label_downgraded", "wrong", "agree") in ops and (
        "label_downgraded",
        "harmful",
        "agree",
    ) in ops
    assert ("harmful_lowered", None, "agree") in ops
    told = [t for who, t in w.channel.notices if "changed run" in t]
    assert (
        len(told) == 2
        and "from harmful to agree" in told[1]
        and "leaves the ceiling count" in told[1]
    )
    text = w.measure.render_report(WEEK, NOW)
    assert (
        f"{a}: wrong -> agree by fake:u2" in text and f"{b}: harmful -> agree by fake:owner" in text
    )


def test_egm_a_clear_is_told_and_a_harmful_demotion_needs_a_second_person(tmp_path):
    w = World(tmp_path)
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    w.edit_principals(
        lambda d: d.append(
            {"id": "fake:owner2", "kind": "person", "admin_rights": ["clear_override"]}
        )
    )
    w.reg.principals["fake:owner2"] = load_registry(load_config(w.cfg)).principals["fake:owner2"]
    rid = w.run()
    assert w.measure.record_label(
        "fake:owner", rid, "harmful"
    ).demoted  # an owner gives the harmful label...
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (
        200,
        "second_person_needed",
    )  # ...and cannot clear
    assert w.measure.clear("fake:owner2", "test-agent", ACTION) == (200, "cleared")
    assert any("cleared the demotion" in t for _, t in w.channel.notices)


# --- D6: the clear button names the demotion it was posted for ------------------------------------------------------------


def test_egm_an_old_clear_button_is_stale_after_the_demotion_moved_on(tmp_path):
    w = World(tmp_path)
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    w.label(w.run(), "harmful")
    old = w.clear_value()
    assert w.click("owner", old, ts=NOW)[0] == 200  # cleared
    w.label(w.run(), "harmful", when=NOW + timedelta(seconds=9))  # a different, newer demotion
    assert (
        w.click("owner", old, ts=NOW + timedelta(seconds=20))[0] == 200
    )  # a fresh click on the OLD card
    assert (
        "test-agent",
        ACTION,
    ) in w.store.current_overrides()  # refused: the card was for another demotion
    assert [
        e.error_code for e in w.audit.events() if e.operation == "clear" and e.result == "refused"
    ] == ["stale_button"]
    assert w.click("owner", w.clear_value(), ts=NOW + timedelta(seconds=30))[0] == 200
    assert not w.store.current_overrides()


# --- D7: the workspace id ----------------------------------------------------------------------------------------------------


def test_egm_clicks_from_another_workspace_are_refused_when_a_team_is_pinned(tmp_path):
    team = "T" + "0ABCDEF12"
    w = _world(tmp_path, allowed_team_id=team)
    rid = w.run()
    assert w.click("u1", f"label|{rid}|agree", team=None)[0] == 200
    assert w.store.list_labels(rid) == []  # no team in the signed payload: refused
    assert (
        w.click("u1", f"label|{rid}|agree", team="T" + "0OTHER999", ts=NOW + timedelta(seconds=1))[
            0
        ]
        == 200
    )
    assert w.store.list_labels(rid) == []
    assert w.click("u1", f"label|{rid}|agree", team=team, ts=NOW + timedelta(seconds=2))[0] == 200
    assert [x.label for x in w.store.list_labels(rid)] == ["agree"]


# --- D10 / M2: an announcement that was not delivered is tried again -------------------------------------------------------


def test_egm_an_undelivered_demotion_card_is_retried_on_the_next_pass_and_sent_once(tmp_path):
    w = World(tmp_path)
    real = w.channel.post_card
    w.channel.post_card = lambda card: (_ for _ in ()).throw(OSError("channel down"))
    w.channel.notify = lambda who, text: (_ for _ in ()).throw(OSError("down"))
    w.label(w.run(), "harmful")
    assert w.channel.cards == []  # inserted, not announced
    w.channel.post_card = real
    w.measure.enforce(NOW)  # the next tick
    assert len(w.channel.cards) == 1
    w.measure.enforce(NOW)
    assert len(w.channel.cards) == 1  # delivered once, then recorded


def test_egm_an_undelivered_breach_notice_is_retried(tmp_path):
    w = World(tmp_path)
    real = w.channel.notify
    w.channel.notify = lambda who, text: (_ for _ in ()).throw(OSError("down"))
    w.label(w.run(), "harmful")  # breaches the default ceiling (max 0)
    assert w.channel.notices == []
    w.channel.notify = real
    w.measure.enforce(NOW)
    assert len([t for _, t in w.channel.notices if "Ceiling breached" in t]) == 1


def test_egm_a_harmful_label_checks_the_ceiling_at_once(tmp_path):
    w = World(tmp_path)
    _suggest_world(w)
    w.label(w.run(action=CD), "harmful")  # no tick in between
    assert [e for e in w.store.list_level_events() if e.reason.startswith("ceiling:")]


# --- CB2 / CB5 / CB7 / M3 ------------------------------------------------------------------------------------------------------


def test_egm_hold_labelled_false_in_the_clients_retention_rule_holds_nothing(tmp_path):
    w = World(tmp_path)
    w.label(w.run(), "wrong")
    assert w.measure.hold_run_ids()
    object.__setattr__(w.reg.config, "retention", SimpleNamespace(hold_labelled=False))
    try:
        assert w.measure.hold_run_ids() == set()
    finally:
        object.__delattr__(w.reg.config, "retention")


def test_egm_a_historical_report_counts_the_ceiling_as_it_stood_when_the_week_ended(tmp_path):
    w = World(tmp_path)
    w.label(w.run(), "harmful")  # given at NOW, after the week of WEEK ended
    text = w.measure.render_report(WEEK, NOW)
    assert "ceiling: 0 of 0 in the last 90 days, breached no" in text
    assert "state when this report was generated" in text


def test_egm_the_report_shows_current_overrides(tmp_path):
    w = World(tmp_path)
    assert "- none: every action is at its configured level" in w.measure.render_report(WEEK, NOW)
    w.label(w.run(), "harmful", when=day(3))
    assert f"test-agent.{ACTION}: shadow since" in w.measure.render_report(WEEK, NOW)


# --- m1: a two-week synthetic pilot with counts ----------------------------------------------------------------------------


def test_egm_two_week_synthetic_pilot_produces_two_reports_with_the_expected_counts(tmp_path):
    w = World(tmp_path)
    week1, week2 = WEEK - timedelta(days=7), WEEK
    for week, (agree, wrong) in ((week1, (4, 1)), (week2, (5, 0))):
        monday = __import__("datetime").datetime(
            week.year, week.month, week.day, 9, tzinfo=__import__("datetime").UTC
        )
        for i in range(agree + wrong):
            rid = w.run(created=monday + timedelta(hours=i))
            w.label(
                rid,
                "wrong" if i < wrong else "agree",
                who=("u1", "u2")[i % 2],
                when=monday + timedelta(hours=i, minutes=5),
            )
    r1 = w.measure.render_report(week1, NOW)
    r2 = w.measure.render_report(week2, NOW)
    assert "- Runs: 5. Proposals: 5." in r1 and "wrong 1, harmful 0" in r1 and "agree 4" in r1
    assert "- Runs: 5. Proposals: 5." in r2 and "wrong 0, harmful 0" in r2 and "agree 5" in r2
    assert "counted by the ceiling this week: 0 (harmful)" in r1


# --- m4: an invalid question is a refusal ------------------------------------------------------------------------------------------


def test_egm_promote_check_exit_code_2_for_an_unknown_agent_or_action(tmp_path, capsys):
    w = World(tmp_path)
    app = SimpleNamespace(
        measure=w.measure, store=w.store, config=SimpleNamespace(environment="dev")
    )
    for agent, action in (("no-agent", CD), ("test-agent", "no_such_action")):
        ns = SimpleNamespace(cmd="promote-check", agent=agent, action=action)
        assert cli.measure_cmd(app, ns) == 2
        assert "refused:" in capsys.readouterr().err
    ns = SimpleNamespace(cmd="promote-check", agent="test-agent", action=CD)
    assert cli.measure_cmd(app, ns) == 1  # a real question with unmet numbers stays 1


# --- D5: a harmful demotion has a minimum age -------------------------------------------------------------------------------


def _two_owners(w):
    w.edit_principals(
        lambda d: d.append(
            {"id": "fake:owner2", "kind": "person", "admin_rights": ["clear_override"]}
        )
    )
    w.reg.principals["fake:owner2"] = load_registry(load_config(w.cfg)).principals["fake:owner2"]


def test_egm_even_a_second_person_cannot_clear_a_harmful_demotion_sooner_than_the_minimum_age(
    tmp_path,
):
    w = World(tmp_path, policy=DEFAULT_POLICY)  # the default: 24 h
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    _two_owners(w)
    assert w.measure.record_label("fake:u1", w.run(), "harmful").demoted
    for hours, want in ((0, "too_soon"), (23, "too_soon"), (24, "cleared")):
        w.box[0] = NOW + timedelta(hours=hours)
        assert w.measure.clear("fake:owner2", "test-agent", ACTION) == (200, want)
    refused = [
        e.error_code for e in w.audit.events() if e.operation == "clear" and e.result == "refused"
    ]
    assert refused == ["too_soon", "too_soon"]


def test_egm_the_minimum_age_does_not_apply_to_a_wrongs_demotion(tmp_path):
    w = World(tmp_path, policy=DEFAULT_POLICY)
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    for i in range(3):
        w.label(w.run(), "wrong", when=NOW - timedelta(minutes=3 - i))
    assert ("test-agent", ACTION) in w.store.current_overrides()
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "cleared")


def test_egm_the_minimum_age_has_a_floor_and_is_printed(tmp_path):
    import pytest

    from hadavin_sdk.config import ConfigError

    assert DEFAULT_POLICY.harmful_clear_min_age_h == 24
    with pytest.raises(ConfigError, match="harmful_clear_min_age_h is weaker"):
        measure._policy_from({"harmful_clear_min_age_h": 23})
    assert measure._policy_from({"harmful_clear_min_age_h": 48}).harmful_clear_min_age_h == 48
    weak = measure._policy_from({"harmful_clear_min_age_h": 0, "allow_weaker_than_spec": True})
    assert weak.harmful_clear_min_age_h == 0
    text = World(tmp_path, policy=DEFAULT_POLICY).measure.render_report(WEEK, NOW)
    assert "at least 24 h after it" in text


# --- D7: the click's workspace id and own timestamp are stored and audited ----------------------------------------------


def test_egm_the_click_team_and_timestamp_are_stored_with_the_nonce_and_on_the_audit_event(
    tmp_path,
):
    from hadavin_sdk.approvals.hmac_v0 import Action

    team, other = "T" + "0ABCDEF12", "T" + "0OTHER999"
    w = _world(tmp_path, allowed_team_id=team)
    rid = w.run()
    ok = Action("fake:u1", f"label|{rid}|agree", nonce="n-ok", team=team, action_ts="1700000000.1")
    assert w.measure.handle_action(ok) == (200, "recorded")
    assert w.store.get_action("n-ok") == (team, "1700000000.1")
    bad = Action(
        "fake:u1", f"label|{rid}|agree", nonce="n-no", team=other, action_ts="1700000001.2"
    )
    assert w.measure.handle_action(bad) == (200, "wrong_team")
    assert w.store.get_action("n-no") is None  # refused before the nonce is spent
    refused = [e for e in w.audit.events() if e.error_code == "wrong_team"]
    assert [(e.team_id, e.action_ts) for e in refused] == [(other, "1700000001.2")]
    labelled = [e for e in w.audit.events() if e.action_ts == "1700000000.1"]
    assert labelled and all(e.team_id == team for e in labelled)
    w.measure.record_label("fake:u2", w.run(), "agree")  # not a click: no team on its audit rows
    assert [e for e in w.audit.events() if e.principal == "fake:u2" and e.team_id] == []


def test_egm_a_signed_click_through_the_receiver_is_audited_with_its_team_and_action_ts(tmp_path):
    team = "T" + "0ABCDEF12"
    w = _world(tmp_path, allowed_team_id=team)
    rid = w.run()
    assert w.click("u1", f"label|{rid}|agree", team=team, action_ts="1700000000.2")[0] == 200
    assert [x.label for x in w.store.list_labels(rid)] == ["agree"]
    assert any(e.team_id == team and e.action_ts == "1700000000.2" for e in w.audit.events())
