"""F-install review 4, round 2: a run never stays WORKING when an end is needed, an end is safe to repeat, and
the error that names a failed end holds no client or store exception. Fakes only: no network, no model call."""

from __future__ import annotations

import pytest

from hadavin_sdk.models import KillSwitch, RunState
from hadavin_sdk.runtime.agent_loop import RunEndFailed
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.conftest import make_cfg
from tests.test_model_gate_install import AGENT, PRINCIPAL, Client
from tests.test_s5_runtime import _doc
from tests.test_s5_runtime import build as build_rt

S = RunState
SECRET = "tenant-acme-secret-value"  # noqa: S105


@pytest.fixture
def cfg_dir(tmp_path):
    return make_cfg(tmp_path)


def _commit_then_fail(rt, monkeypatch, to_state, times=1):
    """The store commits the transition into ``to_state`` and then raises (a lost reply)."""
    real = rt.store.transition
    seen = {"n": 0}

    def flaky(run_id, expected, new, reason_code=None):
        out = real(run_id, expected, new, reason_code)
        if new == to_state and seen["n"] < times:
            seen["n"] += 1
            raise StoreUnavailable(SECRET)
        return out

    monkeypatch.setattr(rt.store, "transition", flaky)
    return seen


def _sink_raises(rt, monkeypatch, domain, operation, times=10**6, result=None):
    real = rt.audit.write_outcome
    seen = {"n": 0}

    def write(event):
        if (
            (event.domain, event.operation) == (domain, operation)
            and result in (None, event.result)
            and seen["n"] < times
        ):
            seen["n"] += 1
            raise OSError(SECRET)
        return real(event)

    monkeypatch.setattr(rt.audit, "write_outcome", write)
    return seen


def test_a_failing_commit_then_a_retry_ends_the_run_without_raising(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=RuntimeError(SECRET))
    seen = _commit_then_fail(rt, monkeypatch, S.NEEDS_PERSON)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert seen["n"] == 1
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "model_error")
    assert rt.store.get_run(run.run_id).state == S.NEEDS_PERSON


def test_a_failed_end_audit_row_is_not_a_failed_end(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=RuntimeError(SECRET))
    seen = _sink_raises(rt, monkeypatch, "run", "state", times=1, result="NEEDS_PERSON")
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert seen["n"] == 1
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "model_error")
    assert rt.store.get_run(run.run_id).state == S.NEEDS_PERSON


def test_an_audit_sink_failure_in_the_model_error_branch_still_ends_the_run(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=ValueError(SECRET))
    seen = _sink_raises(rt, monkeypatch, "llm", "chat")
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert seen["n"] >= 1
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "model_error")
    assert rt.store.get_run(run.run_id).state == S.NEEDS_PERSON


def test_the_kill_switch_end_survives_one_store_fault(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    rt.store.set_kill_switch(KillSwitch(on=True, by="t"))
    seen = _commit_then_fail(rt, monkeypatch, S.STOPPED)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert seen["n"] == 1
    assert (run.state, run.reason_code) == (S.STOPPED, "kill_switch")
    assert rt.store.get_run(run.run_id).state == S.STOPPED


def test_a_limits_stop_with_the_store_down_twice_raises_the_named_error(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    rt.store.set_kill_switch(KillSwitch(on=True, by="t"))
    real = rt.store.transition

    def down(run_id, expected, new, reason_code=None):
        if new == S.STOPPED:
            raise StoreUnavailable(SECRET)
        return real(run_id, expected, new, reason_code)

    monkeypatch.setattr(rt.store, "transition", down)
    with pytest.raises(RunEndFailed) as info:
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert info.value.state == S.STOPPED.value


def test_a_heartbeat_fault_ends_the_run(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)

    def down(run_id):
        raise StoreUnavailable(SECRET)

    monkeypatch.setattr(rt.store, "touch", down)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "store_unavailable")


def test_the_working_transition_failing_after_commit_ends_the_run(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    _sink_raises(rt, monkeypatch, "run", "state", times=1)  # the WORKING row is the first state row
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "store_unavailable")
    assert rt.store.get_run(run.run_id).state == S.NEEDS_PERSON


def _chain(exc):
    seen = []
    while exc is not None:
        seen.append(exc)
        exc = exc.__cause__ or exc.__context__
    return seen


@pytest.mark.parametrize("client_fault", [RuntimeError(SECRET), ValueError(SECRET)])
def test_run_end_failed_holds_no_client_or_store_exception(cfg_dir, monkeypatch, client_fault):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=client_fault)
    real = rt.store.transition

    def down(run_id, expected, new, reason_code=None):
        if new == S.NEEDS_PERSON:
            raise StoreUnavailable(SECRET)
        return real(run_id, expected, new, reason_code)

    monkeypatch.setattr(rt.store, "transition", down)
    with pytest.raises(RunEndFailed) as info:
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert _chain(info.value) == [info.value]
    assert info.value.__cause__ is None and info.value.__context__ is None
    assert SECRET not in repr(info.value)


def test_a_meter_outage_is_not_labelled_a_provider_problem(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    client = Client()
    rt.llm = client

    def down(*args, **kw):
        raise OSError(SECRET)

    monkeypatch.setattr(rt.limits, "reserve", down)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits_unavailable")
    assert client.calls == 0
    chat_rows = [
        e for e in rt.audit.events(run.run_id) if (e.domain, e.operation) == ("llm", "chat")
    ]
    assert len(chat_rows) == 1  # the gate's refusal row only
    assert all(e.error_code != "model_error" for e in chat_rows)
    assert SECRET not in repr(rt.audit.events(run.run_id))
