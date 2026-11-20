"""D-config hardening, round 3 (the second hostile review): path-shaped names, Unicode folds, a lying str subclass,
floors on the trigger limits, and a ConfigError for a sender section that keeps no pydantic cause.

Each test was written before its fix and failed on the code at the start of the round."""

import pathlib
import tempfile

import pytest
from pydantic import ValidationError

from hadavin_sdk import defaults
from hadavin_sdk.actions.secrets_env import EnvSecretProvider
from hadavin_sdk.actions.secrets_file import MountedFileProvider
from hadavin_sdk.app import _sender_secrets
from hadavin_sdk.backends import platform_secrets
from hadavin_sdk.config import TriggerSettings, load_config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.secret_name import canonical_secret_name, collides
from tests.conftest import make_cfg
from tests.k5_support import edit_config

VALUE = "x"  # a filler, not a credential


class Provider:
    def __init__(self):
        self.calls: list = []

    def get(self, name):
        self.calls.append(name)
        return VALUE


# --- M1: a name with a dot-segment or a leading/trailing "/" is refused, not folded -------------------------------

PATHY = [
    "a/../slack_token",
    "./slack_token",
    "b/c/../../slack_token",
    "/slack_token",
    "slack_token/",
    "a/./slack_token",
]


@pytest.mark.parametrize("other", PATHY)
def test_check_senders_refuses_a_path_shaped_other_name(other):
    provider = Provider()
    with pytest.raises(ConfigError) as caught:
        platform_secrets.check_senders(provider, {"s": ["slack_token"]}, {other})
    assert other not in str(caught.value) and "slack_token" not in str(caught.value)
    assert provider.calls == []


def test_check_senders_still_accepts_a_plain_slashed_other_name():
    platform_secrets.check_senders(Provider(), {"s": ["slack_token"]}, {"team/other-secret"})


@pytest.mark.parametrize("other", PATHY)
def test_collides_fails_closed_on_a_path_shaped_name(other):
    assert collides(other, ["unrelated"])
    assert collides("unrelated", [other])


def test_the_mounted_file_provider_really_aliases_such_a_name():
    d = pathlib.Path(tempfile.mkdtemp())
    f = d / "slack_token"
    f.write_text("v")
    f.chmod(0o400)
    provider = MountedFileProvider(d)
    assert provider.get("a/../slack_token") == provider.get("slack_token")
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(provider, {"s": ["slack_token"]}, {"a/../slack_token"})


# --- L1: replace non-ASCII-alphanumerics first, then lower-case ----------------------------------------------------


@pytest.mark.parametrize("fold", ["slackİtoken", "slackKtoken"])
def test_unicode_case_folds_collide_with_the_ascii_env_name(fold):
    env = EnvSecretProvider("P_", {})
    assert env.var(fold) == env.var("slack_token")  # the provider really folds them together
    assert canonical_secret_name(fold) == canonical_secret_name("slack_token")
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(Provider(), {"s": ["slack_token"]}, {fold})


# --- L2: the reader accepts only a real str ------------------------------------------------------------------------


class Liar(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return hash("good-name")


def test_the_reader_refuses_a_str_subclass_with_a_lying_eq():
    provider = Provider()
    read = _sender_secrets(provider, {"good-name"})
    with pytest.raises(PermissionError):
        read(Liar("anything"))
    assert provider.calls == []


def test_the_reader_refuses_an_unhashable_argument_as_a_permission_error():
    provider = Provider()
    read = _sender_secrets(provider, {"good-name"})
    with pytest.raises(PermissionError):
        read(["good-name"])  # type: ignore[arg-type]
    assert provider.calls == []


def test_the_reader_still_serves_a_real_name_and_states_the_closure_limit():
    read = _sender_secrets(Provider(), {"good-name"})
    assert read("good-name") == VALUE
    assert "closure" in (_sender_secrets.__doc__ or "")


# --- L3: floors ---------------------------------------------------------------------------------------------------

SENDERS = {"a": {"secret_names": ["k1"], "agent_id": "x", "principal_id": "y"}}


def test_the_floors_are_named_constants():
    assert defaults.TRIGGER_MAX_BODY_BYTES_FLOOR == 1024
    assert defaults.TRIGGER_ACK_WAIT_S_FLOOR == 0.1


@pytest.mark.parametrize("value", [1, 1023])
def test_max_body_bytes_below_the_floor_is_refused(value):
    with pytest.raises(ValidationError):
        TriggerSettings(tenant="t", senders=SENDERS, max_body_bytes=value)


def test_max_body_bytes_at_the_floor_is_accepted():
    t = TriggerSettings(
        tenant="t", senders=SENDERS, max_body_bytes=defaults.TRIGGER_MAX_BODY_BYTES_FLOOR
    )
    assert t.max_body_bytes == 1024


@pytest.mark.parametrize("value", [5e-324, 1e-300, 0.0005, 0.0999])
def test_ack_wait_below_the_floor_is_refused(value):
    with pytest.raises(ValidationError):
        TriggerSettings(tenant="t", senders=SENDERS, ack_wait_s=value)


def test_ack_wait_at_the_floor_is_accepted():
    assert TriggerSettings(tenant="t", senders=SENDERS, ack_wait_s=0.1).ack_wait_s == 0.1


# --- L4: a sender-section ConfigError keeps no pydantic cause --------------------------------------------------------


def test_a_bad_sender_section_raises_a_config_error_without_the_cause(tmp_path):
    secret_like = "hunter2 REAL secret"  # noqa: S105 - a mistyped entry, not a credential
    cfg = make_cfg(tmp_path)
    edit_config(
        cfg,
        lambda c: c.update(
            triggers={
                "tenant": "t1",
                "senders": {
                    "s1": {
                        "secret_names": [secret_like],
                        "agent_id": "test-agent",
                        "principal_id": "p",
                    }
                },
            }
        ),
    )
    with pytest.raises(ConfigError) as caught:
        load_config(cfg)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
    assert secret_like not in str(caught.value)
