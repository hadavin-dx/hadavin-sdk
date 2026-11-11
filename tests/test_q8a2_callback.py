"""The approval receiver answers only the callback path of the configured channel kind (Q8a-2).

No database: a callback with a bad signature is refused before the store is touched. Every server listens on
port 0 (any free port) and is closed in ``finally``. Names that the change adds or removes are looked up with
``getattr`` so this file loads on the code before the change (two small hedges for that fail-on-main proof, in
``_served`` and ``_path_before_and_after``, are marked; every test that matters asserts on its own). Each test of the first section fails there on its
own assertion; the second section holds what is true before and after.
"""

import hashlib
import hmac
import http.client
import inspect
import json
import logging
import math
import re
import socket
import string
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlencode

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.approvals import FakeChannel, hmac_v0, receiver
from hadavin_sdk.approvals.requests import Approvals
from hadavin_sdk.approvals.slack_channel import SlackChannel
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store.protocol import NotFound

SIG = "sig" + "-q8a2"  # built from parts
TOKEN = "xoxb" + "-q8a2-fake"  # built from parts
NEUTRAL, VENDOR = "/channel/actions", "/slack/actions"
REFUSAL = "callback_path must be a path such as /channel/actions"


def _approvals(channel) -> Approvals:
    return Approvals(None, None, None, channel, lambda *a: None)


def _slack() -> SlackChannel:
    return SlackChannel("C1", TOKEN, SIG)  # a callback with a bad signature makes no network call


@contextmanager
def _served(channel, approvals=None, read_timeout_s=None):
    extra = {}
    # hedge for the fail-on-main proof only: the code before the change has no `read_timeout_s`; the timeout tests
    # fail on their own bound, and `test_serve_refuses_a_read_timeout...` fails when the parameter is lost
    if (
        read_timeout_s is not None
        and "read_timeout_s" in inspect.signature(receiver.serve).parameters
    ):
        extra["read_timeout_s"] = read_timeout_s  # the code before the change has no such bound
    server = receiver.serve(approvals or _approvals(channel), port=0, **extra)
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
    no body: the server answers 404 without reading one, and closing with unread data can reset the connection
    before the client has read the status."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("POST", path, body=body)
        return conn.getresponse().status
    finally:
        conn.close()


def _path_before_and_after(channel) -> str:
    # hedge for the fail-on-main proof only: before the change every kind was served on VENDOR (the tests of the
    # first section fail on their own assertion when `callback_path` is lost)
    return getattr(channel, "callback_path", VENDOR)


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


class _LoudStr(str):
    """A str subclass that answers every text question with a line break."""

    def __str__(self):
        return "loud\nstr"

    __repr__ = __str__


@pytest.mark.parametrize(
    ("name", "class_name", "shown"),
    [
        ("", "Plain", "Plain"),  # no usable name: the class name is shown
        (7, "Plain", "Plain"),
        (None, "Plain", "Plain"),
        ("two\nlines", "Plain", "two?lines"),  # whichever was chosen gets the same one check
        ("tab\there", "Plain", "tab?here"),
        (None, "two\nlines", "two?lines"),
        ("", "esc\x1b[31m", "esc?[31m"),
        ("n" * 100, "Plain", "n" * 64),
        (None, "C" * 100, "C" * 64),
        (_LoudStr("quiet"), "Plain", "quiet"),
    ],
    ids=repr,
)
def test_the_name_in_the_refusal_is_one_bounded_printable_line_whatever_its_source(
    name, class_name, shown
):
    channel = type(class_name, (), {"name": name})()
    server = None
    try:
        with pytest.raises(ConfigError) as refused:
            server = receiver.serve(_approvals(channel), port=0)
    finally:
        if server is not None:
            server.server_close()
    message = str(refused.value)
    assert message.startswith(f"channel {shown}: {REFUSAL}"), message
    assert message.isprintable()


def test_the_refusal_states_the_rule_for_a_callback_path():
    with pytest.raises(ConfigError) as refused:
        receiver.serve(_approvals(_with_path("/Teams_Hook")), port=0).server_close()
    assert str(refused.value) == (
        f"channel fake: {REFUSAL} (a `/`, then lower-case letters and digits in parts joined by `/` or `-`, "
        "at most 64 characters)"
    )


class _EqualToAll(str):
    def __eq__(self, other):
        return True

    __hash__ = str.__hash__


def test_a_str_subclass_is_not_a_callback_path():
    """A subclass could bring its own comparison and so match every request path."""
    from hadavin_sdk.approvals import channel as channel_module

    valid = getattr(channel_module, "valid_callback_path", None)
    assert valid is not None
    assert valid("/channel/actions") and not valid(_EqualToAll("/channel/actions"))
    _assert_serve_refuses(_with_path(_EqualToAll("/channel/actions")), f"channel fake: {REFUSAL}")


def test_the_path_is_read_once_when_the_server_starts():
    """A path changed on the channel after start does not move the server: the path answered is the one that was
    checked at start."""
    channel = FutureChannel(SIG)
    with _served(channel) as port:
        channel.callback_path = "/moved/actions"
        assert _post(port, FutureChannel.callback_path, UNSIGNED) == 401
        assert _post(port, "/moved/actions") == 404
        # and an invalid later value cannot stop a running server
        channel.callback_path = "not a path"
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
    path = _path_before_and_after(channel)
    with _served(channel) as port:
        for slashes in ("/", "//", "///"):  # two, three and four slashes in front
            assert _post(port, slashes + path) == 404, slashes
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


def test_the_generated_paths_cover_every_length_and_both_joiners():
    """The generator itself (no product code): the 500 paths of the acceptance test cover what its name says."""
    draws = _Draws(8802)
    paths = [_valid_path(draws) for _ in range(500)]
    assert any("-" in path for path in paths) and any("/" in path[1:] for path in paths)
    assert len(set(paths)) > 450
    # explicit, not left to the order of the draws: every length from 2 to 64 can be built
    assert {len(_valid_path(_Draws(8802 + n), n)) for n in range(2, 65)} == set(range(2, 65))


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


# ---- the receiver against hostile requests, over a real loopback socket (fix batch 2) -----------------------------
# Each of these fails on the code before the fix batch; the first three groups also fail on main, where the same
# faults existed.

TRACEBACK = "Traceback (most recent call last)"


def _raw(port: int, request: bytes, wait_s: float = 5.0) -> tuple[int | None, float]:
    """Send bytes exactly as given and read until the server closes the connection. Returns the status of the
    answer (None when the server closed without one, or did not close within `wait_s`) and the seconds it took."""
    started = time.monotonic()
    with socket.create_connection(("127.0.0.1", port), timeout=wait_s) as conn:
        conn.sendall(request)
        answer = b""
        try:
            while chunk := conn.recv(4096):
                answer += chunk
        except TimeoutError:
            return None, time.monotonic() - started
    taken = time.monotonic() - started
    return (int(answer.split()[1]) if answer.startswith(b"HTTP/") else None), taken


def _request(path: str, *headers: bytes, body: bytes = b"") -> bytes:
    return b"\r\n".join([f"POST {path} HTTP/1.1".encode(), b"Host: x", *headers, b"", body])


def _no_traceback(capsys) -> None:
    time.sleep(
        0.2
    )  # a handler thread that failed prints after the client has been answered or dropped
    assert TRACEBACK not in capsys.readouterr().err


BAD_LENGTHS = [
    (
        b"Content-Length: " + b"9" * 4301,
        413,
    ),  # past Python's limit for converting digits to a number
    (b"Content-Length: " + b"9" * 60000, 413),
    (b"Content-Length: " + b"9" * 13, 413),
    (
        b"Content-Length: " + b"0" * 12 + b"5",
        413,
    ),  # 13 digits are not converted, whatever their value
    (b"Content-Length: +5", 400),
    (b"Content-Length: -5", 400),
    (b"Content-Length: 5 5", 400),
    (b"Content-Length: 5,5", 400),
    (b"Content-Length: 0x5", 400),
    (b"Content-Length: 5.0", 400),
    (b"Content-Length:", 400),  # an empty value
    (
        b"Content-Length: \xb2",
        400,
    ),  # the only case here of a digit that is not an ASCII digit (superscript two)
    (
        b"Content-Length: \xd9\xa5",
        400,
    ),  # two bytes that are not digits when read as latin-1 (the header charset)
    (b"Content-Length: 9\r\nContent-Length: 9", 400),  # the header twice, same value
    (b"Content-Length: 0\r\nContent-Length: 9", 400),
]


@pytest.mark.parametrize(("header", "status"), BAD_LENGTHS, ids=lambda v: repr(v)[:40])
def test_a_malformed_or_oversize_content_length_is_refused_with_a_normal_answer(
    header, status, capsys
):
    with _served(FakeChannel(SIG)) as port:
        assert _raw(port, _request(NEUTRAL, header))[0] == status
        assert _raw(port, _request("/other", header))[0] == 404  # the path is judged first
        assert _raw(port, _request(NEUTRAL, b"Content-Length: 9", body=UNSIGNED))[0] == 401
        _no_traceback(capsys)


def test_the_body_length_reader_never_raises_and_accepts_only_plain_digits():
    read = getattr(receiver, "body_length", None)
    assert read is not None
    assert read([]) == 0 and read(["0"]) == 0 and read(["65536"]) == 65536
    assert read(["9" * 12]) == 999_999_999_999 and read(["9" * 13]) == receiver.MAX_BODY + 1
    draws = _Draws(8804)
    alphabet = "0123456789" * 3 + " +-.,xe_\t²٥５"
    for _ in range(2000):
        text = "".join(draws.pick(alphabet) for _ in range(draws.below(20)))
        got = read([text])
        plain = text != "" and all(c in "0123456789" for c in text)
        assert (got is not None) == plain, text
        if plain and len(text) <= 12:
            assert got == int(text)
        assert read([text, text]) is None


def test_a_request_that_sends_less_than_it_announces_frees_its_thread_within_the_bound(capsys):
    """Content-Length 100, nine bytes sent, connection held open: the server gives up after the read bound and
    closes without an answer (what the standard library server does for a timeout)."""
    with _served(FakeChannel(SIG), read_timeout_s=0.5) as port:
        status, taken = _raw(
            port, _request(NEUTRAL, b"Content-Length: 100", body=UNSIGNED), wait_s=4
        )
        assert status is None and taken < 4, (
            status,
            taken,
        )  # bound 0.5 s; the ceiling allows a loaded runner
        # the server still answers the next caller
        assert _raw(port, _request(NEUTRAL, b"Content-Length: 9", body=UNSIGNED))[0] == 401
        _no_traceback(capsys)


@pytest.mark.parametrize(
    "start",
    [b"POST /chan", b"POST /channel/actions HTTP/1.1\r\nHost: x\r\nContent-Le"],
    ids=["first line", "headers"],
)
def test_a_request_that_arrives_too_slowly_is_dropped_at_the_bound_however_it_is_sent(
    start, capsys
):
    """The bound is for the whole request: a sender that keeps the connection alive with one byte every 0.2
    seconds is dropped at the same moment as one that sends nothing more."""
    with _served(FakeChannel(SIG), read_timeout_s=0.6) as port:
        started = time.monotonic()
        with socket.create_connection(("127.0.0.1", port), timeout=5) as conn:
            conn.sendall(start)
            closed = False
            for _ in range(20):  # at most 4 seconds of dripping
                time.sleep(0.2)
                try:
                    conn.sendall(b"a")
                    conn.settimeout(0.01)
                    try:
                        closed = conn.recv(1) == b""
                    except TimeoutError:
                        closed = False
                except ConnectionError:
                    closed = True
                if closed:
                    break
        assert (
            closed and time.monotonic() - started < 4
        )  # bound 0.6 s; the ceiling allows a loaded runner
        _no_traceback(capsys)


def _reset(conn: socket.socket) -> None:
    """Close with linger 0: the close sends a reset instead of an orderly end."""
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00")
    conn.close()


def test_a_caller_that_resets_while_the_body_is_read_causes_no_traceback(capsys):
    """Content-Length 100, nine bytes, then the caller resets the connection: the server is waiting in the body
    read, so the reset ends the request there (the write of an answer is tested below)."""
    with _served(FakeChannel(SIG), read_timeout_s=3) as port:
        for _ in range(5):
            conn = socket.create_connection(("127.0.0.1", port), timeout=5)
            conn.sendall(_request(NEUTRAL, b"Content-Length: 100", body=UNSIGNED))
            time.sleep(0.05)
            _reset(conn)
        time.sleep(0.3)
        assert _raw(port, _request(NEUTRAL, b"Content-Length: 9", body=UNSIGNED))[0] == 401
        _no_traceback(capsys)


def _signed(secret: str = SIG) -> tuple[list[bytes], bytes]:
    """A correctly signed click for the fake kind, for an approval that does not exist (made-up ids)."""
    value = "apr-q8a2|" + "0" * 64 + "|0|approve"
    body = urlencode(
        {"payload": json.dumps({"user": {"id": "user:a"}, "actions": [{"value": value}]})}
    ).encode()
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"v0:{ts}:".encode() + body, hashlib.sha256).hexdigest()
    headers = [
        b"X-Hadavin-Request-Timestamp: " + ts.encode(),
        b"X-Hadavin-Signature: v0=" + sig.encode(),
        b"Content-Length: " + str(len(body)).encode(),
    ]
    return headers, body


class _Recording:
    """Stands where the approvals object stands: the real channel checks the signature, and every verified
    click is counted and then reported as unknown or as a failure of the store."""

    def __init__(self, channel, failure):
        self.channel, self.failure, self.verified = channel, failure, 0

    def receive(self, headers, body, *, record_only=False):
        if self.channel.parse_decision(headers, body, time.time()) is None:
            return False, "bad_signature"
        self.verified += 1
        raise self.failure


ERROR_LINE = "a request ended with an error: "


def _wait_for(caplog, wanted, seconds: float = 5.0) -> list[logging.LogRecord]:
    """The records that satisfy `wanted`, waiting (up to `seconds`) for the handler thread to log them."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        found = [r for r in list(caplog.records) if wanted(r)]
        if found:
            return found
        time.sleep(0.02)
    return []


def test_a_failure_while_a_signed_click_is_recorded_is_answered_500_and_logged_once_without_its_text(
    caplog,
):
    channel = FakeChannel(SIG)
    headers, body = _signed()
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    for approvals in (_approvals(channel), _Recording(channel, RuntimeError("store is down"))):
        with _served(channel, approvals) as port:  # `_approvals` has no store at all
            status, _ = _raw(port, _request(_path_before_and_after(channel), *headers, body=body))
            assert status == 500
    assert approvals.verified == 1
    errors = _wait_for(
        caplog, lambda r: r.levelno == logging.ERROR and r.getMessage().startswith(ERROR_LINE)
    )
    assert errors, caplog.text
    time.sleep(0.2)  # let a second line show, if one would be written
    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    messages = sorted(r.getMessage() for r in errors)
    # one line per failed request: the first has no store at all (an AttributeError), the second is the RuntimeError
    assert messages[1] == ERROR_LINE + "RuntimeError", messages
    assert all(m.startswith(ERROR_LINE) and "\n" not in m for m in messages)
    assert len(messages) == 2, messages
    assert (
        "store is down" not in caplog.text
    )  # the message of the error can carry request data: never logged
    assert not any(r.exc_info for r in caplog.records)  # and no traceback


@pytest.mark.parametrize(
    "failure",
    [
        ConnectionRefusedError("store refused: secret text"),
        ConnectionResetError("store reset: secret text"),
        BrokenPipeError("store pipe: secret text"),
        ConnectionAbortedError("store abort: secret text"),
        TimeoutError("store timed out: secret text"),
        RuntimeError("secret text"),
    ],
    ids=lambda e: type(e).__name__,
)
def test_a_handler_failure_is_error_whatever_its_kind_also_a_connection_error_of_a_store(
    caplog, failure
):
    """Decided by where the error happens, not by its class: a builtin ConnectionError raised by the store (a
    store that is down) is an outage, so it is logged at ERROR, once, kind only; a caller hanging up is debug."""
    channel = FakeChannel(SIG)
    headers, body = _signed()
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    recorder = _Recording(channel, failure)
    with _served(channel, recorder) as port:
        status, _ = _raw(port, _request(_path_before_and_after(channel), *headers, body=body))
    assert status == 500 and recorder.verified == 1
    errors = _wait_for(caplog, lambda r: r.levelno >= logging.ERROR)
    assert errors, caplog.text
    time.sleep(0.2)  # let a second line show, if one would be written
    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert [r.getMessage() for r in errors] == [ERROR_LINE + type(failure).__name__]
    assert "secret text" not in caplog.text and not any(r.exc_info for r in caplog.records)


def _stopped_reading(self, status, out=b""):
    raise TimeoutError("timed out")  # what the write to a peer that has stopped reading raises


def test_a_handler_failure_is_logged_once_even_when_the_answer_cannot_be_written(caplog):
    """The caller stops reading, so the write of the 500 times out (stdlib catches a `TimeoutError` in
    `handle_one_request` and logs `Request timed out` at DEBUG: `handle_error` is never reached). The handler
    failure must still be an ERROR line, and the only one. The write is replaced on the handler class of this one
    server (the class is made inside `serve`, so no other test sees it): a few answer bytes cannot fill a socket
    buffer, so a real peer cannot be made to stop the write."""
    channel = FakeChannel(SIG)
    headers, body = _signed()
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    recorder = _Recording(channel, RuntimeError("secret text"))
    server = receiver.serve(recorder, port=0)
    server.RequestHandlerClass._answer = _stopped_reading
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = socket.create_connection(("127.0.0.1", server.server_address[1]), timeout=5)
        conn.sendall(_request(_path_before_and_after(channel), *headers, body=body))
        assert _wait_for(caplog, lambda r: r.levelno >= logging.ERROR), caplog.text
        time.sleep(0.3)  # let a second line show, if one would be written
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
    assert recorder.verified == 1
    assert [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR] == [
        ERROR_LINE + "RuntimeError"
    ]
    assert "secret text" not in caplog.text


def test_a_burst_of_silent_connections_is_all_closed_within_the_read_bound_of_its_own_start():
    """150 callers connect at once and send nothing. Measured from the start of its own connect, every connection
    must be closed by the server within the read bound plus a margin. With the standard library's listen backlog
    of 5 the surplus waited for seconds before it was accepted (the bound starts at accept) and some were not
    closed for 30 s (measured: 8 to 25 of 50 over the bound; with backlog 128: none)."""
    bound, margin, callers = 1.0, 1.5, 150
    lives: list[float] = []
    lock = threading.Lock()

    def one(port: int) -> None:
        start = time.perf_counter()
        conn = socket.create_connection(("127.0.0.1", port), timeout=20)
        try:
            conn.settimeout(20)
            try:
                conn.recv(10)  # b"" when the server closes
            except OSError:
                pass
        finally:
            conn.close()
        with lock:
            lives.append(time.perf_counter() - start)

    with _served(FakeChannel(SIG), read_timeout_s=bound) as port:
        threads = [threading.Thread(target=one, args=(port,)) for _ in range(callers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(30)
    assert len(lives) == callers
    assert max(lives) < bound + margin, sorted(lives)[-5:]


def test_the_listen_backlog_is_the_configured_one_not_the_standard_librarys_five():
    server = receiver.serve(_approvals(FakeChannel(SIG)), port=0)
    try:
        assert server.request_queue_size == defaults.RECEIVER_BACKLOG > 5
    finally:
        server.server_close()


def test_a_caller_that_hangs_up_is_logged_at_debug_only(caplog):
    """The server is waiting in the body read when the caller resets: no ERROR line, one DEBUG line."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    with _served(FakeChannel(SIG), read_timeout_s=3) as port:
        conn = socket.create_connection(("127.0.0.1", port), timeout=5)
        conn.sendall(_request(NEUTRAL, b"Content-Length: 100", body=UNSIGNED))
        time.sleep(0.05)
        _reset(conn)
        hung_up = _wait_for(
            caplog, lambda r: r.getMessage().startswith(ERROR_LINE) and "Error" in r.getMessage()
        )
        assert hung_up, caplog.text
    assert [r.levelno for r in hung_up] == [logging.DEBUG], caplog.text
    assert hung_up[0].getMessage() == ERROR_LINE + "ConnectionResetError"
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


class _Slow:
    """Stands where the approvals object stands: answers `bad_signature` after a pause, so a caller can leave
    first and the write of the answer fails (the whole request has been read and the handler has not failed)."""

    def __init__(self, channel):
        self.channel = channel

    def receive(self, headers, body, *, record_only=False):
        time.sleep(0.4)
        return False, "bad_signature"


def test_a_caller_that_leaves_before_the_answer_is_written_is_logged_at_debug_only(caplog):
    """A complete request, then a reset before the answer: the write of the answer fails with a hang-up and the
    handler had not failed, so the line is DEBUG and there is no ERROR line."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    channel = FakeChannel(SIG)
    headers, body = _signed()
    with _served(channel, _Slow(channel)) as port:
        conn = socket.create_connection(("127.0.0.1", port), timeout=5)
        conn.sendall(_request(_path_before_and_after(channel), *headers, body=body))
        time.sleep(0.1)  # the request is read and the handler is paused in `receive`
        _reset(conn)
        written = _wait_for(
            caplog,
            lambda r: (
                r.getMessage().startswith(ERROR_LINE + "ConnectionResetError")
                or r.getMessage().startswith(ERROR_LINE + "BrokenPipeError")
            ),
        )
        assert written, caplog.text
    assert [r.levelno for r in written] == [logging.DEBUG]
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


class _SlowFailure(_Slow):
    """Like `_Slow`, but the handler then fails (so there is a failure and a hang-up in one request)."""

    def receive(self, headers, body, *, record_only=False):
        time.sleep(0.4)
        raise RuntimeError("secret text")


def test_a_handler_failure_and_a_hang_up_in_one_request_are_one_error_line(caplog):
    """The caller leaves while the handler runs, the handler fails, and the write of the 500 fails with a
    hang-up: the failure is the error line, the hang-up adds a debug line and no second error line."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    channel = FakeChannel(SIG)
    headers, body = _signed()
    with _served(channel, _SlowFailure(channel)) as port:
        conn = socket.create_connection(("127.0.0.1", port), timeout=5)
        conn.sendall(_request(_path_before_and_after(channel), *headers, body=body))
        time.sleep(0.1)  # the request is read and the handler is paused in `receive`
        _reset(conn)
        assert _wait_for(
            caplog, lambda r: r.levelno >= logging.ERROR or "Reset" in r.getMessage()
        ), caplog.text
        _wait_for(
            caplog, lambda r: r.levelno == logging.DEBUG and "while handling" in r.getMessage(), 1.0
        )
        time.sleep(0.5)
    errors = [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]
    assert errors == [ERROR_LINE + "RuntimeError"], caplog.text
    assert "secret text" not in caplog.text


def _handle_error_records(caplog, *raises) -> list[logging.LogRecord]:
    """Call `Server.handle_error` inside nested `except` blocks, one per exception: the last one raised is the
    one being handled, the earlier ones are its context (as when an answer cannot be written after a failure)."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    server = receiver.serve(_approvals(FakeChannel(SIG)), port=0)
    try:

        def go(remaining):
            try:
                raise remaining[0]
            except type(remaining[0]):
                if len(remaining) > 1:
                    go(remaining[1:])
                else:
                    server.handle_error(None, None)

        go(list(raises))
    finally:
        server.server_close()
    return [r for r in caplog.records if r.name == "hadavin_sdk.receiver"]


@pytest.mark.parametrize("hangup", [BrokenPipeError, ConnectionResetError, ConnectionAbortedError])
def test_a_hang_up_alone_is_debug(caplog, hangup):
    records = _handle_error_records(caplog, hangup("secret text of the error"))
    assert [(r.levelno, r.getMessage()) for r in records] == [
        (logging.DEBUG, ERROR_LINE + hangup.__name__)
    ]
    assert "secret text" not in caplog.text


def test_a_hang_up_that_has_another_error_as_its_context_is_error_and_names_both_kinds(caplog):
    """A hang-up is debug only when it is the whole story. One that was raised while another error was being
    handled is an ERROR line that names both kinds: the later error first, then `while handling`, then the other.
    (For a request whose click handler failed, `do_POST` has the one error line; see the tests above.)"""
    records = _handle_error_records(
        caplog, RuntimeError("store is down"), ConnectionResetError("peer gone")
    )
    assert [(r.levelno, r.getMessage()) for r in records] == [
        (logging.ERROR, ERROR_LINE + "ConnectionResetError while handling RuntimeError")
    ]
    assert "store is down" not in caplog.text and "peer gone" not in caplog.text


def test_a_chain_of_errors_is_named_to_five_kinds_and_then_dots(caplog):
    kinds = [type(f"Kind{i}", (Exception,), {}) for i in range(10)]
    records = _handle_error_records(caplog, *[k("text of the error") for k in kinds])
    assert [(r.levelno, r.getMessage()) for r in records] == [
        (
            logging.ERROR,
            ERROR_LINE
            + "Kind9 while handling Kind8 while handling Kind7 while handling Kind6 while handling Kind5 while handling ...",
        )
    ]
    assert "text of the error" not in caplog.text


def test_a_chain_of_exactly_five_kinds_has_no_dots(caplog):
    kinds = [type(f"Kind{i}", (Exception,), {}) for i in range(5)]
    records = _handle_error_records(caplog, *[k() for k in kinds])
    assert (
        records[0].getMessage()
        == ERROR_LINE
        + "Kind4 while handling Kind3 while handling Kind2 while handling Kind1 while handling Kind0"
    )


def test_a_chain_that_loops_back_on_itself_stops_at_the_repeat(caplog):
    first, second = ValueError("a"), KeyError("b")
    first.__context__, second.__context__ = (
        second,
        first,
    )  # built by hand: the interpreter never makes a cycle
    assert receiver._kinds(first) == "ValueError while handling KeyError while handling ..."
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    server = receiver.serve(_approvals(FakeChannel(SIG)), port=0)
    try:
        try:
            raise first
        except ValueError:
            server.handle_error(None, None)
    finally:
        server.server_close()
    assert [(r.levelno, r.getMessage()) for r in caplog.records] == [
        (logging.ERROR, ERROR_LINE + "ValueError while handling KeyError while handling ...")
    ]


def test_a_chain_of_one_error_that_is_its_own_context_does_not_loop():
    loop = ValueError("x")
    loop.__context__ = loop
    assert receiver._kinds(loop) == "ValueError while handling ..."
    assert receiver._kinds(None) == ""


def test_any_other_error_is_error_with_its_kind_only(caplog):
    records = _handle_error_records(caplog, ValueError("request text"))
    assert [(r.levelno, r.getMessage()) for r in records] == [
        (logging.ERROR, ERROR_LINE + "ValueError")
    ]
    assert "request text" not in caplog.text and not records[0].exc_info


def test_the_error_line_is_what_the_changelog_says_it_is():
    """The CHANGELOG item for the receiver describes this behaviour; its wording is held to the code."""
    text = (Path(__file__).parents[1] / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "exactly one error level line" in text and "`ConnectionRefusedError`" in text
    assert "at most five at a time" in text and "`...`" in text


def test_the_request_line_is_logged_cut_and_without_control_characters(caplog):
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    with _served(FakeChannel(SIG)) as port:
        # an escape sequence inside the path (no white space, so it stays one word of the line); the 404 is logged
        assert _raw(port, _request("/x\x1b[31mred" + "y" * 400))[0] == 404
        lines = _wait_for(
            caplog, lambda r: "[31mred" in r.getMessage()
        )  # the line is cut before its status
    assert lines, caplog.text
    shown = lines[0].getMessage()
    assert "\x1b" not in shown and '"POST /x?[31mred' in shown and len(shown) == 200, shown


def test_log_message_replaces_every_non_printable_and_cuts_the_text(caplog):
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    server = receiver.serve(_approvals(FakeChannel(SIG)), port=0)
    try:
        handler = server.RequestHandlerClass.__new__(
            server.RequestHandlerClass
        )  # no connection needed
        handler.log_message(
            '"%s" %s %s',
            "GET /a\r\nERROR forged line\x1b[31m\x85\u2028\x7f\u2029\u202e\u2066\u200b",
            404,
            "-",
        )
        handler.log_message(
            "100%"
        )  # a format that does not fit its (no) arguments is logged as it is
        handler.log_message("%s", "z" * 5000)
    finally:
        server.server_close()
    first, second, third = (r.getMessage() for r in caplog.records)
    assert first == '"GET /a??ERROR forged line?[31m???????" 404 -', first
    assert second == "100%" and len(third) == 200
    assert all(r.levelno == logging.DEBUG for r in caplog.records)


def test_log_message_shows_an_error_among_its_arguments_by_kind_only(caplog):
    """The standard library logs `Request timed out: %r` with the error itself; its message must not be logged."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.receiver")
    server = receiver.serve(_approvals(FakeChannel(SIG)), port=0)
    try:
        handler = server.RequestHandlerClass.__new__(server.RequestHandlerClass)
        handler.log_message("Request timed out: %r", TimeoutError("secret text"))
    finally:
        server.server_close()
    assert [r.getMessage() for r in caplog.records] == ["Request timed out: 'TimeoutError'"]


@pytest.mark.parametrize(
    "bad",
    [
        0,
        -1,
        0.0,
        -0.5,
        None,
        "5",
        b"5",
        True,
        False,
        math.nan,
        math.inf,
        -math.inf,
        10**10,
        3601,
        1j,
        [3],
    ],
    ids=repr,
)
def test_serve_refuses_a_read_timeout_that_is_not_a_positive_finite_number(bad):
    with pytest.raises(ConfigError, match="read_timeout_s"):
        receiver.serve(_approvals(FakeChannel(SIG)), port=0, read_timeout_s=bad)


@pytest.mark.parametrize("good", [1e-3, 0.5, 1, 10, 3600, 3600.0, defaults.RECEIVER_READ_TIMEOUT_S])
def test_serve_accepts_a_read_timeout_between_zero_and_the_maximum(good):
    server = receiver.serve(_approvals(FakeChannel(SIG)), port=0, read_timeout_s=good)
    server.server_close()


def test_the_digit_check_is_shared_with_the_signature_check():
    """One rule for a number read from a header: `body_length` and `hmac_v0.verify` both use these two names."""
    assert hmac_v0.MAX_HEADER_DIGITS == 12
    assert hmac_v0.is_plain_digits("0123456789")
    assert not any(
        hmac_v0.is_plain_digits(t)
        for t in ["", " 5", "5 ", "+5", "-5", "5.0", "٥", "²", "５", "1_0"]
    )
    assert receiver.MAX_HEADER_DIGITS is hmac_v0.MAX_HEADER_DIGITS
    assert receiver.is_plain_digits is hmac_v0.is_plain_digits
    now = 1_700_000_000
    assert hmac_v0.verify(*_verify_args(now, str(now)), now, SIG, "X") is True
    assert (
        hmac_v0.verify(*_verify_args(now, "0" * 13 + str(now)), now, SIG, "X") is False
    )  # 13+ digits: no int()
    assert hmac_v0.verify(*_verify_args(now, str(now) + " "), now, SIG, "X") is False


def _verify_args(now: int, ts_text: str) -> tuple[dict[str, str], bytes]:
    body = b"x"
    sig = hmac_v0.sign(body, now, SIG, "X")["x-signature"]
    return {"x-request-timestamp": ts_text, "x-signature": sig}, body


def test_a_correctly_signed_click_on_a_doubled_slash_is_not_handled():
    """The real change of comparing the path as written: before, a correctly SIGNED request to `//<path>` was
    handled like one to `<path>` (the standard library had already rewritten it). Now it is answered 404 and the
    click is never looked at."""
    channel = FakeChannel(SIG)
    approvals = _Recording(channel, NotFound("no such approval"))
    path = _path_before_and_after(channel)
    headers, body = _signed()
    with _served(channel, approvals) as port:
        assert _raw(port, _request(path, *headers, body=body))[0] == 200
        assert approvals.verified == 1
        wrong, _ = _signed("another" + "-secret")
        assert _raw(port, _request(path, *wrong, body=body))[0] == 401
        assert approvals.verified == 1
        assert _raw(port, _request("/" + path, b"Content-Length: 0"))[0] == 404
        assert _raw(port, _request("/" + path, *headers, body=body))[0] in (
            404,
            None,
        )  # unread body: maybe a reset
        assert approvals.verified == 1


@pytest.mark.parametrize(
    ("separator", "status"),
    [(b"\t", 401), (b"\xa0", 401), (b"\x0b", 401), (b"\x1c", 401), (b"  ", 401)],
    ids=["tab", "no-break space", "vertical tab", "file separator", "two spaces"],
)
def test_pinned_other_white_space_between_the_words_of_the_request_line_is_accepted(
    separator, status
):
    """Recorded, not chosen: the standard library splits the first line of a request on any white space (Python's
    `str.split`), and the receiver takes the second word. So these lines reach the signature check, as they did
    before this change. A proxy in front that routes by path may read such a line differently: to be looked at
    when the hosting is decided."""
    channel = FakeChannel(SIG)
    line = separator.join([b"POST", _path_before_and_after(channel).encode(), b"HTTP/1.1"])
    request = b"\r\n".join([line, b"Host: x", b"Content-Length: 9", b"", UNSIGNED])
    with _served(channel) as port:
        assert _raw(port, request)[0] == status
