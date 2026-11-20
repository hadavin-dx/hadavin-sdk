"""F-install review 4: a run never stays WORKING when the model client or the store fails while it is ended.

Fakes only: no network, no real model call. Fixtures come from the existing test modules.
"""

from __future__ import annotations

import pytest

from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.models import RunState
from hadavin_sdk.runtime.agent_loop import RunEndFailed
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.conftest import make_cfg
from tests.test_model_gate_install import AGENT, PRINCIPAL, Client
from tests.test_s5_runtime import _doc
from tests.test_s5_runtime import build as build_rt

S = RunState
SECRET = "tenant-acme-secret-value"  # noqa: S105

# every injectable failure of the model client and the ending the run must reach
CLIENT_FAILURES = [
    (ValueError(SECRET), "model_error"),
    (RuntimeError(SECRET), "model_error"),
    (TimeoutError(SECRET), "model_error"),
    (KeyError(SECRET), "model_error"),
    (ProviderError(SECRET), "provider_error"),
    (ProviderExhausted(SECRET), "provider_exhausted"),
]


@pytest.fixture
def cfg_dir(tmp_path):
    return make_cfg(tmp_path)


@pytest.mark.parametrize(
    ("exc", "code"), CLIENT_FAILURES, ids=[type(e).__name__ for e, _ in CLIENT_FAILURES]
)
def test_a_client_failure_never_leaves_the_run_working(cfg_dir, exc, code):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=exc)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    stored = rt.store.get_run(run.run_id)
    assert stored.state == run.state == S.NEEDS_PERSON != S.WORKING
    assert run.reason_code == code
    assert SECRET not in (run.reason_code or "")


def test_a_client_failure_writes_no_raw_text_to_the_audit_trail(cfg_dir):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=RuntimeError(SECRET))
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert SECRET not in repr(rt.audit.events(run.run_id))


def _fail_transition(rt, monkeypatch, times, to_state):
    """Make the store's transition into ``to_state`` raise the first ``times`` times."""
    real = rt.store.transition
    seen = {"n": 0}

    def flaky(run_id, expected, new, reason_code=None):
        if new == to_state and seen["n"] < times:
            seen["n"] += 1
            raise StoreUnavailable(SECRET)
        return real(run_id, expected, new, reason_code)

    monkeypatch.setattr(rt.store, "transition", flaky)
    return seen


def test_one_store_fault_while_ending_is_retried_and_the_run_ends(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=RuntimeError("x"))
    seen = _fail_transition(rt, monkeypatch, 1, S.NEEDS_PERSON)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert seen["n"] == 1
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "model_error")
    assert rt.store.get_run(run.run_id).state == S.NEEDS_PERSON


def test_a_refusal_ending_survives_one_store_fault(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)

    def down(*args, **kw):
        raise StoreUnavailable("store down")

    monkeypatch.setattr(rt.store, "reserve_spend", down)
    _fail_transition(rt, monkeypatch, 1, S.NEEDS_PERSON)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits_unavailable")
    assert rt.store.get_run(run.run_id).state == S.NEEDS_PERSON


def test_two_store_faults_raise_the_named_error_without_store_text(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    rt.llm = Client(raises=RuntimeError("x"))
    _fail_transition(rt, monkeypatch, 2, S.NEEDS_PERSON)
    with pytest.raises(RunEndFailed) as info:
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
    assert SECRET not in str(info.value)
    assert info.value.reason_code == "model_error" and info.value.state == S.NEEDS_PERSON.value


def test_two_store_faults_in_a_redaction_failure_ending_raise_the_named_error(cfg_dir, monkeypatch):
    rt, cfg = build_rt(cfg_dir)
    _fail_transition(rt, monkeypatch, 2, S.NEEDS_PERSON)

    def down(*args, **kw):
        raise StoreUnavailable("store down")

    monkeypatch.setattr(rt.store, "reserve_spend", down)
    with pytest.raises(RunEndFailed):
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "create.txt"))
