# ruff: noqa: S311, UP031, C408
"""FUZZ-1: four seeded, deterministic properties of the signed trigger endpoint (300 cases each).

Same stack as tests/triggers/test_t5_fuzz.py (real Runner and Runtime on the memory store), reused through
`make_stack`; plain loops over `random.Random(seed)` (hypothesis is not installed). Expected outcomes are
written out here, not taken from the product. Every assertion message carries the property, the seed and the case
number; `GENERATORS[name](seed, i)` rebuilds one case.

 1. whatever arrives, the answer is one of the documented statuses, never an exception, and never holds the
    secret, the signature or the body;
 2. a signed request with one flipped bit in body, timestamp or signature, or a timestamp outside +-300 s, is never 2xx;
 3. the same (sender, key, payload) always gives the same run id and one row; another payload gives 409;
 4. raw garbage on a socket to the real quiet server: one well-formed answer in ONE write, or a clean close, and the
    server still takes a valid signed request afterwards.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import http.client
import io
import json
import random
import socket
import threading
from types import SimpleNamespace
from wsgiref.util import setup_testing_defaults

import pytest

from hadavin_sdk.store import MemoryStore
from hadavin_sdk.triggers import worker
from tests.triggers.test_t5_fuzz import (
    A_NEW,
    A_OLD,
    NOW,
    PATH,
    SENDER_A,
    SIG_ENV,
    TENANT,
    TS_ENV,
    make_stack,
    memory_rows,
)

N = 300
SEEDS = {1: 20261120_11, 2: 20261120_12, 3: 20261120_13, 4: 20261120_14}
ALLOWED = frozenset({200, 202, 400, 401, 404, 405, 409, 413, 431, 503})
WIRE_ALLOWED = ALLOWED | {414}  # the quiet server writes 414 for a request line over 64 KB
OK = frozenset({200, 202})
WIRE_TIMEOUT_S = 3.0
MAX_BODY = 65536


def _sig(body: bytes, ts: int, secret: str = A_OLD) -> str:
    return "v0=" + hmac.new(secret.encode(), b"v0:%d:" % ts + body, hashlib.sha256).hexdigest()


def _body(key: str, document: str) -> bytes:
    return json.dumps({"key": key, "document": document}).encode()


def _rid(sender: str, key: str) -> str:
    return "run-" + hashlib.sha256(f"{TENANT}\0{sender}\0{key}".encode()).hexdigest()[:32]


class _Dies:
    def read(self, n=-1):
        raise TimeoutError("stalled")


def call(app, method, path, headers, body, cl, stream=None):
    """Drive the WSGI app in process; `headers` maps WSGI environ names (HTTP_...) to values."""
    environ: dict = {}
    setup_testing_defaults(environ)
    environ.pop("CONTENT_LENGTH", None)
    environ.update({"REQUEST_METHOD": method, "PATH_INFO": path})
    environ["wsgi.input"] = stream if stream is not None else io.BytesIO(body)
    if cl is not None:
        environ["CONTENT_LENGTH"] = cl
    environ.update(headers)
    seen: dict = {}

    def start_response(status, response_headers, exc_info=None):
        seen["status"], seen["headers"] = int(status.split()[0]), list(response_headers)

    chunks = app(environ, start_response)
    try:
        data = b"".join(chunks)
    finally:
        if hasattr(chunks, "close"):
            chunks.close()
    return seen["status"], seen["headers"], data


# ---- property 1 ---------------------------------------------------------------------------------------

METHODS = [
    "POST",
    "GET",
    "PUT",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "PATCH",
    "post",
    "",
    "P\x00ST",
    "TRACE",
]
PATHS = [PATH, PATH + "/", "/v1/trigger?x=1", "/", "", "/health", "/V1/TRIGGER", "/v1//trigger", "/v1/trigger%00",
         "//v1/trigger", "/v1/trigger ", "*", "/../v1/trigger"]  # fmt: skip


def _cl(rng: random.Random, n: int):
    nasty = [None, "", "-1", "-0", "+5", "1e3", "0x10", "9" * 30, "99999999999", "NaN", "0", "00" + str(n),
             f" {n}", f"{n} ", f"{n}\t", f"\t{n}", f"{n}, {n}", f"{n},{n}", f"{n} {n}", "５", "١٢",
             f"{n}\x00", str(n + 1), str(max(n - 1, 0)), "65537", "524289", "1" + "0" * 12, "٣", "5.0", "1_0"]  # fmt: skip
    return rng.choice(nasty) if rng.random() < 0.7 else str(n)


def gen_1(seed: int, i: int):
    rng = random.Random(f"{seed}/{i}")
    kind = rng.choice(["random", "signed", "signed", "wrong-sig", "stale"])
    if kind == "random":
        body = rng.randbytes(rng.choice([0, 1, 8, 40, 300, 5000]))
    else:
        body = _body(
            rng.choice(["k1", "a.b:c-d", "x" * rng.choice([1, 128, 129]), "bad key", ""]),
            "doc " * rng.randint(0, 20) + f"m{i:04d}",
        )
    ts = NOW if kind != "stale" else NOW + rng.choice([-301, -(10**6), 301, 10**9])
    sig = _sig(body, ts)
    if kind == "wrong-sig":
        sig = _sig(body, ts, A_NEW[::-1]) if rng.random() < 0.5 else sig[:-1] + "0"
    hdr = {TS_ENV: str(ts), SIG_ENV: sig}
    for name in rng.sample([TS_ENV, SIG_ENV], rng.choice([0, 0, 0, 1])):
        hdr[name] = rng.choice(
            ["", " ", "v0=", "\x00", "9" * 40, "-1", "v0=" + "z" * 64, "é" * 3, "０" * 10]
        )
    for j in range(rng.choice([0, 0, 3])):
        hdr[f"HTTP_X_{rng.randrange(10**6)}_{j}"] = rng.randbytes(8).decode("latin-1")
    stream = None
    declared = _cl(rng, len(body))
    r = rng.random()
    if r < 0.08:
        stream = _Dies()
    elif r < 0.16:
        stream = io.BytesIO(body[: len(body) // 2])
    return dict(method=rng.choice(METHODS) if rng.random() < 0.3 else "POST",
                path=rng.choice(PATHS) if rng.random() < 0.3 else PATH,
                headers=hdr, body=body, cl=declared, stream=stream, sig=sig)  # fmt: skip


def test_p1_never_500_never_leaks():
    seed = SEEDS[1]
    store = MemoryStore()
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        app, runner = make_stack(Path(tmp), store)
        try:
            seen: dict[int, int] = {}
            for i in range(N):
                c = gen_1(seed, i)
                where = f"[P1 seed={seed} case={i}]"
                try:
                    status, headers, data = call(
                        app, c["method"], c["path"], c["headers"], c["body"], c["cl"], c["stream"]
                    )
                except Exception as e:  # noqa: BLE001
                    pytest.fail(f"{where} exception out of the app: {type(e).__name__}: {e}")
                seen[status] = seen.get(status, 0) + 1
                assert status in ALLOWED, f"{where} status {status}"
                wire = data + b"\n".join(f"{k}: {v}".encode() for k, v in headers)
                for secret in (A_OLD, A_NEW):
                    assert secret.encode() not in wire, f"{where} secret in answer"
                assert c["sig"].encode() not in wire, f"{where} signature in answer"
                if len(c["body"]) >= 8:
                    assert c["body"] not in wire, f"{where} body in answer"
            print("P1 statuses", dict(sorted(seen.items())))
            assert seen.keys() & OK and 401 in seen and 400 in seen, f"too narrow: {seen}"
        finally:
            runner.close()


# ---- property 2 ---------------------------------------------------------------------------------------


def _flip(rng: random.Random, raw: bytes) -> bytes:
    k = rng.randrange(len(raw) * 8)
    out = bytearray(raw)
    out[k // 8] ^= 1 << (k % 8)
    return bytes(out)


def gen_2(seed: int, i: int):
    rng = random.Random(f"{seed}/{i}")
    what = ["body", "timestamp", "signature", "old", "future"][i % 5]
    body = _body(f"key-{rng.randrange(10**6)}", "payload %d" % rng.randrange(10**9))
    ts, sig = NOW, None
    if what == "old":
        ts = NOW - 301 - rng.choice([0, 1, 59, 10**4, 10**8])
    elif what == "future":
        ts = NOW + 301 + rng.choice([0, 1, 59, 10**4, 10**8])
    signed_ts = ts
    sig = _sig(body, ts, rng.choice([A_OLD, A_NEW]))
    ts_text, sent_body = str(ts), body
    if what == "body":
        sent_body = _flip(rng, body)
    elif what == "timestamp":
        ts_text = _flip(rng, ts_text.encode()).decode("latin-1")
    elif what == "signature":
        sig = _flip(rng, sig.encode()).decode("latin-1")
    return what, signed_ts, ts_text, sig, sent_body


def test_p2_one_flipped_bit_or_stale_timestamp_is_never_accepted():
    seed = SEEDS[2]
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore()
        app, runner = make_stack(Path(tmp), store)
        try:
            for i in range(N):
                what, _ts, ts_text, sig, body = gen_2(seed, i)
                where = f"[P2 seed={seed} case={i} what={what} ts={ts_text!r}]"
                status, _h, _d = call(
                    app, "POST", PATH, {TS_ENV: ts_text, SIG_ENV: sig}, body, str(len(body))
                )
                assert status not in OK, (
                    f"{where} accepted with {status}: sig={sig!r} body={body!r}"
                )
                assert status in ALLOWED, f"{where} status {status}"
            assert memory_rows(store) == [], "a refused request left a run row"
            # control: the same generator, untouched, is accepted
            b = _body("control", "x")
            status, _h, _d = call(
                app, "POST", PATH, {TS_ENV: str(NOW), SIG_ENV: _sig(b, NOW)}, b, str(len(b))
            )
            assert status in OK
            for edge in (NOW - 300, NOW + 300):  # inside the window (clock is cut to whole seconds)
                status, _h, _d = call(
                    app, "POST", PATH, {TS_ENV: str(edge), SIG_ENV: _sig(b, edge)}, b, str(len(b))
                )
                assert status in OK, f"edge {edge - NOW}: {status}"
        finally:
            runner.close()


# ---- property 3 ---------------------------------------------------------------------------------------


def test_p3_same_key_same_payload_same_run_other_payload_409():
    seed = SEEDS[3]
    import tempfile
    from pathlib import Path

    rng = random.Random(seed)
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore()
        app, runner = make_stack(Path(tmp), store)
        try:
            keys: list[str] = []
            for i in range(N):
                where = f"[P3 seed={seed} case={i}]"
                key = f"k{i}-{rng.randrange(10**9)}"
                keys.append(key)
                doc = f"document {rng.randrange(10**9)} " + "é☃" * rng.randint(0, 5)
                b = _body(key, doc)
                send = lambda body: call(
                    app,
                    "POST",
                    PATH,
                    {TS_ENV: str(NOW), SIG_ENV: _sig(body, NOW, A_NEW)},
                    body,
                    str(len(body)),
                )
                ids = set()
                for _ in range(rng.randint(1, 3)):
                    status, _h, data = send(b)
                    assert status in OK, f"{where} repeat gave {status}"
                    ids.add(json.loads(data)["run_id"])
                assert ids == {_rid(SENDER_A, key)}, f"{where} run ids {ids}"
                status, _h, data = send(_body(key, doc + "!"))
                assert status == 409 and data == b"", f"{where} other payload gave {status}"
            rows = [r[0] for r in memory_rows(store)]
            assert len(rows) == len(set(rows)) == N, f"rows {len(rows)} distinct {len(set(rows))}"
            assert set(rows) == {_rid(SENDER_A, k) for k in keys}
        finally:
            runner.close()


# ---- property 4 ---------------------------------------------------------------------------------------


class Recorder:
    def __init__(self, sock, log):
        self._sock, self.writes = sock, []
        log.append(self.writes)

    def sendall(self, data, *a):
        self.writes.append(bytes(data))
        return self._sock.sendall(data, *a)

    def send(self, data, *a):
        self.writes.append(bytes(data))
        return self._sock.send(data, *a)

    def __getattr__(self, name):
        return getattr(self._sock, name)


def _signed_raw(key: str, doc: str, declared=None, extra: bytes = b"") -> bytes:
    b = _body(key, doc)
    head = (
        f"POST {PATH} HTTP/1.1\r\nHost: x\r\nContent-Length: {len(b) if declared is None else declared}\r\n"
        f"X-Hadavin-Request-Timestamp: {NOW}\r\nX-Hadavin-Signature: {_sig(b, NOW)}\r\n"
    ).encode()
    return head + extra + b"\r\n" + b


def gen_4(seed: int, i: int) -> tuple[bytes, str]:
    rng = random.Random(f"{seed}/{i}")
    kind = rng.choice(["bytes", "mutated", "headers", "length", "trunc", "lines"])
    base = _signed_raw(f"w{i}", "doc")
    if kind == "bytes":
        return rng.randbytes(rng.choice([1, 2, 16, 200, 3000, 20000])), kind
    if kind == "mutated":
        raw = bytearray(base)
        for _ in range(rng.randint(1, 6)):
            raw[rng.randrange(len(raw))] = rng.randrange(256)
        return bytes(raw), kind
    if kind == "headers":
        n = rng.choice([1, 50, 200, 2000])
        return _signed_raw(
            f"w{i}",
            "doc",
            extra=b"".join(
                b"X-%d: %s\r\n" % (j, b"v" * rng.choice([1, 50, 400])) for j in range(n)
            ),
        ), kind
    if kind == "length":
        d = rng.choice(["-1", "99999999999999999999", "abc", "5, 5", " 7", "0", "1e3", "", "\t9"])
        return _signed_raw(f"w{i}", "doc", declared=d), kind
    if kind == "trunc":
        return base[: rng.randrange(1, len(base))], kind
    line = rng.choice(
        [
            b"GET",
            b"POST",
            b"\x00",
            b"BREW",
            b"P" * 70000,
            b"POST /v1/trigger HTTP/9.9",
            b"POST /v1/trigger HTTP/1.1\n\n",
            b"\r\n\r\n",
            b"POST  /v1/trigger  HTTP/1.1",
        ]
    )
    return line + rng.choice([b"\r\n", b"\n", b"", b"\r\nHost: x\r\n\r\n"]), kind


def _exchange(port: int, data: bytes, drop: bool) -> bytes:
    sock = socket.create_connection((worker.LOOPBACK, port), timeout=WIRE_TIMEOUT_S)
    raw = b""
    try:
        with contextlib.suppress(OSError):
            sock.sendall(data)
            if drop:
                return b""
            sock.shutdown(socket.SHUT_WR)
            while part := sock.recv(65536):
                raw += part
    finally:
        sock.close()
    return raw


def test_p4_raw_garbage_on_the_real_server():
    seed = SEEDS[4]
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore()
        app, runner = make_stack(Path(tmp), store)
        server = worker.make_server(worker.LOOPBACK, 0, app, 1.0)
        log: list[list[bytes]] = []
        real = server.get_request

        def get_request():
            s, a = real()
            return Recorder(s, log), a

        server.get_request = get_request
        t = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
        t.start()
        port = server.server_address[1]
        try:
            kinds: dict[str, int] = {}
            answers = closes = 0
            for i in range(N):
                data, kind = gen_4(seed, i)
                where = f"[P4 seed={seed} case={i} kind={kind} len={len(data)} head={data[:60]!r}]"
                raw = _exchange(port, data, drop=(i % 25 == 24))
                kinds[kind] = kinds.get(kind, 0) + 1
                if raw:
                    answers += 1
                    assert raw.startswith(b"HTTP/1."), f"{where} not HTTP: {raw[:60]!r}"
                    head, sep, tail = raw.partition(b"\r\n\r\n")
                    assert sep, f"{where} no header end"
                    status = int(raw.split(b" ", 2)[1])
                    assert status in WIRE_ALLOWED, f"{where} status {status}"
                    for secret in (A_OLD, A_NEW):
                        assert secret.encode() not in raw, f"{where} secret"
                    clen = [
                        int(x.split(b":")[1])
                        for x in head.split(b"\r\n")
                        if x.lower().startswith(b"content-length:")
                    ]
                    assert clen == [len(tail)], f"{where} content-length {clen} vs {len(tail)}"
                    http.client.HTTPResponse  # noqa: B018 - parsed above by hand
                else:
                    closes += 1
                if i % 60 == 59:
                    good = _exchange(port, _signed_raw(f"alive{i}", "ok"), drop=False)
                    assert good.startswith((b"HTTP/1.0 202", b"HTTP/1.0 200")), (
                        f"{where} server stopped serving: {good[:60]!r}"
                    )
            good = _exchange(port, _signed_raw("final", "ok"), drop=False)
            assert good.startswith((b"HTTP/1.0 202", b"HTTP/1.0 200")), good[:80]
            multi = [w for w in log if len(w) > 1]
            assert not multi, (
                f"{len(multi)} connections wrote more than once: {[x[:30] for x in multi[0]]}"
            )
            print("P4 kinds", kinds, "answers", answers, "clean closes", closes)
        finally:
            server.shutdown()
            t.join(5)
            server.server_close()
            runner.close()


GENERATORS = {"p1": gen_1, "p2": gen_2, "p4": gen_4}
_ = SimpleNamespace
