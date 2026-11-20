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
from tests.triggers.conftest import require_core_b, strict

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


@pytest.fixture(autouse=True)
def _no_worker_log_handler():
    """`main` and `_log_to_stderr` put a handler on the `hadavin_sdk.triggers` logger, bound to the stream of
    that moment (a captured one, closed when the test ends). It is removed after every test of this file."""
    yield
    worker._unlog_stderr()


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
    with Runner(rt, rt.store, max_running=1) as runner:
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
    with Runner(rt, rt.store, max_running=1) as runner:
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
    with Runner(rt, rt.store, max_running=1) as runner:
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
    with Runner(rt, rt.store, max_running=1) as runner:
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
    with (
        Runner(rt, rt.store, max_running=1) as other,
        Runner(busy, rt.store, max_running=1, ack_wait_s=0.6, poll_s=0.02) as here,
    ):
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
    with Runner(fake, store, max_running=1) as runner:
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
    with Runner(fake, store, max_running=1) as runner:
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
            assert not runner._slots.acquire(blocking=False), (
                "the slot was given back before the loop ended"
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
    with Runner(FakeRuntime(store, lost_a_state_race), store, max_running=1) as runner:
        assert runner.start(_req(1)) == (202, {"run_id": _req(1).run_id, "state": "RECEIVED"})

    def raced_by_another_document(store, **kw):
        _insert(store, **{**kw, "trigger_ref": endpoint.trigger_ref(SENDER, "key-1", b"x")})
        raise StaleState("run exists")

    store = MemoryStore()
    with Runner(FakeRuntime(store, raced_by_another_document), store, max_running=1) as runner:
        assert runner.start(_req(1)) == (409, {})


def test_handle_raising_after_the_row_is_logged_by_class_name_only(caplog):
    def fails_late(store, **kw):
        _insert(store, **kw)
        raise RuntimeError("private text of the failure")

    store = MemoryStore()
    with (
        caplog.at_level("WARNING", logger="hadavin_sdk.triggers"),
        Runner(FakeRuntime(store, fails_late), store, max_running=1) as runner,
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
    runner = Runner(rt, rt.store, max_running=1)
    runner.close()
    assert runner.start(_req()) == (503, {})
    assert rt.store._runs == {} and rt.llm.calls == 0


def test_bad_arguments_are_refused(rt):
    for kw in ({"max_running": 0}, {"ack_wait_s": 0}, {"poll_s": 0}):
        with pytest.raises(ValueError) as refused:
            Runner(rt, rt.store, **{"max_running": 1, **kw})
        assert "above zero" in str(refused.value), f"bound {kw} refused with another text"
    with Runner(rt, rt.store, max_running=1) as runner:
        assert runner._slots._value == 1  # the Runner has no default: the value given is the bound


# --- crash after the row (step E helper) --------------------------------------------------------------------


def test_crash_after_the_row_then_tick_ends_with_a_person(rt):
    from hadavin_sdk.testing import crash

    req, plain = _req(), rt.store
    with crash.CrashPoints() as cp, Runner(rt, plain, max_running=1) as runner:
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
    }
    return SimpleNamespace(**{**base, **over})


def _app(rt, settings, secrets=None):
    values = {"door-a": SECRET} if secrets is None else secrets
    return SimpleNamespace(
        config=SimpleNamespace(triggers=settings, environment="demo"),
        registry=rt.registry,
        runtime=rt,
        store=rt.store,
        trigger_secret=values.__getitem__,
    )


def test_main_without_a_triggers_block_exits_2(cfg_dir, capsys):
    require_core_b()  # the real Config must have the `triggers` field
    assert worker.main(["--config-dir", str(cfg_dir)]) == 2
    err = capsys.readouterr().err
    assert "triggers block not configured" in err and "Traceback" not in err


def test_main_with_an_unreadable_config_exits_2(tmp_path, capsys):
    assert worker.main(["--config-dir", str(tmp_path / "missing")]) == 2
    assert "config error" in capsys.readouterr().err


def test_make_app_refuses_a_config_without_a_triggers_block(rt):
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
    for host in ("0.0.0.0", "10.1.2.3"):
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
    with Runner(rt, rt.store, max_running=1) as runner:
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
    with Runner(
        FakeRuntime(store, holds_its_slot), store, max_running=1
    ) as runner:  # the defaults: one slot, 5 s
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
    running = 0

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
        running = 0

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
    assert runner.closed, "serve returned without closing the runner"
    assert signal.getsignal(signal.SIGTERM) is before
    assert server.socket.fileno() == -1


@pytest.mark.parametrize(
    ("error", "code"),
    [(ConfigError, 2), (RuntimeError, 3)],
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
    (a start with /health 503 since d-fix6). The port is taken first by a listening socket of this test."""
    taken = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # A plain occupier, no exclusive flag: the server itself must refuse a second bind (code review 1, DC1-1).
        taken.bind((worker.LOOPBACK, 0))
        taken.listen(1)
        port = taken.getsockname()[1]
        line = f"cannot listen on {worker.LOOPBACK}:{port} (OSError)"
        with pytest.raises(ConfigError) as refused:
            worker.make_server(worker.LOOPBACK, port, lambda e, s: [], 5.0)
        assert str(refused.value) == line
        assert refused.value.__cause__ is None and refused.value.__suppress_context__

        def binds(args):
            return worker.make_server(worker.LOOPBACK, port, lambda e, s: [], 5.0), None

        monkeypatch.setattr(worker, "_prepare", binds)
        assert worker.main([]) == 2
    finally:
        taken.close()
    err = capsys.readouterr().err
    assert err == f"trigger worker: config error: {line}\n"
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


# --- design review round 1: M2 cap, M3 close warning, N1, N3, N5, N7, N15 --------------------------------


def _log_lines(caplog, level):
    return [r.getMessage() for r in caplog.records if r.levelname == level]


def test_m2_a_hung_store_cannot_pile_up_request_threads(caplog):
    """M2. `get_run` blocks on an Event: `max_waiting` requests sit inside `start`, the next one is 503 at once
    and the store is not asked again. (Without the cap the third call blocks in `get_run` as well.)"""

    class Hung(MemoryStore):
        reads = 0

        def get_run(self, run_id):
            type(self).reads += 1
            release.wait(30)
            return super().get_run(run_id)

    store, release = Hung(), threading.Event()
    fake = FakeRuntime(store, lambda *a, **kw: None)
    with Runner(fake, store, max_running=1, max_waiting=2) as runner, caplog.at_level("WARNING"):
        inside = [
            threading.Thread(target=runner.start, args=(_req(n),), daemon=True) for n in (1, 2)
        ]
        try:
            for thread in inside:
                thread.start()
            deadline = time.monotonic() + 10
            while Hung.reads < 2 and time.monotonic() < deadline:
                time.sleep(0.01)
            assert Hung.reads == 2
            third: list = []
            caller = threading.Thread(
                target=lambda: third.append(runner.start(_req(3))), daemon=True
            )
            began = time.monotonic()
            caller.start()
            caller.join(5)
            assert third == [(503, {})] and time.monotonic() - began < 2.0
            assert Hung.reads == 2  # the store was not asked for the third
        finally:
            release.set()
            for thread in inside:
                thread.join(10)
    assert any("too many waiting" in line for line in _log_lines(caplog, "WARNING"))
    assert runner._waiting._value == 2  # every place was given back


def test_m2_a_place_is_given_back_after_every_answer(rt):
    with Runner(rt, rt.store, max_running=1, max_waiting=1) as runner:
        for n in range(1, 4):
            assert runner.start(_req(n))[0] in OK
            _settle(rt.store, _req(n).run_id)
            _free(runner)


def test_m2_fifty_parallel_requests_of_one_key_stay_under_the_default_cap(rt):
    assert worker.MAX_WAITING >= 50
    with Runner(rt, rt.store, max_running=1) as runner:
        answers = _parallel(runner, [_req(1)] * 50)
        _free(runner)
    assert all(a[0] in OK for a in answers if isinstance(a, tuple)), answers
    assert not any(isinstance(a, BaseException) for a in answers)


def test_m3_close_warns_once_when_a_loop_is_still_going(rt, caplog):
    rt.llm.gate.clear()
    runner = Runner(rt, rt.store, max_running=1)
    try:
        assert runner.start(_req())[0] in OK
        with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
            runner.close(wait_s=0.05)
        lines = _log_lines(caplog, "WARNING")
        assert len(lines) == 1 and "1 run(s) still going" in lines[0]
    finally:
        rt.llm.gate.set()
    _free(runner)


def test_m3_close_with_nothing_running_is_quiet(rt, caplog):
    with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
        Runner(rt, rt.store, max_running=1).close()
    assert _log_lines(caplog, "WARNING") == []


def test_n1_the_memory_store_is_warned_about_and_the_start_goes_on(rt, caplog):
    with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
        assert worker.check_durable(MemoryStore()) is False
        assert worker.check_durable(SimpleNamespace()) is True  # any other kind: quiet
    lines = _log_lines(caplog, "WARNING")
    assert len(lines) == 1 and "memory kind" in lines[0]


def test_n1_make_app_warns_about_a_memory_store(rt, caplog):
    with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
        _wsgi, runner = worker.make_app(_app(rt, _settings(max_running=1)))
    runner.close(0)
    assert sum("memory kind" in line for line in _log_lines(caplog, "WARNING")) == 1


def test_n3_a_waiter_gets_503_at_once_when_the_runner_is_closed(rt):
    """No slot, no row: the waiter polls. `close` must end that at once, not at the end of `ack_wait_s`.
    (Before the fix it kept polling for the whole 5 s.)"""
    hold = threading.Event()
    fake = FakeRuntime(rt.store, lambda store, **kw: (_insert(store, **kw), hold.wait(30)))
    with Runner(fake, rt.store, max_running=1, ack_wait_s=5.0, poll_s=0.02) as runner:
        try:
            assert runner.start(_req(1))[0] in OK
            answer: list = []
            waiter = threading.Thread(target=lambda: answer.append(runner.start(_req(2))))
            waiter.start()
            time.sleep(0.3)
            began = time.monotonic()
            runner.close(wait_s=0.01)
            waiter.join(4)
            assert answer == [(503, {})] and time.monotonic() - began < 2.5
        finally:
            hold.set()
        _free(runner)


def test_n5_a_store_error_is_a_warning_and_a_bug_is_an_error_both_503(caplog):
    class Broken(MemoryStore):
        def __init__(self, exc):
            super().__init__()
            self.exc = exc

        def get_run(self, run_id):
            raise self.exc

    fake = FakeRuntime(MemoryStore(), lambda *a, **kw: None)
    for exc, level, other in (
        (StoreUnavailable("secret-text-1"), "WARNING", "ERROR"),
        (OSError("secret-text-2"), "WARNING", "ERROR"),
        (StaleState("secret-text-3"), "WARNING", "ERROR"),
        (ZeroDivisionError("secret-text-4"), "ERROR", "WARNING"),
        (KeyError("secret-text-5"), "ERROR", "WARNING"),
    ):
        caplog.clear()
        with (
            caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"),
            Runner(fake, Broken(exc), max_running=1) as runner,
        ):
            assert runner.start(_req()) == (503, {})
        assert any(type(exc).__name__ in line for line in _log_lines(caplog, level)), exc
        assert _log_lines(caplog, other) == [], exc
        assert "secret-text" not in caplog.text
        if level == "ERROR":
            assert "internal error" in _log_lines(caplog, "ERROR")[0]


def test_n7_a_base_exception_of_a_run_thread_is_logged_by_class_name_and_frees_the_slot(caplog):
    class Stop(BaseException):
        pass

    def stops(store, **kw):
        raise Stop("private text")

    store = MemoryStore()
    with (
        caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"),
        Runner(
            FakeRuntime(store, stops), store, max_running=1, ack_wait_s=0.3, poll_s=0.02
        ) as runner,
    ):
        assert runner.start(_req()) == (503, {})  # no row was written
        _free(runner)
        assert runner._slots.acquire(blocking=False)
        runner._slots.release()
    errors = _log_lines(caplog, "ERROR")
    assert len(errors) == 1 and "Stop" in errors[0] and "private text" not in caplog.text


@pytest.mark.parametrize(
    ("kw", "words"),
    [
        ({"max_running": 65}, "at most 64"),
        ({"ack_wait_s": 30.5}, "at most 30"),
        ({"poll_s": 0.005}, "between 0.01 and 1"),
        ({"poll_s": 1.5}, "between 0.01 and 1"),
        ({"max_waiting": 0}, "max_waiting"),
        ({"max_waiting": True}, "max_waiting"),
    ],
)
def test_n15_runner_bounds_are_refused(rt, kw, words):
    with pytest.raises(ValueError, match=words):
        Runner(rt, rt.store, **{"max_running": 1, **kw})


def test_n15_the_bounds_themselves_are_allowed(rt):
    for kw in ({"max_running": 64}, {"ack_wait_s": 30.0}, {"poll_s": 0.01}, {"poll_s": 1.0}):
        Runner(rt, rt.store, **{"max_running": 1, **kw}).close(0)


def test_n15_make_app_turns_a_bound_into_a_config_error(rt):
    with pytest.raises(ConfigError, match="at most 64"):
        worker.make_app(_app(rt, _settings(max_running=65)))


def test_spend_warning_only_above_one_loop_and_without_reserve(caplog):
    plain = SimpleNamespace(limits=SimpleNamespace())
    reserving = SimpleNamespace(limits=SimpleNamespace(reserve=lambda *a: None))
    with caplog.at_level("WARNING", logger="hadavin_sdk.triggers"):
        assert worker.check_spend(plain, 1) is True
        assert worker.check_spend(reserving, 4) is True
        assert _log_lines(caplog, "WARNING") == []
        assert worker.check_spend(plain, 4) is False
        assert worker.check_spend(SimpleNamespace(), 2) is False
    assert len(_log_lines(caplog, "WARNING")) == 2 and "max_running is 4" in caplog.text


def test_make_app_reads_secrets_only_through_the_named_reader_and_refuses_other_names(rt):
    asked: list[str] = []

    def reader(name):
        asked.append(name)
        if name != "door-a":
            raise PermissionError("not one of the secret names")
        return SECRET

    app = _app(rt, _settings(max_running=1))
    app.trigger_secret = reader
    _wsgi, runner = worker.make_app(app)
    runner.close(0)
    assert asked == ["door-a"]


# --- code review 1 (DC1-3, DC1-4, DC1-7 and the mutant gap in Runner.close) ----------------------------------


def test_ack_wait_nan_is_refused_and_a_non_int_max_running_is_a_config_error_in_make_app(rt):
    """DC1-7. NaN passed both comparisons of the old bound; a string or a float as max_running was a TypeError
    (or a float limit) and not a config error."""
    with pytest.raises(ValueError, match="at most 30"):
        Runner(rt, rt.store, max_running=1, ack_wait_s=float("nan"))
    for bad in ("2", 2.0, True, None):
        with pytest.raises(ValueError, match="whole number"):
            Runner(rt, rt.store, max_running=bad)
        with pytest.raises(ConfigError, match="whole number") as refused:
            worker.make_app(_app(rt, _settings(max_running=bad)))
        assert "Traceback" not in str(refused.value)
    with pytest.raises(ConfigError, match="at most 30"):
        worker.make_app(_app(rt, _settings(ack_wait_s=float("nan"))))


def test_serve_installs_the_break_signal_where_it_exists_and_puts_the_old_handlers_back(
    monkeypatch,
):
    """DC1-4. SIGBREAK is Windows only; a stand-in number is used here."""
    monkeypatch.setattr(signal, "SIGBREAK", signal.SIGUSR1, raising=False)
    before = {n: signal.getsignal(n) for n in (signal.SIGTERM, signal.SIGUSR1)}
    seen: dict[int, object] = {}

    class Server:
        server_port = 0

        def serve_forever(self):
            seen.update({n: signal.getsignal(n) for n in before})

        def server_close(self):
            pass

        def shutdown(self):
            pass

    closed = []
    runner = SimpleNamespace(close=lambda: closed.append(True), running=0)
    assert worker.serve(Server(), runner) == worker.EXIT_OK  # type: ignore[arg-type]
    assert (
        seen[signal.SIGTERM] is seen[signal.SIGUSR1]
        and seen[signal.SIGTERM] != before[signal.SIGTERM]
    )
    assert {n: signal.getsignal(n) for n in before} == before and closed == [True]


def test_after_close_a_new_key_is_503_at_once_with_no_error_line_and_the_pool_is_never_asked(
    rt, caplog
):
    """Mutant gap: with `self._closed = True` removed in `close`, `start` hands the work to a pool that has
    been shut down; the pool raises, the answer is still 503, but an ERROR line is logged. The spy on the
    pool's `submit` and the ERROR check kill that mutant."""
    submitted: list[object] = []
    runner = Runner(rt, rt.store, max_running=1)
    real = runner._pool.submit

    def spy(*args, **kwargs):
        submitted.append(args)
        return real(*args, **kwargs)

    runner._pool.submit = spy  # type: ignore[method-assign]
    runner.close()
    with caplog.at_level("DEBUG", logger="hadavin_sdk.triggers"):
        began = time.monotonic()
        assert runner.start(_req()) == (503, {})
        assert time.monotonic() - began < 2.0
    assert submitted == []
    assert [r for r in caplog.records if r.levelno >= 40] == []
    assert rt.store._runs == {} and rt.llm.calls == 0


# --- d-fix2: Runner and make_app validation, and the 409 rule on agent and principal ------------------------


@pytest.mark.parametrize("bad", [2.0, True, False, float("nan"), float("inf"), "2", None])
def test_max_running_that_is_not_a_whole_number_is_refused_in_runner_and_make_app(rt, bad):
    with pytest.raises(ValueError, match="whole number"):
        Runner(rt, rt.store, max_running=bad)
    with pytest.raises(ConfigError, match="whole number"):
        worker.make_app(_app(rt, _settings(max_running=bad)))


@pytest.mark.parametrize(
    ("bad", "words"),
    [
        (True, "must be a number"),
        (False, "must be a number"),
        ("5", "must be a number"),
        (None, "must be a number"),
        (float("nan"), "at most 30"),
        (float("inf"), "at most 30"),
        (0, "at most 30"),
        (-1.0, "at most 30"),
        (30.5, "at most 30"),
    ],
)
def test_ack_wait_s_that_is_not_a_usable_number_is_refused_in_runner_and_make_app(rt, bad, words):
    with pytest.raises(ValueError, match=words):
        Runner(rt, rt.store, max_running=1, ack_wait_s=bad)
    with pytest.raises(ConfigError, match=words):
        worker.make_app(_app(rt, _settings(ack_wait_s=bad)))


@pytest.mark.parametrize("bad", ["0.05", None, True, [0.05]])
def test_a_poll_s_that_is_not_a_number_is_a_value_error_not_a_type_error(rt, bad):
    with pytest.raises(ValueError, match="poll_s must be a number"):
        Runner(rt, rt.store, max_running=1, poll_s=bad)
    with pytest.raises(ConfigError, match="poll_s must be a number"):
        worker.make_app(_app(rt, _settings()), poll_s=bad)


@pytest.mark.parametrize("other", ["agent_id", "principal_id"])
def test_same_key_and_ref_but_another_agent_or_principal_is_409(other):
    """T-1: the row is for the same key and document, so the trigger_ref matches; it was written for another
    agent (or principal), so it is not this sender's run: 409, and nothing is written."""
    req = _req(1)
    store = MemoryStore()
    _insert(
        store,
        run_id=req.run_id,
        trigger_kind="event",
        trigger_ref=req.trigger_ref,
        **{
            "agent_id": AGENT,
            "principal_id": PRINCIPAL,
            other: "someone-else",
        },
    )
    fake = FakeRuntime(store, lambda store, **kw: None)
    with Runner(fake, store, max_running=1) as runner:
        assert runner.start(req) == (409, {})
    assert len(store._runs) == 1


def test_the_defaults_constants_of_core_b_equal_the_literals_of_the_worker():
    from hadavin_sdk import defaults

    for ours, theirs in (
        (worker.MAX_RUNNING_CEILING, "TRIGGER_MAX_RUNNING_CEILING"),
        (worker.ACK_WAIT_S, "TRIGGER_ACK_WAIT_S"),
        (worker.ACK_WAIT_S_CEILING, "TRIGGER_ACK_WAIT_S_CEILING"),
    ):
        if hasattr(defaults, theirs):  # only on a tree that has core-b's defaults
            assert ours == getattr(defaults, theirs), theirs
        elif strict():
            pytest.fail(f"the strict switch is on: defaults.{theirs} is not on this tree")


def test_the_logging_of_the_worker_is_set_on_the_triggers_logger_only():
    import logging

    root, sdk = logging.getLogger(), logging.getLogger("hadavin_sdk")
    top = logging.getLogger("hadavin_sdk.triggers")
    before = (root.level, list(root.handlers), sdk.level, list(sdk.handlers))
    first = worker._log_to_stderr()
    assert worker._log_to_stderr() is first  # twice: the same one handler
    assert (root.level, root.handlers) == (before[0], before[1])
    assert (sdk.level, sdk.handlers) == (before[2], before[3])  # the parent logger is untouched
    assert top.level == logging.INFO
    assert [h for h in top.handlers if getattr(h, "_trigger_worker", False)] == [first]
    worker._unlog_stderr()
    assert not [h for h in top.handlers if getattr(h, "_trigger_worker", False)]
    assert top.level == logging.NOTSET


def _missing(name, base):
    """`base` without the attribute `name`."""
    return SimpleNamespace(**{k: v for k, v in vars(base).items() if k != name})


@pytest.mark.parametrize("field", ["max_running", "ack_wait_s"])
def test_d3_a_settings_object_without_a_field_is_a_config_error_naming_it(rt, field):
    words = (
        "triggers.max_running missing" if field == "max_running" else f"triggers.{field} is missing"
    )
    with pytest.raises(ConfigError, match=words) as refused:
        worker.make_app(_app(rt, _missing(field, _settings())))
    assert not isinstance(refused.value, AttributeError)


def test_d3_a_config_without_triggers_or_an_app_without_a_secret_reader_is_a_config_error(rt):
    app = _app(rt, _settings())
    with pytest.raises(ConfigError, match=r"config\.triggers is missing"):
        worker.make_app(SimpleNamespace(**{**vars(app), "config": SimpleNamespace()}))
    with pytest.raises(ConfigError, match=r"App\.trigger_secret is missing"):
        worker.make_app(_missing("trigger_secret", app))


def test_d3_a_principal_without_a_kind_is_a_config_error_naming_the_field(rt):
    app = _app(rt, _settings())
    bare = SimpleNamespace()  # a stand-in principal with no `kind`
    registry = SimpleNamespace(principals={PRINCIPAL: bare})
    with pytest.raises(ConfigError, match="kind is missing"):
        worker.make_app(SimpleNamespace(**{**vars(app), "registry": registry}))


def test_d3_main_exits_2_for_a_missing_core_b_field(monkeypatch, capsys):
    def missing(args):
        raise worker.ConfigError("triggers.max_running is missing: x")

    monkeypatch.setattr(worker, "_prepare", missing)
    assert worker.main([]) == 2
    assert "triggers.max_running is missing" in capsys.readouterr().err


def test_d3_runner_has_a_read_only_ack_wait(rt):
    with Runner(rt, rt.store, max_running=1, ack_wait_s=7) as runner:
        assert runner.ack_wait_s == 7.0
        with pytest.raises(AttributeError):
            runner.ack_wait_s = 1.0  # type: ignore[misc]


@pytest.mark.parametrize("port", [-1, 65536, True, "80", 1.5, None])
def test_d3_a_bad_port_is_a_config_error_in_make_server(port):
    with pytest.raises(ConfigError, match="--port"):
        worker.make_server(worker.LOOPBACK, port, lambda e, s: [], 5.0)


@pytest.mark.parametrize(
    "kw",
    [
        {"read_deadline_s": 0},
        {"read_deadline_s": -1.0},
        {"read_deadline_s": float("nan")},
        {"read_deadline_s": float("inf")},
        {"read_deadline_s": 301},
        {"read_deadline_s": True},
        {"read_deadline_s": "5"},
        {"max_connections": 0},
        {"max_connections": 4097},
        {"max_connections": True},
        {"max_connections": 2.0},
    ],
)
def test_d3_server_bounds_are_config_errors(kw):
    with pytest.raises(ConfigError, match="read_deadline_s|max_connections"):
        worker.make_server(worker.LOOPBACK, 0, lambda e, s: [], 5.0, **kw)


def test_d3_the_edges_of_the_bounds_are_accepted():
    server = worker.make_server(
        worker.LOOPBACK, 0, lambda e, s: [], 5.0, max_connections=4096, read_deadline_s=300
    )
    server.server_close()


def test_d3_main_with_a_bad_port_exits_2_before_anything_is_built(monkeypatch, capsys):
    import hadavin_sdk.app
    import hadavin_sdk.config

    def not_built(*a, **kw):
        raise AssertionError("built before the port was checked")

    monkeypatch.setattr(
        hadavin_sdk.config, "load_config", lambda d: SimpleNamespace(triggers=_settings())
    )
    monkeypatch.setattr(hadavin_sdk.app, "build", not_built)
    assert worker.main(["--port", "70000"]) == 2
    assert "--port must be" in capsys.readouterr().err


def _quiet_server(max_connections):
    from hadavin_sdk.triggers.server import QuietRequestHandler, QuietServer

    class Handler(QuietRequestHandler):
        def __init__(self, *args, **kwargs) -> None:  # no request is handled
            pass

    return QuietServer((worker.LOOPBACK, 0), Handler, max_connections=max_connections)


class _Req:
    def __init__(self, raises=False) -> None:
        self.raises, self.closed = raises, False

    def shutdown(self, how):
        if self.raises:
            raise RuntimeError("shutdown")

    def close(self):
        self.closed = True


def test_d3_a_shutdown_that_raises_does_not_leak_the_connection_slot():
    server = _quiet_server(1)
    try:
        assert server._slots.acquire(blocking=False)  # what `process_request` does
        with pytest.raises(RuntimeError, match="shutdown"):
            server.process_request_thread(_Req(raises=True), ("127.0.0.1", 1))
        assert server._slots.acquire(blocking=False)  # the cap is free again
    finally:
        server.server_close()


def test_d3_the_connection_cap_is_a_warning_at_most_once_a_minute_with_no_client_data(
    monkeypatch, caplog
):
    import logging

    from hadavin_sdk.triggers import server as quiet

    clock = [1000.0]
    monkeypatch.setattr(quiet, "_monotonic", lambda: clock[0])
    server = _quiet_server(1)
    try:
        assert server._slots.acquire(
            blocking=False
        )  # the one slot is taken: every connection is over the cap
        with caplog.at_level(logging.DEBUG, logger="hadavin_sdk.triggers"):
            for at in (1000.0, 1010.0, 1059.9, 1060.0, 1061.0, 1120.1):
                clock[0] = at
                req = _Req()
                server.process_request(req, ("203.0.113.9", 4444))
                assert req.closed
        warned = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warned) == 3  # at 1000.0, 1060.0 and 1120.1
        text = " ".join(r.getMessage() for r in caplog.records)
        assert "203.0.113.9" not in text and "4444" not in text
        assert all("cap" in r.getMessage() for r in warned)
    finally:
        server.server_close()


# --- d-fix4: R3-2 fields in a config error, R3-3 log format, R3-9 empty host, R3-10 start and stop lines --------


def test_d4_a_config_error_of_the_sdk_names_the_fields_of_its_pydantic_cause_and_no_value(
    monkeypatch, capsys
):
    """R3-2. The SDK's `load_config` chains pydantic's error, whose text repeats the value that was given. `main`
    prints only the location and the error type of each entry, never the text."""
    import pydantic

    fake_secret = "pw" + "-value-" + "Qz9" * 6

    class Backend(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        endpoint: int

    def fails(args):
        try:
            Backend(endpoint=fake_secret, extra_key=fake_secret)  # type: ignore[call-arg]
        except pydantic.ValidationError as exc:
            raise ConfigError(f"backends.llm: {exc}") from exc

    assert fake_secret in str(
        pytest.raises(ConfigError, fails, None).value
    )  # the text does hold it
    monkeypatch.setattr(worker, "_prepare", fails)
    assert worker.main([]) == 2
    err = capsys.readouterr().err
    assert (
        "ConfigError (fields: " in err
        and "endpoint (" in err
        and "extra_key (extra_forbidden)" in err
    )
    assert fake_secret not in err and "Traceback" not in err


def test_d4_a_config_error_of_the_sdk_without_a_pydantic_cause_stays_class_name_only(
    monkeypatch, capsys
):
    def fails(args):
        raise ConfigError("secret 'x' value=hunter2-hunter2")

    monkeypatch.setattr(worker, "_prepare", fails)
    assert worker.main([]) == 2
    assert capsys.readouterr().err == "trigger worker: config error: ConfigError\n"


def test_d4_a_warning_line_of_the_worker_carries_a_time_and_a_level_word(capsys):
    import re

    worker._log_to_stderr()
    worker._LOG.warning("trigger worker: a test line")
    err = capsys.readouterr().err
    assert re.fullmatch(
        r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} WARNING trigger worker: a test line\n", err
    ), err


def test_d4_an_empty_host_is_refused_not_turned_into_loopback(monkeypatch, capsys):
    import hadavin_sdk.app
    import hadavin_sdk.config

    def not_built(*a, **kw):
        raise AssertionError("built although the host was refused")

    monkeypatch.setattr(
        hadavin_sdk.config, "load_config", lambda d: SimpleNamespace(triggers=_settings())
    )
    monkeypatch.setattr(hadavin_sdk.app, "build", not_built)
    assert worker.main(["--host", "", "--port", "0"]) == 2
    err = capsys.readouterr().err
    assert "--host must be an IP address or localhost" in err and "Traceback" not in err


def test_d4_start_says_where_it_listens_and_stop_says_it_is_waiting(monkeypatch, capsys):
    class Runner_:
        running = 3
        closed = False

        def close(self):
            self.closed = True

    server = worker.make_server(worker.LOOPBACK, 0, lambda e, s: [], 5.0)
    runner = Runner_()
    monkeypatch.setattr(worker, "_prepare", lambda args: (server, runner))
    monkeypatch.setattr(
        server, "serve_forever", lambda *a, **kw: (_ for _ in ()).throw(KeyboardInterrupt)
    )
    try:
        assert worker.main(["--port", "0"]) == 0
    finally:
        server.server_close()
    lines = capsys.readouterr().err.splitlines()
    port = server.server_port
    listening = [x for x in lines if "listening on" in x]
    stopping = [x for x in lines if "stopping" in x]
    assert (
        len(listening) == 1
        and f"listening on http://127.0.0.1:{port}{endpoint.PATH}" in listening[0]
    )
    assert len(stopping) == 1 and stopping[0].endswith("stopping, waiting for 3 runs")
    assert runner.closed


# ruff: noqa: S104
# --- d-fix5: R4-3 bind wiring and defaults, R4-4 Runner.running, R4-6 plain location segments ------------------


def _patched_main(monkeypatch, seen):
    """`main` with load_config and build patched: build raises a marker, so a run that passes the bind check ends
    with exit 3 ('start failed: _Built'), and one the bind check refuses ends with 2."""
    import hadavin_sdk.app
    import hadavin_sdk.config

    class _Built(Exception):
        pass

    def built(*a, **kw):
        seen.append("built")
        raise _Built

    monkeypatch.setattr(
        hadavin_sdk.config, "load_config", lambda d: SimpleNamespace(triggers=_settings())
    )
    monkeypatch.setattr(hadavin_sdk.app, "build", built)
    real_registry = __import__("hadavin_sdk.registry", fromlist=["load_registry"])
    monkeypatch.setattr(real_registry, "load_registry", lambda config: [])
    monkeypatch.setattr(worker, "qualified_agents", lambda registry: [])


def test_d5_a_host_that_is_not_loopback_is_refused_with_exit_2_before_anything_is_built(
    monkeypatch, capsys
):
    seen: list[str] = []
    _patched_main(monkeypatch, seen)
    assert worker.main(["--host", "0.0.0.0", "--port", "0"]) == 2
    err = capsys.readouterr().err
    assert "not loopback" in err and "--allow-non-loopback" in err and "Traceback" not in err
    assert seen == []


def test_d5_with_the_switch_a_host_that_is_not_loopback_passes_the_bind_check(monkeypatch, capsys):
    seen: list[str] = []
    _patched_main(monkeypatch, seen)
    binds: list[tuple[str, object]] = []
    real = worker.check_bind
    monkeypatch.setattr(
        worker,
        "check_bind",
        lambda host, allow: (binds.append((host, allow)), real(host, allow))[1],
    )
    assert worker.main(["--host", "0.0.0.0", "--port", "0", "--allow-non-loopback"]) == 3
    err = capsys.readouterr().err
    assert "not loopback" not in err and "start failed: _Built" in err
    assert seen == ["built"] and binds == [("0.0.0.0", True)]


def test_d5_the_defaults_are_host_127_0_0_1_and_port_8081(monkeypatch, capsys):
    seen: list[str] = []
    _patched_main(monkeypatch, seen)
    parsed: list[object] = []
    real_prepare = worker._prepare
    monkeypatch.setattr(
        worker, "_prepare", lambda args: (parsed.append(args), real_prepare(args))[1]
    )
    checks: list[tuple[str, object]] = []
    real_port, real_bind = worker.check_port, worker.check_bind
    monkeypatch.setattr(
        worker, "check_port", lambda p: (checks.append(("port", p)), real_port(p))[1]
    )
    monkeypatch.setattr(
        worker, "check_bind", lambda h, a: (checks.append(("host", (h, a))), real_bind(h, a))[1]
    )
    assert worker.main([]) == 3  # passes both checks, stops in the patched build
    args = parsed[0]
    assert args.host == "127.0.0.1" and args.port is None and args.allow_non_loopback is False  # type: ignore[attr-defined]
    assert worker.LOOPBACK == "127.0.0.1" and worker.PORT == 8081
    assert checks == [("port", 8081), ("host", ("127.0.0.1", False))]
    capsys.readouterr()


def test_d5_runner_running_counts_the_loops_that_have_not_ended(rt):
    rt.llm.gate.clear()
    try:
        with Runner(rt, rt.store, max_running=1, ack_wait_s=5.0) as runner:
            assert runner.running == 0
            status, _ = runner.start(_req(1))
            assert status in OK
            deadline = time.monotonic() + 20
            while rt.llm.calls < 1 and time.monotonic() < deadline:
                time.sleep(0.01)
            assert rt.llm.calls == 1  # the loop is inside the model, held by the gate
            assert runner.running == 1
            rt.llm.gate.set()
            _free(runner)
            assert runner.running == 0
    finally:
        rt.llm.gate.set()


def test_d5_serve_reads_running_from_the_runner_with_no_default(monkeypatch):
    class Server:
        server_port = 0

        def serve_forever(self):
            pass

        def server_close(self):
            pass

        def shutdown(self):
            pass

    monkeypatch.setattr(signal, "SIGBREAK", signal.SIGUSR1, raising=False)
    runner = SimpleNamespace(close=lambda: None)  # no `running`: reading it must raise, not give 0
    with pytest.raises(AttributeError):
        worker.serve(Server(), runner)  # type: ignore[arg-type]


def test_d5_a_location_segment_with_user_text_is_printed_as_a_question_mark(monkeypatch, capsys):
    import pydantic

    text_key = "my secret key " + "Zq7" * 5
    long_key = "k" * 41

    class Backend(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(extra="forbid")
        endpoint: int

    def fails(args):
        try:
            Backend.model_validate({"endpoint": 1, text_key: 1, long_key: 2, "ok-key.1": 3})
        except pydantic.ValidationError as exc:
            raise ConfigError("x") from exc

    monkeypatch.setattr(worker, "_prepare", fails)
    assert worker.main([]) == 2
    err = capsys.readouterr().err
    assert "ok-key.1 (extra_forbidden)" in err and "? (extra_forbidden)" in err
    assert "Zq7" not in err and "secret" not in err and "k" * 20 not in err
    assert worker._loc_text(("a", 3, "b c", "x" * 40, "x" * 41)) == "a.3.?." + "x" * 40 + ".?"
