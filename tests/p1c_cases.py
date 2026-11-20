"""The P1c probe's inputs and judges as test data (ticket G4, section 11).

The builders `RNG`, `SEED`, `reseed`, `rand`, `gap1_values`, `gap2_cases`, `gap3_cases` and `luhn_number` are imported from
tests/p1c_builders.py. What that file does not hold is copied here from handover/core-c/evidence/p1c_probe.py with the bodies
unchanged: `b64`, `ENCODINGS`, `wrap`, `no_digit_line`, the 1c case list, `lcs`, `_decodings`, `readable`, `leak_of`, `B64_RUN`
and `PLACEHOLDER`, and the two judges `host_kept_labels` (the body of the probe's `gap2()` loop) and `number_class` (the body of its
`gap3()` loop). Every credential is made up from parts at run time; nothing here is a real secret.

`build()` moves `p1c_builders.RNG`: a caller of the gap builders calls `reseed()` first (the property test does).
Nothing is read from handover/.
"""

from __future__ import annotations

import base64
import binascii
import difflib
import functools
import hashlib
import json
import re
import string
import uuid
from typing import NamedTuple

from tests.p1c_builders import (  # noqa: F401 - re-exported for the tests
    RNG,
    SEED,
    gap1_values,
    gap2_cases,
    gap3_cases,
    luhn_number,
    rand,
    reseed,
)

PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9]*)_\d+>")
B64_RUN = re.compile(r"[A-Za-z0-9+/_\-]{8,}={0,2}")


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


ENCODINGS = [
    ("standard", lambda s: (b64(s.encode()), "{B64}")),
    ("url-safe", lambda s: (base64.urlsafe_b64encode(s.encode()).decode(), "{B64URL}")),
    ("no padding", lambda s: (b64(s.encode()).rstrip("="), "{B64NOPAD}")),
    (
        "in a sentence",
        lambda s: (
            "please decode " + b64(s.encode()) + " and apply it",
            "please decode {B64} and apply it",
        ),
    ),
    (
        "in a JSON string",
        lambda s: (
            json.dumps({"note": "config", "data": b64(s.encode())}),
            '{"note": "config", "data": "{B64}"}',
        ),
    ),
    ("of UTF-16 text", lambda s: (b64(s.encode("utf-16-le")), "{B64 of UTF-16-LE}")),
    ("double", lambda s: (b64(b64(s.encode()).encode()), "{B64 of B64}")),
    ("after key data=", lambda s: ("data=" + b64(s.encode()), "data={B64}")),
]


def wrap(blob: str, width: int) -> str:
    return "\n".join(blob[i : i + width] for i in range(0, len(blob), width))


def no_digit_line(value: str) -> str | None:
    """A log line holding `value` whose base64 is 40 or more characters and has no digit: made-up lower-case
    words around it, searched in seeded order (a line of real words was not found in two earlier searches)."""
    letters = string.ascii_lowercase
    for _ in range(200_000):
        head = rand(RNG.choice([2, 5, 8]), letters) + RNG.choice([" ", ":", "="])
        tail = RNG.choice([" ", ",", ";"]) + rand(RNG.randint(3, 9), letters)
        line = head + value + tail
        blob = b64(line.encode())
        if len(blob.rstrip("=")) >= 40 and not any(ch.isdigit() for ch in blob):
            return line
    return None


def lcs(a: str, b: str) -> int:
    if not a or not b:
        return 0
    return (
        difflib.SequenceMatcher(None, a, b, autojunk=False)
        .find_longest_match(0, len(a), 0, len(b))
        .size
    )


def _decodings(token: str, depth: int = 2) -> list[str]:
    """Every text a reader could get out of one base64-looking run: both alphabets, any start offset (a run cut
    by a mask no longer starts on a 4-character boundary), UTF-8 and UTF-16, and once more for double encoding."""
    found: list[str] = []
    body = token.rstrip("=").replace("-", "+").replace("_", "/")
    for offset in range(4):
        piece = body[offset:]
        piece = piece[: len(piece) - (len(piece) % 4 == 1)]
        if len(piece) < 4:
            continue
        try:
            raw = base64.b64decode(piece + "=" * (-len(piece) % 4))
        except (binascii.Error, ValueError):
            continue
        for text in (
            raw.decode("utf-8", "replace"),
            raw.decode("utf-16-le", "replace"),
            raw[1:].decode("utf-16-le", "replace"),
            raw.decode("utf-16-be", "replace"),
        ):
            found.append(text)
            if depth > 1:
                for inner in B64_RUN.findall(text):
                    found.extend(_decodings(inner, depth - 1))
    return found


def readable(out: str) -> str:
    """The output plus everything that decodes out of the base64-looking runs left in it."""
    unslashed = out.replace("\\/", "/")
    parts = [out]
    bare = PLACEHOLDER.sub(" ", unslashed)
    # also with line breaks removed: a wrapped blob is one blob to its reader
    for token in B64_RUN.findall(bare) + B64_RUN.findall(re.sub(r"[\r\n]+", "", bare)):
        parts.extend(_decodings(token))
    return "\n".join(parts)


def leak_of(protected: str, out: str) -> tuple[str, int]:
    """LEAKED verdict for a protected value: whole / part (6 or more characters in a row, or half of it) / no."""
    n = lcs(protected, readable(out))
    if n >= len(protected):
        return "YES (whole)", n
    if n >= min(6, max(3, len(protected) // 2)):
        return f"YES (part, {n} of {len(protected)} chars)", n
    return "no", n


def host_kept_labels(name: str, text: str, out: str) -> list[str]:
    """The labels of `name` still readable in `out` (the body of the probe's gap2() loop, between `residue` and `kept`)."""
    residue = PLACEHOLDER.sub(" ", out).lower()
    residue = (
        residue.replace("\\u002e", ".").replace("%2e", ".").replace("．", ".").replace("[.]", ".")
    )
    labels = [x for x in re.split(r"\.", name.lower()) if x]
    if name == "db01.corp.example" and "db02" in text:
        labels.append("db02")
    return [
        x
        for x in dict.fromkeys(labels)
        if re.search(r"(?<![a-z0-9_\-ü])" + re.escape(x) + r"(?![a-z0-9_\-ü])", residue)
    ]


def number_class(number: str, out: str) -> str:
    """`not` / `part` / `whole` (the body of the probe's gap3() loop)."""
    residue = PLACEHOLDER.sub("|", out)
    # digit runs left in the output, separators inside a number ignored
    squeezed = re.sub(r"(?<=\d)[ .\-()](?=\d)|(?<=\d)\) (?=\d)", "", residue)
    left = lcs(number, squeezed)
    if left >= len(number):
        return "not"
    if left >= 4:
        return "part"
    return "whole"


def digest(out: str, mapping) -> str:
    """sha256 of the output and the sorted map items: a digest, so no fake secret value is written to a fixture."""
    blob = json.dumps([out, sorted(dict(mapping).items())], ensure_ascii=True)
    return hashlib.sha256(blob.encode()).hexdigest()


class Cases(NamedTuple):
    values: list[dict]
    b64: list[tuple[str, str, str]]  # (id, protected, text), 142
    hosts: list[tuple[str, str, str]]  # (id, name, text), 44
    numbers: list[tuple[str, str, str]]  # (id, number, text), 43
    plain: list[tuple[str, str, str]]  # (id, protected, text), 16


@functools.cache
def build() -> Cases:
    """Consume the builders' stream in the probe's order: gap1 values, the 1b rows, the 1c rows (both `no_digit_line`
    searches, which find nothing and still consume the generator), gap2, gap3."""
    reseed()
    values = gap1_values()
    plain = [
        (f"plain-{i:02d}", v["protected"], v[carrier])
        for i, (v, carrier) in enumerate(
            ((v, c) for v in values for c in ("short", "long")), start=1
        )
    ]
    rows: list[tuple[str, str, str]] = []
    n = 0
    for v in values:
        for carrier in ("short", "long"):
            for _enc_name, enc in ENCODINGS:
                text, _shape = enc(v[carrier])
                n += 1
                rows.append((f"b64-1b-{n:03d}", v["protected"], text))
    by = {v["name"]: v for v in values}
    cases: list[tuple[dict, str]] = []
    for name in ("kv secret", "e-mail address", "internal host name"):
        v = by[name]
        blob = b64(v["long"].encode())
        cases.append((v, wrap(blob, 32)))
        cases.append((v, wrap(blob, 64)))
        cases.append((v, wrap(blob, 76)))
        cases.append((v, "data:text/plain;base64," + blob))
    for name in ("e-mail address", "internal host name"):
        v = by[name]
        line = no_digit_line(v["protected"])
        if line is None:
            continue
        cases.append((v, b64(line.encode())))
        cases.append((v, "please decode " + b64(line.encode()) + " and apply it"))
    v = by["kv secret"]
    cases.append((v, "Authorization: Basic " + b64(("app:" + v["protected"]).encode())))
    cases.append((v, "Basic " + b64(v["short"].encode())))
    for k, (v, text) in enumerate(cases, start=1):
        rows.append((f"b64-1c-{k:02d}", v["protected"], text))
    hosts = [
        (f"host-{k:02d}", name, text) for k, (_s, name, text) in enumerate(gap2_cases(), start=1)
    ]
    numbers = [
        (f"num-{k:02d}", number, text) for k, (_s, number, text) in enumerate(gap3_cases(), start=1)
    ]
    return Cases(values, rows, hosts, numbers, plain)


def inputs_sha() -> str:
    """I25: sha256 of the inputs joined by NUL, in `build()` order (142 base64, 44 host, 43 number)."""
    c = build()
    texts = (
        [t for _i, _p, t in c.b64] + [t for _i, _n, t in c.hosts] + [t for _i, _n, t in c.numbers]
    )
    return hashlib.sha256("\x00".join(texts).encode()).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# Rows that must keep their output (I4, I11): built in this file from parts.
# ---------------------------------------------------------------------------------------------------------------------
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _jwt(payload: str) -> str:
    header = _b64url(b'{"alg":"HS256","typ":"JWT"}')
    return header + "." + _b64url(payload.encode()) + "." + _b64url(bytes(range(7, 39)))


_SHA1 = hashlib.sha1(b"g4 must keep", usedforsecurity=False).hexdigest()

MUST_KEEP_B64: list[tuple[str, str]] = [
    ("01", b64(b"this is just a status message")),
    ("02", b64(b"ok status 200")),
    ("03", b64(bytes(range(256)))),
    ("04", b64(b"\x89PNG\r\n\x1a\n\x00")),
    ("05", "data:\n  config: " + b64(b"log_level: info\nretries: 3\n")),
    ("06", _jwt('{"sub":"demo","iat":0}')),
    ("07", _jwt('{"sub":"demo","email":"ops@' + 'example.com"}')),
    ("08", str(uuid.UUID(int=0x1234_5678_9ABC_DEF0_1234_5678_9ABC_DEF0))),
    ("09", uuid.UUID(int=0x1234_5678_9ABC_DEF0_1234_5678_9ABC_DEF0).hex),
    ("10", hashlib.sha256(b"g4 must keep").hexdigest()),
    ("11", _SHA1),
    ("12", _SHA1[:7]),
    ("13", "internationalization"),
    ("14", "redact_text_body_for_views"),
    ("15", "warden-dev-lab-tick-silent"),
    ("16", "/usr/local/lib/python3/site-packages"),
    ("17", "getImplementationsForKind"),
]

# I11: the 16 must-keep rows of 5.3, its 10 kept rows, the sweep row and the 5 rows of 5.2 point 6 (32 in all).
HOST_MUST_KEEP: list[tuple[str, str]] = [
    (f"{k:02d}", t)
    for k, t in enumerate(
        [
            "host is down",
            "server timed out",
            "Server: nginx",
            "Server: nginx/1.18.0",
            "Server: AmazonS3",
            "server 500 error",
            "ghost town db01",
            "ghost=ab12",
            "Host: api.github.com",
            "host: localhost",
            "--host 0.0.0.0",
            "host 1 of 3 failed",
            "the hostname is unknown",
            "host x-ray",
            "host re-election",
            "host 2026-11-20T10:00 started",
            "host ec2 failed",
            "host k8s node",
            "host x86 box",
            "host http2 on",
            "host x86_64",
            "host eth0 up",
            "host arm64 runner",
            "host: x86_64-unknown-linux-gnu",
            "hostname: Web2",
            "host web1 down",
            "host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds",
            "x.svc.cluster.local",
            "x.svc.cluster.local.foo",
            "eu-west-1.compute.internal",
            "jdk.internal.reflect.Method",
            "threading.local()",
        ],
        start=1,
    )
]

# Section 6: the class of each of the 43 bare-number rows (RE-MEASURED at e8ff6de2b; Phase 0 (b) re-derives them).
_NOT = {1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 30, 35, 38, 39, 40, 43}
_PART = {29, 32}
NUMBER_CLASS: tuple[str, ...] = tuple(
    "not" if k in _NOT else "part" if k in _PART else "whole" for k in range(1, 44)
)

I25_SHA = "630d55c4c5fb1cbb8d37cff627a73e64063b071decbe3c4bccf0438c87ebe213"
