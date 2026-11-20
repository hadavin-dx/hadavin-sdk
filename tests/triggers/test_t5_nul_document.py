"""Ticket D, ORDER 013: what happens TODAY to a NUL character (and other control characters) in the
DOCUMENT of a signed trigger request, followed end to end. These tests pin today's behaviour; they
decide nothing. A change of behaviour must change the "today:" sentence of the test it breaks.

Three levels:
1. the endpoint alone, in-process, with a recording `start`;
2. endpoint + Runner + Runtime on the MEMORY store with the scripted model double of k5_support;
3. the same on PostgreSQL. Needs HADAVIN_TEST_PG_DSN (a superuser on a throwaway server); without
   the variable the level-3 tests skip with the usual reason, with it they run. Rows are read back
   by plain SQL on a connection of the test's own.

Summary of what is pinned (every case below is SAFE; this file holds no FINDING):
- The endpoint accepts the document as it is. The raw bytes, NUL included, are what `trigger_ref`
  and the audit `inputs_hash` are computed from, so a document with and without a NUL are two
  different requests (same key: 409).
- The run ends like the same document without the NUL. The redactor removes every NUL before
  anything else (`guard/runmap.py` `_clean`), so the model double never sees one, and an address
  cut in two by a NUL is still redacted as one address.
- No document text reaches a store column: the runs row holds a hash, the redaction map holds
  values taken from the cleaned text, audit events hold hashes and codes. No INSERT fails on
  PostgreSQL. A control test shows that PostgreSQL WOULD refuse a NUL, so "nothing failed" is a
  result and not an accident of the driver.
- Other control characters (U+0001, U+001F) are NOT removed: they reach the model double unchanged.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import logging
import os
import time
from types import SimpleNamespace
from wsgiref.util import setup_testing_defaults

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.config import load_config
from hadavin_sdk.models import sha256_hex
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.triggers import worker
from hadavin_sdk.triggers.endpoint import make_wsgi
from tests.contracts.kinds.store_postgres import pg_schema
from tests.fixtures import k5_tools
from tests.k5_support import ScriptLLM, build_runtime, k5_cfg
from tests.triggers.crash_launcher import (
    AGENT,
    PATH,
    PREFIX,
    PRINCIPAL,
    TENANT,
    make_trigger_app,
    wire_body,
)

if os.environ.get("HADAVIN_TEST_PG_DSN"):  # set: the driver must be there, never a silent skip
    import psycopg
    from psycopg.types.json import Jsonb

SENDER = "sender-a"
SECRET = "t5" * 4 + "n" * 32  # a fake secret, built from parts (40 characters)
KEY = "key-nul"
NUL = "\x00"
ADDRESS = "10.0.0.5"
IN_PROGRESS = ("RECEIVED", "WORKING")
SETTLE_S = 30.0
MAP_OF_ADDRESS = {"<IPV4_1>": ADDRESS}
# The audit trail of a run that proposed nothing: (domain, operation, result, error_code).
QUIET_TRAIL = [
    ("run", "received", None, None),
    ("run", "state", "WORKING", None),
    ("run", "state", "NO_ACTION", None),
    ("card", "abstain", "posted", None),
]

# name -> (the document as the sender wrote it, the bytes the model double is sent, the stored map)
CASES: dict[str, tuple[str, bytes, dict[str, str]]] = {
    "nul_in_the_middle": (
        f"checkout 5xx from {ADDRESS}{NUL}, revision 17",
        b"checkout 5xx from <IPV4_1>, revision 17",
        MAP_OF_ADDRESS,
    ),
    "only_a_nul": (NUL, b"", {}),
    "nul_at_the_start": (f"{NUL}checkout {ADDRESS}", b"checkout <IPV4_1>", MAP_OF_ADDRESS),
    "nul_at_the_end": (f"checkout {ADDRESS}{NUL}", b"checkout <IPV4_1>", MAP_OF_ADDRESS),
    "many_nuls": (f"{NUL * 3}a{NUL}b{NUL * 2}", b"ab", {}),
    "nul_inside_an_address": (f"10.0.{NUL}0.5 rev", b"<IPV4_1> rev", MAP_OF_ADDRESS),
    "u0001_stays": (f"a\x01b {ADDRESS}", b"a\x01b <IPV4_1>", MAP_OF_ADDRESS),
    "u001f_stays": ("a\x1fb", b"a\x1fb", {}),
}
NUL_CASES = [name for name, case in CASES.items() if NUL in case[0]]


# --- helpers --------------------------------------------------------------------------------------


def _run_id(key: str = KEY) -> str:
    """Invariant 4 written out, so the derivation is not judged with itself."""
    return "run-" + hashlib.sha256(f"{TENANT}\0{SENDER}\0{key}".encode()).hexdigest()[:32]


def _ref(document: str, key: str = KEY) -> str:
    """Invariant 5 written out: sender/key#sha256(document bytes, a NUL included)."""
    return f"{SENDER}/{key}#" + hashlib.sha256(document.encode("utf-8")).hexdigest()


def _post(wsgi, key: str, document: str) -> SimpleNamespace:
    """One signed request, in-process. The body is JSON, so a NUL travels as the escape u0000."""
    body, seen = wire_body(key, document), {}
    if NUL in document:
        assert b"\\u0000" in body and b"\x00" not in body
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
    for name, value in hmac_v0.sign(body, int(time.time()), SECRET, PREFIX).items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value

    def start_response(status, headers, exc_info=None):
        seen["status"] = int(status.split()[0])

    data = b"".join(wsgi(environ, start_response))
    return SimpleNamespace(status=seen["status"], body=data)


def _door(tmp_path, store, script: list[dict]) -> SimpleNamespace:
    """Runtime (scripted model double, cards captured), Runner and the WSGI callable on `store`."""
    cfg_dir = k5_cfg(tmp_path)
    llm = ScriptLLM(script)
    runtime, cards = build_runtime(cfg_dir, llm, store=store)
    wsgi, runner = worker.make_app(
        make_trigger_app(runtime, store, {SENDER: SECRET}, max_running=1)
    )
    audit_dir = load_config(cfg_dir).backends.audit.dir

    def audit_events() -> list[dict]:
        found = [json.loads(p.read_text(encoding="utf-8")) for p in audit_dir.glob("objects/*")]
        return sorted(found, key=lambda event: event["ts"])

    def audit_bytes() -> bytes:
        return b"".join(p.read_bytes() for p in sorted(audit_dir.rglob("*")) if p.is_file())

    def settled(run_id: str):
        deadline = time.monotonic() + SETTLE_S
        while True:
            run = store.get_run(run_id)
            if run.state.value not in IN_PROGRESS:
                return run
            assert time.monotonic() < deadline, f"run did not end: {run.state}"
            time.sleep(0.02)

    return SimpleNamespace(
        post=lambda document, key=KEY: _post(wsgi, key, document),
        store=store,
        llm=llm,
        cards=cards,
        settled=settled,
        drain=runner.close,  # waits for the loop thread: the card and its audit event are out
        audit_events=audit_events,
        audit_bytes=audit_bytes,
    )


@pytest.fixture
def memory_door(tmp_path):
    door = _door(tmp_path, MemoryStore(), [{"noaction": True}])
    try:
        yield door
    finally:
        door.drain()


@pytest.fixture
def dsn():
    """A DSN on a fresh migrated schema; the schema is dropped afterwards. Skips without the
    HADAVIN_TEST_PG_DSN variable."""
    yield from pg_schema()


@pytest.fixture
def pg_conn(dsn):
    from hadavin_sdk.store.postgres import connect

    conn = connect(dsn)
    try:
        yield conn
    finally:
        conn.close()


def _pg_door(tmp_path, conn, script: list[dict]) -> SimpleNamespace:
    from hadavin_sdk.store.postgres import PostgresStore

    return _door(tmp_path, PostgresStore(conn), script)


def _sql(dsn: str, query: str) -> list[tuple]:
    with psycopg.connect(dsn) as db:
        return [tuple(row) for row in db.execute(query).fetchall()]


def _follow(door, caplog, name: str) -> str:
    """Send case `name`, wait for the end, and assert everything that is the same on both stores.
    Returns the run id."""
    document, sent, stored_map = CASES[name]
    raw = document.encode("utf-8")
    run_id = _run_id()

    first = door.post(document)
    # 202 while the loop is at work; 200 when it had already ended at the Runner's first read.
    assert first.status in (200, 202)
    assert json.loads(first.body)["run_id"] == run_id

    run = door.settled(run_id)
    assert (run.state.value, run.reason_code) == ("NO_ACTION", None)
    assert (run.agent_id, run.principal_id, run.trigger_ref) == (AGENT, PRINCIPAL, _ref(document))
    again = door.post(document)
    assert again.status == 200
    assert json.loads(again.body) == {"run_id": run_id, "state": "NO_ACTION"}
    door.drain()

    # The model double: one call, and exactly these document bytes.
    assert [call["documents"] for call in door.llm.sent] == [[sent]]
    everything = door.llm.everything_sent()
    assert NUL not in everything and "\\u0000" not in everything

    # The stored map: values of the cleaned text only.
    assert door.store.get_redaction_map(run_id) == stored_map

    # Audit: the trail of a quiet run; the hash is of the RAW bytes; no NUL in any audit file.
    events = door.audit_events()
    trail = [(e["domain"], e["operation"], e["result"], e["error_code"]) for e in events]
    assert trail == QUIET_TRAIL
    assert {e["run_id"] for e in events} == {run_id}
    assert events[0]["inputs_hash"] == sha256_hex(raw.hex())
    on_disk = door.audit_bytes()
    assert b"\x00" not in on_disk and b"\\u0000" not in on_disk

    # The person: one abstain card, no control character of the document in it.
    assert len(door.cards) == 1
    card_text = json.dumps(dataclasses.asdict(door.cards[0]), ensure_ascii=False)
    assert NUL not in card_text and "\\u0000" not in card_text
    assert "\x01" not in card_text and "\x1f" not in card_text

    # The log: no warning or error from the trigger path, and no NUL in any line.
    lines = [(r.levelno, r.getMessage()) for r in caplog.records if r.name.startswith("hadavin")]
    assert [line for line in lines if line[0] >= logging.WARNING] == []
    assert all(NUL not in text for _level, text in lines)
    return run_id


# --- 1. the endpoint alone ------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(CASES))
def test_level1_endpoint_accepts_the_document_and_hands_on_the_raw_bytes(name):
    """today: the endpoint answers what `start` decides (here 202) for every case; it does not
    refuse, strip or replace a NUL or another control character. `start` gets the document's raw
    bytes (the NUL is one zero byte) and a `trigger_ref` whose hash is of those raw bytes.
    Safe: the endpoint only hashes and hands on; whether the bytes are safe is decided downstream
    (levels 2 and 3)."""
    document = CASES[name][0]
    seen = []

    def start(accepted):
        seen.append(accepted)
        return 202, {"run_id": accepted.run_id, "state": "RECEIVED"}

    settings = SimpleNamespace(
        tenant=TENANT,
        senders=[SimpleNamespace(id=SENDER, agent_id=AGENT, principal_id=PRINCIPAL)],
        max_body_bytes=65536,
    )
    reply = _post(make_wsgi(settings, {SENDER: (SECRET,)}, start), KEY, document)
    assert reply.status == 202
    assert json.loads(reply.body) == {"run_id": _run_id(), "state": "RECEIVED"}
    assert len(seen) == 1
    assert seen[0].document == document.encode("utf-8")
    assert seen[0].document.count(b"\x00") == document.count(NUL)
    assert (seen[0].run_id, seen[0].trigger_ref) == (_run_id(), _ref(document))


# --- 2. Runner + Runtime on the memory store --------------------------------------------------------


@pytest.mark.parametrize("name", NUL_CASES)
def test_level2_memory_nul_is_removed_before_the_model_and_the_run_ends_normally(
    name, memory_door, caplog
):
    """today: 2xx; the run ends NO_ACTION with no reason code, exactly like the same document
    without the NUL; the settled repeat is 200 NO_ACTION. The model double is sent the document
    with every NUL REMOVED (not replaced): a document that is only a NUL arrives as empty bytes,
    and an address cut in two by a NUL is redacted as one address. The stored map holds no NUL.
    Audit: received, WORKING, NO_ACTION, abstain card posted; `inputs_hash` is of the raw bytes
    with the NUL. One abstain card, no NUL in it; no warning in the log.
    Safe: no crash, no lost request, no row in WORKING, the person gets the card."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk")
    _follow(memory_door, caplog, name)


@pytest.mark.parametrize("name", ["u0001_stays", "u001f_stays"])
def test_level2_memory_other_control_characters_reach_the_model_unchanged(
    name, memory_door, caplog
):
    """today: U+0001 and U+001F are neither refused nor removed: the model double is sent the
    document with the character still in it; the rest (state, audit, card, log) is as for any
    document. Safe for the run (no crash, the run ends, the person gets the card). Pinned so that
    a later decision to strip control characters shows up here."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk")
    _follow(memory_door, caplog, name)
    control = "\x01" if name == "u0001_stays" else "\x1f"
    assert control.encode() in memory_door.llm.sent[0]["documents"][0]


def test_level2_memory_same_key_with_and_without_the_nul_are_two_documents(tmp_path):
    """today: the NUL counts for the payload hash although the model never sees it. After the
    document with a NUL has been stored, the same key with the NUL taken out is 409 with an empty
    body and writes nothing; and the other way round. Safe: a sender that strips the NUL on a
    retry gets a plain refusal, never a second run."""
    with_nul = CASES["nul_in_the_middle"][0]
    without = with_nul.replace(NUL, "")
    door = _door(tmp_path, MemoryStore(), [{"noaction": True}, {"noaction": True}])
    try:
        assert door.post(with_nul, "key-1").status in (200, 202)
        door.settled(_run_id("key-1"))
        refused = door.post(without, "key-1")
        assert (refused.status, refused.body) == (409, b"")
        assert door.post(without, "key-2").status in (200, 202)
        door.settled(_run_id("key-2"))
        refused = door.post(with_nul, "key-2")
        assert (refused.status, refused.body) == (409, b"")
    finally:
        door.drain()
    assert len(door.llm.sent) == 2


def _tooled(door, monkeypatch) -> str:
    """A run that reads a log and proposes, from a document whose address is cut by a NUL."""
    monkeypatch.setitem(k5_tools.RESULTS, "app", f"ERROR upstream {ADDRESS}; revision 17 failed")
    document = CASES["nul_inside_an_address"][0]
    run_id = _run_id()
    assert door.post(document).status in (200, 202)
    door.drain()  # the loop passes PLAN_READY on its way: wait for the thread, then read the row
    run = door.store.get_run(run_id)
    assert (run.state.value, run.reason_code) == ("NO_ACTION", "shadow")
    assert door.store.get_plan(run_id).inputs == {"host": "<IPV4_1>", "revision": "17"}
    assert door.store.get_redaction_map(run_id) == MAP_OF_ADDRESS
    assert [call.call_id for call in door.store.list_tool_calls(run_id)] == [f"{run_id}:1"]
    everything = door.llm.everything_sent()
    assert NUL not in everything and "\\u0000" not in everything
    assert len(door.cards) == 1
    card_text = json.dumps(dataclasses.asdict(door.cards[0]), ensure_ascii=False)
    assert NUL not in card_text and "\\u0000" not in card_text
    on_disk = door.audit_bytes()
    assert b"\x00" not in on_disk and b"\\u0000" not in on_disk
    return run_id


TOOLED_SCRIPT = [{"tool": "app"}, {"propose": {"host": "<IPV4_1>", "revision": "17"}}]


def test_level2_memory_tooled_run_from_a_nul_document_ends_in_shadow(tmp_path, monkeypatch):
    """today: a document whose address is cut by a NUL still grounds a proposal: one tool call is
    kept, the plan holds the placeholder of the whole address, the run ends NO_ACTION `shadow`
    with one card; no NUL in the model's input, the card or the audit files. Safe."""
    door = _door(tmp_path, MemoryStore(), list(TOOLED_SCRIPT))
    try:
        _tooled(door, monkeypatch)
    finally:
        door.drain()


# --- 3. the same on PostgreSQL ----------------------------------------------------------------------


def test_level3_control_postgres_refuses_a_nul_in_text_and_in_jsonb(dsn):
    """Control for this level. today: a NUL in a text parameter is refused (psycopg DataError) and a
    NUL in a jsonb value is refused by the server (UntranslatableCharacter). So if document text
    with a NUL reached a text column or the redaction map, the INSERT would fail; the tests below
    show that it does not get there."""
    with psycopg.connect(dsn) as db:
        with pytest.raises(psycopg.DataError):
            db.execute("SELECT %s::text", (f"a{NUL}b",))
        db.rollback()
        with pytest.raises(psycopg.errors.UntranslatableCharacter):
            db.execute("SELECT %s::jsonb", (Jsonb({"<IPV4_1>": f"a{NUL}b"}),))


@pytest.mark.parametrize("name", sorted(CASES))
def test_level3_postgres_no_insert_fails_and_the_run_ends_normally(
    name, dsn, pg_conn, tmp_path, caplog
):
    """today: on PostgreSQL every case behaves as on the memory store: 2xx, NO_ACTION, the
    settled repeat 200, the model double sent the document without the NUL (U+0001 and U+001F
    kept), the same audit trail, one card, no warning in the log (so no "store error", no "loop
    raised"). No INSERT fails, because no document text is written: by SQL the one runs row holds
    the hash-only `trigger_ref`, the redaction map holds values of the cleaned text, and there is
    no tool call, plan or dead letter.
    Safe: no 503, no row left in RECEIVED or WORKING, the person gets the card."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk")
    document, _sent, stored_map = CASES[name]
    door = _pg_door(tmp_path, pg_conn, [{"noaction": True}])
    try:
        run_id = _follow(door, caplog, name)
    finally:
        door.drain()
    assert _sql(
        dsn, "SELECT run_id, agent_id, principal_id, trigger_ref, state, reason_code FROM runs"
    ) == [(run_id, AGENT, PRINCIPAL, _ref(document), "NO_ACTION", None)]
    assert _sql(dsn, "SELECT run_id, mapping FROM redaction_maps") == [(run_id, stored_map)]
    for table in ("tool_calls", "plans", "gate_decisions", "dead_letters"):
        assert _sql(dsn, f"SELECT count(*) FROM {table}") == [(0,)]  # noqa: S608 - fixed names


def test_level3_postgres_same_key_with_and_without_the_nul_is_409(dsn, pg_conn, tmp_path):
    """today: as on the memory store, the NUL counts for the payload hash: the same key with the
    NUL taken out is 409 with an empty body; the stored row is unchanged and there is one model
    call. Safe."""
    with_nul = CASES["nul_in_the_middle"][0]
    door = _pg_door(tmp_path, pg_conn, [{"noaction": True}])
    try:
        assert door.post(with_nul).status in (200, 202)
        door.settled(_run_id())
        before = _sql(dsn, "SELECT run_id, trigger_ref, state, updated_at FROM runs")
        refused = door.post(with_nul.replace(NUL, ""))
        assert (refused.status, refused.body) == (409, b"")
    finally:
        door.drain()
    assert _sql(dsn, "SELECT run_id, trigger_ref, state, updated_at FROM runs") == before
    assert len(before) == 1 and len(door.llm.sent) == 1


def test_level3_postgres_tooled_run_from_a_nul_document_ends_in_shadow(
    dsn, pg_conn, tmp_path, monkeypatch, caplog
):
    """today: the run that reads a log and proposes, from a document whose address is cut by a
    NUL, writes every row it writes on a normal document: one tool call, one plan, one gate
    decision, the map; it ends NO_ACTION `shadow` with one card. No INSERT fails and no stored
    text holds a NUL (PostgreSQL could not hold one). Safe."""
    caplog.set_level(logging.DEBUG, logger="hadavin_sdk")
    door = _pg_door(tmp_path, pg_conn, list(TOOLED_SCRIPT))
    try:
        run_id = _tooled(door, monkeypatch)
    finally:
        door.drain()
    assert _sql(dsn, "SELECT run_id, state, reason_code FROM runs") == [
        (run_id, "NO_ACTION", "shadow")
    ]
    for table in ("tool_calls", "plans", "gate_decisions", "redaction_maps"):
        assert _sql(dsn, f"SELECT count(*) FROM {table}") == [(1,)]  # noqa: S608 - fixed names
    warnings = [
        r.getMessage()
        for r in caplog.records
        if r.name.startswith("hadavin") and r.levelno >= logging.WARNING
    ]
    assert warnings == []
