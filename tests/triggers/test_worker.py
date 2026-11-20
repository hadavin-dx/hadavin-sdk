"""Worker half of the signed trigger endpoint (ticket D): `Runner.start`, the start-up checks and `main`.

Memory store and a scripted model double; one test opens a loopback socket on a free port and closes it. Every
Runner is used in a `with` block, so no pool thread outlives its test.
"""

from __future__ import annotations

import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import Reply, Run, RunState, TickState, now
from hadavin_sdk.runtime import tick
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import NotFound, StaleState, StoreUnavailable
from hadavin_sdk.triggers import endpoint, worker
from hadavin_sdk.triggers.endpoint import Accepted
from hadavin_sdk.triggers.worker import Runner
from tests.k5_support import ScriptLLM, build_runtime, k5_cfg

AGENT, PRINCIPAL, SENDER, TENANT = "test-agent", "svc:test-agent", "sender-a", "tenant-a"
DOCUMENT = b"checkout 5xx from 10.0.0.5, revision 17"
OTHER_DOCUMENT = b"checkout 5xx from 10.0.0.6, revision 18"
SECRET = "s" * 40
OK = (200, 202)
IN_PROGRESS = (RunState.RECEIVED, RunState.WORKING)


class GateLLM(ScriptLLM):
    """Always answers "nothing to do". Counts its calls under a lock and waits at `gate` (open by default)."""

    def __init__(self) -> None:
        super().__init__([])
        self.calls = 0
        self.gate = threading.Event()
        self.gate.set()
        self._lock = threading.Lock()

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        with self._lock:
            self.calls += 1
        self.gate.wait(30)
        return Reply(text="Nothing to do.", model_id="fake-model")


def _req(n: int = 1, document: bytes = DOCUMENT) -> Accepted:
    key = f"key-{n}"
    return Accepted(
        sender=SENDER,
        agent_id=AGENT,
        principal_id=PRINCIPAL,
        run_id=endpoint.derive_run_id(TENANT, SENDER, key),
        trigger_ref=endpoint.trigger_ref(SENDER, key, document),
        document=document,
    )


@pytest.fixture
def rt(tmp_path):
    runtime, _cards = build_runtime(k5_cfg(tmp_path), GateLLM())
    return runtime


def _settle(store, run_id: str, timeout_s: float = 20.0) -> Run:
    """Wait until the run has left RECEIVED and WORKING."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        run = store.get_run(run_id)
        if run.state not in IN_PROGRESS:
            return run
        time.sleep(0.01)
    raise AssertionError(f"run did not end: {run_id}")


def _free(runner: Runner, timeout_s: float = 20.0) -> None:
    """Wait until every loop of this Runner has ended and given its slot back."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with runner._lock:
            if not runner._jobs:
                return
        time.sleep(0.01)
    raise AssertionError("a loop is still running")


def _parallel(runner: Runner, reqs: list[Accepted]) -> list:
    """All `start` calls released together; an exception is returned in place of the answer."""
    barrier = threading.Barrier(len(reqs))

    def go(req):
        barrier.wait(30)
        try:
            return runner.start(req)
        except BaseException as exc:  # noqa: BLE001 - the caller asserts there is none
            return exc

    with ThreadPoolExecutor(max_workers=len(reqs)) as pool:
        return list(pool.map(go, reqs))


def _received(rt, run_id: str) -> int:
    return sum(1 for e in rt.audit.events(run_id) if e.operation == "received")


class FakeRuntime:
    """A `handle` the test scripts: `fn(store, **call)` runs in the pool thread."""

    def __init__(self, store, fn) -> None:
        self.store, self.fn, self.calls = store, fn, 0

    def handle(self, agent_id, principal_id, document, **kw):
        self.calls += 1
        return self.fn(self.store, agent_id=agent_id, principal_id=principal_id, **kw)


def _insert(store, *, agent_id, principal_id, trigger_kind, trigger_ref, run_id) -> None:
    store.create_run(
        Run(
            run_id=run_id,
            agent_id=agent_id,
            principal_id=principal_id,
            trigger_kind=trigger_kind,
            trigger_ref=trigger_ref,
        )
    )


# --- one request ------------------------------------------------------------------------------------


def test_new_request_is_acked_only_with_a_matching_row(rt):
    req = _req()
    with Runner(rt, rt.store) as runner:
        status, body = runner.start(req)
        assert status in OK
        assert set(body) == {"run_id", "state"} and body["run_id"] == req.run_id
        row = rt.store.get_run(req.run_id)
        assert (row.agent_id, row.principal_id, row.trigger_ref, row.trigger_kind) == (
            AGENT,
            PRINCIPAL,
            req.trigger_ref,
            "event",
        )
        assert (status == 202) == (body["state"] in IN_PROGRESS)
        assert _settle(rt.store, req.run_id).state == RunState.NO_ACTION
        _free(runner)
    assert _received(rt, req.run_id) == 1
    assert rt.llm.calls == 1 and len(rt.store._runs) == 1


def test_repeat_with_the_same_document_returns_the_stored_run(rt):
    req = _req()
    with Runner(rt, rt.store) as runner:
        assert runner.start(req)[0] in OK
        ended = _settle(rt.store, req.run_id)
        _free(runner)
        calls = rt.llm.calls
        assert runner.start(req) == (200, {"run_id": req.run_id, "state": ended.state.value})
    assert rt.llm.calls == calls == 1
    assert _received(rt, req.run_id) == 1 and len(rt.store._runs) == 1


def test_same_key_with_another_document_is_409_and_writes_nothing(rt):
    first, other = _req(), _req(document=OTHER_DOCUMENT)
    assert first.run_id == other.run_id and first.trigger_ref != other.trigger_ref
    with Runner(rt, rt.store) as runner:
        assert runner.start(first)[0] in OK
        before = _settle(rt.store, first.run_id)
        _free(runner)
        calls, events = rt.llm.calls, len(rt.audit.events())
        assert runner.start(other) == (409, {})
    assert rt.store.get_run(first.run_id) == before
    assert rt.llm.calls == calls and len(rt.audit.events()) == events
    assert len(rt.store._runs) == 1


# --- several at once ---------------------------------------------------------------------------------


@pytest.mark.parametrize("max_running", [1, 4])
def test_50_parallel_requests_with_one_key_make_one_run(rt, max_running):
    req = _req()
    with Runner(rt, rt.store, max_running=max_running) as runner:
        answers = _parallel(runner, [req] * 50)
        assert all(isinstance(a, tuple) for a in answers), answers
        assert [a[0] for a in answers if a[0] not in OK] == []
        assert {a[1]["run_id"] for a in answers} == {req.run_id}
        _settle(rt.store, req.run_id)
        _free(runner)
    assert len(rt.store._runs) == 1
    assert rt.llm.calls == 1 and _received(rt, req.run_id) == 1


def test_one_slot_still_answers_every_parallel_request_for_one_key(rt):
    """The default of one running loop must not turn a duplicate delivery into a 503."""
    req = _req()
    with Runner(rt, rt.store) as runner:
        answers = _parallel(runner, [req] * 12)
        assert [a for a in answers if not isinstance(a, tuple) or a[0] not in OK] == []
        _settle(rt.store, req.run_id)
        _free(runner)
    assert len(rt.store._runs) == 1 and rt.llm.calls == 1


@pytest.mark.parametrize("max_running", [1, 4])
def test_one_key_with_two_documents_in_parallel_is_one_ack_and_one_409(rt, max_running):
    for n in range(5):
        first, other = _req(n), _req(n, OTHER_DOCUMENT)
        with Runner(rt, rt.store, max_running=max_running) as runner:
            answers = _parallel(runner, [first, other])
            assert all(isinstance(a, tuple) for a in answers), answers
            statuses = sorted(a[0] for a in answers)
            assert statuses[0] in OK and statuses[1] == 409, answers  # never 503
            won = first if answers[0][0] in OK else other
            assert rt.store.get_run(first.run_id).trigger_ref == won.trigger_ref
            _settle(rt.store, first.run_id)
            _free(runner)
        assert len(rt.store._runs) == n + 1 and rt.llm.calls == n + 1


@pytest.mark.parametrize(
    ("document", "expected"), [(DOCUMENT, OK), (OTHER_DOCUMENT, (409,)), (None, (503,))]
)
def test_no_slot_here_while_another_worker_writes_the_row(rt, document, expected):
    """Two Runners on one store stand for two worker processes. Ours has its one slot taken by a run of another
    key; the other one writes the row for our key a little later (or never). The answer comes from the row."""

    def holds_its_slot(store, **kw):
        _insert(store, **kw)
        hold.wait(30)

    hold, ours = threading.Event(), _req(1, document or DOCUMENT)
    busy = FakeRuntime(rt.store, holds_its_slot)
    with Runner(rt, rt.store) as other, Runner(busy, rt.store, ack_wait_s=0.6, poll_s=0.02) as here:
        try:
            assert here.start(_req(9))[0] in OK
            assert not here._slots.acquire(blocking=False)  # the one slot is taken
            late = threading.Timer(0.15, other.start, args=(_req(1),))
            if document is not None:
                late.start()
            began = time.monotonic()
            try:
                answer = here.start(ours)
            finally:
                if document is not None:
                    late.join(30)
            waited = time.monotonic() - began
            assert answer[0] in expected, answer
            if document is None:
                assert answer == (503, {}) and 0.6 <= waited < 5.0
                with pytest.raises(NotFound):
                    rt.store.get_run(ours.run_id)
            else:
                assert rt.store.get_run(ours.run_id).trigger_ref == _req(1).trigger_ref
                _settle(rt.store, ours.run_id)
                _free(other)
        finally:
            hold.set()
        _free(here)
    assert busy.calls == 1  # our Runner never started a loop for the key


def test_20_parallel_requests_with_distinct_keys_are_acked_or_refused(rt):
    reqs = [_req(n) for n in range(20)]
    rt.llm.gate.clear()  # every started loop waits in the model, so the four slots stay taken
    try:
        with Runner(rt, rt.store, max_running=4, ack_wait_s=0.5) as runner:
            try:
                began = time.monotonic()
                answers = _parallel(runner, reqs)
                assert time.monotonic() - began >= 0.5  # a refusal comes only after ack_wait_s
                assert all(isinstance(a, tuple) for a in answers), answers
                assert {a[0] for a in answers} <= {200, 202, 503}
                acked = [r for r, a in zip(reqs, answers, strict=True) if a[0] in OK]
                refused = [r for r, a in zip(reqs, answers, strict=True) if a[0] == 503]
                assert len(acked) == 4 and len(refused) == 16
                for r, a in zip(reqs, answers, strict=True):
                    if a[0] in OK:
                        assert rt.store.get_run(r.run_id).trigger_ref == r.trigger_ref
                    else:
                        assert a == (503, {})
                        with pytest.raises(NotFound):
                            rt.store.get_run(r.run_id)
            finally:
                rt.llm.gate.set()
            for r in acked:
                assert _settle(rt.store, r.run_id).state == RunState.NO_ACTION
            _free(runner)
    finally:
        rt.llm.gate.set()
    assert len(rt.store._runs) == 4 and rt.llm.calls == 4


def test_pool_full_is_503_and_a_later_retry_is_acked(rt):
    first, second = _req(1), _req(2)
    rt.llm.gate.clear()
    try:
        with Runner(rt, rt.store, max_running=1, ack_wait_s=1.0) as runner:
            try:
                assert runner.start(first)[0] in OK
                began = time.monotonic()
                assert runner.start(second) == (503, {})
                assert time.monotonic() - began >= 1.0  # not at once: only after ack_wait_s
                with pytest.raises(NotFound):
                    rt.store.get_run(second.run_id)
                assert runner.start(first)[0] in OK  # a repeat of the running key needs no slot
            finally:
                rt.llm.gate.set()
            _settle(rt.store, first.run_id)
            _free(runner)
            assert runner.start(second)[0] in OK
            _settle(rt.store, second.run_id)
            _free(runner)
    finally:
        rt.llm.gate.set()
    assert len(rt.store._runs) == 2 and rt.llm.calls == 2


# --- failures: no ack ---------------------------------------------------------------------------------


def test_store_down_is_503_and_nothing_starts():
    class Down(MemoryStore):
        def get_run(self, run_id):
            raise OSError("store down")

    store = Down()
    fake = FakeRuntime(store, lambda *a, **kw: None)
    with Runner(fake, store) as runner:
        assert runner.start(_req()) == (503, {})
    assert fake.calls == 0 and store._runs == {}


def test_store_failing_while_waiting_for_the_row_is_503():
    class Flaky(MemoryStore):
        looks = 0

        def get_run(self, run_id):
            self.looks += 1
            if self.looks > 1:
                raise OSError("store down")
            return super().get_run(run_id)

    store, hold = Flaky(), threading.Event()
    fake = FakeRuntime(store, lambda *a, **kw: hold.wait(30))
    with Runner(fake, store) as runner:
        try:
            assert runner.start(_req()) == (503, {})
        finally:
            hold.set()


def test_handle_raising_before_the_row_is_503_and_frees_the_slot(rt):
    real, failed = rt.handle, []

    def once(store, *, agent_id, principal_id, **kw):
        if not failed:
            failed.append(1)
            raise RuntimeError("boom")
        return real(agent_id, principal_id, DOCUMENT, **kw)

    fake = FakeRuntime(rt.store, once)
    with Runner(fake, rt.store, max_running=1) as runner:
        assert runner.start(_req(1)) == (503, {})
        with pytest.raises(NotFound):
            rt.store.get_run(_req(1).run_id)
        _free(runner)
        assert runner._slots.acquire(blocking=False)  # the one slot is back
        runner._slots.release()
        assert runner.start(_req(1))[0] in OK  # the retry with the same key starts the run
        _settle(rt.store, _req(1).run_id)
        _free(runner)
    assert fake.calls == 2 and len(rt.store._runs) == 1


def test_no_row_within_ack_wait_is_503_and_the_slot_stays_taken():
    store, hold = MemoryStore(), threading.Event()
    fake = FakeRuntime(store, lambda *a, **kw: hold.wait(30))
    with Runner(fake, store, max_running=1, ack_wait_s=0.3, poll_s=0.02) as runner:
        try:
            began = time.monotonic()
            assert runner.start(_req(1)) == (503, {})
            assert 0.3 <= time.monotonic() - began < 5.0
            assert not runner._slots.acquire(
                blocking=False
            )  # handle has not ended: slot not given back
            assert runner.start(_req(2)) == (503, {})
        finally:
            hold.set()
        _free(runner)
        assert runner._slots.acquire(blocking=False)
        runner._slots.release()
    assert store._runs == {} and fake.calls == 1


def test_the_row_decides_not_the_exception():
    """`StaleState` from the loop with a matching row is an ack; with a foreign row it is 409."""

    def lost_a_state_race(store, **kw):
        _insert(store, **kw)
        raise StaleState("state changed")

    store = MemoryStore()
    with Runner(FakeRuntime(store, lost_a_state_race), store) as runner:
        assert runner.start(_req(1)) == (202, {"run_id": _req(1).run_id, "state": "RECEIVED"})

    def raced_by_another_document(store, **kw):
        _insert(store, **{**kw, "trigger_ref": endpoint.trigger_ref(SENDER, "key-1", b"x")})
        raise StaleState("run exists")

    store = MemoryStore()
    with Runner(FakeRuntime(store, raced_by_another_document), store) as runner:
        assert runner.start(_req(1)) == (409, {})


def test_handle_raising_after_the_row_is_logged_by_class_name_only(caplog):
    def fails_late(store, **kw):
        _insert(store, **kw)
        raise RuntimeError("private text of the failure")

    store = MemoryStore()
    with (
        caplog.at_level("WARNING", logger="hadavin_sdk.triggers"),
        Runner(FakeRuntime(store, fails_late), store) as runner,
    ):
        assert runner.start(_req())[0] in OK  # the row exists: acked, the tick ends the run later
        _free(runner)
        assert runner._slots.acquire(blocking=False)
        runner._slots.release()
    assert "RuntimeError" in caplog.text and "private text" not in caplog.text
    assert DOCUMENT.decode() not in caplog.text and _req().trigger_ref not in caplog.text


def test_close_lets_a_running_loop_end_and_refuses_new_keys(rt):
    first, second = _req(1), _req(2)
    rt.llm.gate.clear()
    runner = Runner(rt, rt.store, max_running=2)
    try:
        assert runner.start(first)[0] in OK
        runner.close(
            wait_s=0.05
        )  # the loop is still in the model: close returns, the loop is not cut off
        began = time.monotonic()
        assert runner.start(second) == (503, {})
        assert time.monotonic() - began < 2.0  # closed: refused at once, no wait
        assert runner.start(first)[0] in OK  # a stored row is still answered
    finally:
        rt.llm.gate.set()
    assert _settle(rt.store, first.run_id).state == RunState.NO_ACTION
    _free(runner)
    runner.close()
    assert len(rt.store._runs) == 1 and rt.llm.calls == 1


def test_closed_runner_takes_no_new_work(rt):
    runner = Runner(rt, rt.store)
    runner.close()
    assert runner.start(_req()) == (503, {})
    assert rt.store._runs == {} and rt.llm.calls == 0


def test_bad_arguments_are_refused(rt):
    for kw in ({"max_running": 0}, {"ack_wait_s": 0}, {"poll_s": 0}):
        with pytest.raises(ValueError, match="above zero"):
            Runner(rt, rt.store, **kw)
    with Runner(rt, rt.store) as runner:
        assert (
            runner._slots._value == 1
        )  # the default is one loop at a time (spend, see the module text)


# --- crash after the row (step E helper) --------------------------------------------------------------------


def test_crash_after_the_row_then_tick_ends_with_a_person(rt):
    crash = pytest.importorskip("hadavin_sdk.testing.crash")
    req, plain = _req(), rt.store
    with crash.CrashPoints() as cp, Runner(rt, plain) as runner:
        rt.store = cp.wrap(plain, "store", ["create_run"])  # after the build, as ticket E says
        cp.arm("store.create_run:after")
        status, body = runner.start(req)
        assert status in OK and body["run_id"] == req.run_id
        _free(runner)
        assert cp.fired == ("store.create_run:after",)
        rt.store = plain
        app = SimpleNamespace(
            config=rt.registry.config, registry=rt.registry, store=plain, audit=rt.audit
        )
        steps = [s for s in tick.STEPS if s.name == "stuck"]
        assert tick.run_tick(app, now=now() + timedelta(days=1), steps=steps) == 0
        row = plain.get_run(req.run_id)
        assert (row.state, row.reason_code) == (RunState.NEEDS_PERSON, "interrupted")
        assert runner.start(req) == (200, {"run_id": req.run_id, "state": "NEEDS_PERSON"})
    assert rt.llm.calls == 0 and _received(rt, req.run_id) == 0 and len(plain._runs) == 1


# --- start-up checks and main ---------------------------------------------------------------------------


def _sender(**over):
    base = {"id": SENDER, "secret_names": ["door-a"], "agent_id": AGENT, "principal_id": PRINCIPAL}
    return SimpleNamespace(**{**base, **over})


def _settings(senders=None, **over):
    base = {
        "tenant": TENANT,
        "senders": senders or [_sender()],
        "max_body_bytes": 65536,
        "max_running": 2,
        "ack_wait_s": 5.0,
        "poll_s": 0.02,
    }
    return SimpleNamespace(**{**base, **over})


def _app(rt, settings, secrets=None):
    values = {"door-a": SECRET} if secrets is None else secrets
    return SimpleNamespace(
        config=SimpleNamespace(triggers=settings),
        registry=rt.registry,
        runtime=rt,
        store=rt.store,
        trigger_resolve=values.__getitem__,
    )


def test_main_without_a_triggers_block_exits_2(cfg_dir, capsys):
    assert worker.main(["--config-dir", str(cfg_dir)]) == 2
    err = capsys.readouterr().err
    assert "triggers block not configured" in err and "Traceback" not in err


def test_main_with_an_unreadable_config_exits_2(tmp_path, capsys):
    assert worker.main(["--config-dir", str(tmp_path / "missing")]) == 2
    assert "config error" in capsys.readouterr().err


def test_make_app_refuses_an_app_without_the_secret_reader(rt):
    app = _app(rt, _settings())
    del app.trigger_resolve
    with pytest.raises(ConfigError, match="trigger_resolve"):
        worker.make_app(app)
    with pytest.raises(ConfigError, match="triggers block not configured"):
        worker.make_app(_app(rt, None))


@pytest.mark.parametrize(
    ("sender", "words"),
    [
        ({"agent_id": "ghost-agent"}, "not qualified"),
        ({"principal_id": "svc:ghost"}, "not in principals"),
        ({"principal_id": "person-principal"}, "not of kind service"),
    ],
)
def test_make_app_refuses_a_sender_with_a_bad_agent_or_principal(rt, sender, words):
    principals = {**rt.registry.principals, "person-principal": SimpleNamespace(kind="person")}
    with pytest.raises(ConfigError, match=words):
        worker.check_senders([(SENDER, _sender(**sender))], rt.agents, principals)
    with pytest.raises(ConfigError):
        worker.make_app(_app(rt, _settings([_sender(agent_id="ghost-agent")])))


def test_make_app_refuses_bad_secrets_without_printing_them(rt):
    short = "q" * 31
    with pytest.raises(ConfigError) as refused:
        worker.make_app(_app(rt, _settings(), {"door-a": short}))
    assert short not in str(refused.value)
    two = [_sender(), _sender(id="sender-b", secret_names=["door-b"])]
    with pytest.raises(ConfigError, match="share a secret") as refused:
        worker.make_app(_app(rt, _settings(two), {"door-a": SECRET, "door-b": SECRET}))
    assert SECRET not in str(refused.value)
    with pytest.raises(ConfigError, match="could not be read") as refused:
        worker.make_app(_app(rt, _settings(), {}))
    assert "door-a" not in str(refused.value)


def test_non_loopback_host_needs_the_switch():
    worker.check_bind("127.0.0.1", False)
    worker.check_bind("localhost", False)
    for host in ("", " ", "door-host", "127.0.0.1:80", "localhost.", "999.1.1.1"):
        for allow in (False, True):
            with pytest.raises(ConfigError, match="IP address or localhost"):
                worker.check_bind(host, allow)
    for host in ("0.0.0.0", "10.1.2.3"):  # noqa: S104 - the refusal under test
        with pytest.raises(ConfigError, match="not loopback"):
            worker.check_bind(host, False)
        with pytest.raises(ConfigError):
            worker.check_bind(host, "yes")  # only the value True is the switch
        worker.check_bind(host, True)


def test_served_over_loopback_a_signed_request_is_acked(rt):
    """The one socket test: `make_app` + `make_server` on a free loopback port, closed in the `finally`."""
    wsgi, runner = worker.make_app(_app(rt, _settings()))
    server = thread = None
    try:
        server = worker.make_server(worker.LOOPBACK, 0, wsgi, 15.0)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05})
        thread.start()
        body = json.dumps({"key": "key-1", "document": DOCUMENT.decode()}).encode()
        answers = []
        for _ in range(2):
            conn = http.client.HTTPConnection(worker.LOOPBACK, server.server_port, timeout=15)
            try:
                headers = hmac_v0.sign(body, int(time.time()), SECRET, endpoint.PREFIX)
                conn.request("POST", endpoint.PATH, body=body, headers=headers)
                reply = conn.getresponse()
                answers.append((reply.status, json.loads(reply.read())))
            finally:
                conn.close()
            _settle(rt.store, _req(1).run_id)
        assert answers[0][0] in OK and answers[1][0] == 200
        assert {a[1]["run_id"] for a in answers} == {_req(1).run_id}
        assert answers[1][1]["state"] == "NO_ACTION"
    finally:
        if server is not None:
            if thread is not None:
                server.shutdown()
                thread.join(15)
            server.server_close()
        runner.close()
    assert thread is not None and not thread.is_alive()
    assert len(rt.store._runs) == 1 and rt.llm.calls == 1


# --- ORDER 009: the 409 log line, and a waiting request takes a slot that frees ---------------------------


def test_409_writes_one_log_line_with_status_sender_and_run_id_only(rt, caplog):
    first, other = _req(), _req(document=OTHER_DOCUMENT)
    with Runner(rt, rt.store) as runner:
        assert runner.start(first)[0] in OK
        _settle(rt.store, first.run_id)
        _free(runner)
        with caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"):
            assert runner.start(other) == (409, {})
    lines = [r.getMessage() for r in caplog.records if r.name == "hadavin_sdk.triggers"]
    assert len(lines) == 1, lines
    assert "409" in lines[0] and SENDER in lines[0] and other.run_id in lines[0]
    for private in (
        DOCUMENT.decode(),
        OTHER_DOCUMENT.decode(),
        first.trigger_ref,
        other.trigger_ref,
        "key-1",
        other.trigger_ref.rpartition("#")[2],
    ):
        assert private not in caplog.text


def test_a_waiting_request_takes_the_slot_as_soon_as_it_is_free(rt):
    """One slot, held by a run of another key and given back after 0.3 s: the second key is acked then, well
    before `ack_wait_s`, and not refused."""
    first, second = _req(1), _req(2)
    rt.llm.gate.clear()
    release = threading.Timer(0.3, rt.llm.gate.set)
    try:
        with Runner(rt, rt.store, max_running=1, ack_wait_s=2.0, poll_s=0.02) as runner:
            assert runner.start(first)[0] in OK
            assert not runner._slots.acquire(blocking=False)  # the one slot is taken
            release.start()
            began = time.monotonic()
            status, body = runner.start(second)
            waited = time.monotonic() - began
            assert status in OK and body["run_id"] == second.run_id, (status, body)
            assert 0.25 <= waited < 1.5, waited
            assert rt.store.get_run(second.run_id).trigger_ref == second.trigger_ref
            _settle(rt.store, first.run_id)
            _settle(rt.store, second.run_id)
            _free(runner)
    finally:
        release.cancel()
        rt.llm.gate.set()
        release.join(30)
    assert len(rt.store._runs) == 2 and rt.llm.calls == 2


def test_a_waiting_request_is_503_when_the_slot_stays_taken_past_ack_wait(rt):
    first, second = _req(1), _req(2)
    rt.llm.gate.clear()
    try:
        with Runner(rt, rt.store, max_running=1, ack_wait_s=0.5, poll_s=0.02) as runner:
            try:
                assert runner.start(first)[0] in OK
                began = time.monotonic()
                assert runner.start(second) == (503, {})
                assert 0.5 <= time.monotonic() - began < 2.0
                with pytest.raises(NotFound):
                    rt.store.get_run(second.run_id)
            finally:
                rt.llm.gate.set()
            _settle(rt.store, first.run_id)
            _free(runner)
    finally:
        rt.llm.gate.set()
    assert len(rt.store._runs) == 1 and rt.llm.calls == 1


def test_a_refused_request_reads_the_store_a_few_times_not_a_hundred():
    """No free slot and no row for the whole default `ack_wait_s`: the waits double up to the cap."""

    class Counting(MemoryStore):
        reads = 0

        def get_run(self, run_id):
            type(self).reads += 1
            return super().get_run(run_id)

    def holds_its_slot(store, **kw):
        _insert(store, **kw)
        hold.wait(30)

    store, hold = Counting(), threading.Event()
    with Runner(FakeRuntime(store, holds_its_slot), store) as runner:  # the defaults: one slot, 5 s
        try:
            assert runner.start(_req(1))[0] in OK
            before, began = Counting.reads, time.monotonic()
            assert runner.start(_req(2)) == (503, {})
            waited, reads = time.monotonic() - began, Counting.reads - before
        finally:
            hold.set()
        _free(runner)
    assert worker.ACK_WAIT_S <= waited < worker.ACK_WAIT_S + 3.0
    assert 5 <= reads <= 12, reads


# --- ORDER 012: stop on SIGTERM, start-up texts, the tick warning, IPv6 ------------------------------------

_CHILD = """
import sys
from hadavin_sdk.triggers import worker

class Closes:
    def close(self):
        print("runner closed", flush=True)

def app(environ, start_response):
    start_response("200 OK", [("Content-Length", "0")])
    return [b""]

server = worker.make_server(worker.LOOPBACK, 0, app, 5.0)
print(server.server_port, flush=True)
code = worker.serve(server, Closes())
print("served", code, flush=True)
raise SystemExit(code)
"""


@pytest.mark.skipif(sys.platform == "win32", reason="SIGTERM cannot be handled on Windows")
def test_sigterm_stops_a_serving_process_cleanly_with_exit_0():
    """`main` cannot pass its config check yet (no `triggers` block exists), so the child runs `serve`, the
    part of `main` after the start-up checks, on a real server on a free loopback port."""
    child = subprocess.Popen(  # noqa: S603 - this interpreter, a fixed script
        [sys.executable, "-c", _CHILD], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        port = int(child.stdout.readline())
        conn = http.client.HTTPConnection(worker.LOOPBACK, port, timeout=15)
        try:
            conn.request("GET", "/")
            assert conn.getresponse().status == 200  # it serves
        finally:
            conn.close()
        child.send_signal(signal.SIGTERM)
        out, err = child.communicate(timeout=20)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=20)
    assert child.returncode == 0, (child.returncode, err)
    assert "runner closed" in out and "served 0" in out
    assert "Traceback" not in err


@pytest.mark.skipif(sys.platform == "win32", reason="SIGTERM cannot be handled on Windows")
def test_serve_gives_the_previous_sigterm_handler_back():
    if threading.current_thread() is not threading.main_thread():
        pytest.skip("signal handlers can be set in the main thread only")

    class Closes:
        closed = False

        def close(self):
            self.closed = True

    runner, before = Closes(), signal.getsignal(signal.SIGTERM)
    server = worker.make_server(worker.LOOPBACK, 0, lambda e, s: [], 5.0)
    kill = threading.Timer(0.2, os.kill, args=(os.getpid(), signal.SIGTERM))
    try:
        kill.start()
        assert worker.serve(server, runner) == 0  # returns only because the signal stopped it
    finally:
        kill.cancel()
        kill.join(30)
        server.server_close()
        signal.signal(signal.SIGTERM, before)
    assert runner.closed and signal.getsignal(signal.SIGTERM) is before
    assert server.socket.fileno() == -1


@pytest.mark.parametrize(
    ("error", "code"),
    [(ConfigError, 2), (StoreUnavailable, 4), (RuntimeError, 3), (ConnectionRefusedError, 4)],
)
def test_main_prints_a_foreign_start_error_by_class_name_only(monkeypatch, capsys, error, code):
    fake_secret = "pg" + "-pass-" + "Zq7" * 6

    def fails(args):
        raise error(f"cannot connect to postgresql://app:{fake_secret}@db-host/hadavin")

    monkeypatch.setattr(worker, "_prepare", fails)
    assert worker.main([]) == code
    err = capsys.readouterr().err
    assert error.__name__ in err and err.startswith("trigger worker: ")
    for private in (fake_secret, "postgresql", "db-host", "Traceback"):
        assert private not in err


def test_a_port_in_use_is_a_listen_error_exit_2_not_store_unreachable(monkeypatch, capsys):
    """Review 2, Minor 6: the bind failure is an OSError, which `main` would report as "store unreachable"
    (exit 4). The port is taken first by a listening socket of this test."""
    taken = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # Windows: else a second bind of the port passes
            taken.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        taken.bind((worker.LOOPBACK, 0))
        taken.listen(1)
        port = taken.getsockname()[1]
        with pytest.raises(ConfigError, match=f"cannot listen on {worker.LOOPBACK}:{port}") as refused:
            worker.make_server(worker.LOOPBACK, port, lambda e, s: [], 5.0)
        assert "OSError" in str(refused.value)
        assert refused.value.__cause__ is None and refused.value.__suppress_context__

        def binds(args):
            return worker.make_server(worker.LOOPBACK, port, lambda e, s: [], 5.0), None

        monkeypatch.setattr(worker, "_prepare", binds)
        assert worker.main([]) == 2
    finally:
        taken.close()
    err = capsys.readouterr().err
    assert err == f"trigger worker: config error: cannot listen on {worker.LOOPBACK}:{port} (OSError)\n"
    assert "store unreachable" not in err and "Traceback" not in err


def test_main_prints_the_text_of_a_refusal_written_in_the_worker(monkeypatch, capsys):
    def fails(args):
        worker.check_bind("10.1.2.3", False)

    monkeypatch.setattr(worker, "_prepare", fails)
    assert worker.main([]) == 2
    assert "is not loopback" in capsys.readouterr().err


def test_ipv6_hosts_are_refused_the_loopback_one_too():
    for host in ("::1", "::", "fe80::1", "::ffff:127.0.0.1"):
        for allow in (False, True):
            with pytest.raises(ConfigError, match="IPv4 only"):
                worker.check_bind(host, allow)


def test_start_warns_once_when_no_recent_stuck_tick_is_recorded(caplog):
    def warnings():
        return [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]

    class Down(MemoryStore):
        def get_tick_state(self, step):
            raise OSError("private text of the store failure")

    def tick_at(age_s, ok=True):
        at = now() - timedelta(seconds=age_s)
        store = MemoryStore()
        store.save_tick_state(
            TickState(step="stuck", last_run_at=at, last_ok_at=at if ok else None, last_error=None)
        )
        return store

    with caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"):
        assert worker.check_tick(tick_at(30)) is True
        assert warnings() == []
        cases = (MemoryStore(), tick_at(worker.TICK_MAX_AGE_S + 60), tick_at(30, ok=False), Down())
        for n, store in enumerate(cases, start=1):
            assert worker.check_tick(store) is False  # a warning, never an error
            assert len(warnings()) == n and "stuck tick" in warnings()[-1]
    assert "OSError" in caplog.text and "private text" not in caplog.text
