"""Stop state on the memory store and the `Limits` wrapper: requests, version, pair-checked reset, label rules."""

from __future__ import annotations

import pytest

from hadavin_sdk.audit.labelkey import NOKEY_LABEL
from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.limits import Limits, StopNotConfirmed, StopNotPermitted, SwitchChanged
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import LabelRefused, StaleCount
from tests.stop_state_helpers import KEY, RESET_NAME, expect


class Audit:
    def __init__(self, down: bool = False):
        self.events, self.down = [], down

    def write_intent(self, event):
        if self.down:
            raise AuditUnavailable("audit down")
        self.events.append(("intent", event.operation))
        return "i"

    def write_outcome(self, event):
        self.events.append(("outcome", event.operation))


def make(**kw) -> Limits:
    kw.setdefault("reset_names", {RESET_NAME})
    store = MemoryStore()
    kw.setdefault("reset_store", store)
    return Limits(store, Audit(), None, environment="dev", label_key=KEY, **kw)


def test_stop_is_a_request_and_state_reads_on():
    lim = make()
    s = lim.stop("user:a")
    assert s.on and s.open_requests == 1 and s.by.startswith("id:k1:")
    assert lim.stop("user:b").open_requests == 2
    assert ("outcome", "stop") in lim.audit.events


def test_reset_needs_the_exact_pair():
    lim = make()
    lim.stop("user:a")
    e = expect(lim)
    lim.stop("user:b")  # a second stop lands after the operator read the status
    with pytest.raises(SwitchChanged):
        lim.reset(RESET_NAME, **e)
    assert lim.status().on
    s = lim.reset(RESET_NAME, **expect(lim))
    assert not s.on and s.open_requests == 0 and s.version == 1


def test_reset_of_an_already_off_switch_is_stale():
    lim = make()
    with pytest.raises(SwitchChanged):
        lim.reset(RESET_NAME, **expect(lim))


def test_unlisted_name_and_missing_handle_refused_and_switch_stays_on():
    lim = make()
    lim.stop("user:a")
    with pytest.raises(StopNotPermitted):
        lim.reset("user:z", **expect(lim))
    assert ("outcome", "reset_denied") in lim.audit.events
    no_handle = make(reset_store=None)
    no_handle.stop("user:a")
    with pytest.raises(StopNotPermitted):
        no_handle.reset(RESET_NAME, **expect(no_handle))
    assert no_handle.status().on


def test_reset_with_listed_name_refused_when_audit_down():
    lim = make()
    lim.stop("user:a")
    lim.audit.down = True
    with pytest.raises(AuditUnavailable):
        lim.reset(RESET_NAME, **expect(lim))
    assert lim.status().on


@pytest.mark.parametrize("bad", [True, -1, 2**63, "1", 1.0, None])
def test_reset_rejects_out_of_range_counts(bad):
    lim = make()
    lim.stop("user:a")
    with pytest.raises(ValueError):
        lim.reset(RESET_NAME, expect_version=bad, expect_open=1)
    with pytest.raises(ValueError):
        lim.reset(RESET_NAME, expect_version=0, expect_open=bad)


def test_stop_survives_a_short_key_with_the_nokey_label():
    store = MemoryStore()
    lim = Limits(store, Audit(), None, environment="dev", label_key=b"short")
    s = lim.stop("user:a")
    assert s.on and s.by == NOKEY_LABEL
    with pytest.raises(StopNotPermitted):
        lim.label("user:a")
    with pytest.raises(StopNotPermitted):
        lim.reset("user:a", expect_version=0, expect_open=1)


def test_store_refuses_forged_labels_and_start_state():
    st = MemoryStore()
    with pytest.raises(LabelRefused):
        st.set_kill_switch(KillSwitch(on=True, by="user:a"))
    with pytest.raises(LabelRefused):
        st.set_kill_switch(KillSwitch(on=True, by="id:k1:" + "a" * 32 + "\n"))
    with pytest.raises(ValueError):
        st.set_kill_switch(KillSwitch(on=False, by="id:k1:" + "a" * 32))
    with pytest.raises(LabelRefused):
        st.reset_kill_switch("user:a", 0, 0)
    with pytest.raises(StaleCount):
        st.reset_kill_switch("id:k1:" + "a" * 32, 0, 0)


def test_memory_store_refused_outside_demo_stage_and_key_required():
    with pytest.raises(ValueError):
        Limits(MemoryStore(), Audit(), None, environment="pilot", label_key=KEY)
    with pytest.raises(ValueError):
        Limits(object(), Audit(), None, environment="pilot")
    with pytest.raises(ValueError):
        Limits(MemoryStore(), Audit(), None, environment="dev", label_key=KEY, key_id="bad id")


def test_confirmation_failure_is_loud():
    class Lying(MemoryStore):
        def set_kill_switch(self, ks):
            return super().get_kill_switch()

    lim = Limits(Lying(), Audit(), None, environment="dev", label_key=KEY)
    with pytest.raises(StopNotConfirmed):
        lim.stop("user:a")


def test_a_wrong_version_alone_makes_the_pair_stale():
    lim = make()
    lim.stop("user:a")
    good = expect(lim)
    with pytest.raises(SwitchChanged):
        lim.reset(
            RESET_NAME, expect_version=good["expect_version"] + 1, expect_open=good["expect_open"]
        )
    assert lim.status().on
