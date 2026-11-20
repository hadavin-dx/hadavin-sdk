"""`triggers.conflict_events_per_minute` (request 005): the cap on `trigger.conflict` audit events per sender per
minute. Strict int, 1 to 1000, default 10, outside ``config_hash`` like the rest of `triggers`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hadavin_sdk import defaults
from hadavin_sdk.config import TriggerSettings

SENDERS = {
    "alpha": {"secret_names": ["k1"], "agent_id": "test-agent", "principal_id": "svc:test-agent"}
}


def make(**more):
    return TriggerSettings(tenant="acme", senders=SENDERS, **more)


def test_constants():
    assert defaults.TRIGGER_CONFLICT_EVENTS_DEFAULT == 10
    assert defaults.TRIGGER_CONFLICT_EVENTS_MIN == 1
    assert defaults.TRIGGER_CONFLICT_EVENTS_MAX == 1000


def test_default_is_ten():
    assert make().conflict_events_per_minute == 10


@pytest.mark.parametrize("ok", [1, 10, 1000])
def test_accepts_in_range(ok):
    assert make(conflict_events_per_minute=ok).conflict_events_per_minute == ok


@pytest.mark.parametrize("bad", [0, 1001, -1, True, 5.0, "10", None])
def test_refuses_out_of_range_or_wrong_type(bad):
    with pytest.raises(ValidationError) as caught:
        make(conflict_events_per_minute=bad)
    assert "conflict_events_per_minute" in str(caught.value)


def test_unknown_extra_key_still_refused():
    with pytest.raises(ValidationError):
        make(conflict_events_per_minut=5)
