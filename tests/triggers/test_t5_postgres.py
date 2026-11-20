"""Ticket D on real PostgreSQL: store-level T5 cases, child-process kill cases, two worker processes.

Needs HADAVIN_TEST_PG_DSN (a superuser on a throwaway server). Without the variable every test here
is skipped with that reason; with it nothing skips (psycopg is imported at module level then, so a
missing driver is an error, not a skip). Each test gets its own schema, migrated fresh and dropped
afterwards (`pg_schema` of tests/contracts). Rows are read back by plain SQL on a connection of the
test's own, never through the code under test.

Group A drives the WSGI callable in-process (Runner and Runtime on a PostgresStore). Groups B and C
start `tests/triggers/crash_launcher.py` as child processes and talk to them over loopback sockets.
Ticket case ids (tickets/D-signed-endpoint.md, section 10) are named in each docstring.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from wsgiref.util import setup_testing_defaults

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.config import load_config
from hadavin_sdk.models import now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick
from hadavin_sdk.testing.crash import CRASH_EXIT_CODE, CRASH_MARKER, CrashPoints
from hadavin_sdk.triggers import worker
from tests.contracts.kinds.store_postgres import pg_schema
from tests.k5_support import build_runtime, k5_cfg
from tests.triggers.crash_launcher import (
    AGENT,
    PATH,
    PREFIX,
    PRINCIPAL,
    TENANT,
    Child,
    CountingLLM,
    make_trigger_app,
    signed_post,
    wire_body,
)

if os.environ.get("HADAVIN_TEST_PG_DSN"):  # set: the driver must be there, never a silent skip
    import psycopg

SENDER, OTHER_SENDER = "sender-a", "sender-b"
# Fake secrets, built from parts at run time (40 characters each, all different).
SECRET = "t5" * 4 + "a" * 32
OTHER_SECRET = "t5" * 4 + "b" * 32
ONE = {SENDER: SECRET}
TWO = {SENDER: SECRET, OTHER_SENDER: OTHER_SECRET}
DOCUMENT = "checkout 5xx from 10.0.0.5, revision 17"
OTHER_DOCUMENT = "checkout 5xx from 10.0.0.6, revision 18"
OK = (200, 202)
IN_PROGRESS = ("RECEIVED", "WORKING")
SETTLE_S = 30.0


# --- helpers --------------------------------------------------------------------------------------


@pytest.fixture
def dsn():
    """A DSN on a fresh migrated schema; the schema is dropped afterwards."""
    yield from pg_schema()


def _rows(dsn: str) -> list[tuple]:
    """Every run row, by SQL: (run_id, agent_id, principal_id, trigger_ref, state, reason_code)."""
    with psycopg.connect(dsn) as db:
        found = db.execute(
            "SELECT run_id, agent_id, principal_id, trigger_ref, state, reason_code"
            " FROM runs ORDER BY run_id"
        ).fetchall()
    return [tuple(row) for row in found]


def _settled(dsn: str, run_id: str) -> tuple:
    """The row of `run_id` once it has left RECEIVED and WORKING."""
    deadline = time.monotonic() + SETTLE_S
    while True:
        mine = [row for row in _rows(dsn) if row[0] == run_id]
        if mine and mine[0][4] not in IN_PROGRESS:
            return mine[0]
        if time.monotonic() > deadline:
            raise AssertionError(f"run did not end: {mine}")
        time.sleep(0.02)


def _run_id(sender: str, key: str) -> str:
    """Invariant 4 written out, so the derivation is not judged with itself."""
    return "run-" + hashlib.sha256(f"{TENANT}\0{sender}\0{key}".encode()).hexdigest()[:32]


def _ref(sender: str, key: str, document: str) -> str:
    """Invariant 5 written out: sender/key#sha256(document bytes)."""
    return f"{sender}/{key}#" + hashlib.sha256(document.encode("utf-8")).hexdigest()


def _calls(path: Path) -> int:
    """Model calls so far: the model double of the launcher writes one byte per call."""
    return path.stat().st_size if path.exists() else 0


@pytest.fixture
def door(dsn, tmp_path):
    """Runtime, Runner and the WSGI callable in this process, on a PostgresStore. `door.post` sends
    one signed request in-process; `door.calls()` counts model calls."""
    from hadavin_sdk.store.postgres import PostgresStore, connect

    conn = connect(dsn)
    store, calls_file = PostgresStore(conn), tmp_path / "calls"
    runtime, _cards = build_runtime(k5_cfg(tmp_path), CountingLLM(calls_file, 0.0), store=store)
    cap = runtime.registry.config.evidence.max_document_bytes
    app = make_trigger_app(runtime, store, TWO, max_body_bytes=2 * cap + 4096, max_running=4)
    wsgi, runner = worker.make_app(app)

    def post(key: str, document: str, sender: str = SENDER):
        body, seen = wire_body(key, document), {}
        environ: dict = {}
        setup_testing_defaults(environ)
        environ.update(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": PATH,
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": io.BytesIO(body),
            }
        )
        signed = hmac_v0.sign(body, int(time.time()), TWO[sender], PREFIX)
        for name, value in signed.items():
            environ["HTTP_" + name.upper().replace("-", "_")] = value

        def start_response(status, headers, exc_info=None):
            seen["status"] = int(status.split()[0])

        data = b"".join(wsgi(environ, start_response))
        return SimpleNamespace(status=seen["status"], body=data)

    try:
        yield SimpleNamespace(
            post=post,
            dsn=dsn,
            calls=lambda: _calls(calls_file),
            document_cap=cap,
            body_cap=2 * cap + 4096,
        )
    finally:
        runner.close()
        conn.close()


def _child(tmp_path: Path, name: str, dsn: str, secrets: dict[str, str], *, crash: bool = False):
    """A launcher child on the schema of `dsn`. Each `name` has its own config and audit folder;
    the same `name` again is a restart of that worker (same folders, same flag, same calls file)."""
    home = tmp_path / name
    config_dir = home / "config"
    if not config_dir.exists():
        k5_cfg(home)
    args = ["--calls-file", str(home / "calls")]
    if crash:
        args += ["--flag", str(home / "flag")]
    runs = len(list(home.glob("run-*")))
    return Child(home / f"run-{runs}", config_dir, secrets, *args, dsn=dsn)


def _killed(child: Child) -> None:
    """The child ended at the armed crash point: exit code and marker of the crash helper."""
    assert child.wait() == CRASH_EXIT_CODE, child.stderr()[-2000:]
    out = child.stdout()
    assert CRASH_MARKER in out and "stopped" not in out


def _arm(tmp_path: Path, name: str, point: str, nth: int = 1) -> Path:
    flag = tmp_path / name / "flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    CrashPoints(mode="exit", flag_path=flag).arm(point, nth=nth)
    return flag


def _stuck_tick(tmp_path: Path, name: str, dsn: str) -> int:
    """One tick with only the real `stuck` step, a day later, on a store connection of its own."""
    from hadavin_sdk.store.postgres import PostgresStore, connect

    cfg = load_config(tmp_path / name / "config")
    conn = connect(dsn)
    try:
        app = SimpleNamespace(
            config=cfg,
            registry=load_registry(cfg),
            store=PostgresStore(conn),
            audit=LocalDirSink(tmp_path / "tick-audit"),
        )
        steps = [step for step in tick.STEPS if step.name == "stuck"]
        assert len(steps) == 1
        return tick.run_tick(app, now=now() + timedelta(days=1), steps=steps)
    finally:
        conn.close()


def _answer(reply: tuple[int | None, bytes]) -> dict:
    return json.loads(reply[1])


# --- A. store level, in-process Runner on PostgreSQL ----------------------------------------------


def test_a1_new_signed_request_gives_one_row_with_the_expected_fields(door):
    """A1 (ticket P1, N1 on PostgreSQL). Request: a new signed key. Expected: 2xx with the derived
    run id. Store: exactly one row with that run id, the configured agent and principal and the
    trigger_ref that carries the payload hash."""
    reply = door.post("key-1", DOCUMENT)
    assert reply.status in OK
    run_id = _run_id(SENDER, "key-1")
    assert json.loads(reply.body)["run_id"] == run_id
    row = _settled(door.dsn, run_id)
    assert row[:4] == (run_id, AGENT, PRINCIPAL, _ref(SENDER, "key-1", DOCUMENT))
    assert len(_rows(door.dsn)) == 1 and door.calls() == 1


def test_a2_repeat_gives_the_same_run_and_no_model_call(door):
    """A2 (ticket P2 on PostgreSQL). Request: the same key and document again, twice. Expected: 200
    with the same run id and the stored state. Store: still one row, unchanged; zero further model
    calls."""
    first = door.post("key-1", DOCUMENT)
    assert first.status in OK
    row = _settled(door.dsn, _run_id(SENDER, "key-1"))
    calls = door.calls()
    for _ in range(2):
        again = door.post("key-1", DOCUMENT)
        assert again.status == 200
        assert json.loads(again.body) == {"run_id": row[0], "state": row[4]}
    assert _rows(door.dsn) == [row] and door.calls() == calls


def test_a3_same_key_with_another_document_is_409_and_the_row_stays(door):
    """A3 (ticket P3 on PostgreSQL). Request: a stored key with a different document. Expected:
    409 with an empty body. Store: the row is unchanged, no second row, no model call."""
    assert door.post("key-1", DOCUMENT).status in OK
    row = _settled(door.dsn, _run_id(SENDER, "key-1"))
    calls = door.calls()
    refused = door.post("key-1", OTHER_DOCUMENT)
    assert (refused.status, refused.body) == (409, b"")
    assert _rows(door.dsn) == [row] and door.calls() == calls


def test_a4_two_senders_with_one_key_give_two_rows(door):
    """A4 (ticket N5 at store level). Request: the same key and document signed by two senders.
    Expected: 2xx each, two different run ids. Store: two rows, each with its sender's ref."""
    first = door.post("key-1", DOCUMENT, SENDER)
    second = door.post("key-1", DOCUMENT, OTHER_SENDER)
    assert first.status in OK and second.status in OK
    ids = {_run_id(SENDER, "key-1"), _run_id(OTHER_SENDER, "key-1")}
    assert len(ids) == 2
    assert {json.loads(first.body)["run_id"], json.loads(second.body)["run_id"]} == ids
    for run_id in ids:
        _settled(door.dsn, run_id)
    rows = _rows(door.dsn)
    assert {row[0] for row in rows} == ids and len(rows) == 2
    assert {row[3] for row in rows} == {
        _ref(SENDER, "key-1", DOCUMENT),
        _ref(OTHER_SENDER, "key-1", DOCUMENT),
    }


def test_a5_fifty_parallel_requests_with_one_key_give_one_row(door):
    """A5 (ticket C1 on PostgreSQL). Request: 50 signed requests with one key, released together.
    Expected: every answer 2xx with the same run id. Store: one row, one model call."""
    barrier = threading.Barrier(50)

    def go(_n):
        barrier.wait(30)
        return door.post("key-1", DOCUMENT)

    with ThreadPoolExecutor(max_workers=50) as pool:
        replies = list(pool.map(go, range(50)))
    run_id = _run_id(SENDER, "key-1")
    assert [r.status for r in replies if r.status not in OK] == []
    assert {json.loads(r.body)["run_id"] for r in replies} == {run_id}
    _settled(door.dsn, run_id)
    assert len(_rows(door.dsn)) == 1 and door.calls() == 1


def test_a6_document_over_the_document_cap_is_accepted_and_ends_with_a_person(door):
    """A6a (ticket E6). Request: a document one byte over evidence.max_document_bytes inside the
    body cap. Expected: 2xx; the settled repeat is 200 NEEDS_PERSON. Store: one row, NEEDS_PERSON
    with reason document_too_large; no model call."""
    big = "a" * (door.document_cap + 1)
    assert len(wire_body("key-big", big)) <= door.body_cap
    reply = door.post("key-big", big)
    assert reply.status in OK
    run_id = _run_id(SENDER, "key-big")
    row = _settled(door.dsn, run_id)
    assert row[4:] == ("NEEDS_PERSON", "document_too_large")
    again = door.post("key-big", big)
    assert again.status == 200
    assert json.loads(again.body) == {"run_id": run_id, "state": "NEEDS_PERSON"}
    assert len(_rows(door.dsn)) == 1 and door.calls() == 0


def test_a6_body_over_the_body_cap_is_413_and_writes_nothing(door):
    """A6b (ticket E3 on PostgreSQL). Request: a signed body one byte over max_body_bytes.
    Expected: 413 with an empty body. Store: no row; no model call."""
    filler = door.body_cap + 1 - len(wire_body("key-huge", ""))
    body_len = len(wire_body("key-huge", "a" * filler))
    assert body_len == door.body_cap + 1
    refused = door.post("key-huge", "a" * filler)
    assert (refused.status, refused.body) == (413, b"")
    assert _rows(door.dsn) == [] and door.calls() == 0


# --- B. a child process killed at a crash point ---------------------------------------------------


def test_b1_kill_before_the_row_gives_no_ack_and_the_retry_is_accepted(dsn, tmp_path):
    """B1 (ticket K3). Child killed at store.create_run:before. Request: one signed key. Expected:
    no 2xx (no answer, or 503); child exit code 137 with the marker. Store: no row. After a
    restart the same request, signed again, gets 2xx. Store: one row."""
    body = wire_body("key-1", DOCUMENT)
    _arm(tmp_path, "w", "store.create_run:before")
    with _child(tmp_path, "w", dsn, ONE, crash=True) as child:
        status, _data = signed_post(child.port, body, SECRET)
        _killed(child)
    assert status in (None, 503)
    assert _rows(dsn) == []
    with _child(tmp_path, "w", dsn, ONE, crash=True) as child:
        status, data = signed_post(child.port, body, SECRET)
        assert status in OK and json.loads(data)["run_id"] == _run_id(SENDER, "key-1")
        _settled(dsn, _run_id(SENDER, "key-1"))
    assert len(_rows(dsn)) == 1


def _cut_off_then_tick(dsn, tmp_path, point: str, state_left: str) -> None:
    """Shared by B2 and B3: kill at `point`, find the row in `state_left`, restart, repeat (202,
    stored state), tick (NEEDS_PERSON interrupted), repeat (200), one row, no model call."""
    body, run_id = wire_body("key-1", DOCUMENT), _run_id(SENDER, "key-1")
    home = tmp_path / "w"
    _arm(tmp_path, "w", point)
    with _child(tmp_path, "w", dsn, ONE, crash=True) as child:
        status, _data = signed_post(child.port, body, SECRET)
        _killed(child)
    assert status in (None, 202, 503)  # the row may have been read just before the kill
    assert not (home / "flag").exists()
    expected = (run_id, AGENT, PRINCIPAL, _ref(SENDER, "key-1", DOCUMENT), state_left, None)
    assert _rows(dsn) == [expected]
    with _child(tmp_path, "w", dsn, ONE, crash=True) as child:
        before = signed_post(child.port, body, SECRET)
        assert before[0] == 202 and _answer(before) == {"run_id": run_id, "state": state_left}
        assert _rows(dsn) == [expected]  # the restart alone ends nothing: the tick must run
        assert _stuck_tick(tmp_path, "w", dsn) == 0
        assert _rows(dsn) == [(*expected[:4], "NEEDS_PERSON", "interrupted")]
        after = signed_post(child.port, body, SECRET)
        assert after[0] == 200 and _answer(after) == {"run_id": run_id, "state": "NEEDS_PERSON"}
    assert _rows(dsn) == [(*expected[:4], "NEEDS_PERSON", "interrupted")]
    assert _calls(home / "calls") == 0


def test_b2_kill_after_the_row_then_tick_ends_with_a_person(dsn, tmp_path):
    """B2 (ticket K1 and K2 on PostgreSQL, child process). Child killed at store.create_run:after.
    Store: one row in RECEIVED. Restart: the repeat is 202 RECEIVED. Tick with the stuck step a day
    later: NEEDS_PERSON, reason interrupted. Repeat: 200 NEEDS_PERSON, one row, no model call."""
    _cut_off_then_tick(dsn, tmp_path, "store.create_run:after", "RECEIVED")


def test_b3_kill_inside_handle_after_working_then_tick_ends_with_a_person(dsn, tmp_path):
    """B3 (ticket K2, inside the loop). Child killed at store.transition:after, nth 1: the first
    transition `handle` makes, RECEIVED to WORKING (agent_loop.py `_to`). Store: one row in WORKING.
    Then as B2: 202 WORKING, tick, NEEDS_PERSON interrupted, 200, one row, no model call."""
    _cut_off_then_tick(dsn, tmp_path, "store.transition:after", "WORKING")


def test_b4_no_answer_is_sent_before_the_row_was_read(dsn, tmp_path):
    """B4 (ticket K2, store.get_run:after; invariant 7). Child killed at store.get_run:after, nth 1,
    on the store handed to the Runner: `:after` fires only when the read returned a row, so this
    is the Runner's first successful read, before any answer is written. Expected: the client got
    no 2xx. Store: the row exists. After a restart the repeat is 200 or 202. Store: one row."""
    body, run_id = wire_body("key-1", DOCUMENT), _run_id(SENDER, "key-1")
    _arm(tmp_path, "w", "store.get_run:after")
    with _child(tmp_path, "w", dsn, ONE, crash=True) as child:
        status, data = signed_post(child.port, body, SECRET)
        _killed(child)
    assert status is None, (status, data)
    rows = _rows(dsn)
    assert [row[:4] for row in rows] == [(run_id, AGENT, PRINCIPAL, _ref(SENDER, "key-1", DOCUMENT))]
    with _child(tmp_path, "w", dsn, ONE, crash=True) as child:
        status, data = signed_post(child.port, body, SECRET)
        assert status in OK and json.loads(data)["run_id"] == run_id
        assert json.loads(data)["state"] == _rows(dsn)[0][4]
    assert len(_rows(dsn)) == 1
    assert _calls(tmp_path / "w" / "calls") <= 1


# --- C. two worker processes on one database ------------------------------------------------------


def _both_at_once(first: Child, second: Child, bodies: tuple[bytes, bytes]) -> list:
    barrier = threading.Barrier(2)

    def go(pair):
        child, body = pair
        barrier.wait(30)
        return signed_post(child.port, body, SECRET)

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(go, [(first, bodies[0]), (second, bodies[1])]))


def test_c1_two_processes_and_one_request_give_one_row(dsn, tmp_path):
    """C1 (ticket C4). Two worker processes on one schema. Request: the same signed key and
    document to both at once, three keys in a row. Expected: both answers 2xx with the same run id.
    Store: one row per key; one model call per key over both processes."""
    with _child(tmp_path, "w1", dsn, ONE) as first, _child(tmp_path, "w2", dsn, ONE) as second:
        for n in range(3):
            key = f"key-{n}"
            body = wire_body(key, DOCUMENT)
            replies = _both_at_once(first, second, (body, body))
            assert [status for status, _ in replies if status not in OK] == [], replies
            assert {_answer(reply)["run_id"] for reply in replies} == {_run_id(SENDER, key)}
            _settled(dsn, _run_id(SENDER, key))
            assert len(_rows(dsn)) == n + 1
    assert _calls(tmp_path / "w1" / "calls") + _calls(tmp_path / "w2" / "calls") == 3


def test_c2_two_processes_and_two_documents_give_one_run_and_one_409(dsn, tmp_path):
    """C2 (ticket C4 with P3). Two worker processes on one schema. Request: one key with two
    different documents, one to each process at once, three keys in a row. Expected: exactly one
    2xx and one 409 (never 503). Store: one row per key, with the ref of the document that won."""
    refs = {
        _ref(SENDER, f"key-{n}", doc) for n in range(3) for doc in (DOCUMENT, OTHER_DOCUMENT)
    }
    with _child(tmp_path, "w1", dsn, ONE) as first, _child(tmp_path, "w2", dsn, ONE) as second:
        for n in range(3):
            key = f"key-{n}"
            bodies = (wire_body(key, DOCUMENT), wire_body(key, OTHER_DOCUMENT))
            replies = _both_at_once(first, second, bodies)
            statuses = sorted(status or 0 for status, _ in replies)
            assert statuses in ([200, 409], [202, 409]), replies
            assert [data for status, data in replies if status == 409] == [b""]
            row = _settled(dsn, _run_id(SENDER, key))
            assert row[3] in refs and len(_rows(dsn)) == n + 1
    assert _calls(tmp_path / "w1" / "calls") + _calls(tmp_path / "w2" / "calls") == 3
