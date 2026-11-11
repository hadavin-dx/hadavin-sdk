"""The approval receiver answers only the callback path of the configured channel kind (Q8a-2).

No database: a callback with a bad signature is refused before the store is touched. Every server listens on
port 0 (any free port) and is closed in ``finally``. Names that the change adds or removes are looked up with
``getattr`` so this file loads on the code before the change and each test fails there on its own assertion.
"""

import http.client
import random
import re
import string
import threading
from contextlib import contextmanager

import pytest

from hadavin_sdk.approvals import FakeChannel, receiver
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.approvals.slack_channel import SlackChannel
from hadavin_sdk.errors import ConfigError

SIG = "sig" + "-q8a2"  # built from parts
TOKEN = "xoxb" + "-q8a2-fake"  # built from parts
NEUTRAL, VENDOR = "/channel/actions", "/slack/actions"
REFUSAL = "callback_path must be a path such as /channel/actions"


def _approvals(channel) -> Approvals:
    return Approvals(None, None, None, channel, lambda *a: None)


def _slack() -> SlackChannel:
    return SlackChannel("C1", TOKEN, SIG)  # a callback with a bad signature makes no network call


@contextmanager
def _served(channel):
    server = receiver.serve(_approvals(channel), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def _post(port: int, path: str) -> int:
    """POST an unsigned body to `path` exactly as written (no normalising) and return the status."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("POST", path, body=b"payload=x")
        return conn.getresponse().status
    finally:
        conn.close()


class FutureChannel(FakeChannel):
    name = "future"
    callback_path = "/future-kind/actions"


class BareChannel:
    """A channel object that names no callback path at all (not derived from FakeChannel)."""

    name = "bare"

    def parse_decision(self, headers, body, now_ts):
        return None


class NamelessChannel:
    def parse_decision(self, headers, body, now_ts):
        return None


# ---- must fail on the code before the change ----------------------------------------------------------------------


def test_the_fake_kind_is_served_on_the_neutral_path():
    with _served(FakeChannel(SIG)) as port:
        assert _post(port, NEUTRAL) == 401  # reached the signature check


def test_the_fake_kind_does_not_answer_the_vendor_path():
    with _served(FakeChannel(SIG)) as port:
        assert _post(port, VENDOR) == 404


def test_a_future_kind_is_served_on_its_own_path_only():
    with _served(FutureChannel(SIG)) as port:
        assert _post(port, FutureChannel.callback_path) == 401
        assert _post(port, NEUTRAL) == 404
        assert _post(port, VENDOR) == 404


def _with_path(value) -> FakeChannel:
    return type("BadPathChannel", (FakeChannel,), {"callback_path": value})(SIG)


BAD_PATHS = [
    None,
    "",
    "slack/actions",
    "/a b",
    "/a?x",
    "/a/../b",
    "/",
    "/a//b",
    "/A",
    "/" + "a" * 64,  # 65 characters
    5,
    "/a\n",
    "/a/",
    "/-a",
    "/a-",
    b"/a",
]


def _assert_serve_refuses(channel, message: str) -> None:
    server = None
    try:
        with pytest.raises(ConfigError, match=re.escape(message)):
            server = receiver.serve(_approvals(channel), port=0)
    finally:
        if server is not None:
            server.server_close()


@pytest.mark.parametrize("value", BAD_PATHS, ids=repr)
def test_serve_refuses_a_malformed_callback_path(value):
    _assert_serve_refuses(_with_path(value), f"channel fake: {REFUSAL}")


def test_serve_refuses_a_channel_without_a_callback_path_and_names_it():
    _assert_serve_refuses(BareChannel(), f"channel bare: {REFUSAL}")
    _assert_serve_refuses(NamelessChannel(), f"channel NamelessChannel: {REFUSAL}")


def test_each_kind_names_its_callback_path():
    assert getattr(FakeChannel, "callback_path", None) == NEUTRAL
    assert getattr(SlackChannel, "callback_path", None) == VENDOR


def test_the_handler_was_renamed_without_an_alias():
    assert hasattr(receiver, "handle_action")
    assert not hasattr(receiver, "handle_slack_action")
    assert not hasattr(receiver, "PATH")


def test_handle_action_refuses_an_oversize_body_and_a_bad_signature():
    handle = getattr(receiver, "handle_action", None)
    assert handle is not None
    approvals = _approvals(FakeChannel(SIG))
    assert handle(approvals, {}, b"x" * (receiver.MAX_BODY + 1)) == (413, b"")
    assert handle(approvals, {}, b"payload=x") == (401, b"")


def _checked_path(value):
    check = getattr(receiver, "callback_path", None)
    assert check is not None
    return check(_approvals(_with_path(value)))


_OK_CHARS = string.ascii_lowercase + string.digits


def _valid_path(rng: random.Random, length: int | None = None) -> str:
    """A path of the grammar: `/`, then runs of lower-case letters and digits joined by single `/` or `-`."""
    length = length or rng.randint(2, 64)
    chars = ["/", rng.choice(_OK_CHARS)]
    while len(chars) < length:
        joiner_fits = chars[-1] in _OK_CHARS and len(chars) < length - 1
        chars.append(
            rng.choice("/-") if joiner_fits and rng.random() < 0.2 else rng.choice(_OK_CHARS)
        )
    return "".join(chars)


def test_property_paths_of_the_grammar_are_accepted_up_to_64_characters():
    rng = random.Random(8802)  # noqa: S311 - test data, not a secret
    for _ in range(500):
        path = _valid_path(rng)
        assert _checked_path(path) == path
    assert len(_checked_path(_valid_path(rng, 64))) == 64
    with pytest.raises(ConfigError, match=re.escape(REFUSAL)):
        _checked_path(_valid_path(rng, 65))


def test_property_one_foreign_character_empty_segment_or_missing_slash_is_refused():
    rng = random.Random(8803)  # noqa: S311 - test data, not a secret
    foreign = [c for c in map(chr, range(256)) if c not in _OK_CHARS + "/-"] + ["é", " ", "／"]
    for _ in range(300):
        path = _valid_path(rng, rng.randint(2, 40))
        at = rng.randint(1, len(path))
        bad = [
            path[:at] + rng.choice(foreign) + path[at:],  # any character outside [a-z0-9/-]
            path[:at] + rng.choice(["//", "/-", "-/", "--"]) + path[at:],  # an empty segment
            path[1:],  # no leading slash
            path + rng.choice("/-"),  # ends on a joiner
        ]
        for value in bad:
            with pytest.raises(ConfigError, match=re.escape(REFUSAL)):
                _checked_path(value)


# ---- regression guards: true before and after the change ----------------------------------------------------------


def test_the_vendor_kind_keeps_its_path():
    with _served(_slack()) as port:
        assert _post(port, VENDOR) == 401
        assert _post(port, NEUTRAL) == 404
        assert _post(port, "/other") == 404


@pytest.mark.parametrize("make", [lambda: FakeChannel(SIG), _slack], ids=["fake", "slack"])
def test_a_near_miss_of_a_path_is_not_served(make):
    with _served(make()) as port:
        for base in (NEUTRAL, VENDOR):
            for path in (base + "/", base + "?x=1", base.upper(), base + "/x", base[:-1]):
                assert _post(port, path) == 404, path
