"""`App.trigger_secret`, the reader the trigger worker gets (fix round 3 of F-store): a provider failure becomes
RuntimeError("sender secret unavailable") with no secret name anywhere in it, and a name that is not a sender
secret is a PermissionError that never reaches the provider.

Written by a different agent than the builder, through the real build path (`app.build` on the fixture config
folder, as tests/test_p1b_backends.py does). The provider is a double that counts its calls and can be told to fail
after start-up, with an error whose text carries the name that was asked for.
"""

import pathlib

import pytest

from hadavin_sdk.app import build
from hadavin_sdk.config import load_config
from hadavin_sdk.registry import load_registry
from tests.conftest import make_cfg, qualify
from tests.k5_support import edit_config

TOKEN = "tok" + "-sender"  # built from parts: not a real-looking credential
SENDER_A = "sender-key-a"
SENDER_B = "sender-key-b"
EXECUTOR = "fixture-token"
STRANGER = "not-a-sender-secret"


class CountingProvider:
    """A secret provider that remembers every name it was asked for and can fail on demand."""

    def __init__(self, values):
        self.values = dict(values)
        self.calls: list[str] = []
        self.failure: Exception | None = None

    def get(self, name):
        self.calls.append(name)
        if self.failure is not None:
            raise self.failure
        if name not in self.values:
            raise KeyError(name)
        return self.values[name]


@pytest.fixture
def world(tmp_path: pathlib.Path):
    cfg = make_cfg(tmp_path)
    edit_config(
        cfg,
        lambda c: c.update(
            triggers={
                "tenant": "t1",
                "senders": {
                    "s1": {
                        "secret_names": [SENDER_A, SENDER_B],
                        "agent_id": "test-agent",
                        "principal_id": "svc:test-agent",
                    }
                },
            }
        ),
    )
    qualify(load_registry(load_config(cfg)))
    provider = CountingProvider({EXECUTOR: TOKEN, SENDER_A: TOKEN + "-a", SENDER_B: TOKEN + "-b"})
    app = build(cfg, ["test-agent"], secrets=provider)
    provider.calls.clear()  # what the start-up read is not under test
    return app, provider


def test_a_sender_secret_is_read_through_the_provider(world):
    app, provider = world
    assert app.trigger_secret(SENDER_A) == TOKEN + "-a"
    assert app.trigger_secret(SENDER_B) == TOKEN + "-b"
    assert provider.calls == [SENDER_A, SENDER_B]


@pytest.mark.parametrize(
    "error",
    [
        KeyError(SENDER_A),
        RuntimeError(f"cannot read {SENDER_A} from the vault"),
        ValueError(SENDER_A),
        PermissionError(f"denied: {SENDER_A}"),
        OSError(f"/run/secrets/{SENDER_A}: no such file"),
        TimeoutError(SENDER_A),
        Exception(f"boom {SENDER_A} boom"),
    ],
    ids=lambda e: type(e).__name__,
)
def test_a_provider_failure_is_one_generic_runtime_error_without_the_name(world, error):
    app, provider = world
    provider.failure = error
    with pytest.raises(RuntimeError) as caught:
        app.trigger_secret(SENDER_A)
    exc = caught.value
    assert type(exc) is RuntimeError
    assert str(exc) == "sender secret unavailable"
    assert exc.args == ("sender secret unavailable",)
    assert exc.__cause__ is None
    assert (
        exc.__suppress_context__ is True
    )  # `from None`: the provider's error is not shown as the context
    assert SENDER_A not in repr(exc) and SENDER_A not in str(exc)
    assert provider.calls == [SENDER_A]


def test_the_failure_text_holds_the_name_nowhere_in_the_whole_chain(world):
    import traceback

    app, provider = world
    provider.failure = RuntimeError(f"vault said no for {SENDER_B}")
    with pytest.raises(RuntimeError) as caught:
        app.trigger_secret(SENDER_B)
    shown = "".join(traceback.format_exception(caught.value))
    assert SENDER_B not in shown and "vault said no" not in shown


@pytest.mark.parametrize("name", [STRANGER, EXECUTOR, "", "SENDER-KEY-A", SENDER_A + " ", "s1"])
def test_a_name_that_is_not_a_sender_secret_is_a_permission_error_and_never_reaches_the_provider(
    world, name
):
    app, provider = world
    with pytest.raises(PermissionError) as caught:
        app.trigger_secret(name)
    assert provider.calls == []
    if len(name) > 3:
        assert name not in str(caught.value)  # the refusal never shows the name that was asked for
    # the same refusal while the provider is down: the name check wins, the provider is still not called
    provider.failure = RuntimeError("down")
    with pytest.raises(PermissionError):
        app.trigger_secret(name)
    assert provider.calls == []


def test_a_provider_that_recovers_serves_the_next_call(world):
    app, provider = world
    provider.failure = OSError("down")
    with pytest.raises(RuntimeError, match="sender secret unavailable"):
        app.trigger_secret(SENDER_A)
    provider.failure = None
    assert app.trigger_secret(SENDER_A) == TOKEN + "-a"
    assert provider.calls == [SENDER_A, SENDER_A]


def test_a_missing_value_in_the_provider_is_the_same_generic_error(world):
    app, provider = world
    del provider.values[SENDER_B]  # the provider raises its own KeyError(name)
    with pytest.raises(RuntimeError, match="^sender secret unavailable$") as caught:
        app.trigger_secret(SENDER_B)
    assert SENDER_B not in str(caught.value)
    assert caught.value.__cause__ is None


def test_the_reader_is_not_the_global_provider(world):
    app, provider = world
    assert not hasattr(app.trigger_secret, "get")
    with pytest.raises(PermissionError):
        app.trigger_secret(EXECUTOR)  # a real secret of the app that is no sender's
    assert provider.calls == []
