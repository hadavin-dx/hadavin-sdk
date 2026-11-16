"""Test harness for the service (package 6d): a real ``service.start`` on test addresses and port 0 with the real pages (portal P1 ``ui.py``, package 6c),
a scripted scanner, and a raw-socket client that controls every byte of a request."""

from __future__ import annotations

import dataclasses
import re
import socket
import threading
import time
from dataclasses import dataclass, field

from conftest import settings_for_tests
from intake import access, content_code, inbox, review_page, service, ui

HOSTS = {"token": "127.0.0.1", "work": "127.0.0.21", "dash": "127.0.0.22"}
NAV = {"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document", "Sec-Fetch-Site": "none"}
STYLE = ui.STYLE_SHA256


def txt(s, code: str) -> str:
    """The plain-words text the service shows for a code, exactly as ``review_page.ERROR_TEXT`` has it (reason limits filled in)."""
    text = review_page.ERROR_TEXT["halted" if code == "budget_halted" else code]
    return text.format(reason_min_chars=s.review.reason_min_chars, reason_max_chars=s.review.reason_max_chars)


def install_stand_ins(monkeypatch) -> None:
    """Kept as a no-op for the tests that call it: the real ``ui`` and ``review_page`` (portal P1, package 6c) are merged, so nothing is replaced."""


class FakeResult:
    """Stands in for ``inbox.ScanResult`` (its ``as_json`` is package 6b's)."""

    refused_total = 0

    def as_json(self):
        return {"examined": 0, "new": [], "refused": [], "duplicates": 0, "remaining": 0}


class FakeScanner:
    """Stands in for ``inbox.Scanner`` (package 6b/6a): scripted outcomes, a call counter, an optional delay."""

    script: list = []
    calls = 0
    done = 0
    delay = 0.0
    lock = threading.Lock()

    def __init__(self, s, model):
        self.s, self.model = s, model

    def try_scan(self):
        with FakeScanner.lock:
            FakeScanner.calls += 1
        if FakeScanner.delay:
            import time

            time.sleep(FakeScanner.delay)
        with FakeScanner.lock:
            FakeScanner.done += 1
        if FakeScanner.script:
            out = FakeScanner.script.pop(0)
            if isinstance(out, BaseException):
                raise out
            return out
        return FakeResult()

    def running(self):
        return False

    def last_refused(self):
        return ()


def reset_scanner() -> None:
    FakeScanner.script, FakeScanner.calls, FakeScanner.done, FakeScanner.delay = [], 0, 0, 0.0


# ---- the running service --------------------------------------------------------------------------------------------------------------------
def fast_limits(**kw) -> service.Limits:
    base = {"conn_work": 16, "conn_dash": 12, "conn_token": 4, "read_s": 15, "handle_s": 30, "scan_s": 30, "socket_s": 10}
    base.update(kw)
    return service.Limits(**base)


@dataclass
class Env:
    s: object
    run: service.Running
    ports: dict
    tmp: object
    clients: list = field(default_factory=list)

    @property
    def work(self):
        return HOSTS["work"], self.ports["work"]

    @property
    def token(self):
        return HOSTS["token"], self.ports["token"]

    @property
    def dash(self):
        return HOSTS["dash"], self.ports["dash"]

    def secret(self, name: str) -> str:
        from conftest import fake_secret_values

        return fake_secret_values()[name]

    def close(self):
        self.run.stop()


def monotone_clocks() -> access.Clocks:
    """Real clocks whose wall clock never steps back. The product expires a session on ANY backward wall step (spec M-B, no tolerance), and a
    container's wall clock does step back a few seconds (evidence 6d-5, Linux), so every service test that signs in and requests later uses this."""
    lock, last = threading.Lock(), [0.0]

    def wall() -> float:
        with lock:
            last[0] = max(last[0], time.time())
            return last[0]

    return access.Clocks(time.monotonic, wall)


def start_service(tmp_path, monkeypatch, *, limits=None, hosts=None, port=0, with_scanner=True):
    install_stand_ins(monkeypatch)
    reset_scanner()
    s = settings_for_tests(tmp_path, with_ledger=True)
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=port))
    if with_scanner:
        monkeypatch.setattr(inbox, "Scanner", FakeScanner)
    lim = limits or fast_limits()
    run = service.start(s, hosts=hosts or HOSTS, limits=lim)
    run.shared.sessions._clocks = monotone_clocks()  # the stores are empty here; see monotone_clocks
    run.shared.pre._clocks = monotone_clocks()
    return Env(s, run, run.ports, tmp_path)


# ---- raw client -----------------------------------------------------------------------------------------------------------------------------
@dataclass
class Resp:
    status: int
    headers: list
    body: bytes

    def h(self, name: str) -> list[str]:
        return [v for k, v in self.headers if k.lower() == name.lower()]

    def first(self, name: str) -> str | None:
        v = self.h(name)
        return v[0] if v else None

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")


def parse_response(data: bytes) -> Resp:
    if not data:
        return Resp(0, [], b"")  # the server closed without a reply: status 0 fails the caller's assertion (not an IndexError)
    head, _, body = data.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n")
    status = int(lines[0].split(" ")[1])
    hs = [tuple(x.split(": ", 1)) for x in lines[1:]]
    return Resp(status, hs, body)


def raw(addr, data: bytes, *, timeout: float = 5.0, shutdown_write: bool = False) -> Resp:
    with socket.create_connection(addr, timeout=timeout) as c:
        c.sendall(data)
        if shutdown_write:
            c.shutdown(socket.SHUT_WR)
        buf = b""
        try:
            while True:
                chunk = c.recv(65536)
                if not chunk:
                    break
                buf += chunk
        except (TimeoutError, ConnectionError):
            pass
    return parse_response(buf)


def build(
    method: str, path: str, host: str, headers: dict | None = None, body: bytes | None = None, *, version: str = "HTTP/1.1", drop=()
) -> bytes:
    h: dict[str, str] = {"Host": host}
    h.update(headers or {})
    if body is not None and "Content-Length" not in h:
        h["Content-Length"] = str(len(body))
    for k in drop:
        h.pop(k, None)
    lines = [f"{method} {path} {version}"] + [f"{k}: {v}" for k, v in h.items()]
    return ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1") + (body or b"")


def get(env: Env, app: str, path: str, headers: dict | None = None, host: str | None = None) -> Resp:
    addr = getattr(env, app)
    return raw(addr, build("GET", path, host or f"{addr[0]}:{addr[1]}", headers))


def form_post(env: Env, path: str, fields: dict, *, cookies: str = "", extra: dict | None = None, app: str = "work") -> Resp:
    from urllib.parse import urlencode

    addr = getattr(env, app)
    if path == "/export" and "passphrase" in fields and "preview" not in fields:
        fields = {**fields, "preview": review_page.export_token(env.s)}  # what the page's hidden field carries: the list as it is now
    body = urlencode(fields).encode()
    hs = {
        "Origin": f"http://{addr[0]}:{addr[1]}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if cookies:
        hs["Cookie"] = cookies
    hs.update(extra or {})
    return raw(addr, build("POST", path, f"{addr[0]}:{addr[1]}", hs, body))


def cookie_of(resp: Resp, name: str) -> str | None:
    for v in resp.h("Set-Cookie"):
        if v.startswith(name + "="):
            val = v.split(";", 1)[0].split("=", 1)[1]
            return val or None
    return None


def csrf_in(resp: Resp) -> str:
    m = re.search(r'name="csrf" value="([^"]+)"', resp.text)
    assert m, resp.text
    return m.group(1)


def login_form(env: Env) -> tuple[Resp, str, str]:
    r = get(env, "work", "/login", NAV)
    assert r.status == 200, r.status
    return r, cookie_of(r, access.COOKIE_PRE), csrf_in(r)


def sign_in(env: Env, name: str = "ap-a", passphrase: str | None = None) -> tuple[str, str]:
    """Returns (cookie header for later requests, the session's csrf token)."""
    _, pre, tok = login_form(env)
    r = form_post(
        env,
        "/login",
        {"csrf": tok, "login": name, "passphrase": passphrase or env.secret("HADAVIN_APPROVER_PASSPHRASE")},
        cookies=f"{access.COOKIE_PRE}={pre}",
    )
    assert r.status == 303, (r.status, r.text)
    sid = cookie_of(r, access.COOKIE_SESSION)
    return f"{access.COOKIE_SESSION}={sid}", env.run.shared.sessions._by_sid[sid].csrf


def make_viewer(env: Env) -> tuple[str, str]:
    sess = env.run.shared.sessions.create(access.Login("vw-1", "viewer", "HADAVIN_APPROVER_PASSPHRASE"))
    return f"{access.COOKIE_SESSION}={sess.sid}", sess.csrf


def ready_item(env: Env, name: str = "inv"):
    from queue_helpers import new_item

    return new_item(env.s, name)


def code_of(item) -> str:
    return content_code.content_code(item)


def use_fake_clocks(env):
    """Give the running service's session store a clock the test moves by hand (call BEFORE signing in). Returns the clock: ``fc.advance(seconds)``."""
    from test_access import FakeClocks

    fc = FakeClocks()
    env.run.shared.sessions._clocks = fc.clocks()
    return fc
