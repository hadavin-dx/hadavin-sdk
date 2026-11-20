"""Unit tests of the signed trigger endpoint: the pure functions and the WSGI app, driven in-process
(no socket), with a recording fake ``start`` and a fixed clock. Secrets are built from parts."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.models import RUN_ID_PATTERN
from hadavin_sdk.triggers import endpoint
from hadavin_sdk.triggers.endpoint import (
    Accepted,
    BadRequest,
    check_secrets,
    derive_run_id,
    make_wsgi,
    parse_body,
    trigger_ref,
    verify_any,
)

NOW = 1_700_000_000
CAP = 4096


def fake_secret(*parts: str) -> str:
    return "".join(parts)


OLD_A = fake_secret("a" * 20, "b" * 20)
NEW_A = fake_secret("c" * 20, "d" * 20)
ONLY_B = fake_secret("e" * 20, "f" * 20)
STRANGER = fake_secret("x" * 20, "y" * 20)
SECRETS = {"sender-a": (OLD_A, NEW_A), "sender-b": (ONLY_B,)}


@dataclass(frozen=True)
class FakeSender:
    id: str
    agent_id: str
    principal_id: str
    secret_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class FakeSettings:
    tenant: str = "tenant-one"
    senders: tuple[FakeSender, ...] = (
        FakeSender("sender-a", "agent-a", "svc-a"),
        FakeSender("sender-b", "agent-b", "svc-b"),
    )
    max_body_bytes: int = CAP


class Recorder:
    """A fake ``start``: records every Accepted and answers what the test set."""

    def __init__(self, answer=None, error: Exception | None = None):
        self.calls: list[Accepted] = []
        self.answer = answer
        self.error = error

    def __call__(self, req: Accepted):
        self.calls.append(req)
        if self.error is not None:
            raise self.error
        if self.answer is not None:
            return self.answer
        return 202, {"run_id": req.run_id, "state": "RECEIVED"}


class SpyInput(io.BytesIO):
    def __init__(self, data: bytes):
        super().__init__(data)
        self.reads = 0

    def read(self, *args):
        self.reads += 1
        return super().read(*args)


def signed(body: bytes, secret: str, ts: int = NOW) -> dict[str, str]:
    return hmac_v0.sign(body, ts, secret, endpoint.PREFIX)


def call(
    app, method="POST", path=endpoint.PATH, headers=None, body=b"", length="auto", stream=None
):
    """Calls a WSGI callable in-process. Returns (status int, response headers dict, body bytes)."""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "SERVER_NAME": "test",
        "SERVER_PORT": "0",
        "wsgi.input": stream if stream is not None else io.BytesIO(body),
        "wsgi.errors": io.StringIO(),
        "wsgi.url_scheme": "http",
    }
    if length == "auto":
        environ["CONTENT_LENGTH"] = str(len(body))
    elif length is not None:
        environ["CONTENT_LENGTH"] = length
    for name, value in (headers or {}).items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value
    seen: list[tuple[str, list[tuple[str, str]]]] = []
    chunks = app(environ, lambda status, hdrs: seen.append((status, hdrs)))
    assert len(seen) == 1
    status, hdrs = seen[0]
    return int(status.split(" ", 1)[0]), dict(hdrs), b"".join(chunks)


def body_of(key="order-1", document="hello") -> bytes:
    return json.dumps({"key": key, "document": document}).encode()


def build(start=None, secrets=None, settings=None, now=NOW):
    start = start if start is not None else Recorder()
    app = make_wsgi(settings or FakeSettings(), secrets or SECRETS, start, clock=lambda: now)
    return app, start


def refused(result, status):
    got, headers, out = result
    assert got == status
    assert out == b""
    assert headers["Content-Length"] == "0"
    assert "Content-Type" not in headers
    # the exact header set of a refusal (ticket H10): nothing that names a reason or the server
    assert {name.title() for name in headers} <= {"Content-Length", "Allow", "Retry-After"}, headers


# ---- derive_run_id, trigger_ref ----


def test_derive_run_id_is_stable_and_has_the_run_id_shape():
    rid = derive_run_id("tenant-one", "sender-a", "order-1")
    assert rid == derive_run_id("tenant-one", "sender-a", "order-1")
    assert RUN_ID_PATTERN.fullmatch(rid)
    expected = hashlib.sha256(b"tenant-one\0sender-a\0order-1").hexdigest()[:32]
    assert rid == "run-" + expected


def test_derive_run_id_separates_tenant_sender_and_key():
    base = derive_run_id("t1", "s1", "k1")
    assert derive_run_id("t2", "s1", "k1") != base
    assert derive_run_id("t1", "s2", "k1") != base
    assert derive_run_id("t1", "s1", "k2") != base
    # moving a character across a field boundary changes the id
    assert derive_run_id("ab", "c", "d") != derive_run_id("a", "bc", "d")
    assert derive_run_id("a", "b", "cd") != derive_run_id("a", "bc", "d")


def test_derive_run_id_many_seeded_triples():
    rng = random.Random(1234)  # noqa: S311 - a seeded test generator
    ids = "abcdefghijklmnopqrstuvwxyz0123456789-"
    keys = "ABCxyz019._:-"
    seen = {}
    for _ in range(2000):
        triple = (
            "".join(rng.choice(ids) for _ in range(rng.randint(1, 6))),
            "".join(rng.choice(ids) for _ in range(rng.randint(1, 6))),
            "".join(rng.choice(keys) for _ in range(rng.randint(1, 8))),
        )
        rid = derive_run_id(*triple)
        assert RUN_ID_PATTERN.fullmatch(rid)
        assert seen.setdefault(rid, triple) == triple


@pytest.mark.parametrize(
    "triple",
    [
        ("t", "a\0b", "k"),
        ("t\0a", "b", "k"),
        ("t", "s", "k\0x"),
        ("", "s", "k"),
        ("t", "", "k"),
        ("t", "s", ""),
        ("T", "s", "k"),
        ("t", "s/x", "k"),
        ("t", "s", "a/b"),
        ("t", "s", "a#b"),
        ("t", "s", "k\n"),
        ("t" * 41, "s", "k"),
        ("t", "s", "k" * 129),
        ("t\n", "s", "k"),
        ("t", "s\n", "k"),
        ("t", "s", "\nk"),
    ],
)
def test_derive_run_id_refuses_bad_input(triple):
    with pytest.raises(ValueError):
        derive_run_id(*triple)


def test_trigger_ref_changes_with_the_document():
    one = trigger_ref("sender-a", "order-1", b"hello")
    assert one == "sender-a/order-1#" + hashlib.sha256(b"hello").hexdigest()
    assert trigger_ref("sender-a", "order-1", b"hello!") != one
    assert trigger_ref("sender-a", "order-2", b"hello") != one
    assert trigger_ref("sender-b", "order-1", b"hello") != one


# ---- parse_body ----


def test_parse_body_round_trip():
    rng = random.Random(7)  # noqa: S311 - a seeded test generator
    for _ in range(200):
        key = "".join(rng.choice("Aa0._:-") for _ in range(rng.randint(1, 128)))
        doc = "".join(chr(rng.choice([65, 233, 0x4E2D, 0x1F600, 10, 0])) for _ in range(20))
        assert parse_body(json.dumps({"key": key, "document": doc}).encode()) == (
            key,
            doc.encode("utf-8"),
        )
    assert parse_body(body_of("k", "")) == ("k", b"")


MALFORMED = {
    "not json": b"{not json",
    "empty": b"",
    "array": b'["key", "document"]',
    "string": b'"key"',
    "null": b"null",
    "missing document": b'{"key": "k"}',
    "missing key": b'{"document": "d"}',
    "extra field": b'{"key": "k", "document": "d", "agent_id": "x"}',
    "key not a string": b'{"key": 1, "document": "d"}',
    "document not a string": b'{"key": "k", "document": {"a": 1}}',
    "document null": b'{"key": "k", "document": null}',
    "key empty": b'{"key": "", "document": "d"}',
    "key slash": b'{"key": "a/b", "document": "d"}',
    "key hash": b'{"key": "a#b", "document": "d"}',
    "key nul": b'{"key": "a\\u0000b", "document": "d"}',
    "key newline": b'{"key": "k\\n", "document": "d"}',
    "key angle": b'{"key": "<id@mail>", "document": "d"}',
    "key 129": json.dumps({"key": "k" * 129, "document": "d"}).encode(),
    "invalid utf-8": b'{"key": "k", "document": "\xff\xfe"}',
    "lone surrogate": b'{"key": "k", "document": "\\ud800"}',
    "duplicate key": b'{"key": "k", "key": "k", "document": "d"}',
    "duplicate document": b'{"key": "k", "document": "d", "document": "e"}',
    "deep nesting": b"[" * 10000 + b"]" * 10000,
    "huge number": b'{"key": "k", "document": ' + b"9" * 3000 + b"}",
    "trailing data": b'{"key": "k", "document": "d"} x',
    "byte-order mark": b'\xef\xbb\xbf{"key": "k", "document": "d"}',
    "document NaN": b'{"key": "k", "document": NaN}',
    "document Infinity": b'{"key": "k", "document": Infinity}',
    "document -Infinity": b'{"key": "k", "document": -Infinity}',
    "key NaN": b'{"key": NaN, "document": "d"}',
    "extra NaN": b'{"key": "k", "document": "d", "n": NaN}',
    "bare NaN": b"NaN",
    "lone low surrogate": b'{"key": "k", "document": "a\\udc00b"}',
    "reversed surrogates": b'{"key": "k", "document": "\\ude00\\ud83d"}',
    "key lone surrogate": b'{"key": "k\\ud800", "document": "d"}',
    "key trailing newline raw": b'{"key": "k\n", "document": "d"}',
}


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_parse_body_refuses(name):
    with pytest.raises(BadRequest):
        parse_body(MALFORMED[name])


def test_parse_body_key_length_bounds():
    assert parse_body(body_of("k"))[0] == "k"
    assert parse_body(body_of("k" * 128))[0] == "k" * 128


def test_bad_request_never_quotes_the_body():
    marker = "MARKER-" + "q" * 10
    with pytest.raises(BadRequest) as info:
        parse_body(json.dumps({"key": marker + "/", "document": marker}).encode())
    assert marker not in str(info.value)


def test_parse_body_takes_a_surrogate_pair_escape_and_refuses_half_of_one():
    assert parse_body(b'{"key": "k", "document": "\\ud83d\\ude00"}') == ("k", "\U0001f600".encode())
    with pytest.raises(BadRequest):
        parse_body(b'{"key": "k", "document": "\\ud83d"}')


# ---- verify_any, check_secrets ----


def test_verify_any_names_the_sender_whose_secret_verified():
    body = body_of()
    assert verify_any(signed(body, OLD_A), body, NOW, SECRETS) == "sender-a"
    assert verify_any(signed(body, NEW_A), body, NOW, SECRETS) == "sender-a"
    assert verify_any(signed(body, ONLY_B), body, NOW, SECRETS) == "sender-b"
    assert verify_any(signed(body, STRANGER), body, NOW, SECRETS) is None
    assert verify_any({}, body, NOW, SECRETS) is None
    assert verify_any(signed(body, OLD_A), body, NOW, {}) is None


def test_verify_any_takes_mixed_case_header_names():
    body = body_of()
    low = signed(body, ONLY_B)
    headers = {
        endpoint.TIMESTAMP_HEADER: low[endpoint.TIMESTAMP_HEADER.lower()],
        endpoint.SIGNATURE_HEADER: low[endpoint.SIGNATURE_HEADER.lower()],
    }
    assert set(low) == {"x-hadavin-request-timestamp", "x-hadavin-signature"}
    assert verify_any(headers, body, NOW, SECRETS) == "sender-b"


def test_verify_any_tries_every_secret_with_no_early_stop(monkeypatch):
    tried = []
    real = hmac_v0.verify

    def spy(headers, body, now_ts, secret, prefix):
        tried.append(secret)
        return real(headers, body, now_ts, secret, prefix)

    monkeypatch.setattr(endpoint.hmac_v0, "verify", spy)
    body = body_of()
    assert verify_any(signed(body, OLD_A), body, NOW, SECRETS) == "sender-a"
    assert tried == [OLD_A, NEW_A, ONLY_B]


def test_verify_any_refuses_when_two_senders_match():
    body = body_of()
    shared = {"sender-a": (OLD_A,), "sender-b": (OLD_A,)}
    assert verify_any(signed(body, OLD_A), body, NOW, shared) is None


@pytest.mark.parametrize(("offset", "sender"), [(-300, "sender-a"), (300, "sender-a")])
@pytest.mark.parametrize("fraction", [0.0, 0.001, 0.5, 0.999])
def test_verify_any_window_edge_is_exact_with_a_fractional_clock(offset, sender, fraction):
    body = body_of()
    assert verify_any(signed(body, OLD_A, NOW + offset), body, NOW + fraction, SECRETS) == sender
    one_more = offset + (1 if offset > 0 else -1)
    assert verify_any(signed(body, OLD_A, NOW + one_more), body, NOW + fraction, SECRETS) is None


def test_check_secrets_accepts_a_good_set():
    check_secrets(SECRETS)
    check_secrets({"sender-a": ("z" * 32,)})
    check_secrets({"sender-a": ("z" * 16 + "  " + "z" * 16,)})  # spaces inside are kept
    assert endpoint.MAX_SECRETS_PER_SENDER == 2


WHITESPACE_EDGES = {
    "trailing newline": ("", "\n"),
    "trailing CRLF": ("", "\r\n"),
    "trailing space": ("", " "),
    "trailing tab": ("", "\t"),
    "leading space": (" ", ""),
    "leading newline": ("\n", ""),
    "no-break space": ("", "\u00a0"),
    "both ends": (" ", " "),
}


@pytest.mark.parametrize("name", sorted(WHITESPACE_EDGES))
@pytest.mark.parametrize("position", [0, 1])
def test_check_secrets_refuses_whitespace_around_a_value_and_names_only_the_sender(name, position):
    before, after = WHITESPACE_EDGES[name]
    bad = before + STRANGER + after
    values = (bad, NEW_A) if position == 0 else (NEW_A, bad)
    with pytest.raises(ValueError) as info:
        check_secrets({"sender-a": values, "sender-b": (ONLY_B,)})
    text = str(info.value)
    assert "sender-a" in text and "whitespace" in text
    assert "sender-b" not in text
    for value in (bad, STRANGER, NEW_A, ONLY_B):
        assert value not in text
    start = Recorder()
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(), {"sender-a": values, "sender-b": (ONLY_B,)}, start)


def test_check_secrets_refuses_more_than_two_secrets_per_sender():
    third = fake_secret("g" * 20, "h" * 20)
    check_secrets({"sender-a": (OLD_A, NEW_A), "sender-b": (ONLY_B, third)})
    three = {"sender-a": (OLD_A,), "sender-b": (ONLY_B, NEW_A, third)}
    with pytest.raises(ValueError) as info:
        check_secrets(three)
    text = str(info.value)
    assert "sender-b" in text and "more than 2" in text
    assert "sender-a" not in text
    for value in (OLD_A, NEW_A, ONLY_B, third):
        assert value not in text
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(), three, Recorder())


@pytest.mark.parametrize(
    ("secrets", "named"),
    [
        ({"sender-a": (OLD_A,), "sender-b": (OLD_A,)}, "sender-b"),
        ({"sender-a": (OLD_A,), "sender-b": (NEW_A, OLD_A)}, "sender-b"),
        ({"sender-a": ("s" * 31,)}, "sender-a"),
        ({"sender-a": (OLD_A, "")}, "sender-a"),
        ({"sender-a": ()}, "sender-a"),
        ({"sender-a": OLD_A}, "sender-a"),
        ({}, "no trigger sender"),
        ({f"sender-{i}": (f"{i}" * 40,) for i in range(9)}, "more than 8"),
    ],
)
def test_check_secrets_refuses_and_names_the_sender_not_the_value(secrets, named):
    with pytest.raises(ValueError) as info:
        check_secrets(secrets)
    text = str(info.value)
    assert named in text
    for values in secrets.values():
        for value in [values] if isinstance(values, str) else values:
            assert not value or value not in text


UNSEEN = {
    "byte-order mark": "\ufeff",
    "zero-width space": "\u200b",
    "zero-width non-joiner": "\u200c",
    "zero-width joiner": "\u200d",
    "word joiner": "\u2060",
}


@pytest.mark.parametrize("name", sorted(UNSEEN))
@pytest.mark.parametrize("place", ["start", "middle", "end"])
def test_check_secrets_refuses_an_unseen_character_anywhere_in_a_value(name, place):
    """A secret file saved with a byte-order mark or a zero-width character would never verify (review 2,
    Minor 12): refused at start, at any place in the value, and the error names only the sender."""
    char = UNSEEN[name]
    assert char.strip() == char  # strip() does not cut it, so the whitespace rule cannot catch it
    assert char in endpoint.UNSEEN_CHARS and len(endpoint.UNSEEN_CHARS) == len(UNSEEN)
    cut = {"start": 0, "middle": 20, "end": len(STRANGER)}[place]
    bad = STRANGER[:cut] + char + STRANGER[cut:]
    secrets = {"sender-a": (NEW_A, bad), "sender-b": (ONLY_B,)}
    with pytest.raises(ValueError) as info:
        check_secrets(secrets)
    text = str(info.value)
    assert "sender-a" in text and "zero-width" in text and "byte-order mark" in text
    assert "sender-b" not in text
    for value in (bad, STRANGER, STRANGER[:20], NEW_A, ONLY_B, char):
        assert value not in text
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(), secrets, Recorder())


CONTROL = {
    "NUL": "\x00",
    "tab": "\t",
    "newline": "\n",
    "escape": "\x1b",
    "DEL": "\x7f",
    "C1": "\x85",
}


@pytest.mark.parametrize("name", sorted(CONTROL))
def test_check_secrets_refuses_a_control_character_inside_a_value(name):
    """Design review 1, N12: any character of Unicode category Cc (NUL included) inside a value is
    refused at start, also through make_wsgi; the error names the sender only."""
    char = CONTROL[name]
    bad = STRANGER[:20] + char + STRANGER[20:]
    assert bad == bad.strip()  # inside the value, so the whitespace rule does not see it
    secrets = {"sender-a": (NEW_A, bad), "sender-b": (ONLY_B,)}
    with pytest.raises(ValueError) as info:
        check_secrets(secrets)
    text = str(info.value)
    assert "sender-a" in text and "control character" in text
    assert "sender-b" not in text
    for value in (bad, STRANGER, STRANGER[:20], NEW_A, ONLY_B, char):
        assert value not in text
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(), secrets, Recorder())


def test_check_secrets_refuses_a_value_that_cannot_be_written_as_utf8_and_names_the_sender_only():
    """Code review 1, DC1-6: a lone surrogate (category Cs, so neither the whitespace, the unseen-character
    nor the control rule sees it) cannot be encoded: without this check every request would end in a 503 and
    an ERROR line. Refused at start, also through make_wsgi."""
    lone = "\ud800"
    bad = STRANGER[:20] + lone + STRANGER[20:]
    secrets = {"sender-a": (NEW_A, bad), "sender-b": (ONLY_B,)}
    with pytest.raises(ValueError) as info:
        check_secrets(secrets)
    text = str(info.value)
    assert "sender-a" in text and "UTF-8" in text and "sender-b" not in text
    for value in (bad, STRANGER, STRANGER[:20], NEW_A, ONLY_B, lone):
        assert value not in text
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(), secrets, Recorder())


def test_make_wsgi_has_its_own_upper_bounds_for_a_callers_settings_object():
    """Design review 1, N15: the body cap and the number of senders are bounded here, not only in a
    config model the caller may not use."""
    from hadavin_sdk import defaults

    limit = endpoint.MAX_BODY_BYTES_LIMIT
    assert limit == 8 * defaults.MAX_DOCUMENT_BYTES
    make_wsgi(FakeSettings(max_body_bytes=limit), SECRETS, Recorder())
    for over in (limit + 1, 10**12):
        with pytest.raises(ValueError, match="max_body_bytes is over"):
            make_wsgi(FakeSettings(max_body_bytes=over), SECRETS, Recorder())
    assert endpoint.MAX_SENDERS == 8
    for count, good in ((8, True), (9, False)):
        senders = tuple(FakeSender(f"sender-{i}", "agent-a", "svc-a") for i in range(count))
        secrets = {f"sender-{i}": (f"{i}" * 40,) for i in range(count)}
        if good:
            make_wsgi(FakeSettings(senders=senders), secrets, Recorder())
        else:
            with pytest.raises(ValueError, match="more than 8 trigger senders"):
                make_wsgi(FakeSettings(senders=senders), secrets, Recorder())


def test_check_secrets_refuses_the_same_value_twice_for_one_sender():
    """Review 2, Minor 12: the second copy would only cost one more HMAC per request and hides a failed
    secret change. The error names the sender, never the value."""
    twice = {"sender-a": (OLD_A, fake_secret("a" * 20, "b" * 20)), "sender-b": (ONLY_B,)}
    with pytest.raises(ValueError) as info:
        check_secrets(twice)
    text = str(info.value)
    assert "sender-a" in text and "the same secret twice" in text
    assert "sender-b" not in text and OLD_A not in text and ONLY_B not in text
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(), twice, Recorder())
    check_secrets({"sender-a": (OLD_A, NEW_A), "sender-b": (ONLY_B,)})  # two different values pass


def test_make_wsgi_refuses_a_bad_setup():
    start = Recorder()
    with pytest.raises(ValueError):  # T5 8c: A's secret equals B's
        make_wsgi(FakeSettings(), {"sender-a": (OLD_A,), "sender-b": (OLD_A,)}, start)
    with pytest.raises(ValueError):  # T5 8c: under 32 characters
        make_wsgi(FakeSettings(), {"sender-a": ("s" * 31,), "sender-b": (ONLY_B,)}, start)
    with pytest.raises(ValueError):  # a configured sender without a secret
        make_wsgi(FakeSettings(), {"sender-a": (OLD_A,)}, start)
    with pytest.raises(ValueError):  # a secret for a sender that is not configured
        make_wsgi(FakeSettings(), {**SECRETS, "sender-c": (STRANGER,)}, start)
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(tenant="Bad Tenant"), SECRETS, start)
    with pytest.raises(ValueError):  # fullmatch: a trailing newline is not part of an id
        make_wsgi(FakeSettings(tenant="tenant-one\n"), SECRETS, start)
    newline = (FakeSender("sender-a\n", "agent-a", "svc-a"),)
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(senders=newline), {"sender-a\n": (OLD_A,)}, start)
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(max_body_bytes=0), SECRETS, start)
    twice = (FakeSender("sender-a", "agent-a", "svc-a"), FakeSender("sender-a", "agent-b", "svc-b"))
    with pytest.raises(ValueError):
        make_wsgi(FakeSettings(senders=twice), {"sender-a": (OLD_A,)}, start)


# ---- the WSGI app: accepted requests ----


def test_signed_fresh_request_reaches_start_with_config_identity():
    app, start = build()
    body = body_of("order-1", "héllo")
    status, headers, out = call(app, headers=signed(body, OLD_A), body=body)
    assert status == 202
    assert headers["Content-Type"] == "application/json"
    assert headers["Content-Length"] == str(len(out))
    rid = derive_run_id("tenant-one", "sender-a", "order-1")
    assert json.loads(out) == {"run_id": rid, "state": "RECEIVED"}
    assert start.calls == [
        Accepted(
            sender="sender-a",
            agent_id="agent-a",
            principal_id="svc-a",
            run_id=rid,
            trigger_ref=trigger_ref("sender-a", "order-1", "héllo".encode()),
            document="héllo".encode(),
        )
    ]


def test_t5_8_old_and_new_secret_give_the_same_run_id():
    app, start = build()
    body = body_of()
    assert call(app, headers=signed(body, OLD_A), body=body)[0] == 202
    assert call(app, headers=signed(body, NEW_A, NOW + 5), body=body)[0] == 202
    assert [c.run_id for c in start.calls] == [
        derive_run_id("tenant-one", "sender-a", "order-1")
    ] * 2
    assert start.calls[0] == start.calls[1]


def test_t5_8b_removed_old_secret_is_refused():
    app, start = build(secrets={"sender-a": (NEW_A,), "sender-b": (ONLY_B,)})
    body = body_of()
    refused(call(app, headers=signed(body, OLD_A), body=body), 401)
    assert start.calls == []
    assert call(app, headers=signed(body, NEW_A), body=body)[0] == 202


def test_two_senders_same_key_give_two_run_ids_and_their_own_identity():
    app, start = build()
    body = body_of()
    call(app, headers=signed(body, OLD_A), body=body)
    call(app, headers=signed(body, ONLY_B), body=body)
    a, b = start.calls
    assert (a.sender, a.agent_id, a.principal_id) == ("sender-a", "agent-a", "svc-a")
    assert (b.sender, b.agent_id, b.principal_id) == ("sender-b", "agent-b", "svc-b")
    assert a.run_id != b.run_id
    assert a.trigger_ref != b.trigger_ref


def test_a_sender_header_is_ignored():
    app, start = build()
    body = body_of()
    headers = {**signed(body, OLD_A), "X-Hadavin-Sender": "sender-b"}
    assert call(app, headers=headers, body=body)[0] == 202
    assert start.calls[0].sender == "sender-a"


def test_tenant_is_part_of_the_run_id_at_the_endpoint():
    body = body_of()
    ids = []
    for tenant in ("tenant-one", "tenant-two"):
        app, start = build(settings=FakeSettings(tenant=tenant))
        call(app, headers=signed(body, OLD_A), body=body)
        ids.append(start.calls[0].run_id)
    assert ids[0] != ids[1]
    assert ids[0] == "run-" + hashlib.sha256(b"tenant-one\0sender-a\0order-1").hexdigest()[:32]


def test_body_exactly_at_the_cap_is_accepted_and_one_more_is_413_unread():
    pad = CAP - len(body_of("k", ""))
    body = body_of("k", "d" * pad)
    assert len(body) == CAP
    app, start = build()
    assert call(app, headers=signed(body, OLD_A), body=body)[0] == 202
    bigger = body_of("k", "d" * (pad + 1))
    stream = SpyInput(bigger)
    refused(call(app, headers=signed(bigger, OLD_A), body=bigger, stream=stream), 413)
    assert stream.reads == 0
    assert len(start.calls) == 1


def test_answer_holds_only_run_id_and_state():
    start = Recorder(answer=(200, {"run_id": "run-x", "state": "DONE", "document": "leak"}))
    app, _ = build(start)
    body = body_of()
    status, _, out = call(app, headers=signed(body, OLD_A), body=body)
    assert status == 200
    assert json.loads(out) == {"run_id": "run-x", "state": "DONE"}


@pytest.mark.parametrize("answer", [(409, {}), (409, None), (409, {"run_id": "r", "state": "s"})])
def test_start_409_passes_through_with_an_empty_body(answer):
    start = Recorder(answer=answer)
    app, _ = build(start)
    body = body_of()
    refused(call(app, headers=signed(body, OLD_A), body=body), 409)
    assert len(start.calls) == 1


def test_start_503_passes_through():
    app, _ = build(Recorder(answer=(503, None)))
    body = body_of()
    refused(call(app, headers=signed(body, OLD_A), body=body), 503)


def test_503_carries_retry_after_and_no_other_answer_does():
    assert endpoint.RETRY_AFTER_SECONDS == 1
    body = body_of()
    for answer in [
        (503, None),
        (202, {"run_id": "run-x", "state": "RECEIVED"}),
        (200, {}),
        (409, {}),
    ]:
        app, _ = build(Recorder(answer=answer))
        status, headers, out = call(app, headers=signed(body, OLD_A), body=body)
        assert status == answer[0]
        assert headers.get("Retry-After") == ("1" if status == 503 else None)
        assert (out == b"") == (status in (503, 409))
    app, _ = build(Recorder(error=RuntimeError("down")))
    status, headers, out = call(app, headers=signed(body, OLD_A), body=body)
    assert (status, headers["Retry-After"], out) == (503, "1", b"")
    app, _ = build()
    for result in (
        call(app, headers={}, body=body),
        call(app, headers=signed(body, OLD_A.replace(OLD_A[0], "z")), body=body),
        call(app, headers=signed(b"{", OLD_A), body=b"{"),
    ):
        assert result[0] in (400, 401)
        assert "Retry-After" not in result[1]
        assert result[2] == b""


@pytest.mark.parametrize("error", [RuntimeError("store down"), KeyError("x"), ValueError("y")])
def test_start_raising_gives_503(error):
    app, start = build(Recorder(error=error))
    body = body_of()
    refused(call(app, headers=signed(body, OLD_A), body=body), 503)
    assert len(start.calls) == 1


@pytest.mark.parametrize("answer", [(500, {}), (299, {}), ("200", {}), (True, {}), None, (200,)])
def test_start_answering_nonsense_gives_503(answer):
    app, _ = build(Recorder(answer=answer) if answer is not None else (lambda req: None))
    body = body_of()
    refused(call(app, headers=signed(body, OLD_A), body=body), 503)


# ---- the WSGI app: refusals ----


def bad_signature_cases() -> dict[str, tuple[dict[str, str], bytes]]:
    body = body_of()
    good = signed(body, OLD_A)
    ts_name, sig_name = endpoint.TIMESTAMP_HEADER.lower(), endpoint.SIGNATURE_HEADER.lower()
    sig = good[sig_name]
    return {
        "wrong secret": (signed(body, STRANGER), body),
        "altered body": (good, body.replace(b"hello", b"hellp")),
        "no headers": ({}, body),
        "missing signature": ({ts_name: good[ts_name]}, body),
        "missing timestamp": ({sig_name: sig}, body),
        "v1 prefix": ({**good, sig_name: "v1=" + sig[3:]}, body),
        "no prefix": ({**good, sig_name: sig[3:]}, body),
        "upper-case hex": ({**good, sig_name: "v0=" + sig[3:].upper()}, body),
        "non-ascii signature": ({**good, sig_name: "v0=" + "é" * 64}, body),
        "empty signature": ({**good, sig_name: ""}, body),
        "truncated signature": ({**good, sig_name: sig[:-1]}, body),
        "other timestamp": ({**good, ts_name: str(NOW + 1)}, body),
    }


@pytest.mark.parametrize("name", sorted(bad_signature_cases()))
def test_t5_2_bad_signature_is_401_and_the_body_is_never_parsed(name, monkeypatch):
    headers, body = bad_signature_cases()[name]
    parsed = []
    monkeypatch.setattr(endpoint, "parse_body", lambda b: parsed.append(b) or ("k", b"d"))
    app, start = build()
    refused(call(app, headers=headers, body=body), 401)
    assert start.calls == []
    assert parsed == []


@pytest.mark.parametrize(("offset", "status"), [(-300, 202), (300, 202), (-301, 401), (301, 401)])
def test_t5_3_timestamp_window(offset, status):
    body = body_of()
    headers = signed(body, OLD_A, NOW + offset)  # a correct signature over that timestamp
    app, start = build()
    got = call(app, headers=headers, body=body)
    assert got[0] == status
    assert len(start.calls) == (1 if status == 202 else 0)
    if status == 401:
        refused(got, 401)


@pytest.mark.parametrize("fraction", [0.001, 0.5, 0.999])
@pytest.mark.parametrize(("offset", "status"), [(-300, 202), (300, 202), (-301, 401), (301, 401)])
def test_t5_3_timestamp_window_is_exact_with_a_fractional_clock(offset, status, fraction):
    body = body_of()
    headers = signed(body, OLD_A, NOW + offset)
    app, start = build(now=NOW + fraction)
    got = call(app, headers=headers, body=body)
    assert got[0] == status
    assert len(start.calls) == (1 if status == 202 else 0)
    if status == 401:
        refused(got, 401)


def test_t5_9b_replay_after_the_window_is_401_and_inside_it_is_accepted():
    body = body_of()
    headers = signed(body, OLD_A, NOW)
    app, start = build(now=NOW + 299)
    assert call(app, headers=headers, body=body)[0] == 202
    assert len(start.calls) == 1
    late, late_start = build(now=NOW + 301)
    refused(call(late, headers=headers, body=body), 401)
    assert late_start.calls == []


@pytest.mark.parametrize(
    "ts",
    [
        "1" * 13,
        "",
        "abc",
        "+" + str(NOW),
        "-" + str(NOW),
        " " + str(NOW),
        str(NOW) + " ",
        str(NOW) + ".0",
        "١٧٠٠٠٠٠٠٠٠",
        "9" * 5000,
    ],
)
def test_t5_3b_malformed_timestamp_is_401(ts):
    body = body_of()
    ts_name, sig_name = endpoint.TIMESTAMP_HEADER.lower(), endpoint.SIGNATURE_HEADER.lower()
    sig = hmac_v0._sig(body, ts, OLD_A)  # signed over exactly that text: only the shape is wrong
    app, start = build()
    refused(call(app, headers={ts_name: ts, sig_name: sig}, body=body), 401)
    assert start.calls == []


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_t5_6_malformed_but_signed_is_400(name):
    body = MALFORMED[name]
    if not body:
        pytest.skip("an empty body is refused at Content-Length (own test)")
    app, start = build(settings=FakeSettings(max_body_bytes=64 * 1024))
    refused(call(app, headers=signed(body, OLD_A), body=body), 400)
    assert start.calls == []


def test_t5_6_a_very_long_key_inside_the_cap_is_400():
    body = body_of("k" * 200_000)
    app, start = build(settings=FakeSettings(max_body_bytes=400_000))
    refused(call(app, headers=signed(body, OLD_A), body=body), 400)
    assert start.calls == []


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_t5_6b_malformed_and_unsigned_is_401_not_400(name):
    body = MALFORMED[name]
    if not body:
        pytest.skip("an empty body is refused at Content-Length (own test)")
    app, start = build(settings=FakeSettings(max_body_bytes=64 * 1024))
    refused(call(app, body=body), 401)
    refused(call(app, headers=signed(body, STRANGER), body=body), 401)
    assert start.calls == []


def test_t5_7_content_length_over_the_cap_is_413_without_reading():
    app, start = build()
    for length in (str(CAP + 1), "9" * 12, "9" * 13, "9" * 5000):
        stream = SpyInput(b"x" * 10)
        refused(call(app, length=length, stream=stream), 413)
        assert stream.reads == 0
    assert start.calls == []


@pytest.mark.parametrize(
    "length", [None, "", "abc", "-1", "+5", "5 ", " 5", "5.0", "0x10", "٥", "0"]
)
def test_t5_7b_content_length_missing_or_not_digits_or_zero_is_400(length):
    body = body_of()
    app, start = build()
    stream = SpyInput(body)
    refused(call(app, headers=signed(body, OLD_A), length=length, stream=stream), 400)
    assert stream.reads == 0
    assert start.calls == []


def test_t5_7b_body_shorter_than_declared_is_400_in_process():
    # In-process only: a stream that ends early. On a real blocking socket the read waits instead.
    body = body_of()
    app, start = build()
    refused(call(app, headers=signed(body, OLD_A), body=body, length=str(len(body) + 1)), 400)
    assert start.calls == []


def test_declared_length_shorter_than_the_body_signs_differently_and_is_401():
    body = body_of()
    app, start = build()
    refused(call(app, headers=signed(body, OLD_A), body=body, length=str(len(body) - 1)), 401)
    assert start.calls == []


def test_a_failing_input_stream_is_400():
    class Broken:
        def read(self, n):
            raise TimeoutError("timed out")

    app, start = build()
    refused(call(app, length="10", stream=Broken()), 400)
    assert start.calls == []


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE", "HEAD", "OPTIONS", "post"])
def test_other_method_is_405_before_any_signature_work(method, monkeypatch):
    monkeypatch.setattr(endpoint, "verify_any", lambda *a: pytest.fail("verify_any was called"))
    body = body_of()
    app, start = build()
    stream = SpyInput(body)
    got = call(app, method=method, headers=signed(body, OLD_A), body=body, stream=stream)
    refused(got, 405)
    assert got[1]["Allow"] == "POST"
    assert stream.reads == 0
    assert start.calls == []


@pytest.mark.parametrize("path", ["/", "", "/v1/trigger/", "/v1/triggers", "/v1", "/V1/TRIGGER"])
def test_other_path_is_404_before_any_signature_work(path, monkeypatch):
    monkeypatch.setattr(endpoint, "verify_any", lambda *a: pytest.fail("verify_any was called"))
    body = body_of()
    app, start = build()
    for method in ("POST", "GET"):
        refused(call(app, method=method, path=path, headers=signed(body, OLD_A), body=body), 404)
    assert start.calls == []


def test_an_internal_error_gives_503_and_never_raises(monkeypatch):
    def boom(*a):
        raise RuntimeError("inside")

    monkeypatch.setattr(endpoint, "verify_any", boom)
    body = body_of()
    app, start = build()
    refused(call(app, headers=signed(body, OLD_A), body=body), 503)
    assert start.calls == []


# ---- property-style loops (seeded, no new dependency) ----


def test_random_requests_never_raise_and_never_start_without_a_valid_signature():
    rng = random.Random(20261120)  # noqa: S311 - a seeded test generator
    app, start = build()
    ts_name, sig_name = endpoint.TIMESTAMP_HEADER.lower(), endpoint.SIGNATURE_HEADER.lower()
    odd = ["", "v0=", "v0=" + "0" * 64, "é", "\x00", "1" * 13, str(NOW), "v0=" + "f" * 63, " "]
    for _ in range(1500):
        body = rng.randbytes(rng.randint(0, 300))
        headers = {}
        if rng.random() < 0.8:
            headers[ts_name] = rng.choice([*odd, str(NOW + rng.randint(-400, 400))])
        if rng.random() < 0.8:
            headers[sig_name] = rng.choice(
                [*odd, "v0=" + rng.randbytes(32).hex(), rng.randbytes(8).decode("latin-1")]
            )
        length = rng.choice(["auto", "auto", "auto", None, "abc", "0", str(len(body) + 3), "99999"])
        method = rng.choice(["POST", "POST", "POST", "GET", "PUT"])
        path = rng.choice([endpoint.PATH, endpoint.PATH, endpoint.PATH, "/", "/v1/other"])
        status, _, out = call(app, method, path, headers, body, length)
        assert status in (400, 401, 404, 405, 413)
        assert out == b""
    assert start.calls == []


def test_random_bodies_with_a_valid_signature_never_give_5xx_and_start_only_on_the_exact_shape():
    rng = random.Random(99)  # noqa: S311 - a seeded test generator
    app, start = build()
    pieces = [b'{"key":', b'"k"', b',"document":', b'"d"', b"}", b"[", b"]", b"\xff", b" ", b"1"]
    for _ in range(1000):
        if rng.random() < 0.5:
            body = rng.randbytes(rng.randint(1, 200))
        else:
            body = b"".join(rng.choice(pieces) for _ in range(rng.randint(1, 8)))
        before = len(start.calls)
        status, _, _ = call(app, headers=signed(body, ONLY_B), body=body)
        try:
            parse_body(body)
        except BadRequest:
            assert status == 400
            assert len(start.calls) == before
        else:
            assert status == 202
            assert len(start.calls) == before + 1


def test_any_single_byte_change_of_a_valid_request_is_401():
    rng = random.Random(5)  # noqa: S311 - a seeded test generator
    body = body_of()
    good = signed(body, OLD_A)
    ts_name, sig_name = endpoint.TIMESTAMP_HEADER.lower(), endpoint.SIGNATURE_HEADER.lower()
    app, start = build()
    for _ in range(300):
        what = rng.choice(["body", "ts", "sig"])
        headers, sent = dict(good), body
        if what == "body":
            i = rng.randrange(len(body))
            sent = body[:i] + bytes([body[i] ^ (1 << rng.randrange(8))]) + body[i + 1 :]
        else:
            name = ts_name if what == "ts" else sig_name
            old = good[name]
            i = rng.randrange(len(old))
            new = rng.choice([c for c in "0123456789abcdef" if c != old[i]])
            headers[name] = old[:i] + new + old[i + 1 :]
        refused(call(app, headers=headers, body=sent), 401)
    assert start.calls == []


# ---- logs and imports ----


def test_logs_hold_neither_body_nor_signature_nor_secret(caplog):
    caplog.set_level(logging.DEBUG)
    marker = "DOCMARK" + "z" * 12
    key = "KEYMARK-" + "9" * 6
    body = body_of(key, marker)
    good = signed(body, OLD_A)
    sig = good[endpoint.SIGNATURE_HEADER.lower()]
    for start in (Recorder(), Recorder(error=RuntimeError(marker)), Recorder(answer=(409, {}))):
        app, _ = build(start)
        call(app, headers=good, body=body)  # accepted, start failing, conflict
        call(app, headers=signed(body, STRANGER), body=body)  # 401
        call(app, headers={**good, "x-hadavin-signature": "v1=" + sig[3:]}, body=body)  # 401
        bad = marker.encode() + b"{not json"
        call(app, headers=signed(bad, OLD_A), body=bad)  # 400
        call(app, method="GET", headers=good, body=body)  # 405
        call(app, path="/" + marker, headers=good, body=body)  # 404
        call(app, headers=good, body=body, length=str(CAP + 1))  # 413
    text = "\n".join(
        f"{r.getMessage()} {r.args!r} {r.exc_text or ''} {r.exc_info or ''}" for r in caplog.records
    )
    assert "status=202 sender=sender-a" in text
    assert "status=401 sender=-" in text
    assert "status=400 sender=sender-a" in text
    for forbidden in (marker, key, sig, sig[3:], OLD_A, NEW_A, ONLY_B, STRANGER, str(NOW)):
        assert forbidden not in text
    assert all(r.exc_info is None for r in caplog.records)


def test_one_line_per_request_and_the_409_line_is_left_to_start(caplog):
    """ORDER 009 E1a: the 409 line (status, sender id, run id) is written by ``start``, which decides
    the 409; the endpoint adds no second line for that request."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk.triggers")
    body = body_of()
    good = signed(body, OLD_A)

    levels: list[str] = []

    def lines():
        mine = [r for r in caplog.records if r.name == "hadavin_sdk.triggers"]
        levels[:] = [r.levelname for r in mine]
        caplog.clear()
        return [r.getMessage() for r in mine]

    app, _ = build()
    assert call(app, headers=good, body=body)[0] == 202
    assert lines() == ["trigger status=202 sender=sender-a"] and levels == ["INFO"]
    # Design review 1, N10: not verified, so DEBUG (the number of these lines is the caller's choice)
    refused(call(app, headers=signed(body, STRANGER), body=body), 401)
    assert lines() == ["trigger status=401 sender=-"] and levels == ["DEBUG"]
    refused(call(app, method="GET", headers=good, body=body), 405)
    refused(call(app, path="/other", headers=good, body=body), 404)
    refused(call(app, headers=good, body=body, length=None), 400)
    refused(call(app, headers=good, body=body, length=str(CAP + 1)), 413)
    assert [text[:18] for text in lines()] == [
        "trigger status=" + s for s in ("405", "404", "400", "413")
    ]
    assert levels == ["DEBUG"] * 4
    bad = b"{not json"  # verified, then refused: the sender is known, so INFO
    refused(call(app, headers=signed(bad, OLD_A), body=bad), 400)
    assert lines() == ["trigger status=400 sender=sender-a"] and levels == ["INFO"]

    app, _ = build(Recorder(answer=(409, {})))  # a start that logs nothing
    refused(call(app, headers=good, body=body), 409)
    assert lines() == []

    def conflict(req):  # the shape of the worker's line
        logging.getLogger("hadavin_sdk.triggers").warning(
            "trigger status=409 sender=%s run=%s", req.sender, req.run_id
        )
        return 409, {}

    app, _ = build(conflict)
    refused(call(app, headers=good, body=body), 409)
    rid = derive_run_id("tenant-one", "sender-a", "order-1")
    assert lines() == [f"trigger status=409 sender=sender-a run={rid}"]


def test_endpoint_imports_no_runtime_store_or_app_module():
    tree = ast.parse(Path(endpoint.__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            names |= {node.module} | {f"{node.module}.{a.name}" for a in node.names}
    ours = {n for n in names if n.startswith("hadavin_sdk")}
    assert ours == {
        "hadavin_sdk.approvals",
        "hadavin_sdk.approvals.hmac_v0",
        "hadavin_sdk.defaults",  # constants only: the document cap the body bound is built from
        "hadavin_sdk.defaults.MAX_DOCUMENT_BYTES",
    }


def test_constants_are_the_wire_contract():
    assert endpoint.PATH == "/v1/trigger"
    assert endpoint.TIMESTAMP_HEADER == "X-Hadavin-Request-Timestamp"
    assert endpoint.SIGNATURE_HEADER == "X-Hadavin-Signature"
    assert endpoint.KEY_RE.pattern == "[A-Za-z0-9._:-]{1,128}"
    assert hmac_v0.MAX_AGE_S == 300
