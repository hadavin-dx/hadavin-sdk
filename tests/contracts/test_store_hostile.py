"""P4d-a2-ii, both stores: plan_id reuse, the tick step grammar, list_approvals order, hostile values."""

from datetime import timedelta

import pytest

from hadavin_sdk.models import (
    ApprovalRequest,
    ChainStep,
    DeadLetter,
    Plan,
    Run,
    Target,
    TickState,
    now,
)
from hadavin_sdk.store.protocol import StaleState, check_step_name, check_text


def _run(store, agent="a"):
    run = Run(agent_id=agent, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


def _plan(run_id, **kw):
    return Plan(
        run_id=run_id,
        agent_id="a",
        action_id="act",
        action_version=1,
        risk_class="reversible",
        inputs=kw.pop("inputs", {"k": 1}),
        target=Target(system="crm", ref="r-1"),
        idempotency_key="idem-1",
        expected_outcome=kw.pop("outcome", "done"),
        **kw,
    )


def _request(store, approval_id, created_at):
    store.save_approval_request(
        ApprovalRequest(
            approval_id=approval_id,
            run_id="run-x",
            plan_hash="h",
            risk_class="reversible",
            chain_id="c",
            steps=[ChainStep(approver_ids=["user:a"], timeout_s=60)],
            status="PENDING",
            step_expires_at=now() + timedelta(minutes=1),
            requested_by="svc:a",
            summary="s",
            created_at=created_at,
        )
    )


def test_a_plan_id_used_by_another_run_is_stale_state_and_the_first_plan_stays(store):
    first, second = _run(store), _run(store)
    plan = _plan(first.run_id)
    store.save_plan(plan)
    with pytest.raises(StaleState):
        store.save_plan(_plan(second.run_id, plan_id=plan.plan_id, outcome="other"))
    assert store.get_plan(first.run_id).expected_outcome == "done"
    store.save_plan(
        plan.model_copy(update={"expected_outcome": "again"})
    )  # same run: still a replace
    assert store.get_plan(first.run_id).expected_outcome == "again"


@pytest.mark.parametrize("step", ["abc\n", "abc ", "ABC", "", "sweep-1", "sweep1", "é", "a\x00b"])
def test_a_bad_tick_step_is_refused(store, step):
    with pytest.raises(ValueError):
        store.save_tick_state(TickState(step=step, last_run_at=now()))
    assert store.get_tick_state("sweep") is None


def test_a_good_tick_step_is_kept(store):
    store.save_tick_state(TickState(step="sweep_old", last_run_at=now()))
    assert store.get_tick_state("sweep_old") is not None


def test_check_step_name_is_a_full_match():
    assert check_step_name("a_b") == "a_b"
    for bad in ("a_b\n", "A", "", "a-b", 5, None):
        with pytest.raises(ValueError):
            check_step_name(bad)


def test_list_approvals_is_oldest_first_with_the_id_as_tie_break(store):
    base = now()
    _request(store, "apr-3", base)
    _request(store, "apr-1", base + timedelta(seconds=5))
    _request(store, "apr-2", base)
    got = [r.approval_id for r in store.list_approvals({"PENDING"})]
    assert got == ["apr-2", "apr-3", "apr-1"]


@pytest.mark.parametrize(
    "text", ["a\x00b", "a\ud800b", "\udfff"], ids=["nul", "lone-high-surrogate", "lone-low"]
)
def test_nul_and_lone_surrogates_are_refused_in_any_text_field(store, text):
    run = _run(store)
    with pytest.raises(ValueError):
        store.transition(run.run_id, run.state, run.state.__class__.WORKING, reason_code=text)
    with pytest.raises(ValueError):
        store.add_dead_letter(DeadLetter(run_id=run.run_id, reason=text, errors=[]))
    with pytest.raises(ValueError):
        store.save_plan(_plan(run.run_id, inputs={"deep": [{"k": text}]}))
    with pytest.raises(ValueError):
        store.save_plan(_plan(run.run_id, inputs={text: 1}))  # a dict key too
    assert store.get_run(run.run_id).reason_code is None
    assert store.list_dead_letters(run.run_id) == []


def test_non_finite_floats_in_nested_data_are_refused(store):
    run = _run(store)
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            store.save_plan(_plan(run.run_id, inputs={"x": [bad]}))


def test_check_text_message_does_not_echo_the_value():
    with pytest.raises(ValueError) as caught:
        check_text(DeadLetter(run_id="r", reason="sec\x00ret-value", errors=[]))
    assert "ret-value" not in str(caught.value)


@pytest.mark.parametrize(
    "text",
    [
        "x" * 1_000_000,
        "".join(
            map(
                chr,
                [
                    0x65,
                    0x301,
                    0x20,
                    0xE9,
                    0x20,
                    0x1F600,
                    0x20,
                    0x5E9,
                    0x5DC,
                    0x5D5,
                    0x5DD,
                    0x20,
                    0x202E,
                ],
            )
        ),
        "'; DROP TABLE runs;--",
        "%s %(x)s {} {0}",
    ],
    ids=["one-megabyte", "unicode", "sql-looking", "format-looking"],
)
def test_hostile_text_round_trips_verbatim_and_the_tables_remain(store, text):
    run = _run(store)
    store.save_plan(_plan(run.run_id, outcome=text))
    assert store.get_plan(run.run_id).expected_outcome == text
    store.add_dead_letter(DeadLetter(run_id=run.run_id, reason=text, errors=[text]))
    assert store.list_dead_letters(run.run_id)[0].errors == [text]
    assert store.get_run(run.run_id).run_id == run.run_id
