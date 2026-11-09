"""`Limits` rules that need no database: the stage names, the one retry of a busy stop, the probe verdicts."""

from __future__ import annotations

import pytest

from hadavin_sdk.limits import Limits
from hadavin_sdk.models import GuardReport, KillSwitch, StopState
from hadavin_sdk.runtime import stop_state
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import StoreBusy
from tests.stop_state_helpers import KEY


class Audit:
    def write_intent(self, event):
        return "i"

    def write_outcome(self, event):
        return None


@pytest.mark.parametrize("stage", ["demo", "staging", "test", "", "DEV", None])
def test_only_dev_pilot_prod_are_stages_and_demo_is_not_an_alias_of_dev(stage):
    with pytest.raises(ValueError, match="environment must be one of"):
        Limits(MemoryStore(), Audit(), None, environment=stage, label_key=KEY)


@pytest.mark.parametrize("stage", ["pilot", "prod"])
def test_a_memory_store_and_a_missing_key_are_refused_outside_dev(stage):
    with pytest.raises(ValueError, match="memory store"):
        Limits(MemoryStore(), Audit(), None, environment=stage, label_key=KEY)


class Flaky:
    """A store whose stop is busy `fails` times, then works."""

    def __init__(self, fails):
        self.fails, self.calls = fails, 0

    def set_kill_switch(self, ks: KillSwitch) -> StopState:
        self.calls += 1
        if self.calls <= self.fails:
            raise StoreBusy("busy")
        return StopState(on=True, by=ks.by, open_requests=1)


def _limits(stop_store):
    return Limits(
        MemoryStore(), Audit(), None, environment="dev", label_key=KEY, stop_store=stop_store
    )


def test_a_busy_stop_is_tried_once_more_then_works():
    s = Flaky(1)
    assert _limits(s).stop("user:a").on is True and s.calls == 2


def test_a_stop_that_is_busy_twice_raises_store_busy_and_is_not_tried_a_third_time():
    s = Flaky(5)
    with pytest.raises(StoreBusy):
        _limits(s).stop("user:a")
    assert s.calls == 2


def test_store_busy_is_not_a_connectivity_error():
    from hadavin_sdk.store.protocol import is_connectivity_error

    assert is_connectivity_error(StoreBusy("x")) is False


class Reporting:
    def __init__(self, report=None, exc=None):
        self.report, self.exc = report, exc

    def guard_report(self, runtime_role, stop_role, reset_group):
        if self.exc:
            raise self.exc
        return self.report


def _probe(store, env="pilot"):
    return stop_state.probe(
        store, environment=env, runtime_role="rt", stop_role="st", reset_group="g"
    )


def test_probe_verdicts():
    ok = GuardReport(runtime_connection_limit=20, stop_connection_limit=2)
    assert _probe(Reporting(ok)).status == stop_state.OK
    assert _probe(Reporting(GuardReport(problems=("x",)))).status == stop_state.FAILED
    assert _probe(Reporting(exc=StoreBusy("b"))).status == stop_state.INCONCLUSIVE


def test_a_superuser_owned_function_fails_pilot_and_prod_but_only_warns_in_dev():
    r = GuardReport(dev_tolerated=("owned by a superuser",), runtime_connection_limit=20)
    assert _probe(Reporting(r), "dev").status == stop_state.OK
    assert _probe(Reporting(r), "pilot").status == stop_state.FAILED
    assert _probe(Reporting(r), "prod").status == stop_state.FAILED


def test_a_runtime_role_without_a_connection_limit_fails_in_pilot():
    assert _probe(Reporting(GuardReport(runtime_connection_limit=-1))).status == stop_state.FAILED


def test_the_memory_store_probe_is_ok():
    assert _probe(MemoryStore(), "dev").status == stop_state.OK
