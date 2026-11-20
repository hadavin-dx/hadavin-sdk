"""d-fix28: the bounds that ONLY the Runner (and the secret check) enforce, after `check_fields` has taken
max_running, conflict_events_per_minute and ack_wait_s: poll_s and max_waiting (arguments of make_app) and the
secret values. make_app turns each into a worker ConfigError that names the bound and never a value."""

from __future__ import annotations

import pytest

from hadavin_sdk.triggers import worker
from tests.triggers.test_worker import (
    SECRET,
    _app,
    _settings,
    rt,  # noqa: F401 - fixture
)


@pytest.mark.parametrize(
    ("kw", "words"),
    [
        ({"poll_s": 5.0}, "poll_s"),
        ({"poll_s": 0.0001}, "poll_s"),
        ({"max_waiting": 0}, "max_waiting"),
        ({"max_waiting": True}, "max_waiting"),
    ],
)
def test_make_app_turns_a_runner_only_bound_into_a_config_error(rt, kw, words):  # noqa: F811
    with pytest.raises(worker.ConfigError, match=words) as info:
        worker.make_app(_app(rt, _settings(max_running=1)), **kw)
    assert type(info.value) is worker.ConfigError  # not the Runner's plain ValueError
    assert SECRET not in str(info.value)


def test_make_app_turns_a_bad_secret_into_a_config_error_without_the_value(rt):  # noqa: F811
    bad = " padded-secret-value "
    with pytest.raises(worker.ConfigError, match="whitespace") as info:
        worker.make_app(_app(rt, _settings(max_running=1), secrets={"door-a": bad}))
    assert "padded-secret-value" not in str(info.value)
