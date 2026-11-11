"""The approval receiver answers only the callback path of the configured channel kind (Q8a-2).

No database: a callback with a bad signature is refused before the store is touched. Every server listens on
port 0 (any free port) and is closed in ``finally``. Names that the change adds or removes are looked up with
``getattr`` so this file loads on the code before the change and each test fails there on its own assertion.
"""

import http.client
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


UNSIGNED = b"payload=x"


def _post(port: int, path: str, body: bytes | None = None) -> int:
    """POST to `path` exactly as written (no normalising) and return the status. A probe that expects 404 sends
    no body: the server answers 404 without reading one."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("POST", path, body=body)
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
        assert _post(port, NEUTRAL, UNSIGNED) == 401  # reached the signature check


def test_the_fake_kind_does_not_answer_the_vendor_path():
    with _served(FakeChannel(SIG)) as port:
        assert _post(port, VENDOR) == 404


def test_a_future_kind_is_served_on_its_own_path_only():
    with _served(FutureChannel(SIG)) as port:
        assert _post(port, FutureChannel.callback_path, UNSIGNED) == 401
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


class _NamedChannel:
    def __init__(self, name):
        self.name = name


@pytest.mark.parametrize("name", ["", "two\nlines", "tab\there", 7, None], ids=repr)
def test_the_refusal_names_the_class_when_the_channel_name_is_not_a_printable_word(name):
    _assert_serve_refuses(_NamedChannel(name), f"channel _NamedChannel: {REFUSAL}")


def test_the_path_is_read_once_when_the_server_starts():
    """A path changed on the channel after start does not move the server: the path answered is the one that was
    checked at start."""
    channel = FutureChannel(SIG)
    with _served(channel) as port:
        channel.callback_path = "/moved/actions"
        assert _post(port, FutureChannel.callback_path, UNSIGNED) == 401
        assert _post(port, "/moved/actions") == 404
        channel.callback_path = (
            "not a path"  # and an invalid later value cannot stop a running server
        )
        assert _post(port, FutureChannel.callback_path, UNSIGNED) == 401


def test_one_checker_holds_the_grammar_and_the_length_limit():
    from hadavin_sdk.approvals import channel as channel_module

    valid = getattr(channel_module, "valid_callback_path", None)
    assert valid is not None
    assert valid("/" + "a" * 63) and not valid("/" + "a" * 64)
    assert valid(NEUTRAL) and valid(VENDOR) and valid("/a-b/c9")
    for value in BAD_PATHS:
        assert not valid(value), value
    assert not hasattr(receiver, "MAX_PATH_CHARS")  # the limit has one home, beside the grammar


@pytest.mark.parametrize(
    "make", [lambda: FakeChannel(SIG), lambda: _slack()], ids=["fake", "slack"]
)
def test_a_double_slash_in_front_of_the_path_is_not_served(make):
    """The standard library server rewrites a request target that starts with `//` to one `/`; the receiver
    compares the target as it was sent, so the rewritten form does not reach the signature check."""
    channel = make()
    path = getattr(
        channel, "callback_path", VENDOR
    )  # before the change every kind was served on VENDOR
    with _served(channel) as port:
        for slashes in ("/", "//", "///"):  # two, three and four slashes in front
            assert _post(port, slashes + path) == 404, slashes
            assert _post(port, slashes + path, UNSIGNED) == 404, slashes
        assert _post(port, path, UNSIGNED) == 401


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


class _Draws:
    """A small deterministic number source (a 64-bit linear congruential generator with Knuth's MMIX constants),
    so the generated cases are the same on every run. It is test data, not a secret."""

    def __init__(self, seed: int) -> None:
        self._state = seed

    def below(self, n: int) -> int:
        self._state = (self._state * 6364136223846793005 + 1442695040888963407) % 2**64
        return (self._state >> 33) % n

    def pick(self, items):
        return items[self.below(len(items))]


def _valid_path(draws: _Draws, length: int | None = None) -> str:
    """A path of the grammar: `/`, then runs of lower-case letters and digits joined by single `/` or `-`."""
    length = length or 2 + draws.below(63)  # 2 to 64 characters
    chars = ["/", draws.pick(_OK_CHARS)]
    while len(chars) < length:
        joiner_fits = chars[-1] in _OK_CHARS and len(chars) < length - 1
        chars.append(
            draws.pick("/-") if joiner_fits and draws.below(5) == 0 else draws.pick(_OK_CHARS)
        )
    return "".join(chars)


def test_the_generated_paths_cover_every_length_and_both_joiners():
    draws = _Draws(8802)
    paths = [_valid_path(draws) for _ in range(500)]
    assert {len(path) for path in paths} == set(range(2, 65))
    assert any("-" in path for path in paths) and any("/" in path[1:] for path in paths)
    assert len(set(paths)) > 450


def test_property_paths_of_the_grammar_are_accepted_up_to_64_characters():
    draws = _Draws(8802)
    for _ in range(500):
        path = _valid_path(draws)
        assert _checked_path(path) == path
    assert len(_checked_path(_valid_path(draws, 64))) == 64
    with pytest.raises(ConfigError, match=re.escape(REFUSAL)):
        _checked_path(_valid_path(draws, 65))


FOREIGN = [c for c in map(chr, range(256)) if c not in _OK_CHARS + "/-"] + [
    chr(0x2028),  # a line separator
    chr(0xFF0F),  # a full-width slash
    chr(0x0430),  # a Cyrillic letter that looks like "a"
]


def test_property_one_foreign_character_empty_segment_or_missing_slash_is_refused():
    draws = _Draws(8803)
    paths = [_valid_path(draws, 2 + draws.below(39)) for _ in range(300)]
    # every foreign character is tried (in turn, at a drawn position), not a sample of them
    for i, char in enumerate(FOREIGN):
        path = paths[i % len(paths)]
        at = draws.below(len(path) + 1)
        with pytest.raises(ConfigError, match=re.escape(REFUSAL)):
            _checked_path(path[:at] + char + path[at:])
    for path in paths:
        at = 1 + draws.below(len(path))
        bad = [
            *(
                path[:at] + pair + path[at:] for pair in ("//", "/-", "-/", "--")
            ),  # an empty segment
            path[1:],  # no leading slash
            path + "/",  # ends on a joiner
            path + "-",
        ]
        for value in bad:
            with pytest.raises(ConfigError, match=re.escape(REFUSAL)):
                _checked_path(value)


# ---- regression guards: true before and after the change ----------------------------------------------------------


def test_the_vendor_kind_keeps_its_path():
    with _served(_slack()) as port:
        assert _post(port, VENDOR, UNSIGNED) == 401
        assert _post(port, VENDOR) == 401  # an empty body is refused at the signature check too
        assert _post(port, NEUTRAL) == 404
        assert _post(port, "/other") == 404


@pytest.mark.parametrize("make", [lambda: FakeChannel(SIG), _slack], ids=["fake", "slack"])
def test_a_near_miss_of_a_path_is_not_served(make):
    with _served(make()) as port:
        for base in (NEUTRAL, VENDOR):
            near = (
                base + "/",
                base + "?x=1",
                base.upper(),
                base + "/x",
                base[:-1],
                base.replace("a", "%61", 1),  # percent-encoding is not undone
                base.replace("/actions", "//actions"),  # and inside
                f"http://127.0.0.1:{port}{base}",  # the absolute form of the request target
            )
            for path in near:
                assert _post(port, path) == 404, path
