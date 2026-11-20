"""The loop's two limit reads: an unreadable limits store sends the run to a person (stop means stop); it never
raises out of the loop and never lets the action go ahead."""

from __future__ import annotations

import pytest

from hadavin_sdk.models import RunState
from tests.test_review_pr3_round2 import _approve, _doc, _pending
from tests.test_review_pr3_round2 import app as _pr3_app

S = RunState


@pytest.fixture(name="app")
def loop_app(live_cfg_dir, fake_system):
    return _pr3_app.__wrapped__(live_cfg_dir, fake_system)


def _boom(*a, **k):
    raise RuntimeError("limits store down")


def test_unreadable_limits_at_the_recheck_needs_a_person_and_nothing_runs(
    app, fake_system, monkeypatch
):
    run = app.runtime.handle("test-agent", "svc:test-agent", _doc(app, "create.txt"))
    monkeypatch.setattr(app.limits, "blocked", _boom)
    _approve(app, _pending(app, run.run_id))
    final = app.store.get_run(run.run_id)
    assert (final.state, final.reason_code) == (S.NEEDS_PERSON, "recheck.limits_unavailable")
    assert fake_system.creates == 0


def test_unreadable_limits_at_the_first_check_needs_a_person(app, fake_system, monkeypatch):
    monkeypatch.setattr(app.limits, "blocked", _boom)
    run = app.runtime.handle("test-agent", "svc:test-agent", _doc(app, "create.txt"))
    assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "limits_unavailable")
    assert fake_system.creates == 0
