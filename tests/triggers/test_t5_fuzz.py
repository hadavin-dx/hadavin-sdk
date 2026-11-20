"""Seeded fuzz of the signed trigger endpoint (ORDER 016, item 4): three layers, one grammar.

Layer 1 calls the WSGI callable in-process (endpoint + real Runner + real Runtime on the memory
store, a model double that does nothing). Layer 2 sends raw bytes over a loopback socket to
`worker.make_server` (the quiet server). Layer 3 is layer 1 on PostgreSQL and needs
HADAVIN_TEST_PG_DSN (skipped with the usual reason without it).

The cases are not noise: `make_case` starts from a correctly signed, well-formed request and applies
a few mutations (route, Content-Length, timestamp, signature, body, input stream), so most cases get
past the early checks. The generator is its own oracle: it knows which mutation it applied, so it
knows the one status the request must get (`Case.refusal`), or that the request must reach `start`
(`refusal is None`). `Model` then says what `start` must answer from the keys accepted so far. No
function of the product decides what is expected; signatures, run ids and trigger refs are written
out here.

Every assertion message starts with the seed and the case number. To replay one case:
`make_case`/`wire_cases` are pure functions of the seed (no answer feeds back into the generator),
so `inproc_cases(SEED, n)[i]` or `wire_cases(SEED, n)[i]` is that case again.

FINDING, fixed: a request line with HTTP version 2.0 or higher got 505 from the stdlib parser under
the quiet server. It is 400 now; the wire loop sends that case class and one test replays a case.
Also refused with 400 by the quiet server since then: header names with an underscore, more than
one Content-Length header, any Transfer-Encoding header.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import io
import json
import logging
import os
import random
import re
import socket
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import timedelta
from types import SimpleNamespace

import pytest

from hadavin_sdk.models import RunState, now
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.triggers import worker
from tests.contracts.kinds.store_postgres import pg_schema
from tests.k5_support import build_runtime, k5_cfg
from tests.triggers.crash_launcher import AGENT, PRINCIPAL, TENANT, CountingLLM

if os.environ.get("HADAVIN_TEST_PG_DSN"):  # set: the driver must be there, never a silent skip
    import psycopg

SEED_INPROC, SEED_WIRE, SEED_PG = 20261120_1, 20261120_2, 20261120_3
N_INPROC, N_WIRE, N_PG = 2000, 304, 300  # 304 made: the cases of the FINDING are not sent
INPROC, WIRE = "inproc", "wire"

# ---- the wire contract, written out (not imported from the endpoint) ----
PATH, POST = "/v1/trigger", "POST"
TS_HEADER, SIG_HEADER = "X-Hadavin-Request-Timestamp", "X-Hadavin-Signature"
TS_ENV, SIG_ENV = "HTTP_X_HADAVIN_REQUEST_TIMESTAMP", "HTTP_X_HADAVIN_SIGNATURE"
MAX_BODY = 65536
WINDOW_S = 300
ENDPOINT_STATUSES = frozenset({200, 202, 400, 401, 404, 405, 409, 413, 503})
SERVER_STATUSES = frozenset({400, 414, 431})  # written by the quiet server before the endpoint
OK = frozenset({200, 202})
NOW = 1_700_000_000
CLOCK = NOW + 0.7  # a clock with a fraction: the window edge must not depend on it

# ---- fake secrets and planted markers, all built from parts ----
SENDER_A, SENDER_B = "sender-a", "sender-b"
A_OLD = "fz" * 4 + "a" * 16 + "1" * 16
A_NEW = "fz" * 4 + "b" * 16 + "2" * 16
B_ONLY = "fz" * 4 + "c" * 16 + "3" * 16
STRANGER = "fz" * 4 + "d" * 16 + "4" * 16  # a well-formed secret no sender has
SECRETS = {SENDER_A: (A_OLD, A_NEW), SENDER_B: (B_ONLY,)}
OWNER = {A_OLD: SENDER_A, A_NEW: SENDER_A, B_ONLY: SENDER_B}
ALL_SECRETS = (A_OLD, A_NEW, B_ONLY, STRANGER)
TOKEN = "Zq7" + "fuzz" + "Tok" + "x41c9"  # planted in every body
KEY_MARK = "kq7" + "m" + "-"  # the start of every key of the pool
KEY_POOL = tuple(f"{KEY_MARK}{i:02d}" for i in range(24))
DOC_POOL = tuple(f"checkout 5xx {TOKEN} from 10.0.0.{i}, revision {i}" for i in (5, 6, 7))
KEY_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-"
HEX64 = re.compile(r"[0-9a-fA-F]{64}")

SERVER_TIMEOUT_S = 0.3  # the server's socket timeout in layer 2
CLIENT_TIMEOUT_S = 8.0
LOOPBACK = "127.0.0.1"
HANDLER_THREAD = "process_request_thread"


# ---- the oracle's own arithmetic ----------------------------------------------------------------


def sig_hex(body: bytes, ts: str, secret: str) -> str:
    """The "v0" signature, written out: hex(HMAC-SHA256(secret, "v0:" + ts + ":" + body))."""
    base = b"v0:" + ts.encode("utf-8") + b":" + body
    return hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()


def run_id_of(sender: str, key: str) -> str:
    return "run-" + hashlib.sha256(f"{TENANT}\0{sender}\0{key}".encode()).hexdigest()[:32]


def ref_of(sender: str, key: str, document: bytes) -> str:
    return f"{sender}/{key}#" + hashlib.sha256(document).hexdigest()


# ---- one generated request ----------------------------------------------------------------------


@dataclass
class Case:
    index: int
    notes: list[str]  # the mutations applied, for the assertion message
    method: str | None  # None = the environ has no such member (in-process only)
    path: str | None
    sent: bytes  # the body bytes offered to the server
    length: object  # the Content-Length value (str; an int in-process once), None = no header
    ts: object  # the timestamp header as sent, None = no header
    sig: str | None
    made_sig: str  # the 64 hex digits of the signature made for this case
    noise: list[tuple[str, str]]  # other headers that must change nothing
    stream: str = "bytes"  # in-process: how wsgi.input behaves
    dup: tuple[str, ...] = ()  # wire: these headers are sent twice
    # --- the oracle ---
    refusal: int | None = None  # the one status this request must get; None = it reaches `start`
    signed: bool = False  # a valid signature of a configured sender over the bytes read
    sender: str | None = None
    key: str | None = None
    document: bytes | None = None
    unread: bool = False  # wire: the server answers without reading all that was sent
    short: bool = False  # wire: fewer body bytes than declared, the server waits for more

    def where(self, seed: int, layer: str) -> str:
        return f"[{layer} seed={seed} case={self.index} mutations={self.notes}]"


def _valid_body(rng: random.Random, key: str, doc: str) -> tuple[bytes, bool, str]:
    """(bytes, tight, style). tight = cutting the last byte off cannot leave a valid body."""
    obj = {"key": key, "document": doc}
    style = rng.choice(["dumps", "dumps", "utf8", "reordered", "padded", "compact", "escaped-key"])
    if style == "utf8":
        return json.dumps(obj, ensure_ascii=False).encode("utf-8"), True, style
    if style == "reordered":
        return json.dumps({"document": doc, "key": key}).encode(), True, style
    if style == "padded":
        inner = f' "key" :\t{json.dumps(key)} ,\r\n "document":{json.dumps(doc)} '
        return (" \r\n\t{" + inner + "}\n ").encode(), False, style
    if style == "compact":
        return json.dumps(obj, separators=(",", ":")).encode(), True, style
    if style == "escaped-key":
        escaped = "".join(f"\\u{ord(c):04x}" for c in key)
        return f'{{"key":"{escaped}","document":{json.dumps(doc)}}}'.encode(), True, style
    return json.dumps(obj).encode(), True, style


def _document(rng: random.Random) -> tuple[str, str]:
    base = f"checkout 5xx {TOKEN} revision {rng.randrange(10**6)}"
    kind = rng.choice(
        ["plain", "plain", "unicode", "nul", "control", "bom", "quotes", "huge", "lines"]
    )
    if kind == "unicode":
        return base + " žluťoučký 日本語 \U0001f600", kind
    if kind == "nul":
        return base[:9] + "\x00" + base[9:] + "\x00", kind
    if kind == "control":
        return base + "".join(chr(c) for c in rng.sample(range(1, 32), 6)) + "\x7f\x85", kind
    if kind == "bom":
        return "﻿" + base, kind
    if kind == "quotes":
        return base + ' "q" \\ / \b\f\n\r\t <script> %s {0}', kind
    if kind == "huge":
        return base + "x" * rng.randrange(8000, 40000), kind
    if kind == "lines":
        return base.replace(" ", "\r\n"), kind
    return base, kind


def _nested(depth: int, opener: bytes, closer: bytes) -> bytes:
    return opener * depth + json.dumps(TOKEN).encode() + closer * depth


def _invalid_body(rng: random.Random, key: str, doc: str) -> tuple[bytes, str]:
    """A body the body rules refuse. Each holds TOKEN; none is the exact {key, document} shape."""
    k, d = json.dumps(key).encode(), json.dumps(doc).encode()
    tk = json.dumps(TOKEN + "-k").encode()  # a key that carries the token when no document does
    good = b'{"key":' + k + b',"document":' + d + b"}"
    table: dict[str, object] = {
        # extra or missing members
        "extra-member": lambda: good[:-1] + b',"extra":1}',
        "extra-sender": lambda: good[:-1] + b',"sender":"sender-b"}',
        "extra-run-id": lambda: good[:-1] + b',"run_id":"run-' + b"0" * 32 + b'"}',
        "missing-key": lambda: b'{"document":' + d + b"}",
        "missing-document": lambda: b'{"key":' + tk + b"}",
        "member-case": lambda: b'{"Key":' + k + b',"Document":' + d + b"}",
        "member-empty-name": lambda: b'{"":' + k + b',"document":' + d + b"}",
        # wrong types
        "key-number": lambda: b'{"key":12,"document":' + d + b"}",
        "key-null": lambda: b'{"key":null,"document":' + d + b"}",
        "key-list": lambda: b'{"key":[' + k + b'],"document":' + d + b"}",
        "key-object": lambda: b'{"key":{"k":' + k + b'},"document":' + d + b"}",
        "document-number": lambda: b'{"key":' + tk + b',"document":5}',
        "document-null": lambda: b'{"key":' + tk + b',"document":null}',
        "document-bool": lambda: b'{"key":' + tk + b',"document":true}',
        "document-list": lambda: b'{"key":' + k + b',"document":[' + d + b"]}",
        "document-object": lambda: b'{"key":' + k + b',"document":{"text":' + d + b"}}",
        "document-nan": lambda: b'{"key":' + tk + b',"document":NaN}',
        "document-infinity": lambda: b'{"key":' + tk + b',"document":-Infinity}',
        "document-1e999": lambda: b'{"key":' + tk + b',"document":1e999}',
        "document-huge-int": lambda: b'{"key":' + tk + b',"document":' + b"9" * 6000 + b"}",
        "top-array": lambda: b"[" + good + b"]",
        "top-array-pair": lambda: b"[" + k + b"," + d + b"]",
        "top-string": lambda: d,
        "string-of-json": lambda: json.dumps(good.decode()).encode(),
        # duplicate members
        "dup-key": lambda: good[:-1] + b',"key":' + k + b"}",
        "dup-key-first-bad": lambda: b'{"key":1,' + good[1:],
        "dup-document": lambda: good[:-1] + b',"document":' + d + b"}",
        # deep nesting
        "deep-document": lambda: (
            b'{"key":' + k + b',"document":' + _nested(9000, b"[", b"]") + b"}"
        ),
        "deep-arrays": lambda: _nested(rng.choice([1500, 20000]), b"[", b"]"),
        "deep-objects": lambda: _nested(8000, b'{"a":', b"}"),
        "deep-unclosed": lambda: b"[" * 30000 + json.dumps(TOKEN).encode(),
        # the key rule
        "key-129": lambda: b'{"key":"' + b"k" * 129 + b'","document":' + d + b"}",
        "key-huge": lambda: b'{"key":"' + b"k" * 30000 + b'","document":' + d + b"}",
        "key-empty": lambda: b'{"key":"","document":' + d + b"}",
        "key-space": lambda: b'{"key":"a b","document":' + d + b"}",
        "key-slash": lambda: b'{"key":"a/b","document":' + d + b"}",
        "key-newline": lambda: b'{"key":"ab\\n","document":' + d + b"}",
        "key-nul": lambda: b'{"key":"ab\\u0000","document":' + d + b"}",
        "key-not-ascii": lambda: '{"key":"klíč","document":'.encode() + d + b"}",
        "key-fullwidth": lambda: '{"key":"ｋ１","document":'.encode() + d + b"}",
        "key-lone-surrogate": lambda: b'{"key":"k\\ud800","document":' + d + b"}",
        # text that is not text
        "utf8-ff": lambda: good[:-2] + b'\xff"}',
        "utf8-cut-sequence": lambda: good[:-2] + b'\xc3"}',
        "utf8-overlong": lambda: good[:-2] + b'\xc0\xaf"}',
        "utf8-encoded-surrogate": lambda: good[:-2] + b'\xed\xa0\x80"}',
        "lone-high-surrogate": lambda: good[:-2] + b'\\ud800"}',
        "lone-low-surrogate": lambda: good[:-2] + b'\\udc00"}',
        "swapped-surrogates": lambda: good[:-2] + b'\\udc00\\ud800"}',
        "raw-control-char": lambda: good[:-2] + b'\x01"}',
        "raw-newline": lambda: good[:-2] + b'\n"}',
        "raw-nul": lambda: good[:-2] + b'\x00"}',
        "nul-after": lambda: good + b"\x00",
        "nul-before": lambda: b"\x00" + good,
        "bom-before": lambda: b"\xef\xbb\xbf" + good,
        "utf16": lambda: good.decode().encode("utf-16"),
        "utf16-le": lambda: good.decode().encode("utf-16-le"),
        "utf32": lambda: good.decode().encode("utf-32"),
        "random-bytes": lambda: (
            rng.randbytes(rng.randrange(1, 400))
            + TOKEN.encode()
            + rng.randbytes(rng.randrange(0, 400))
        ),
        # nearly JSON
        "cut-one": lambda: good[:-1],
        "cut-two": lambda: good[:-2],
        "trailing-comma": lambda: good[:-1] + b",}",
        "single-quotes": lambda: good.replace(b'"', b"'"),
        "bare-names": lambda: b"{key:" + k + b",document:" + d + b"}",
        "comment": lambda: good[:-1] + b"/* c */}",
        "garbage-after": lambda: good + b"x",
        "two-objects": lambda: good + good,
        "form-encoded": lambda: b"key=" + key.encode() + b"&document=" + TOKEN.encode(),
        "bad-escape": lambda: good[:-2] + b'\\x41"}',
        "cut-escape": lambda: good[:-2] + b'\\u12"}',
    }
    name = rng.choice(sorted(table))
    return table[name](), name  # type: ignore[operator]


def _key(rng: random.Random, index: int, unique: bool) -> str:
    if unique:  # a key no other case has: a row for it can only come from this case
        return f"u{index}-" + "".join(rng.choice(KEY_CHARS) for _ in range(12))
    if rng.random() < 0.5:
        return rng.choice(KEY_POOL)
    size = rng.choice([1, 2, 8, 20, 64, 127, 128])
    return "".join(rng.choice(KEY_CHARS) for _ in range(size))


def _timestamp(rng: random.Random, wire: bool, mutate: bool) -> tuple[str, object, bool, str]:
    """(the text that is signed, the header as sent, inside the contract?, note)."""
    plain = str(NOW + rng.randint(-WINDOW_S, WINDOW_S))
    if not mutate:
        edge = rng.choice([None, None, None, 0, 1, -1, 299, -299, 300, -300])
        if edge is not None:
            plain = str(NOW + edge)
            return plain, plain, True, f"ts{edge:+d}"
        if rng.random() < 0.1:
            padded = plain.rjust(12, "0")  # 12 digits at most: still a timestamp
            return padded, padded, True, "ts-zero-padded-12"
        return plain, plain, True, ""
    spaced = [(" " + plain, "ts-space-before"), (plain + " ", "ts-space-after")]
    spaced += [("\t" + plain + " \t", "ts-tabs-around")]
    bad: list[tuple[str, object, str]] = [
        (str(NOW + 301), str(NOW + 301), "ts+301"),
        (str(NOW - 301), str(NOW - 301), "ts-301"),
        (str(NOW + 302), str(NOW + 302), "ts+302"),
        (str(NOW - 86400), str(NOW - 86400), "ts-one-day"),
        (str(NOW + 10**6), str(NOW + 10**6), "ts-far-ahead"),
        ("0", "0", "ts-zero"),
        (plain.rjust(13, "0"), plain.rjust(13, "0"), "ts-zero-padded-13"),
        (str(NOW * 1000), str(NOW * 1000), "ts-13-digits-ms"),
        ("9" * 40, "9" * 40, "ts-40-digits"),
        ("9" * 5000, "9" * 5000, "ts-5000-digits"),
        ("+" + plain, "+" + plain, "ts-plus-sign"),
        ("-" + plain, "-" + plain, "ts-minus-sign"),
        ("-0", "-0", "ts-minus-zero"),
        (plain[:5] + " " + plain[5:], plain[:5] + " " + plain[5:], "ts-space-inside"),
        (plain + ".0", plain + ".0", "ts-decimal"),
        ("1.7e9", "1.7e9", "ts-exponent"),
        (hex(NOW), hex(NOW), "ts-hex"),
        (plain[:-1] + "_" + plain[-1], plain[:-1] + "_" + plain[-1], "ts-underscore"),
        ("", "", "ts-empty"),
        (plain, None, "ts-missing"),
        (plain + "x", plain + "x", "ts-letter"),
    ]
    for zero, name in ((0x0660, "arabic-indic"), (0xFF10, "fullwidth"), (0x0966, "devanagari")):
        other = "".join(chr(zero + int(c)) for c in plain)
        bad.append((other, other, f"ts-{name}-digits"))
    bad.append((plain[:-1] + "²", plain[:-1] + "²", "ts-superscript-digit"))
    if not wire:  # values a WSGI server never hands over, but the callable must not trip on
        bad += [(plain, plain.encode(), "ts-bytes"), (plain, int(plain), "ts-int")]
        bad += [(plain + "\n", plain + "\n", "ts-newline"), (plain, f"{plain},{plain}", "ts-twice")]
        bad += [(plain, sent, name) for sent, name in spaced]
    choice = rng.randrange(len(bad) + (len(spaced) if wire else 0))
    if choice >= len(bad):  # the server strips the header value: the stripped text is what counts
        sent, name = spaced[choice - len(bad)]
        return plain, sent, True, name + "(stripped by the server)"
    signed, sent, name = bad[choice]
    return signed, sent, False, name


def _signature(
    rng: random.Random, wire: bool, mutate: bool, good: str, read: bytes, ts: str, secret: str
) -> tuple[str | None, bool, str]:
    """(the header as sent, still the signature of what is read?, note). `good` is 64 hex."""
    full = "v0=" + good
    if not mutate:
        return full, True, ""
    at = rng.randrange(len(good))
    flipped = good[:at] + f"{int(good[at], 16) ^ (1 << rng.randrange(4)):x}" + good[at + 1 :]
    bad: list[tuple[str | None, str]] = [
        ("v0=" + sig_hex(read + b" ", ts, secret), "sig-of-another-body"),
        ("v0=" + sig_hex(read[:-1], ts, secret), "sig-of-a-shorter-body"),
        ("v0=" + sig_hex(read, str(int(NOW) + 7), secret), "sig-of-another-timestamp"),
        ("v0=" + sig_hex(read, ts, STRANGER), "sig-stranger-secret"),
        ("v0=" + sig_hex(read, ts, secret[:-1]), "sig-secret-cut"),
        ("v0=" + sig_hex(read, ts, secret.upper()), "sig-secret-upper"),
        ("v0=" + hashlib.sha256(b"v0:" + ts.encode() + b":" + read).hexdigest(), "sig-no-key"),
        ("v1=" + good, "sig-prefix-v1"),
        ("V0=" + good, "sig-prefix-upper"),
        ("v0:" + good, "sig-prefix-colon"),
        ("sha256=" + good, "sig-prefix-sha256"),
        (good, "sig-no-prefix"),
        ("v0=v0=" + good, "sig-prefix-twice"),
        ("v0=" + good[:-1], "sig-cut-one"),
        ("v0=" + good[:32], "sig-cut-half"),
        ("v0=", "sig-prefix-only"),
        ("v0=" + flipped, "sig-one-bit"),
        ("v0=" + good + "00", "sig-two-more-digits"),
        ("v0=" + good + "a" * 9000, "sig-very-long"),
        ("v0=" + good + "é", "sig-not-ascii"),
        ("v0=" + good[:20] + " " + good[20:], "sig-space-inside"),
        ("v0=" + "0" * 64, "sig-zeros"),
        ("", "sig-empty"),
        (None, "sig-missing"),
    ]
    if good.upper() != good:  # hex with a letter (all but never not the case)
        bad.append(("v0=" + good.upper(), "sig-upper-hex"))
    spaced = [(" " + full, "sig-space-before"), (full + "  ", "sig-space-after")]
    if not wire:
        bad += [(f"{full},{full}", "sig-twice"), (full + "\n", "sig-newline"), *spaced]
    choice = rng.randrange(len(bad) + (len(spaced) + 1 if wire else 0))
    if choice == len(bad) + len(spaced):
        return full, False, "sig-header-twice"  # wire: two header lines, the server joins them
    if choice >= len(bad):
        sent, name = spaced[choice - len(bad)]
        return sent, True, name + "(stripped by the server)"
    sent, name = bad[choice]
    return sent, False, name


BAD_METHODS = ("GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "post", "Post", "POSTS")
BAD_METHODS_INPROC = ("", "POST ", " POST", "POST\n", None)
BAD_PATHS = ("/", "/v1", "/v1/", "/v1/trigger/", "/v1/Trigger", "/V1/TRIGGER", "/v1/triggers")
BAD_PATHS += ("/v1/trigger/x", "/v2/trigger", "/v1/trigger%20", "/v1/trigger;a=1", "/v1/./trigger")
BAD_PATHS += ("/v1/../v1/trigger", "*", "/v1/trigger#f", "/v1/trigger%00", "/" + TOKEN)
# In-process PATH_INFO is taken as it is; a WSGI server would have split or decoded these.
BAD_PATHS_INPROC = ("", "/v1/trigger?x=1", "/v1/trigger\x00", "//v1/trigger", "/v1/%74rigger", None)
# What the stdlib server turns into exactly PATH before the endpoint sees it.
WIRE_SAME_PATHS = ("/v1/trigger?x=1", "/v1/trigger?", "/v1/%74rigger", "/%76%31/trigger")
WIRE_SAME_PATHS += ("//v1/trigger", "/v1/trigger?" + TOKEN)
NOISE = (
    ("X-Hadavin-Sender", SENDER_B),  # a claim the endpoint must not read
    ("X-Hadavin-Run-Id", "run-" + "0" * 32),
    ("X-Hadavin-Signature-V1", "v0=" + "0" * 64),
    ("X-Forwarded-For", "10.1.2.3"),
    ("Content-Type", "text/plain; charset=utf-16"),
    ("Authorization", "Bearer " + "x" * 24),
    ("X-Long", "a" * 30000),
    ("X-Odd", "ÿé 日"),
    ("X-Empty", ""),
    ("Cookie", "session=" + "c" * 40),
)


def _length(
    rng: random.Random, wire: bool, mutate: bool, body: bytes, valid_tight: bool
) -> tuple[bytes, object, int | None, bytes, bool, str]:
    """(bytes offered, header value, the length the endpoint must take it as or None for "not a
    length", the bytes the signature is made over, the bytes read are cut?, note)."""
    n = len(body)
    if not mutate:
        style = rng.random()
        if style < 0.08 and len(str(n)) < 12:
            padded = str(n).rjust(rng.randint(len(str(n)) + 1, 12), "0")
            return body, padded, n, body, False, "length-zero-padded"
        if style < 0.16:
            junk = rng.randbytes(rng.randrange(1, 200)) + TOKEN.encode()
            return body + junk, str(n), n, body, False, "junk-after-the-declared-length"
        return body, str(n), n, body, False, ""
    k = rng.randrange(1, min(n, 64))
    not_a_length: list[tuple[object, str]] = [
        (None, "length-missing"),
        ("", "length-empty"),
        ("0", "length-zero"),
        ("00", "length-zeros"),
        (f"-{n}", "length-negative"),
        ("-0", "length-minus-zero"),
        (f"+{n}", "length-plus-sign"),
        ("abc", "length-letters"),
        (f"{n}a", "length-digit-letter"),
        (f"{n}.0", "length-decimal"),
        ("1e3", "length-exponent"),
        (hex(n), "length-hex"),
        (f"{n},{n}", "length-twice-joined"),
        (f"{str(n)[0]} {str(n)[1:]}", "length-space-inside"),
        ("".join(chr(0x0660 + int(c)) for c in str(n)), "length-arabic-indic-digits"),
        ("".join(chr(0xFF10 + int(c)) for c in str(n)), "length-fullwidth-digits"),
        (str(n)[:-1] + "²", "length-superscript-digit"),
    ]
    if not wire:
        not_a_length += [(n, "length-int"), (f" {n}", "length-space-before")]
        not_a_length += [(f"{n} ", "length-space-after"), (f"{n}\n", "length-newline")]
        not_a_length += [(str(n).encode(), "length-bytes")]
    over: list[tuple[str, int, str]] = [
        (str(MAX_BODY + 1), MAX_BODY + 1, "length-cap-plus-one"),
        ("9" * 11, int("9" * 11), "length-11-digits"),
        ("9" * 13, 10**12, "length-13-digits"),
        ("9" * 40, 10**12, "length-40-digits"),
        ("9" * 5000, 10**12, "length-5000-digits"),
        (str(n).rjust(13, "0"), 10**12, "length-zero-padded-13"),
        (str(2**63), 10**12, "length-2-to-63"),
    ]
    pick = rng.random()
    if pick < 0.40:
        value, name = rng.choice(not_a_length)
        return body, value, None, body, False, name
    if pick < 0.60:
        value, declared, name = rng.choice(over)
        return body, value, declared, body, False, name
    if pick < 0.75:
        return body, str(n + k), n + k, body, False, f"length-larger-by-{k}"
    if pick < 0.88 or not valid_tight:
        # the signature is over the whole body, the server reads less: the two differ
        return body, str(n - k), n - k, body, False, f"length-smaller-by-{k}"
    # the sender signed exactly what the server reads: verified, but the body is cut JSON
    return body, str(n - k), n - k, body[: n - k], True, f"length-smaller-by-{k}-signed-as-read"


def make_case(rng: random.Random, index: int, layer: str, force: str | None = None) -> Case:
    """One request and what must happen to it. `force`: "valid" = no mutation and a key no other
    case has; "stranger" = the same, signed with a secret no sender has."""
    wire, free = layer == WIRE, force is None
    notes: list[str] = []

    method: str | None = POST
    path: str | None = PATH
    route = None
    pick = rng.random()
    if free and pick < 0.035:
        path = rng.choice(BAD_PATHS + (() if wire else BAD_PATHS_INPROC))
        route = 404
        notes.append(f"path={path!r}")
    elif wire and pick < 0.15:
        path = rng.choice(WIRE_SAME_PATHS)
        notes.append(f"path={path!r}(the server makes it the path)")
    if free and rng.random() < 0.035:
        method = rng.choice(BAD_METHODS + (() if wire else BAD_METHODS_INPROC))
        route = route or 405
        notes.append(f"method={method!r}")

    key = _key(rng, index, unique=not free)
    if free and key in KEY_POOL:  # pool keys repeat: the same document again, or another one
        doc, doc_note = rng.choice(DOC_POOL), "pool-document"
    else:
        doc, doc_note = _document(rng)
    body_ok = not free or rng.random() < 0.60
    if body_ok:
        body, tight, style = _valid_body(rng, key, doc)
        notes.append(f"body=valid/{style}/{doc_note}")
    else:
        body, style = _invalid_body(rng, key, doc)
        tight = False
        notes.append(f"body={style}")
    if free and rng.random() < 0.012:  # the size cap itself, with an exact length
        over = rng.random() < 0.5
        room = MAX_BODY + (1 if over else 0) - len(json.dumps({"key": key, "document": ""}))
        doc = (TOKEN + " " + "y" * MAX_BODY)[:room]
        body, body_ok, tight = json.dumps({"key": key, "document": doc}).encode(), True, True
        notes[-1] = "body=valid/one-byte-over-the-cap" if over else "body=valid/exactly-the-cap"

    sent, length, declared, signed_bytes, cut, note = _length(
        rng, wire, free and rng.random() < 0.10, body, body_ok and tight
    )
    notes.append(note)
    if cut:
        body_ok = False
    stream = "bytes"
    if free and not wire and rng.random() < 0.02:
        stream = rng.choice(["one-byte-short", "raises-oserror", "raises-timeout", "gives-text"])
        notes.append(f"input-{stream}")

    secret = STRANGER if force == "stranger" else rng.choice((A_OLD, A_NEW, B_ONLY, B_ONLY))
    ts_signed, ts_sent, ts_ok, note = _timestamp(rng, wire, free and rng.random() < 0.09)
    notes.append(note)
    good = sig_hex(signed_bytes, ts_signed, secret)
    sig_sent, sig_ok, note = _signature(
        rng, wire, free and rng.random() < 0.13, good, signed_bytes, ts_signed, secret
    )
    notes.append(note)
    dup = (SIG_HEADER,) if note == "sig-header-twice" else ()
    if force == "stranger":
        notes.append("signed-with-a-secret-no-sender-has")

    noise = [NOISE[i] for i in sorted(rng.sample(range(len(NOISE)), rng.choice([0, 0, 1, 2, 4])))]
    notes += [f"header={name}" for name, _ in noise]

    reads = route is None and declared is not None and 0 < declared <= MAX_BODY
    short = reads and declared > len(sent)  # type: ignore[operator]
    read_ok = reads and not short and stream == "bytes"
    signed = (
        read_ok and ts_ok and sig_ok and secret in OWNER and signed_bytes == sent[:declared]  # type: ignore[misc]
    )
    if route is not None:
        refusal: int | None = route
    elif declared is None or declared <= 0:
        refusal = 400
    elif declared > MAX_BODY:
        refusal = 413
    elif not read_ok:
        refusal = 400
    elif not signed:
        refusal = 401
    elif not body_ok:
        refusal = 400
    else:
        refusal = None
    return Case(
        index=index,
        notes=[n for n in notes if n],
        method=method,
        path=path,
        sent=sent,
        length=length,
        ts=ts_sent,
        sig=sig_sent,
        made_sig=good,
        noise=noise,
        stream=stream,
        dup=dup,
        refusal=refusal,
        signed=bool(signed),
        sender=OWNER.get(secret),
        key=key if body_ok else None,
        document=doc.encode("utf-8") if body_ok else None,
        unread=len(sent) > (declared if reads and not short else 0),  # type: ignore[operator]
        short=bool(short),
    )


def inproc_cases(seed: int, count: int) -> list[Case]:
    rng = random.Random(seed)  # noqa: S311 - a seeded test generator
    return [make_case(rng, i, INPROC) for i in range(count)]


# ---- the stack under test -----------------------------------------------------------------------


def make_stack(tmp_path, store):
    """The WSGI callable and its Runner on a real Runtime; two senders, one of them with two
    secrets. The model double answers "nothing to do" and is safe under threads."""
    runtime, _cards = build_runtime(k5_cfg(tmp_path), CountingLLM(None, 0.0), store=store)
    names = {f"{s}-secret-{i}": v for s, values in SECRETS.items() for i, v in enumerate(values)}
    senders = [
        SimpleNamespace(
            id=sender,
            secret_names=[f"{sender}-secret-{i}" for i in range(len(values))],
            agent_id=AGENT,
            principal_id=PRINCIPAL,
        )
        for sender, values in SECRETS.items()
    ]
    triggers = SimpleNamespace(
        tenant=TENANT,
        senders=senders,
        max_body_bytes=MAX_BODY,
        max_running=4,
        ack_wait_s=20.0,
    )
    app = SimpleNamespace(
        config=SimpleNamespace(triggers=triggers),
        registry=runtime.registry,
        runtime=runtime,
        store=store,
        trigger_secret=names.__getitem__,
    )
    return worker.make_app(app, clock=lambda: CLOCK, poll_s=0.01)


def memory_rows(store) -> list[tuple[str, str, str, str]]:
    later = now() + timedelta(days=1)
    runs = [run for state in RunState for run in store.list_runs(state, later, limit=100_000)]
    return [(r.run_id, r.agent_id, r.principal_id, r.trigger_ref) for r in runs]


def sql_rows(dsn: str) -> list[tuple[str, str, str, str]]:
    with psycopg.connect(dsn) as db:
        found = db.execute(
            "SELECT run_id, agent_id, principal_id, trigger_ref FROM runs ORDER BY run_id"
        ).fetchall()
    return [tuple(row) for row in found]


@contextlib.contextmanager
def product_log():
    """Every record of the product's loggers from DEBUG up, as text lines (args and tracebacks too)."""
    lines: list[str] = []

    class Keep(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            trace = logging.Formatter().formatException(record.exc_info) if record.exc_info else ""
            lines.append(
                f"{record.name} {record.levelname} {record.getMessage()} | {record.args!r} "
                f"| {record.exc_text or ''} {trace}"
            )

    logger, handler = logging.getLogger("hadavin_sdk"), Keep(level=logging.DEBUG)
    before = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    try:
        yield lines
    finally:
        logger.removeHandler(handler)
        logger.setLevel(before)


def check_log(lines: list[str], signatures: set[str], where: str) -> None:
    text = "\n".join(lines)
    assert "hadavin_sdk.triggers" in text, f"{where} the trigger log was not captured"
    for name, needle in (("body token", TOKEN), ("pool key", KEY_MARK), ("traceback", "Traceback")):
        at = text.find(needle)
        assert at < 0, f"{where} {name} in the log: {text[max(0, at - 200) : at + 200]!r}"
    for i, value in enumerate(ALL_SECRETS):
        assert value not in text, f"{where} secret number {i} is in the log"
    leaked = {h.lower() for h in HEX64.findall(text)} & signatures
    assert not leaked, f"{where} {len(leaked)} signature(s) in the log"


# ---- the model: what `start` must answer, and which rows may exist -------------------------------


@dataclass
class Model:
    rows: dict[str, tuple[str, str, bytes]] = field(default_factory=dict)

    def expected(self, case: Case) -> frozenset[int]:
        if case.refusal is not None:
            return frozenset({case.refusal})
        row = self.rows.get(run_id_of(case.sender, case.key))  # type: ignore[arg-type]
        return OK if row is None or row[2] == case.document else frozenset({409})

    def accept(self, case: Case) -> None:
        """Called for every case that must reach `start`: the first one of a key owns the row."""
        if case.refusal is None:
            run_id = run_id_of(case.sender, case.key)  # type: ignore[arg-type]
            self.rows.setdefault(run_id, (case.sender, case.key, case.document))  # type: ignore[arg-type]

    def check_store(self, rows: list[tuple[str, str, str, str]], where: str) -> None:
        """Every row belongs to a request that was signed by a configured sender and passed the
        body rules; one row per (sender, key); nothing else is in the table."""
        ids = [row[0] for row in rows]
        assert len(ids) == len(set(ids)), f"{where} a run id is stored twice"
        foreign = sorted(set(ids) - set(self.rows))
        assert not foreign, f"{where} rows no valid request asked for: {foreign[:5]}"
        missing = sorted(set(self.rows) - set(ids))
        assert not missing, f"{where} acknowledged runs with no row: {missing[:5]}"
        pairs = {(sender, key) for sender, key, _ in self.rows.values()}
        assert len(pairs) == len(self.rows) == len(rows), f"{where} not one row per (sender, key)"
        for run_id, agent, principal, ref in rows:
            sender, key, document = self.rows[run_id]
            assert (agent, principal) == (AGENT, PRINCIPAL), f"{where} {run_id}: wrong identity"
            assert ref == ref_of(sender, key, document), f"{where} {run_id}: wrong trigger_ref"


@dataclass
class Stats:
    sent: int = 0
    signed: int = 0  # a valid signature of a configured sender
    valid: int = 0  # signed and the body rules passed: the request reached `start`
    skipped: int = 0  # the case class of a FINDING, not sent
    no_answer: int = 0  # wire: nothing came back (allowed for that case)
    statuses: Counter = field(default_factory=Counter)
    kinds: Counter = field(default_factory=Counter)

    def line(self) -> str:
        codes = " ".join(f"{code}:{n}" for code, n in sorted(self.statuses.items()))
        return (
            f"sent={self.sent} signed={self.signed} valid={self.valid} skipped={self.skipped} "
            f"no_answer={self.no_answer} statuses[{codes}]"
        )


# ---- layer 1 and 3: the callable, in-process ----------------------------------------------------


class _Input(io.BytesIO):
    """wsgi.input with one of the faults a server's stream can have."""

    def __init__(self, data: bytes, fault: str) -> None:
        super().__init__(data)
        self._fault = fault

    def read(self, size: int | None = -1):  # type: ignore[override]
        if self._fault == "raises-oserror":
            raise ConnectionResetError("the peer is gone")
        if self._fault == "raises-timeout":
            raise TimeoutError("timed out")
        data = super().read(size)
        if self._fault == "one-byte-short":
            return data[:-1]
        if self._fault == "gives-text":
            return data.decode("latin-1")
        return data


def call_inproc(wsgi, case: Case) -> tuple[str, list[tuple[str, str]], bytes, str]:
    """(status line, headers, body, what the callable wrote to wsgi.errors)."""
    errors = io.StringIO()
    environ: dict[str, object] = {
        "SERVER_NAME": "test",
        "SERVER_PORT": "0",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.errors": errors,
        "wsgi.input": _Input(case.sent, case.stream),
    }
    for name, value in case.noise:
        environ["HTTP_" + name.upper().replace("-", "_")] = value
    pairs = (
        ("REQUEST_METHOD", case.method),
        ("PATH_INFO", case.path),
        ("CONTENT_LENGTH", case.length),
        (TS_ENV, case.ts),
        (SIG_ENV, case.sig),
    )
    for name, value in pairs:
        if value is not None:
            environ[name] = value
    if SIG_HEADER in case.dup:
        environ[SIG_ENV] = f"{case.sig},{case.sig}"  # what a WSGI server makes of two lines
    seen: list[tuple[str, list[tuple[str, str]]]] = []

    def start_response(status, headers, exc_info=None):
        seen.append((status, headers))

    chunks = wsgi(environ, start_response)
    out = b"".join(chunks)
    assert len(seen) == 1, f"start_response was called {len(seen)} times"
    return seen[0][0], seen[0][1], out, errors.getvalue()


def check_answer(case: Case, status: int, body: bytes, model: Model, where: str) -> None:
    """The rules every answer obeys, on either layer."""
    expected = model.expected(case)
    assert status in expected, f"{where} got {status}, expected {sorted(expected)}"
    if status in OK:
        try:
            answer = json.loads(body)
        except ValueError:
            raise AssertionError(
                f"{where} a {status} body that is not JSON: {body[:80]!r}"
            ) from None
        assert isinstance(answer, dict) and set(answer) == {"run_id", "state"}, f"{where} {answer}"
        assert answer["run_id"] == run_id_of(case.sender, case.key), f"{where} {answer}"  # type: ignore[arg-type]
        assert answer["state"] in {state.value for state in RunState}, f"{where} {answer}"
    else:
        assert body == b"", f"{where} a refusal ({status}) with a body: {body[:80]!r}"


def fuzz_inproc(seed: int, count: int, wsgi, rows, layer: str, checkpoint: int) -> Stats:
    """Send `count` generated requests to the callable; `rows()` reads the run table."""
    model, stats, signatures = Model(), Stats(), set()
    with product_log() as lines:
        for case in inproc_cases(seed, count):
            where = case.where(seed, layer)
            signatures.add(case.made_sig)
            try:
                status_line, headers, body, errors = call_inproc(wsgi, case)
            except Exception as exc:  # nothing may escape the callable
                raise AssertionError(f"{where} the callable raised {exc!r}") from exc
            status = int(status_line.split(" ", 1)[0])
            assert status in ENDPOINT_STATUSES, f"{where} unknown status {status_line!r}"
            check_answer(case, status, body, model, where)
            assert errors == "", f"{where} wsgi.errors: {errors[:200]!r}"
            names = [name.lower() for name, _ in headers]
            assert dict(headers)["Content-Length"] == str(len(body)), f"{where} {headers}"
            assert ("content-type" in names) == (status in OK), f"{where} {headers}"
            assert TOKEN.encode() not in body and "server" not in names, f"{where} {headers}"
            model.accept(case)
            stats.sent += 1
            stats.signed += case.signed
            stats.valid += case.refusal is None
            stats.statuses[status] += 1
            if stats.sent % checkpoint == 0:
                model.check_store(rows(), f"[{layer} seed={seed} after case={case.index}]")
        end = f"[{layer} seed={seed} at the end]"
        model.check_store(rows(), end)
        check_log(lines, signatures, end)
    assert stats.sent == count
    share = stats.valid / stats.sent
    assert 0.20 <= share <= 0.45, f"{end} {share:.0%} of the cases reached start: {stats.line()}"
    for code in (400, 401, 404, 405, 409, 413):
        assert stats.statuses[code] > 0, f"{end} no case got {code}: {stats.line()}"
    assert stats.statuses[200] + stats.statuses[202] > 0, f"{end} nothing accepted"
    return stats


def test_fuzz_layer_1_in_process_2000_requests_on_the_memory_store(tmp_path):
    store = MemoryStore()
    wsgi, runner = make_stack(tmp_path, store)
    try:
        stats = fuzz_inproc(
            SEED_INPROC, N_INPROC, wsgi, lambda: memory_rows(store), "layer 1", checkpoint=250
        )
    finally:
        runner.close()
    print("layer 1:", stats.line())


@pytest.fixture
def dsn():
    """A DSN on a fresh migrated schema; the schema is dropped afterwards."""
    yield from pg_schema()


def test_fuzz_layer_3_in_process_300_requests_on_postgresql(dsn, tmp_path):
    from hadavin_sdk.store.postgres import PostgresStore, connect

    conn = connect(dsn)
    wsgi, runner = make_stack(tmp_path, PostgresStore(conn))
    try:
        stats = fuzz_inproc(SEED_PG, N_PG, wsgi, lambda: sql_rows(dsn), "layer 3", checkpoint=100)
    finally:
        runner.close()
        conn.close()
    print("layer 3:", stats.line())


# ---- layer 2: raw bytes over a loopback socket --------------------------------------------------


@dataclass
class WireCase:
    index: int
    kind: str
    base: Case | None  # the signed request the bytes were made from
    data: bytes
    tail: str = "read"  # "read": read to the end; "half": half-close, then read; "drop": close
    pieces: int = 1  # the bytes are sent in this many parts
    # what must come back: "model" (the base's own expectation), "status" (exactly `status`),
    # "nothing" (the connection is closed with no byte), "refusal" (any refusal or nothing)
    expect: str = "model"
    status: int = 0

    def where(self, seed: int) -> str:
        notes = self.base.notes if self.base is not None else []
        return f"[layer 2 seed={seed} case={self.index} kind={self.kind} mutations={notes}]"


@dataclass
class Seen:
    raw: bytes
    end: str  # "closed", "reset", "client timeout" or "dropped"

    @property
    def status(self) -> int | None:
        parts = self.raw.split(b"\r\n", 1)[0].split(b" ")
        return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

    @property
    def head(self) -> bytes:
        return self.raw.partition(b"\r\n\r\n")[0]

    @property
    def body(self) -> bytes:
        return self.raw.partition(b"\r\n\r\n")[2]


NAME_STYLES = (str, str, str.lower, str.upper, str.swapcase)
VERSION_FINDING = (b"HTTP/2.0", b"HTTP/9.9", b"HTTP/3.0", b"HTTP/10.1")
BROKEN_LINES = (
    b"\x16\x03\x01\x02\xff\xfe" + TOKEN.encode(),
    b"POST",
    b"POST /v1/trigger HTTP/1.1 " + TOKEN.encode(),
    b"POST /v1/trigger HTTP/abc",
    b"POST /v1/trigger HTTP/1.1.1",
    b"POST /v1/trigger HTTP/1.x",
    b"POST /v1/trigger HTTP/-1.1",
    b"POST /v1/trigger FTP/1.1",
    b"POST /v1/trigger http/1.1",
    b"POST /v1/trigger HTTP/1." + b"1" * 20,
    b"POST /v1/trigger",  # two words: an HTTP/0.9 request, which is GET only
    TOKEN.encode() + b" " + TOKEN.encode(),
)


def render(
    case: Case,
    rng: random.Random,
    *,
    line: bytes | None = None,
    eol: bytes = b"\r\n",
    version: str = "HTTP/1.1",
    gap: str = " ",
    underscore: bool = False,
    first: tuple[bytes, ...] = (),
    more: tuple[bytes, ...] = (),
    end: bool = True,
) -> bytes:
    """The request as bytes: header order, name case and the whitespace around values vary."""
    if line is None:
        line = f"{case.method}{gap}{case.path}{gap}{version}".encode("ascii")
    headers: list[tuple[str, str]] = [("Host", LOOPBACK), *case.noise]
    if case.length is not None:
        headers.append(("Content-Length", str(case.length)))
    for name, value in ((TS_HEADER, case.ts), (SIG_HEADER, case.sig)):
        if value is not None:
            shown = name.replace("-", "_") if underscore else name
            headers += [(shown, str(value))] * (2 if name in case.dup else 1)
    rng.shuffle(headers)
    lines = [line, *first]
    for name, value in headers:
        sep = rng.choice([": ", ": ", ":", ":  ", ":\t"])
        # The length is taken unstripped at its end, so no whitespace is put after it.
        after = "" if name == "Content-Length" else rng.choice(["", "", "", " ", "\t "])
        lines.append(f"{rng.choice(NAME_STYLES)(name)}{sep}{value}{after}".encode())
    lines += more
    head = eol.join(lines) + eol
    return head + eol + case.sent if end else head


def make_wire(rng: random.Random, index: int) -> WireCase:
    """One wire case: seven in ten are the grammar of `make_case` sent as it is, the rest break
    the framing around a request that is otherwise valid (so only the framing can refuse it)."""
    if rng.random() < 0.70:
        base = make_case(rng, index, WIRE)
        tail = "half" if base.short and rng.random() < 0.9 else rng.choice(["read", "read", "half"])
        return WireCase(index, "grammar", base, render(base, rng), tail)
    base = make_case(rng, index, WIRE, force="valid")
    kind = rng.choice(
        ["http-1.0", "lf-only", "two-spaces", "tabs", "trickle", "pipelined", "expect-100"]
        + ["same-length-twice", "underscore-names", "broken-line", "broken-line", "version-2-up"]
        + ["line-too-long", "header-too-long", "too-many-headers", "chunked", "absolute-uri"]
        + ["no-colon-first", "folded-signature", "length-twice-first-wrong", "no-end-half-close"]
        + ["no-end-stall", "silent", "empty-first-line", "http-0.9-get", "early-close", "cut"]
        + ["stranger", "version-2-up", "pipelined"]
    )
    n = len(base.sent)
    # --- the framing differs, the request is the same: it must be accepted ---
    if kind == "http-1.0":
        return WireCase(index, kind, base, render(base, rng, version="HTTP/1.0"))
    if kind == "lf-only":
        return WireCase(index, kind, base, render(base, rng, eol=b"\n"))
    if kind == "two-spaces":
        return WireCase(index, kind, base, render(base, rng, gap="  "))
    if kind == "tabs":
        return WireCase(index, kind, base, render(base, rng, gap="\t"))
    if kind == "trickle":
        return WireCase(index, kind, base, render(base, rng), pieces=rng.randint(2, 5))
    if kind == "pipelined":
        once = render(base, rng)
        base.unread = True  # the second request is never read: one connection, one request
        return WireCase(index, kind, base, once + once)
    if kind == "expect-100":
        return WireCase(index, kind, base, render(base, rng, more=(b"Expect: 100-continue",)))
    # --- refused by the server or the endpoint with one known status ---
    if kind == "same-length-twice":  # two Content-Length headers, also two equal ones
        more = (b"Content-Length: %d" % n,)
        base.unread = True
        return WireCase(
            index, kind, base, render(base, rng, more=more), expect="status", status=400
        )
    if kind == "underscore-names":  # no header name with an underscore is taken
        base.unread = True
        data = render(base, rng, underscore=True)
        return WireCase(index, kind, base, data, expect="status", status=400)
    if kind == "version-2-up":  # was the FINDING: the stdlib parser's 505 is sent as 400
        line = b"POST /v1/trigger " + rng.choice(VERSION_FINDING)
        return WireCase(
            index, kind, base, render(base, rng, line=line), expect="status", status=400
        )
    if kind == "broken-line":
        line = rng.choice(BROKEN_LINES)
        return WireCase(
            index, kind, base, render(base, rng, line=line), expect="status", status=400
        )
    if kind == "line-too-long":
        line = b"POST /" + TOKEN.encode() + b"a" * rng.randint(65536, 70000)
        return WireCase(index, kind, base, line, tail="half", expect="status", status=414)
    if kind == "header-too-long":
        more = (b"X-Long: " + TOKEN.encode() + b"a" * rng.randint(65536, 70000),)
        base.unread = True
        return WireCase(
            index, kind, base, render(base, rng, more=more), expect="status", status=431
        )
    if kind == "too-many-headers":
        more = tuple(b"X-N%d: %d" % (i, i) for i in range(rng.randint(101, 140)))
        base.unread = True
        return WireCase(
            index, kind, base, render(base, rng, more=more), expect="status", status=431
        )
    if kind == "chunked":
        base.length, body = None, b"%x\r\n" % n + base.sent + b"\r\n0\r\n\r\n"
        data = render(base, rng, more=(b"Transfer-Encoding: chunked",), end=False) + b"\r\n" + body
        base.unread = True
        return WireCase(index, kind, base, data, expect="status", status=400)
    if kind == "absolute-uri":
        line = b"POST http://127.0.0.1/v1/trigger HTTP/1.1"
        base.unread = True
        return WireCase(
            index, kind, base, render(base, rng, line=line), expect="status", status=404
        )
    if kind == "no-colon-first":  # the header block ends at a line that is no header
        first = (TOKEN.encode() + b" is no header",)
        base.unread = True
        return WireCase(
            index, kind, base, render(base, rng, first=first), expect="status", status=400
        )
    if kind == "folded-signature":
        sig, base.sig = base.sig, None
        more = (f"{SIG_HEADER}: {sig[:30]}".encode(), b" " + sig[30:].encode())  # type: ignore[index]
        return WireCase(
            index, kind, base, render(base, rng, more=more), expect="status", status=401
        )
    if kind == "length-twice-first-wrong":  # two different lengths: refused before the body is read
        first = (b"Content-Length: %d" % (n - 1),)
        base.unread = True
        return WireCase(
            index, kind, base, render(base, rng, first=first), expect="status", status=400
        )
    if kind == "no-end-half-close":
        data = render(base, rng, end=False)
        return WireCase(index, kind, base, data, tail="half", expect="status", status=400)
    if kind == "no-end-stall":  # answered when the server's socket timeout is over
        data = render(base, rng, end=False)
        return WireCase(index, kind, base, data, expect="status", status=400)
    if kind == "stranger":
        other = make_case(rng, index, WIRE, force="stranger")
        return WireCase(index, kind, other, render(other, rng), expect="status", status=401)
    # --- no answer at all ---
    if kind == "silent":
        return WireCase(index, kind, None, b"", tail="half", expect="nothing")
    if kind == "empty-first-line":
        return WireCase(index, kind, base, b"\r\n" + render(base, rng), expect="nothing")
    if kind == "http-0.9-get":  # HTTP/0.9 has no status line: the connection is just closed
        line = b"GET /v1/trigger"
        return WireCase(index, kind, base, render(base, rng, line=line), expect="nothing")
    # --- the client leaves in the middle ---
    data = render(base, rng)
    data = data[: rng.randrange(1, len(data))]  # at least one byte is missing: never valid
    if kind == "early-close":
        return WireCase(index, kind, base, data, tail="drop", expect="refusal")
    return WireCase(index, "cut", base, data, tail="half", expect="refusal")


def wire_cases(seed: int, count: int) -> list[WireCase]:
    rng = random.Random(seed)  # noqa: S311 - a seeded test generator
    return [make_wire(rng, i) for i in range(count)]


def exchange(port: int, case: WireCase) -> Seen:
    """Send the bytes of `case` and read until the server closes. No assertion in here."""
    sock = socket.create_connection((LOOPBACK, port), timeout=CLIENT_TIMEOUT_S)
    try:
        step = max(1, len(case.data) // case.pieces)
        parts = [case.data[i : i + step] for i in range(0, len(case.data), step)]
        try:
            for i, part in enumerate(parts):
                sock.sendall(part)
                if i + 1 < len(parts):
                    time.sleep(0.005)
            if case.tail == "half":
                sock.shutdown(socket.SHUT_WR)
        except OSError:
            pass  # the server answered and closed before it had read everything
        if case.tail == "drop":
            return Seen(b"", "dropped")
        raw, end = b"", "closed"
        try:
            while part := sock.recv(65536):
                raw += part
        except (ConnectionResetError, ConnectionAbortedError):  # Windows aborts where Linux resets
            end = "reset"
        except TimeoutError:
            end = "client timeout"
        return Seen(raw, end)
    finally:
        sock.close()


def _handlers_done(timeout_s: float = CLIENT_TIMEOUT_S) -> bool:
    """True once no connection thread of a server is alive."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not [t for t in threading.enumerate() if HANDLER_THREAD in t.name]:
            return True
        time.sleep(0.01)
    return False


@contextlib.contextmanager
def serving(wsgi):
    """The real server on a free loopback port; shut down, joined and closed on the way out."""
    server = worker.make_server(LOOPBACK, 0, wsgi, SERVER_TIMEOUT_S)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
    try:
        thread.start()
        yield server
    finally:
        if thread.is_alive():
            server.shutdown()
            thread.join(CLIENT_TIMEOUT_S)
        server.server_close()
        done = _handlers_done()
    if thread.is_alive() or not done:
        raise AssertionError("a server thread is still running")


def check_wire(case: WireCase, seen: Seen, model: Model, where: str) -> None:
    """What came back for one wire case. `model` is not changed here."""
    raw, base = seen.raw, case.base
    assert seen.end != "client timeout", f"{where} the server kept the connection open"
    lowered = raw.lower()
    for name, needle in (("the body token", TOKEN), ("python", "python"), ("a traceback", "trace")):
        assert needle.lower().encode() not in lowered, (
            f"{where} {name} in the answer: {raw[:300]!r}"
        )
    for i, value in enumerate(ALL_SECRETS):
        assert value.encode() not in raw, f"{where} secret number {i} in the answer"
    if base is not None:
        assert base.made_sig.encode() not in lowered, f"{where} the signature in the answer"
    if not raw:
        allowed = (
            case.expect in ("nothing", "refusal")
            or case.tail == "drop"
            or (base is not None and base.unread)  # the close can cut the answer off
        )
        assert allowed, f"{where} no answer ({seen.end})"
        return
    assert raw.startswith(b"HTTP/1."), f"{where} not an HTTP answer: {raw[:80]!r}"
    status = seen.status
    assert status is not None, f"{where} no status: {raw[:80]!r}"
    assert status in ENDPOINT_STATUSES | SERVER_STATUSES, f"{where} unknown status {raw[:80]!r}"
    head = seen.head.lower()
    assert b"\r\nserver:" not in head and b"wsgiserver" not in head, f"{where} {seen.head!r}"
    assert b"/3." not in head, f"{where} a version in the answer head: {seen.head!r}"
    if status not in OK:
        assert seen.body == b"", f"{where} a refusal ({status}) with a body: {seen.body[:120]!r}"
        assert b"content-type" not in head, f"{where} {seen.head!r}"
    if case.expect == "model":
        check_answer(base, status, seen.body, model, where)  # type: ignore[arg-type]
    elif case.expect == "status":
        assert status == case.status, f"{where} got {status}, expected {case.status}"
    elif case.expect == "nothing":
        raise AssertionError(f"{where} expected no answer, got {raw[:120]!r}")
    else:
        assert status in (400, 401, 404, 405, 413), f"{where} got {status} for a cut request"


def fuzz_wire(seed: int, count: int, wsgi, rows) -> Stats:
    model, stats, signatures = Model(), Stats(), set()
    after = make_case(random.Random(seed + 1), count, WIRE, force="valid")  # noqa: S311
    with product_log() as lines:
        with serving(wsgi) as server:
            for case in wire_cases(seed, count):
                where = case.where(seed)
                stats.kinds[case.kind] += 1
                if case.base is not None:
                    signatures.add(case.base.made_sig)
                seen = exchange(server.server_port, case)
                check_wire(case, seen, model, where)
                if case.expect == "model":
                    model.accept(case.base)  # type: ignore[arg-type]
                    stats.signed += case.base.signed  # type: ignore[union-attr]
                    stats.valid += case.base.refusal is None  # type: ignore[union-attr]
                stats.sent += 1
                stats.no_answer += not seen.raw
                if seen.status is not None:
                    stats.statuses[seen.status] += 1
            # the server still answers a valid request after all of that
            last = WireCase(count, "afterwards", after, render(after, random.Random(seed + 2)))  # noqa: S311
            seen = exchange(server.server_port, last)
            assert seen.status in OK, (
                f"{last.where(seed)} not served afterwards: {seen.raw[:120]!r}"
            )
            check_wire(last, seen, model, last.where(seed))
            model.accept(after)
            signatures.add(after.made_sig)
        end = f"[layer 2 seed={seed} at the end]"
        model.check_store(rows(), end)  # the server is closed: every connection thread has ended
        check_log(lines, signatures, end)
    assert stats.sent + stats.skipped == count and stats.sent >= 300, f"{end} {stats.line()}"
    share = stats.valid / count
    assert 0.20 <= share <= 0.45, f"{end} {share:.0%} of the cases reached start: {stats.line()}"
    for code in (400, 401, 404, 405, 413, 414, 431):
        assert stats.statuses[code] > 0, f"{end} no case got {code}: {stats.line()}"
    assert stats.statuses[200] + stats.statuses[202] > 0, f"{end} nothing accepted"
    return stats


def test_fuzz_layer_2_raw_socket_300_requests_against_the_quiet_server(tmp_path, capsys):
    store = MemoryStore()
    wsgi, runner = make_stack(tmp_path, store)
    try:
        stats = fuzz_wire(SEED_WIRE, N_WIRE, wsgi, lambda: memory_rows(store))
    finally:
        runner.close()
    captured = capsys.readouterr()
    assert captured.err == "", f"[layer 2 seed={SEED_WIRE}] on stderr: {captured.err[:500]!r}"
    assert captured.out == "", f"[layer 2 seed={SEED_WIRE}] on stdout: {captured.out[:500]!r}"
    print("layer 2:", stats.line())


# ---- FINDING ------------------------------------------------------------------------------------

FINDING_CASE = 144  # the first "version-2-up" case of SEED_WIRE (the others: 164, 201)


def test_finding_layer_2_http_version_2_or_higher_is_answered_400_not_505(tmp_path):
    """Replays exactly one case of the wire layer: seed SEED_WIRE, case FINDING_CASE. The FINDING
    was: a request line with HTTP version 2.0 or higher (HTTP/2.0, HTTP/3.0, HTTP/9.9, HTTP/10.1)
    is answered '505 HTTP Version Not Supported' by the stdlib request parser under the quiet
    server, a 5xx that is not 503. Now: 400, empty body, nothing started."""
    case = wire_cases(SEED_WIRE, FINDING_CASE + 1)[FINDING_CASE]
    assert case.kind == "version-2-up" and case.expect == "status" and case.status == 400
    store = MemoryStore()
    wsgi, runner = make_stack(tmp_path, store)
    try:
        with serving(wsgi) as server:
            seen = exchange(server.server_port, case)
    finally:
        runner.close()
    assert memory_rows(store) == []
    assert seen.raw.startswith(b"HTTP/1.") and seen.body == b""
    where = case.where(SEED_WIRE)
    assert seen.status == 400, f"{where} not 400: {seen.raw[:120]!r}"
