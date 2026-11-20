"""T5 cases of ticket D (thin signed endpoint + worker): a SKELETON, one test per numbered case of the draft.

The whole module is skipped until `hadavin_sdk.triggers.endpoint` and `.worker` exist. The helpers below use what
exists today (hmac_v0 signing, the fixture config, the store kinds of tests/contracts) and call the PLANNED API of
the draft: `derive_run_id`, `make_wsgi`, `Runner`. Three things are assumptions of this skeleton, to be settled by
the checked ticket: the attribute names of the settings object (`_settings`), which call refuses bad secrets at
start (case 8c), and that `make_wsgi` reaches `parse_body` through the module (case 2 swaps it to prove the body is
not parsed). The four mutants of the draft (skip the timestamp check; drop the payload hash from trigger_ref; ack
before the row exists; drop tenant from the derivation) are aimed at cases 3, 5, 1 and 1.
"""

import hashlib
import inspect
import io
import json
import threading
import time
from datetime import timedelta
from types import SimpleNamespace
from wsgiref.util import setup_testing_defaults

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.config import load_config
from hadavin_sdk.guard import RegexDetector
from hadavin_sdk.limits import Limits
from hadavin_sdk.llm import FakeLLM
from hadavin_sdk.models import RunState, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime.agent_loop import Runtime
from hadavin_sdk.store.protocol import NotFound
from tests.conftest import qualify
from tests.contracts.kinds import (
    KINDS,
    builtin,  # noqa: F401 - registers the memory store kind
    store_postgres,  # noqa: F401 - registers the postgres store kind (skipped without HADAVIN_TEST_PG_DSN)
)

endpoint = pytest.importorskip("hadavin_sdk.triggers.endpoint")
worker = pytest.importorskip("hadavin_sdk.triggers.worker")

S = RunState
PATH, PREFIX = "/v1/trigger", "X-Hadavin"
NOW = 1_800_000_000  # the fixed fake clock, Unix seconds
TENANT, SENDER, OTHER_SENDER = "tenant-a", "sender-a", "sender-b"
AGENT, PRINCIPAL = "test-agent", "svc:test-agent"
# Fake secrets, built from parts at run time (32 characters each, all different).
OLD_SECRET = "k" * 16 + "a" * 16
NEW_SECRET = "k" * 16 + "b" * 16
OTHER_SECRET = "k" * 16 + "c" * 16
UNKNOWN_SECRET = "k" * 16 + "z" * 16
IN_FLIGHT = (S.RECEIVED, S.WORKING, S.PLAN_READY)
_AUTO = object()


# --- helpers (defined once) --------------------------------------------------------------------------------------


class _Input(io.BytesIO):
    """The request body stream; counts the bytes the app took from it."""

    taken = 0

    def read(self, size=-1):
        data = super().read(size)
        self.taken += len(data)
        return data


def _body(key, document):
    """The wire body: a JSON object with exactly `key` and `document`, as bytes."""
    return json.dumps({"key": key, "document": document}).encode("utf-8")


def _signed(body, secret, ts):
    """The two request headers for `body`. `ts` is normally an int; a str is passed through as the header text
    (hmac_v0.sign only calls str() on it), which is how case 3b sends a malformed timestamp with a valid HMAC."""
    return hmac_v0.sign(body, ts, secret, PREFIX)


def _call(app, method, path, headers, body, content_length=_AUTO):
    """Drive the WSGI app in-process (no socket). `content_length=None` leaves the header out."""
    source, environ, seen = _Input(body), {}, {}
    setup_testing_defaults(environ)
    environ.pop("CONTENT_LENGTH", None)
    environ.update({"REQUEST_METHOD": method, "PATH_INFO": path, "wsgi.input": source})
    if content_length is _AUTO:
        environ["CONTENT_LENGTH"] = str(len(body))
    elif content_length is not None:
        environ["CONTENT_LENGTH"] = content_length
    for name, value in headers.items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value

    def start_response(status, response_headers, exc_info=None):
        seen["status"], seen["headers"] = int(status.split()[0]), dict(response_headers)

    chunks = app(environ, start_response)
    try:
        data = b"".join(chunks)
    finally:
        if hasattr(chunks, "close"):
            chunks.close()
    return SimpleNamespace(
        status=seen["status"], headers=seen["headers"], body=data, taken=source.taken
    )


def _settings(senders=None, **over):
    """Stand-in for the planned TriggerSettings (SPINE adds the real one; field names from the draft's Config)."""
    one = SimpleNamespace(secret_names=("sender-a-secret",), agent_id=AGENT, principal_id=PRINCIPAL)
    base = {
        "tenant": TENANT,
        "senders": senders or {SENDER: one},
        "max_body_bytes": 262144,
        "max_running": 4,
        "ack_wait_s": 5.0,
    }
    return SimpleNamespace(**{**base, **over})


def _runtime(cfg_dir, store):
    """Like tests.test_s5_runtime.build, but on the given store (memory or Postgres)."""
    cfg = load_config(cfg_dir)
    reg = load_registry(cfg)
    qualify(reg)
    audit = LocalDirSink(cfg.backends.audit.dir)
    rt = Runtime(
        reg,
        store,
        audit,
        FakeLLM(cfg.backends.llm.recorded_dir, cfg.routes),
        RegexDetector(cfg.backends.detector[0].threshold),
        Limits(store, audit, reg),
        [AGENT],
    )
    return rt, cfg


def _door(cfg_dir, store, secrets=None, **over):
    """Runtime + Runner + WSGI app with a clock the test moves (`door.clock[0] = ...`)."""
    rt, cfg = _runtime(cfg_dir, store)
    settings, clock = _settings(**over), [float(NOW)]
    runner = worker.Runner(
        rt, store, max_running=settings.max_running, ack_wait_s=settings.ack_wait_s
    )
    secrets = secrets or {SENDER: (OLD_SECRET,)}
    app = endpoint.make_wsgi(settings, secrets, runner.start, clock=lambda: clock[0])
    return SimpleNamespace(
        rt=rt, cfg=cfg, store=store, app=app, clock=clock, runner=runner, settings=settings
    )


def _post(door, body, secret=OLD_SECRET, ts=NOW, headers=None):
    """A signed POST to the trigger path; `headers` replaces the signed ones when given."""
    return _call(
        door.app, "POST", PATH, _signed(body, secret, ts) if headers is None else headers, body
    )


def _text(door, name="chat.txt"):
    return (door.cfg.inputs_dir / name).read_text(encoding="utf-8")


def _expected_run_id(sender, key, tenant=TENANT):
    """Invariant 4, written out here so the test does not judge the derivation with itself."""
    return "run-" + hashlib.sha256(f"{tenant}\0{sender}\0{key}".encode()).hexdigest()[:32]


def _expected_ref(sender, key, document):
    """Invariant 5: sender/key#sha256(document bytes)."""
    return f"{sender}/{key}#" + hashlib.sha256(document.encode("utf-8")).hexdigest()


def _all_runs(store):
    later = now() + timedelta(days=1)
    return [r for st in RunState for r in store.list_runs(st, later, limit=1000)]


def _settle(door, run_id, wait_s=10.0):
    """Wait until the run has left the states the handle thread passes through; return the stored run."""
    deadline = time.monotonic() + wait_s
    while True:
        run = door.store.get_run(run_id)
        if run.state not in IN_FLIGHT or time.monotonic() > deadline:
            return run
        time.sleep(0.01)


def _received(door, run_id):
    return [e for e in door.rt.audit.events(run_id) if e.operation == "received"]


def _refused(reply, status):
    """A refusal has the given status and an empty body (invariant 10)."""
    return reply.status == status and reply.body == b""


@pytest.fixture(params=sorted(KINDS["store"]))
def store(request, tmp_path):
    """Every store kind of tests/contracts (memory; Postgres when HADAVIN_TEST_PG_DSN is set, else skipped)."""
    made = KINDS["store"][request.param](tmp_path)
    if not inspect.isgenerator(made):
        return made
    value = next(made)
    request.addfinalizer(lambda: next(made, None))
    return value


@pytest.fixture
def door(cfg_dir, store):
    return _door(cfg_dir, store)


# --- cases 1 to 9b ------------------------------------------------------------------------------------------------


def test_case_1_signed_fresh_request_starts_one_run(door):
    """Case 1. Request: POST /v1/trigger, correctly signed, timestamp = now, a key never seen.
    Status: 202 (or 200 if the run already ended). Store: exactly one run row with the derived run_id, the
    configured agent and principal, trigger_ref = sender/key#sha256(document); one "received" audit event."""
    document = _text(door)
    reply = _post(door, _body("key-1", document))
    assert reply.status in (200, 202)
    answer = json.loads(reply.body)
    assert set(answer) == {"run_id", "state"}  # invariant 10
    run_id = _expected_run_id(SENDER, "key-1")
    assert answer["run_id"] == run_id == endpoint.derive_run_id(TENANT, SENDER, "key-1")
    run = _settle(door, run_id)
    assert (run.agent_id, run.principal_id, run.trigger_kind) == (AGENT, PRINCIPAL, "event")
    assert run.trigger_ref == _expected_ref(SENDER, "key-1", document)
    assert [r.run_id for r in _all_runs(door.store)] == [run_id]
    assert len(_received(door, run_id)) == 1


def _wrong_secret(body):
    return _signed(body, UNKNOWN_SECRET, NOW), body


def _altered_body(body):
    return _signed(body, OLD_SECRET, NOW), body.replace(b"key-1", b"key-2")


def _no_signature(body):
    headers = _signed(body, OLD_SECRET, NOW)
    return {k: v for k, v in headers.items() if not k.endswith("signature")}, body


def _no_timestamp(body):
    headers = _signed(body, OLD_SECRET, NOW)
    return {k: v for k, v in headers.items() if not k.endswith("timestamp")}, body


def _v1_prefix(body):
    headers = _signed(body, OLD_SECRET, NOW)
    return {k: v.replace("v0=", "v1=", 1) for k, v in headers.items()}, body


def _non_ascii(body):
    headers = _signed(body, OLD_SECRET, NOW)
    return {
        k: (v if k.endswith("timestamp") else "v0=" + "\xe9" * 64) for k, v in headers.items()
    }, body


@pytest.mark.parametrize(
    "spoil",
    [_wrong_secret, _altered_body, _no_signature, _no_timestamp, _v1_prefix, _non_ascii],
)
def test_case_2_bad_signature_is_401_and_the_body_is_never_parsed(door, monkeypatch, spoil):
    """Case 2. Request: POST with a bad signature (wrong secret, altered body, a missing header, a `v1=` prefix,
    a non-ASCII signature). Status: 401 with an empty body. Store: no run row; the body is never parsed."""
    parsed = []
    monkeypatch.setattr(endpoint, "parse_body", lambda *a, **kw: parsed.append(a) or {})
    headers, body = spoil(_body("key-1", _text(door)))
    assert _refused(_post(door, body, headers=headers), 401)
    assert parsed == []
    assert _all_runs(door.store) == []


@pytest.mark.parametrize(
    ("offset_s", "refused"), [(-301, True), (301, True), (-300, False), (300, False)]
)
def test_case_3_stale_timestamp_is_401_before_any_lookup(door, monkeypatch, offset_s, refused):
    """Case 3. Request: correctly signed over its own timestamp, which is 301 s old or 301 s ahead of the clock
    (the 300 s rows are the boundary and are accepted). Status: 401 with an empty body, before any store lookup.
    Store: no run row and no get_run call for a refused request."""
    lookups, real = [], door.store.get_run

    def spy(run_id):
        lookups.append(run_id)
        return real(run_id)

    monkeypatch.setattr(door.store, "get_run", spy)
    reply = _post(door, _body("key-1", _text(door)), ts=NOW + offset_s)
    if refused:
        assert _refused(reply, 401)
        assert lookups == []
        assert _all_runs(door.store) == []
    else:
        assert reply.status in (200, 202)


@pytest.mark.parametrize("ts", ["1" * 13, "12ab", "", " " + str(NOW), "-5", str(NOW) + ".0"])
def test_case_3b_malformed_timestamp_is_401(door, ts):
    """Case 3b. Request: the timestamp header is 13 digits or not all digits; the HMAC is valid for that text.
    Status: 401 with an empty body. Store: no run row."""
    assert _refused(_post(door, _body("key-1", _text(door)), ts=ts), 401)
    assert _all_runs(door.store) == []


def test_case_4_resigned_retry_returns_the_same_run(door):
    """Case 4. Request: the same key and document again, signed anew with a later timestamp.
    Status: 200 with the same run_id and the run's current state. Store: still one row; no extra model call and
    no second "received" event."""
    body = _body("key-1", _text(door))
    first = json.loads(_post(door, body).body)
    stored = _settle(door, first["run_id"])
    model_calls = len(door.rt.llm.calls)
    door.clock[0] = NOW + 10
    again = _post(door, body, ts=NOW + 10)
    assert again.status == 200
    assert json.loads(again.body) == {"run_id": stored.run_id, "state": stored.state.value}
    assert len(_all_runs(door.store)) == 1
    assert len(door.rt.llm.calls) == model_calls
    assert len(_received(door, stored.run_id)) == 1


def test_case_5_same_key_with_another_document_is_409(door):
    """Case 5. Request: a key already used, with a DIFFERENT document, correctly signed.
    Status: 409 with an empty body. Store: the existing row is unchanged, nothing is written, no model call."""
    first = json.loads(_post(door, _body("key-1", _text(door))).body)
    before = _settle(door, first["run_id"])
    model_calls = len(door.rt.llm.calls)
    reply = _post(door, _body("key-1", _text(door) + " changed"))
    assert _refused(reply, 409)
    assert door.store.get_run(before.run_id) == before
    assert len(_all_runs(door.store)) == 1
    assert len(door.rt.llm.calls) == model_calls


MALFORMED = [
    b"not json",
    b'["key-1", "text"]',
    b'{"key": "key-1"}',
    b'{"document": "text"}',
    b'{"key": "key-1", "document": "text", "more": 1}',
    b'{"key": 7, "document": "text"}',
    b'{"key": "key-1", "document": 7}',
    b'{"key": "key-1", "document": null}',
    b'{"key": "has space", "document": "text"}',
    b'{"key": "a/b", "document": "text"}',
    b'{"key": "", "document": "text"}',
    json.dumps({"key": "k" * 129, "document": "text"}).encode(),
    b'{"key": "key-1", "document": "\xff\xfe"}',
]


@pytest.mark.parametrize("body", MALFORMED)
def test_case_6_malformed_but_signed_is_400(door, body):
    """Case 6. Request: correctly signed, but the body is not JSON, is an array, misses a field, has an extra
    field, has a wrong type, a key outside ^[A-Za-z0-9._:-]{1,128}$, or invalid UTF-8.
    Status: 400 with an empty body. Store: no run row."""
    assert _refused(_post(door, body), 400)
    assert _all_runs(door.store) == []


@pytest.mark.parametrize("body", MALFORMED[:3])
def test_case_6b_malformed_and_unsigned_is_401(door, body):
    """Case 6b. Request: a malformed body with no signature headers (the signature is checked before the JSON).
    Status: 401 with an empty body. Store: no run row."""
    assert _refused(_post(door, body, headers={}), 401)
    assert _all_runs(door.store) == []


def test_case_7_content_length_over_the_cap_is_413_without_reading(door):
    """Case 7. Request: Content-Length is one byte over max_body_bytes.
    Status: 413 with an empty body, and no byte of the body is read. Store: no run row."""
    body = _body("key-1", _text(door))
    over = str(door.settings.max_body_bytes + 1)
    reply = _call(door.app, "POST", PATH, _signed(body, OLD_SECRET, NOW), body, content_length=over)
    assert _refused(reply, 413)
    assert reply.taken == 0
    assert _all_runs(door.store) == []


@pytest.mark.parametrize("content_length", [None, "abc", "-1", "longer"])
def test_case_7b_bad_content_length_is_400(door, content_length):
    """Case 7b. Request: Content-Length is missing, not all digits, or larger than the body that was sent.
    Status: 400 with an empty body. Store: no run row."""
    body = _body("key-1", _text(door))
    if content_length == "longer":
        content_length = str(len(body) + 10)
    reply = _call(
        door.app, "POST", PATH, _signed(body, OLD_SECRET, NOW), body, content_length=content_length
    )
    assert _refused(reply, 400)
    assert _all_runs(door.store) == []


def test_case_8_old_and_new_secret_give_the_same_run(cfg_dir, store):
    """Case 8. Request: one sender with two configured secrets; the same key and document signed with the old
    secret, then with the new one. Status: 2xx both times with the same run_id. Store: one run row."""
    door = _door(cfg_dir, store, secrets={SENDER: (OLD_SECRET, NEW_SECRET)})
    body = _body("key-1", _text(door))
    with_old, with_new = _post(door, body, OLD_SECRET), _post(door, body, NEW_SECRET)
    assert with_old.status in (200, 202) and with_new.status in (200, 202)
    assert json.loads(with_old.body)["run_id"] == json.loads(with_new.body)["run_id"]
    assert len(_all_runs(door.store)) == 1


def test_case_8b_removed_old_secret_is_401(cfg_dir, store):
    """Case 8b. Request: signed with the old secret after it was removed from the sender's configuration.
    Status: 401 with an empty body. Store: no run row."""
    door = _door(cfg_dir, store, secrets={SENDER: (NEW_SECRET,)})
    assert _refused(_post(door, _body("key-1", _text(door)), OLD_SECRET), 401)
    assert _all_runs(door.store) == []


@pytest.mark.parametrize(
    "secrets",
    [
        {SENDER: (OLD_SECRET,), OTHER_SENDER: (OLD_SECRET,)},  # the same value for two senders
        {SENDER: (OLD_SECRET[:31],)},  # under 32 characters
        {SENDER: ("",)},  # empty
    ],
    ids=["shared", "short", "empty"],
)
def test_case_8c_shared_or_short_secret_refuses_to_start(cfg_dir, store, secrets):
    """Case 8c. No request: sender A's secret equals sender B's, or a secret is under 32 characters (or empty).
    Expected: the worker refuses to start. Store: nothing written.
    ASSUMPTION: the check sits in make_wsgi and raises ValueError; the draft only says "checked at start"."""
    one = SimpleNamespace(secret_names=("name-a",), agent_id=AGENT, principal_id=PRINCIPAL)
    two = SimpleNamespace(secret_names=("name-b",), agent_id=AGENT, principal_id=PRINCIPAL)
    senders = {SENDER: one, OTHER_SENDER: two} if OTHER_SENDER in secrets else {SENDER: one}
    with pytest.raises(ValueError):  # the message is not fixed by the draft
        _door(cfg_dir, store, secrets=secrets, senders=senders)
    assert _all_runs(store) == []


def test_case_9_identical_replay_inside_300_s_returns_the_stored_run(door):
    """Case 9. Request: the byte-identical request (same headers, same body) again 299 s later.
    Status: 200 with the stored run. Store: no second run row, no second "received" event."""
    body = _body("key-1", _text(door))
    headers = _signed(body, OLD_SECRET, NOW)
    first = json.loads(_post(door, body, headers=headers).body)
    stored = _settle(door, first["run_id"])
    door.clock[0] = NOW + 299
    replay = _post(door, body, headers=headers)
    assert replay.status == 200
    assert json.loads(replay.body) == {"run_id": stored.run_id, "state": stored.state.value}
    assert len(_all_runs(door.store)) == 1
    assert len(_received(door, stored.run_id)) == 1


def test_case_9b_identical_replay_after_300_s_is_401(door):
    """Case 9b. Request: the byte-identical request again 301 s later.
    Status: 401 with an empty body. Store: still the one row of the first request, unchanged."""
    body = _body("key-1", _text(door))
    headers = _signed(body, OLD_SECRET, NOW)
    first = json.loads(_post(door, body, headers=headers).body)
    stored = _settle(door, first["run_id"])
    door.clock[0] = NOW + 301
    assert _refused(_post(door, body, headers=headers), 401)
    assert _all_runs(door.store) == [stored]


# --- further cases ------------------------------------------------------------------------------------------------


def test_further_50_parallel_requests_with_one_key_make_one_run(door):
    """Further. Request: 50 signed requests with the same key and document, sent at the same moment.
    Status: every answer is 2xx with the same run_id. Store: one run row, one "received" event."""
    body, replies, gate = _body("key-1", _text(door)), [], threading.Barrier(50)

    def one():
        gate.wait()
        replies.append(_post(door, body))

    threads = [threading.Thread(target=one) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert len(replies) == 50
    assert {r.status for r in replies} <= {200, 202}
    run_id = _expected_run_id(SENDER, "key-1")
    assert {json.loads(r.body)["run_id"] for r in replies} == {run_id}
    _settle(door, run_id)
    assert len(_all_runs(door.store)) == 1
    assert len(_received(door, run_id)) == 1


def test_further_get_is_405(door):
    """Further. Request: GET /v1/trigger with valid signature headers.
    Status: 405 with an empty body. Store: no run row."""
    body = _body("key-1", _text(door))
    assert _refused(_call(door.app, "GET", PATH, _signed(body, OLD_SECRET, NOW), body), 405)
    assert _all_runs(door.store) == []


@pytest.mark.parametrize("path", ["/", "/v1", "/v1/trigger/", "/v1/trigger/more", "/v2/trigger"])
def test_further_other_path_is_404(door, path):
    """Further. Request: a correctly signed POST to any path other than /v1/trigger.
    Status: 404 with an empty body. Store: no run row."""
    body = _body("key-1", _text(door))
    assert _refused(_call(door.app, "POST", path, _signed(body, OLD_SECRET, NOW), body), 404)
    assert _all_runs(door.store) == []


def test_further_pool_full_is_503_and_a_later_retry_is_accepted(cfg_dir, store, monkeypatch):
    """Further. Request: max_running = 1; the first run is held after its row exists; a second request with
    another key arrives. Status: 503 with an empty body for the second (no ack); after the first run ends, the
    retry with the same key is 2xx. Store: no row for the second key until the retry, then exactly one."""
    door = _door(cfg_dir, store, max_running=1, ack_wait_s=1.0)
    hold, write = threading.Event(), door.rt.audit.write_outcome

    def held(event):  # the first audit write of a run comes right after its row is created
        hold.wait(10)
        return write(event)

    monkeypatch.setattr(door.rt.audit, "write_outcome", held)
    document = _text(door)
    try:
        assert _post(door, _body("key-1", document)).status == 202
        assert _refused(_post(door, _body("key-2", document)), 503)
        with pytest.raises(NotFound):
            door.store.get_run(_expected_run_id(SENDER, "key-2"))
    finally:
        hold.set()
    _settle(door, _expected_run_id(SENDER, "key-1"))
    assert _post(door, _body("key-2", document)).status in (200, 202)
    _settle(door, _expected_run_id(SENDER, "key-2"))
    assert len(_all_runs(door.store)) == 2


def test_further_store_down_is_503(door, monkeypatch):
    """Further. Request: correctly signed, while every store read fails.
    Status: 503 with an empty body (no ack; the sender retries with the same key). Store: nothing written."""

    def down(run_id):
        raise OSError("store down")

    monkeypatch.setattr(door.store, "get_run", down)
    assert _refused(_post(door, _body("key-1", _text(door))), 503)
    monkeypatch.undo()
    assert _all_runs(door.store) == []


@pytest.mark.skip(reason="needs step E crash hook")
def test_further_kill_during_the_run_then_tick_ends_with_a_person(door):
    """Further. Request: signed and acked (202); the process is killed while the run is WORKING; then a tick runs.
    Status: the repeat of the request is 200 with state NEEDS_PERSON. Store: the one row is NEEDS_PERSON with
    reason "interrupted"; the run is not started again (no second "received" event, no model call)."""
    # 1. from hadavin_sdk.testing.crash import CrashPoints, SimulatedCrash (ticket E; same-process mode).
    # 2. Arm a crash point at a boundary after create_run (for example the audit write of "received" or the
    #    first model call) with CrashPoints.wrap around that collaborator of door.rt.
    # 3. reply = _post(door, _body("key-1", _text(door))); assert reply.status == 202; the handle thread ends
    #    with SimulatedCrash and the row stays RECEIVED or WORKING.
    # 4. Build an App over the same store (as tests/test_p7_tick.py does) and call
    #    run_tick(app, now=<row.updated_at + stuck_after_s + 1 s>).
    # 5. run = door.store.get_run(run_id); assert (run.state, run.reason_code) == (S.NEEDS_PERSON, "interrupted").
    # 6. again = _post(door, body, ts=NOW + 10) with door.clock[0] = NOW + 10; assert again.status == 200 and
    #    json.loads(again.body)["state"] == "NEEDS_PERSON".
    # 7. assert len(_all_runs(door.store)) == 1 and len(_received(door, run_id)) <= 1 and no new model call.


def test_further_kill_switch_on_gives_state_stopped(door):
    """Further. Request: correctly signed, while the kill switch is on.
    Status: 2xx; the repeat is 200 with state STOPPED. Store: one run row, STOPPED with reason kill_switch,
    no model call."""
    door.rt.limits.stop(by="user:a")
    body = _body("key-1", _text(door, "create.txt"))
    first = _post(door, body)
    assert first.status in (200, 202)
    run = _settle(door, json.loads(first.body)["run_id"])
    assert (run.state, run.reason_code) == (S.STOPPED, "kill_switch")
    assert door.rt.llm.calls == []
    again = _post(door, body)
    assert again.status == 200
    assert json.loads(again.body) == {"run_id": run.run_id, "state": S.STOPPED.value}
    assert len(_all_runs(door.store)) == 1


def test_further_every_case_runs_on_the_memory_store_and_on_postgres():
    """Further. No request: the `store` fixture above gives every case that touches the store one run per store
    kind. Expected: both kinds are registered (the Postgres runs are skipped without HADAVIN_TEST_PG_DSN, as in
    tests/contracts). Store: none."""
    assert {"memory", "postgres"} <= set(KINDS["store"])
