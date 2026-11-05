"""Second pass on the service (reviews A and B of a06e7c8): boundaries, drain, duplicate headers, Allow and HEAD, a refused request is not activity, sessions on
error pages, scan_running, parallel guesses, signals, graceful stop, INTAKE_LOG order, SO_EXCLUSIVEADDRUSE, flushed start lines and real subprocess start/stop."""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from service_helpers import (
    HOSTS,
    NAV,
    FakeScanner,
    build,
    fast_limits,
    form_post,
    get,
    login_form,
    make_viewer,
    raw,
    sign_in,
    start_service,
)

from conftest import ROOT, fake_secret_values, settings_for_tests
from intake import access, lockfile, review_page, service, workqueue
from intake.codes import ConfigError


@pytest.fixture
def env(tmp_path, monkeypatch):
    e = start_service(tmp_path, monkeypatch)
    yield e
    e.close()


# ---- limits at the boundary ------------------------------------------------------------------------------------------------------------------
def test_request_line_boundary(env):
    wh, wp = env.work
    for total, want in ((service.LIMIT_REQUEST_LINE, 404), (service.LIMIT_REQUEST_LINE + 1, 414)):
        target = "/" + "a" * (total - len("GET  HTTP/1.1") - 1)
        line = f"GET {target} HTTP/1.1"
        assert len(line) == total
        assert raw(env.work, f"{line}\r\nHost: {wh}:{wp}\r\n\r\n".encode()).status == want, total


def test_header_count_boundary(env):
    wh, wp = env.work
    for n, want in ((service.LIMIT_HEADERS, 200), (service.LIMIT_HEADERS + 1, 431)):
        extra = "".join(f"X-H{i}: v\r\n" for i in range(n - 4))  # Host and the three Sec-Fetch headers make 4
        data = f"GET /login HTTP/1.1\r\nHost: {wh}:{wp}\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Dest: document\r\nSec-Fetch-Site: none\r\n{extra}\r\n"
        assert raw(env.work, data.encode()).status == want, n


def test_header_line_boundary(env):
    wh, wp = env.work
    for total, want in ((service.LIMIT_HEADER_LINE, 200), (service.LIMIT_HEADER_LINE + 1, 431)):
        value = "a" * (total - len("X: "))
        data = f"GET /login HTTP/1.1\r\nHost: {wh}:{wp}\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Dest: document\r\nSec-Fetch-Site: none\r\nX: {value}\r\n\r\n"
        assert raw(env.work, data.encode()).status == want, total


class _Counting:
    def __init__(self, inner):
        self.inner, self.count = inner, 0

    def read(self, n=-1):
        data = self.inner.read(n)
        self.count += len(data)
        return data

    def __getattr__(self, name):
        return getattr(self.inner, name)


def test_drain_reads_the_body_up_to_the_cap(env, monkeypatch):
    seen = []
    real = service.Handler._drain

    def spy(self):
        self.rfile = counting = _Counting(self.rfile)
        real(self)
        seen.append((self._declared, counting.count))

    monkeypatch.setattr(service.Handler, "_drain", spy)
    wh, wp = env.work
    cookie, _ = sign_in(env)
    h = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }
    assert raw(env.work, build("POST", "/logout", f"{wh}:{wp}", h, b"a" * 9000)).status == 413
    assert raw(env.work, build("POST", "/logout", f"{wh}:{wp}", h, b"a" * 99999)).status == 413
    assert seen == [(9000, 9000), (99999, service.LIMIT_DRAIN)]  # the declared body, never more than the cap


def test_411_for_a_work_post_without_a_length_even_for_a_big_declared_body_413_comes_first(env):
    wh, wp = env.work
    cookie, _ = sign_in(env)
    h = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }
    assert raw(env.work, build("POST", "/logout", f"{wh}:{wp}", h)).status == 411
    assert raw(env.work, build("POST", "/logout", f"{wh}:{wp}", h, b"a" * 9000)).status == 413


# ---- headers ---------------------------------------------------------------------------------------------------------------------------------
def test_repeated_security_headers_are_refused(env):
    wh, wp = env.work
    cookie, csrf = sign_in(env)
    base = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }
    body = f"csrf={csrf}".encode()
    ok = build("POST", "/logout", f"{wh}:{wp}", {**base, "Cookie": cookie}, body)
    assert raw(env.work, ok.replace(b"Cookie:", b"X-A: 1\r\nCookie:", 1)).status == 303  # a harmless extra header is fine
    for name, value in (
        ("Origin", base["Origin"]),
        ("Sec-Fetch-Site", "same-origin"),
        ("Content-Type", base["Content-Type"]),
        ("Sec-Fetch-Mode", "navigate"),
        ("Sec-Fetch-Dest", "document"),
    ):
        data = build("POST", "/logout", f"{wh}:{wp}", {**base, name: value}, body).replace(
            b"\r\n\r\n", f"\r\n{name}: {value}\r\n\r\n".encode(), 1
        )
        assert raw(env.work, data).status == 400, name
    data = build("GET", "/login", f"{wh}:{wp}", {**NAV, "X-Request-Id": "first"}).replace(
        b"\r\n\r\n", b"\r\nX-Request-Id: second\r\n\r\n", 1
    )
    assert raw(env.work, data).status == 200  # a repeated X-Request-Id is not refused; the log field uses the first value
    two_hosts = build("GET", "/login", f"{wh}:{wp}", NAV).replace(b"\r\n\r\n", f"\r\nHost: {wh}:{wp}\r\n\r\n".encode(), 1)
    assert raw(env.work, two_hosts).status == 421
    th, tp = env.token
    tok = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}
    twice = build("GET", "/healthz", f"{th}:{tp}", tok).replace(
        b"\r\n\r\n", b"\r\nX-Hadavin-Token: " + tok["X-Hadavin-Token"].encode() + b"\r\n\r\n", 1
    )
    assert raw(env.token, twice).status == 401
    nav = build("GET", "/login", f"{wh}:{wp}", NAV).replace(b"\r\n\r\n", b"\r\nSec-Fetch-Mode: cors\r\n\r\n", 1)
    assert raw(env.work, nav).status == 400  # not read as its first value ("navigate")


def test_form_content_type_refuses_unicode_spaces(env):
    cookie, _ = sign_in(env)
    r = form_post(env, "/logout", {"csrf": "x"}, cookies=cookie, extra={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"})
    assert r.status == 400
    r = form_post(
        env, "/logout", {"csrf": "x"}, cookies=cookie, extra={"Content-Type": "application/x-www-form-urlencoded;\tcharset=utf-8"}
    )
    assert r.status == 403  # a tab is optional whitespace: past the type rule, stopped by the CSRF check


def test_no_reporting_endpoints_header_and_allow_on_405(env):
    wh, wp = env.work
    r = get(env, "work", "/login", NAV)
    assert r.first("Reporting-Endpoints") is None
    r = raw(env.work, build("PUT", "/", f"{wh}:{wp}"))
    assert r.status == 405 and r.first("Allow") == "GET"
    r = get(env, "work", "/logout")
    assert r.status == 405 and r.first("Allow") == "POST"
    assert raw(env.work, build("DELETE", "/nope", f"{wh}:{wp}")).status == 404  # no such path: nothing to allow
    th, tp = env.token
    assert (
        raw(
            env.token, build("GET", "/events/scan", f"{th}:{tp}", {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]})
        ).first("Allow")
        == "POST"
    )


def test_head_gets_no_body_on_early_errors_too(env):
    wh, wp = env.work
    long_target = "/" + "a" * 3000
    many = "".join(f"X-H{i}: v\r\n" for i in range(41))
    for data, want in (
        (f"HEAD {long_target} HTTP/1.1\r\nHost: {wh}:{wp}\r\n\r\n", 414),
        (f"HEAD /login HTTP/2.0\r\nHost: {wh}:{wp}\r\n\r\n", 505),
        (f"HEAD /login HTTP/1.1\r\nHost: {wh}:{wp}\r\n{many}\r\n", 431),
        ("HEAD / HTTP/1.1\r\nHost: evil\r\n\r\n", 421),
    ):
        r = raw(env.work, data.encode())
        assert r.status == want and r.body == b"" and int(r.first("Content-Length")) > 0, want


def test_head_gets_the_headers_and_no_body(env):
    wh, wp = env.work
    r = raw(env.work, build("HEAD", "/", f"{wh}:{wp}"))
    assert r.status == 405 and r.body == b"" and int(r.first("Content-Length")) > 0 and r.first("Allow") == "GET"


# ---- sessions --------------------------------------------------------------------------------------------------------------------------------
def test_a_refused_request_is_not_activity(env):
    from service_helpers import use_fake_clocks

    fc = use_fake_clocks(env)
    wh, wp = env.work
    cookie, csrf = sign_in(env)
    vcookie, vcsrf = make_viewer(env)
    store = env.run.shared.sessions
    sid = cookie.split("=", 1)[1]
    vsid = vcookie.split("=", 1)[1]
    t0, v0 = store._by_sid[sid].last_touch, store._by_sid[vsid].last_touch
    fc.advance(5)
    assert form_post(env, "/logout", {"csrf": "wrong"}, cookies=cookie).status == 403  # CSRF
    assert form_post(env, "/logout", {"csrf": csrf}, cookies=cookie, extra={"Origin": "http://evil.example"}).status == 403  # Origin
    assert form_post(env, "/export", {"csrf": vcsrf, "passphrase": "x"}, cookies=vcookie).status == 403  # role
    assert raw(env.work, build("GET", "/export", f"{wh}:{wp}", {"Cookie": vcookie})).status == 403  # role on a GET
    assert store._by_sid[sid].last_touch == t0 and store._by_sid[vsid].last_touch == v0
    assert get(env, "work", "/", {"Cookie": cookie}).status == 200
    assert store._by_sid[sid].last_touch.mono == t0.mono + 5  # a request that passed every check does refresh it


def test_request_repr_hides_the_form_the_headers_and_the_session(env):
    sess = env.run.shared.sessions.create(access.LOGINS[0])
    req = service.Request(
        "work",
        env.s and __import__("intake.routes").routes.route("login_post"),
        {},
        {},
        {"passphrase": "PW-SECRET-1", "csrf": "CSRF-SECRET"},
        {"cookie": "COOKIE-SECRET"},
        sess,
        env.s,  # fmt: skip
    )
    text = repr(req)
    for secret in ("PW-SECRET-1", "CSRF-SECRET", "COOKIE-SECRET", sess.sid, sess.csrf):
        assert secret not in text


def test_error_pages_of_a_signed_in_person_get_their_session(env, monkeypatch):
    cookie, _ = sign_in(env)
    seen = []
    real = review_page.session_view
    monkeypatch.setattr(review_page, "session_view", lambda s: seen.append(s.login_name) or real(s))
    monkeypatch.setattr(service, "HANDLERS", {**service.HANDLERS, "home": lambda r: (_ for _ in ()).throw(TypeError("planted"))})
    assert get(env, "work", "/", {"Cookie": cookie}).status == 500  # the outer handler path
    assert get(env, "work", "/nope", {"Cookie": cookie}).status == 404
    assert seen[0] == "ap-a" and len(seen) >= 1
    seen.clear()
    monkeypatch.setattr(
        access, "allowed", lambda route, session: (_ for _ in ()).throw(TypeError("planted"))
    )  # an error in the pipeline itself
    assert get(env, "work", "/", {"Cookie": cookie}).status == 500
    assert seen == ["ap-a"]  # the outer handler's error page also knows who is signed in


def test_the_pages_are_told_whether_a_scan_is_running(env, monkeypatch):
    cookie, _ = sign_in(env)
    from service_helpers import ready_item

    it = ready_item(env)
    for flag in (False, True):
        monkeypatch.setattr(FakeScanner, "running", lambda self, flag=flag: flag)
        for p in ("/", f"/item/{it.id}", "/export"):
            text = get(env, "work", p, {"Cookie": cookie}).text
            assert ("A scan is running" in text) is flag, (p, flag)


# ---- guesses in parallel ---------------------------------------------------------------------------------------------------------------------
def test_parallel_wrong_guesses_are_throttled(env):
    forms = [login_form(env) for _ in range(16)]  # sixteen browsers with a sign-in form each
    out = []
    gate = threading.Barrier(16)

    def go(pre, tok):
        gate.wait()
        r = form_post(env, "/login", {"csrf": tok, "login": "ap-a", "passphrase": "wrong-guess"}, cookies=f"{access.COOKIE_PRE}={pre}")
        out.append(r.status)

    ts = [threading.Thread(target=go, args=(pre, tok)) for _, pre, tok in forms]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert out.count(401) <= access.THROTTLE_FAILURES and out.count(429) >= 16 - access.THROTTLE_FAILURES - 1, sorted(out)


# ---- start and stop --------------------------------------------------------------------------------------------------------------------------
def test_a_process_stop_signal_ends_serve_like_ctrl_c():
    for signum in (signal.SIGTERM, signal.SIGINT, *((signal.SIGBREAK,) if sys.platform == "win32" else ())):
        flag = service._StopFlag()
        saved = service._stop_on_signals(flag)
        try:
            assert saved  # installed (this test runs in the main thread)
            assert signal.getsignal(signum) not in (signal.SIG_DFL, signal.SIG_IGN, signal.default_int_handler), (
                "the signal still has the default action"
            )
            signal.raise_signal(signum)
            assert flag.requested is True  # Ctrl+C is a flag too: no KeyboardInterrupt in the middle of a stop
        finally:
            for n, old in saved:
                signal.signal(n, old)
        assert service._StopFlag.requested is False  # the class default is untouched: each serve has its own flag


def test_the_signal_handler_takes_no_lock():
    tree = ast.parse((ROOT / "src" / "intake" / "service.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_stop_on_signals")
    inner = next(n for n in ast.walk(fn) if isinstance(n, ast.FunctionDef) and n.name == "on_signal")
    calls = [n for n in ast.walk(inner) if isinstance(n, ast.Call)]
    assert calls == []  # an assignment and nothing else: Event.set() takes a lock the interrupted code may hold


def test_no_signal_handler_is_installed_off_the_main_thread():
    out = []
    t = threading.Thread(target=lambda: out.append(service._stop_on_signals(service._StopFlag())))
    t.start()
    t.join()
    assert out == [[]]


def test_the_signals_are_in_place_before_the_service_starts(tmp_path, monkeypatch):
    seen = []
    e = start_service(tmp_path, monkeypatch)

    def fake_start(*a, **k):
        seen.append(callable(signal.getsignal(signal.SIGTERM)) and signal.getsignal(signal.SIGTERM) is not signal.SIG_DFL)
        e.run.shared.stop.set()  # stop at once
        return e.run

    monkeypatch.setattr(service, "start", fake_start)
    assert service.serve(e.s) == 0
    assert seen == [True]  # a signal right after "serving:" is already a normal stop
    assert signal.getsignal(signal.SIGTERM) is not None


def test_ctrl_c_stops_serve_with_exit_0_and_releases_the_lock(tmp_path, monkeypatch):
    e = start_service(tmp_path / "x", monkeypatch)  # a started service to hand to serve()
    stopped = []
    real_stop = e.run.stop

    class Boom:
        def wait(self, timeout=None):
            raise KeyboardInterrupt

        def is_set(self):
            return False

    e.run.shared.stop = Boom()
    e.run.stop = lambda *a, **k: (stopped.append(k.get("grace_s")), real_stop(*a, **k))[1]
    monkeypatch.setattr(service, "start", lambda *a, **k: e.run)
    assert service.serve(e.s) == 0 and stopped == [None]
    assert not lockfile.is_held(e.s.intake_home / "serve.lock")


def test_a_second_ctrl_c_during_the_stop_stops_at_once(tmp_path, monkeypatch):
    e = start_service(tmp_path / "y", monkeypatch)
    calls = []
    real_stop = e.run.stop

    def stop(*a, **k):
        calls.append(k.get("grace_s"))
        if len(calls) == 1:
            raise KeyboardInterrupt  # the second Ctrl+C arrives while the first stop is waiting
        return real_stop(*a, **k)

    e.run.stop = stop
    e.run.shared.stop.set()
    monkeypatch.setattr(service, "start", lambda *a, **k: e.run)
    try:
        code = service.serve(e.s)
    except KeyboardInterrupt:
        pytest.fail("a second Ctrl+C escaped serve() as a traceback")
    assert code == 0  # no traceback, exit 0
    assert calls == [None, 0.0]
    assert not lockfile.is_held(e.s.intake_home / "serve.lock")


def test_stop_waits_for_a_request_in_progress_before_the_lock_goes(tmp_path, monkeypatch):
    e = start_service(tmp_path, monkeypatch)
    started, release, done = threading.Event(), threading.Event(), threading.Event()
    got = []

    def slow(req):
        started.set()
        release.wait(5)
        done.set()
        return service.Reply(200, b"late reply", "text/plain")

    monkeypatch.setattr(service, "HANDLERS", {**service.HANDLERS, "home": slow})
    cookie, _ = sign_in(e)
    wh, wp = e.work
    t = threading.Thread(target=lambda: got.append(raw(e.work, build("GET", "/", f"{wh}:{wp}", {"Cookie": cookie}), timeout=8)))
    t.start()
    assert started.wait(5)  # the request is inside the handler: no guessing with sleeps
    threading.Timer(1.5, release.set).start()  # longer than the rest of stop() takes without waiting
    e.run.stop()
    assert done.is_set()  # stop() came back only after the request finished
    assert not lockfile.is_held(e.s.intake_home / "serve.lock")
    t.join()
    assert got[0].status == 200 and got[0].body == b"late reply"


def test_a_stop_in_the_middle_of_a_scan_is_a_crash_the_next_start_repairs(tmp_path, monkeypatch):
    """Errata 101b: stopping equals crash recovery. A received item whose scan was cut off becomes NEEDS_PERSON with L02 at the next start."""
    e = start_service(tmp_path, monkeypatch)
    rec = workqueue.insert_received(e.s, "r.txt", "d" * 64, "text", e.s.tenant_id, "r")  # what a scan stores before its model call
    started = threading.Event()
    real_try = FakeScanner.try_scan

    def slow_scan(self):
        started.set()
        time.sleep(1.5)
        return real_try(self)

    monkeypatch.setattr(FakeScanner, "try_scan", slow_scan)
    th, tp = e.token
    tok = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}
    t = threading.Thread(target=lambda: raw(e.token, build("POST", "/events/scan", f"{th}:{tp}", tok, b""), timeout=8))
    t.start()
    assert started.wait(5)
    e.run.stop(grace_s=0.2)  # shorter than the scan: the scan is cut off
    assert not lockfile.is_held(e.s.intake_home / "serve.lock")
    again = service.start(e.s, hosts=HOSTS, limits=fast_limits())
    try:
        got = workqueue.get(e.s, rec.id)
        assert got.state == "NEEDS_PERSON" and "L02" in got.flags
    finally:
        again.stop()
        t.join()


def test_intake_log_is_read_before_anything_is_bound(tmp_path, monkeypatch):
    from service_helpers import install_stand_ins

    install_stand_ins(monkeypatch)
    monkeypatch.setattr(service.inbox, "Scanner", FakeScanner)
    s = settings_for_tests(tmp_path, with_ledger=True)
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=0))
    rec = workqueue.insert_received(s, "r.txt", "d" * 64, "text", s.tenant_id, "r")
    monkeypatch.setenv("INTAKE_LOG", "bogus")
    with pytest.raises(ConfigError) as e:
        service.start(s, hosts=HOSTS, limits=fast_limits())
    assert e.value.code == "bad_config"
    assert not (s.intake_home / "serve.lock").exists()  # the lock file was never created
    assert workqueue.get(s, rec.id).state == "RECEIVED"  # and the start-up repair never ran


@pytest.mark.skipif(sys.platform != "win32", reason="SO_EXCLUSIVEADDRUSE is a Windows socket option")
def test_a_rival_cannot_share_the_port_of_a_running_service_on_windows(tmp_path, monkeypatch):
    """The attack runs in this order: the service binds first; a rival program then binds the same address with SO_REUSEADDR, which on Windows would
    share the port (and steal requests) unless the service holds it exclusively."""
    e = start_service(tmp_path, monkeypatch)
    try:
        host, port = e.work
        for sv in e.run.servers.values():
            assert (
                sv.socket.getsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE) == 1
            )  # the option itself, whatever this Windows build does without it
        rival = socket.socket()
        rival.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        with pytest.raises(OSError):
            rival.bind((host, port))
        rival.close()
    finally:
        e.close()


def test_a_port_taken_by_another_program_is_port_in_use(tmp_path, monkeypatch):
    from service_helpers import install_stand_ins
    from test_serve import free_port

    install_stand_ins(monkeypatch)
    monkeypatch.setattr(service.inbox, "Scanner", FakeScanner)
    s = settings_for_tests(tmp_path, with_ledger=True)
    port = free_port()
    blocker = socket.socket()
    blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    blocker.bind((HOSTS["work"], port))
    blocker.listen()
    try:
        with pytest.raises(ConfigError) as e:
            service.start(dataclasses.replace(s, service=dataclasses.replace(s.service, port=port)), hosts=HOSTS, limits=fast_limits())
        assert e.value.code == "port_in_use"
    finally:
        blocker.close()


def test_a_closed_stdout_at_start_gives_the_lock_back(tmp_path, monkeypatch):
    from service_helpers import install_stand_ins

    install_stand_ins(monkeypatch)
    monkeypatch.setattr(service.inbox, "Scanner", FakeScanner)
    s = settings_for_tests(tmp_path, with_ledger=True)
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=0))

    def broken_pipe(*a, **k):
        raise BrokenPipeError

    monkeypatch.setattr(service, "print", broken_pipe, raising=False)
    with pytest.raises(BrokenPipeError):
        service.start(s, hosts=HOSTS, limits=fast_limits())
    assert not lockfile.is_held(s.intake_home / "serve.lock")  # listeners closed, lock released


def test_every_start_line_is_flushed():
    tree = ast.parse((ROOT / "src" / "intake" / "service.py").read_text(encoding="utf-8"))
    prints = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "print"]
    assert prints and all(any(k.arg == "flush" and getattr(k.value, "value", None) is True for k in n.keywords) for n in prints)


# ---- a real process --------------------------------------------------------------------------------------------------------------------------
def _cannot(reason: str):
    """A process test that cannot run: a skip on a laptop, a FAILURE in CI and in an evidence run (a leaked serve must not turn it into a quiet skip)."""
    if os.environ.get("CI") or os.environ.get("EVIDENCE"):
        pytest.fail("CANNOT RUN: " + reason)
    pytest.skip(reason)


def _port_free(host: str, port: int) -> bool:
    with socket.socket() as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def _run_serve_process(tmp_path, argv: list[str]):
    """Runs ``_run_serve_process_locked`` one at a time per machine: the product port is fixed, and the evidence chain runs lanes side by side."""
    import tempfile

    gate_path = Path(tempfile.gettempdir()) / "intake_test_serve_port.lock"
    gate = None
    end = time.monotonic() + 240
    while gate is None:
        try:
            gate = lockfile.acquire(gate_path)
        except lockfile.LockHeld:
            if time.monotonic() > end:
                _cannot("another test process held the product port for four minutes")
            time.sleep(0.5)
    try:
        return _run_serve_process_locked(tmp_path, argv)
    finally:
        lockfile.release(gate)


def _run_serve_process_locked(tmp_path, argv: list[str]):
    """Start `serve` as a real process with its output redirected to a file, wait for the 'serving:' line, stop it as the operating system would, and
    return (exit code, output). Uses the product port from config/service.json."""
    s = settings_for_tests(tmp_path, with_ledger=True)
    port = s.service.port
    if not all(_port_free(h, port) for h in ("127.0.0.1", "127.0.0.11", "127.0.0.12")):
        _cannot(f"port {port} is busy on a service address: another intake serve may be running")
    out = tmp_path / "serve.out"
    envv = {**os.environ, "HADAVIN_LOCAL": str(s.local), "INTAKE_MODEL_BACKEND": "fake", "PYTHONUNBUFFERED": ""}
    envv.pop("PYTHONUNBUFFERED")
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    with open(out, "wb") as fh:
        proc = subprocess.Popen(argv, stdout=fh, stderr=subprocess.STDOUT, env=envv, cwd=ROOT, creationflags=flags)  # noqa: S603
        try:
            end = time.monotonic() + 40
            while time.monotonic() < end and b"serving:" not in out.read_bytes() and proc.poll() is None:
                time.sleep(0.2)
            assert b"serving:" in out.read_bytes(), out.read_text(errors="replace")[
                -2000:
            ]  # seen while the process still runs: the lines were flushed
            proc.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == "win32" else signal.SIGTERM)
            code = proc.wait(timeout=30)
        finally:
            if proc.poll() is None:
                proc.kill()
    return code, out.read_text(errors="replace")


def test_python_dash_m_intake_serve_starts_and_stops(tmp_path):
    if importlib.util.find_spec("intake.ui") is None:
        _cannot("intake.ui (portal P1 ui.py) is not importable: `python -m intake serve` cannot start without it")
    code, text = _run_serve_process(tmp_path, [sys.executable, "-m", "intake", "serve"])
    assert code == 0 and "serving: token http://127.0.0.1:" in text and "Traceback" not in text


def test_a_missing_inbox_is_a_fixed_503_and_only_that(env):
    from intake.codes import ConfigError

    th, tp = env.token
    tok = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}

    def scan():
        return raw(env.token, build("POST", "/events/scan", f"{th}:{tp}", tok, b""))

    FakeScanner.script = [service._InboxUnavailable("inbox folder C:\\secret\\path is missing")]
    r = scan()
    assert r.status == 503 and r.text == '{"error": "not_configured"}' and "secret" not in r.text
    for other in (
        ConfigError("bad_config", "queue is not WAL"),
        ConfigError("ledger_inconsistent", "x"),
    ):  # a damaged queue is also bad_config
        FakeScanner.script = [other]
        assert scan().status == 500, other.code


def test_a_hostile_refused_file_name_leaves_no_trace_in_the_log(tmp_path, monkeypatch, capfd):
    import json
    import os

    e = start_service(tmp_path, monkeypatch, with_scanner=False)  # the real scanner
    try:
        name = "x" + chr(0x202E) + chr(0x1B) * 0 + ".txt"  # a right-to-left override in a file name
        path = e.s.intake_home / "inbox" / name
        path.write_bytes(b"hello")
        old = time.time() - 100
        os.utime(path, (old, old))
        th, tp = e.token
        tok = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}
        r = raw(e.token, build("POST", "/events/scan", f"{th}:{tp}", tok, b""))
        assert r.status == 200 and json.loads(r.body)["refused"], r.text
        assert chr(0x202E) not in r.text  # the reply is ASCII-escaped JSON
        out = capfd.readouterr()
        assert chr(0x202E) not in out.out + out.err and "hello" not in out.out + out.err
    finally:
        e.close()


def test_the_refused_total_of_the_last_scan_reaches_the_list_page(env):
    from service_helpers import FakeResult

    cookie, _ = sign_in(env)
    th, tp = env.token
    tok = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}
    assert "files not processed" not in get(env, "work", "/", {"Cookie": cookie}).text  # no scan yet: no note
    res = FakeResult()
    res.refused_total = 250
    FakeScanner.script = [res]
    assert raw(env.token, build("POST", "/events/scan", f"{th}:{tp}", tok, b"")).status == 200
    assert "250 files not processed" in get(env, "work", "/", {"Cookie": cookie}).text  # the real note of the list page


def test_an_idle_service_stops_at_once(tmp_path, monkeypatch):
    e = start_service(tmp_path, monkeypatch)
    assert get(e, "work", "/login", NAV).status == 200  # one request came and went: the count of running handlers is back to zero
    t0 = time.monotonic()
    e.run.stop()
    assert time.monotonic() - t0 < service.STOP_GRACE_S - 1  # it did not sit out the whole grace period


# ---- decide and Write never overlap (review 6d-c M4) -----------------------------------------------------------------------------------------------
def test_an_approval_cannot_slip_into_a_running_write(env, monkeypatch):
    from queue_helpers import GOOD_FIELDS, new_item

    from intake import exporter

    cookie, csrf = sign_in(env)
    first = new_item(env.s, "inv1")
    workqueue_decide = __import__("queue_helpers").approve
    workqueue_decide(env.s, first)
    second = new_item(env.s, "inv2", fields={**GOOD_FIELDS, "invoice_no": "INV-2002"})
    seen = review_page.export_token(env.s)
    real = exporter.export_pending
    blocked, outcome = [], []

    def approve_in_the_middle():
        wh, wp = env.work
        from test_review_http import decide_fields, post_decide

        outcome.append(post_decide(env, cookie, csrf, second.id, decide_fields(second)).status)

    def patched(s):
        t = threading.Thread(target=approve_in_the_middle)
        t.start()
        t.join(1.0)  # the approval is posted from inside the Write: it must wait for the lock
        blocked.append(t.is_alive())
        run = real(s)
        patched.thread = t
        return run

    monkeypatch.setattr(exporter, "export_pending", patched)
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": "pass" + "P" * 30, "preview": seen}, cookies=cookie)
    patched.thread.join(10)
    assert r.status == 200 and blocked == [True]  # the approval was held back while the Write ran
    assert outcome == [200]  # and went through right after
    text = exporter.csv_path(env.s).read_text(encoding="utf-8")
    assert "INV-1001" in text and "INV-2002" not in text  # the Write wrote what was previewed, not the invoice approved during it
    assert workqueue.get(env.s, second.id).state == "APPROVED"  # still waiting for the next Write


# ---- signals: a second press, a stuck start --------------------------------------------------------------------------------------------------------
def test_a_second_signal_raises_and_the_first_only_sets_the_flag():
    flag = service._StopFlag()
    saved = service._stop_on_signals(flag)
    try:
        signal.raise_signal(signal.SIGTERM)
        assert flag.requested is True
        with pytest.raises(KeyboardInterrupt):
            signal.raise_signal(signal.SIGTERM)  # the second press is not ignored
    finally:
        for n, old in saved:
            signal.signal(n, old)


def test_ctrl_c_twice_interrupts_a_stuck_start(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path, with_ledger=True)
    before = signal.getsignal(signal.SIGINT)  # whatever this process started with (a CI runner may ignore SIGINT)

    def stuck_start(*a, **k):
        signal.raise_signal(signal.SIGINT)  # the person presses once: the flag is set, start goes on
        signal.raise_signal(signal.SIGINT)  # and again: KeyboardInterrupt inside start
        raise AssertionError("not reached")

    monkeypatch.setattr(service, "start", stuck_start)
    try:
        code = service.serve(s)
    except KeyboardInterrupt:
        pytest.fail("the second Ctrl+C escaped serve() during a stuck start")
    assert code == 3  # "interrupted during start"
    assert signal.getsignal(signal.SIGINT) is before  # the handlers were put back


# ---- restart after a stop, loopback only -----------------------------------------------------------------------------------------------------------
def test_a_quick_restart_after_a_stop_does_not_fail_with_port_in_use(tmp_path, monkeypatch):
    from service_helpers import install_stand_ins
    from test_serve import free_port

    install_stand_ins(monkeypatch)
    monkeypatch.setattr(service.inbox, "Scanner", FakeScanner)
    s = settings_for_tests(tmp_path, with_ledger=True)
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=free_port()))
    first = service.start(s, hosts=HOSTS, limits=fast_limits())
    host, port = HOSTS["work"], s.service.port
    raw((host, port), build("GET", "/login", f"{host}:{port}", NAV))  # a finished connection leaves the address in TIME_WAIT
    first.stop()
    try:
        second = service.start(s, hosts=HOSTS, limits=fast_limits())  # the same addresses, at once
    except ConfigError as e:
        pytest.fail(f"the same addresses were refused straight after a stop: {e.code}")
    try:
        assert raw((host, port), build("GET", "/login", f"{host}:{port}", NAV)).status == 200
    finally:
        second.stop()


def test_a_listener_address_outside_loopback_is_refused_before_anything_starts(tmp_path, monkeypatch):
    from service_helpers import install_stand_ins

    install_stand_ins(monkeypatch)
    monkeypatch.setattr(service.inbox, "Scanner", FakeScanner)
    s = settings_for_tests(tmp_path, with_ledger=True)
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=0))
    for app in ("token", "work", "dash"):
        for bad in ("0.0.0.0", "192.168.1.5", "localhost", "::", "::1", "10.0.0.1", " 127.0.0.1"):
            try:
                run = service.start(s, hosts={**HOSTS, app: bad}, limits=fast_limits())
            except ConfigError as e:
                assert e.code == "bad_config" and "IPv4 loopback" in e.text, (app, bad)
                assert not (s.intake_home / "serve.lock").exists(), (app, bad)
                continue
            run.stop(grace_s=0.0)  # it started: stop it so the test leaves nothing behind, then fail
            pytest.fail(f"the {app} listener accepted {bad!r}")


# ---- failed sign-in and step-up put their code in the log ----------------------------------------------------------------------------------------------
def test_refused_sign_in_and_step_up_pages_log_their_code(env, capfd):
    from test_review_http import PASS, login

    cookie, csrf = sign_in(env)
    capfd.readouterr()
    assert login(env, {"passphrase": "wrong-guess"}).status == 401
    assert form_post(env, "/export", {"csrf": csrf, "passphrase": "wrong-guess"}, cookies=cookie).status == 401
    for _ in range(access.THROTTLE_FAILURES):
        form_post(env, "/export", {"csrf": csrf, "passphrase": "wrong-guess"}, cookies=cookie)
    assert form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie).status == 429
    log = capfd.readouterr().err
    assert "route=login_post status=401" in log and "code=login_failed" in log
    assert "route=export_run status=401" in log and "route=export_run status=429" in log and "code=too_many_attempts" in log
    assert " code=-" not in "".join(ln for ln in log.splitlines(True) if "status=401" in ln or "status=429" in ln)


# ---- the work lock times out (review 6d-d minor 6) ------------------------------------------------------------------------------------------------------
def test_a_decision_and_a_write_wait_for_the_work_lock_only_briefly(env, monkeypatch):
    from queue_helpers import new_item
    from test_review_http import PASS, approved, decide_fields, post_decide

    monkeypatch.setattr(service, "WORK_LOCK_WAIT_S", 0.05)
    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    approved(env, "inv2", fields={**__import__("queue_helpers").GOOD_FIELDS, "invoice_no": "INV-2002"})
    token = review_page.export_token(env.s)
    lock = env.run.shared.work_lock
    assert lock.acquire(timeout=1)  # somebody else holds the lock (a running Write or approval)
    try:
        r = post_decide(env, cookie, csrf, it.id, decide_fields(it))
        assert r.status == 503 and workqueue.get(env.s, it.id).state == "READY"  # not decided
        r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS, "preview": token}, cookies=cookie)
        assert r.status == 503  # not written
        assert not exporter_csv_exists(env)
    finally:
        lock.release()
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it))
    assert r.status == 200  # and it works again as soon as the lock is free


def exporter_csv_exists(env) -> bool:
    from intake import exporter

    return exporter.csv_path(env.s).exists()


# ---- start gives everything back when it is interrupted half way (review 6d-d part A minor 1) -----------------------------------------------------------
def test_an_interrupt_while_the_threads_start_gives_everything_back(tmp_path, monkeypatch):
    from service_helpers import install_stand_ins
    from test_serve import free_port

    install_stand_ins(monkeypatch)
    monkeypatch.setattr(service.inbox, "Scanner", FakeScanner)
    s = settings_for_tests(tmp_path, with_ledger=True)
    port = free_port()
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=port))

    def interrupted_begin(self):
        self.threads[0].start()  # one listener already serves, then the second Ctrl+C arrives
        raise KeyboardInterrupt

    monkeypatch.setattr(service.Running, "begin", interrupted_begin)
    with pytest.raises(KeyboardInterrupt):
        service.start(s, hosts=HOSTS, limits=fast_limits())
    assert not lockfile.is_held(s.intake_home / "serve.lock")  # the lock is back
    for host in HOSTS.values():
        with socket.socket() as probe:
            try:
                probe.bind((host, port))  # and every address is free again (nothing is left bound)
            except OSError:
                pytest.fail(f"{host}:{port} is still bound after the interrupted start")


def test_a_decision_after_a_container_clock_step_back_keeps_the_session(env, monkeypatch):
    """Evidence 6d-6 (Linux): the wall clock stepped back about 5 s between sign-in and a decision and the session ended (401). With the fixture clocks a
    step back of the system wall clock must not end a session of a test; the product rule itself (a real backward step ends it) is pinned by
    test_a_real_backward_wall_step_ends_the_session."""
    import time as _time

    from queue_helpers import new_item
    from test_review_http import decide_fields, post_decide

    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    real = _time.time
    monkeypatch.setattr(_time, "time", lambda: real() - 5.0)  # the system wall clock steps back 5 s
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it))
    assert r.status == 200, r.status
