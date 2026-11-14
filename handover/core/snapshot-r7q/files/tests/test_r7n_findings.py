"""R7N: tests for the r7k/r7l reviews' findings (the secret in an exception chain, the banner count, the unpinned
mail and server limits). Real classes, real loopback sockets, made-up data only (canary secrets built from parts).

Header table, one entry per finding: finding | planted mutant | what the test pins | why.

* N1 key leak (imap)
    mutant: imap_count._session: `raise ... from None` inside `except` keeps the imaplib error as `__context__`;
      the frame keeps `password`
    pins: no secret form in str/repr/args/chain/traceback/frame locals/logs/output after a refused login (NO,
      BAD, BYE, echo then hang-up, error in the middle of login, odd error type, quoted and backslash passwords)
    why: the server may echo the LOGIN line; imaplib puts that line in its error text

* N1 sweep
    mutant: every function that reads or sends a secret is routed through `lead_desk.scrub`
    pins: repo-wide guard (AST): a function that calls a secret reader, `.login`, builds an auth or key header,
      or opens a secret path must use `secret_boundary` or `scrub_error`; an alias import or a raw open does not
      hide it; a planted site fails
    why: one place for the job (`scrub.py`) and a test that finds a site that forgot it

* N1 smtp / live / crm
    mutant: smtp_provider send and dialogue, live_claude._post and crm_hubspot._once keep `__cause__` / frames
      with the password, token, key
    pins: same collector on each
    why: the AUTH PLAIN blob and the key live in frames

* M9-70, M9-71 (pass 10)
    mutant: run_real_check main: worst-case mails and calls not multiplied by the desk processes; +1; wrong
      variable; number printed is not the number checked
    pins: the real main prints n x per-process numbers and the limit check uses the same numbers
    why: the banner told the owner a smaller worst case than the run can spend

* M9-43 (pass 11, money)
    mutant: live_claude.qualify: reserve counts the question only / the body minus the system text / a wrong
      multiplier; the check scripts' cost lines add a guessed 600 bytes
    pins: the reserve equals worst_case_usd of the exact bytes sent (very long model name); both cost lines use
      the exact request bytes (one builder, `request_body`)
    why: the reserve and the banner must never be below what a call can cost

* N1 chain depth
    mutant: scrub.py: only the cause is followed, not the context of the context
    pins: a chain three deep made by implicit contexts is cut everywhere
    why: the secret may sit in the deepest error

* A (r7l Major 1, A14)
    mutant: smtp_provider._dialogue: `_expect(... "ehlo after tls")` removed
    pins: replies 220, 250, 220, 554 give SendRefused and no AUTH line goes out
    why: the password must not go to a server that refused EHLO after TLS

* B (r7l Major 2, S13R, A17, A19, A22)
    mutant: server.py `_drain` `if budget <= 0: break`; `_send_bytes` `if left <= 0`; `finish` and `_drain` byte
      caps
    pins: one test per mutant (settimeout(negative) raises ValueError, which `except OSError` does not catch)
    why: limits unpinned

* C (A9)
    mutant: smtp_provider.send: the `write_stats(... sent ...)` after a send removed
    pins: the stats file holds attempts and sent after a send
    why: the cap survives a restart
"""

from __future__ import annotations

import ast
import json
import logging
import re
import socket
import ssl
import sys
import threading
import time
import traceback
import types
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from demo_only.fake_smtp_tls import FAKE_PASSWORD, close_listener, make_cert
from lead_desk import imap_count, server
from lead_desk.contract import SendRefused
from lead_desk.imap_count import ImapCountError, ImapSettings, counts_by_key
from lead_desk.smtp_outbox import _Budget

HOST = "localhost"
REPO = Path(__file__).resolve().parent.parent
_THIS = Path(__file__).resolve()

# canary secrets built from parts (no literal secret in the file)
PLAIN = "pw-" + "canary-" + "plain-" + "0001"
QUOTED = "pw-" + 'q"' + "canary-" + "0002"
SLASHED = "pw-" + "b\\" + "canary-" + "0003"


def _forms(secret: str) -> list[str]:
    """Every shape in which a server or a library could repeat the secret."""
    import base64

    quoted = secret.replace("\\", "\\\\").replace('"', '\\"')
    return [
        secret,
        quoted,
        base64.b64encode(f"\0reader-user\0{secret}".encode()).decode(),
        base64.b64encode(secret.encode()).decode(),
        secret.encode().hex(),
    ]


def _chain(exc: BaseException | None) -> Iterator[BaseException]:
    seen: set[int] = set()
    todo = [exc]
    while todo:
        e = todo.pop()
        if e is None or id(e) in seen:
            continue
        seen.add(id(e))
        yield e
        todo += [e.__cause__, e.__context__]


def _texts(exc: BaseException) -> list[str]:
    """Every text a person, a log line or a program reading the exception could reach (a traceback hides a suppressed
    context, a program reading `__context__` does not; frame locals are read the way a debugger reads them)."""
    out: list[str] = []
    for e in _chain(exc):
        out += [str(e), repr(e), repr(e.args), repr(getattr(e, "__dict__", {}))]
        out.append("".join(traceback.format_exception(type(e), e, e.__traceback__)))
        for frame, _ in traceback.walk_tb(e.__traceback__):
            if Path(frame.f_code.co_filename).resolve() == _THIS:
                continue  # the test's own frames hold the canary on purpose
            out.append(repr(frame.f_locals))
    return out


def _assert_clean(secret: str, exc: BaseException, extra: list[str] | None = None) -> None:
    for text in [*_texts(exc), *(extra or [])]:
        for form in _forms(secret):
            assert form not in text, f"the secret is reachable ({form[:6]}...)"


def _catch(call: Callable[[], Any]) -> BaseException:
    try:
        call()
    except BaseException as e:  # the test reads what any caller could read
        return e
    raise AssertionError("no error was raised")


@pytest.fixture
def cert(tmp_path: Path) -> tuple[Path, Path]:
    made = make_cert(tmp_path, HOST)
    if made is None:
        pytest.skip("the openssl program is not installed, so no test certificate can be made")
    return made


# ---------------------------------------------------------------------------------------------------- N1: imap


class _EchoImap:
    """A TLS IMAP server that repeats the client's LOGIN line in its refusal (what a real server may do). It answers
    CAPABILITY the way a real server does (untagged CAPABILITY, then a tagged OK), because Python's imaplib asks first
    and gives up on a BAD answer BEFORE it sends LOGIN (r7n's first version never reached LOGIN, so the echo was never
    exercised: EV7N). `logins` counts the LOGIN lines this server read; the callers assert it is above 0."""

    def __init__(self, cert: Path, key: Path, mode: str) -> None:
        self.mode = mode
        self.logins = 0
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(cert), str(key))
        self._ctx = ctx
        self._srv = socket.socket()
        self._srv.bind(("127.0.0.1", 0))
        self._srv.listen(4)
        self.port = int(self._srv.getsockname()[1])
        self._stop = threading.Event()
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()

    def close(self) -> None:
        close_listener(self._srv, self._stop, self._th)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                c, _ = self._srv.accept()
            except OSError:
                return
            if self._stop.is_set():
                c.close()
                return
            threading.Thread(target=self._serve, args=(c,), daemon=True).start()

    def _serve(self, raw: socket.socket) -> None:
        try:
            conn = self._ctx.wrap_socket(raw, server_side=True)
            f = conn.makefile("rwb", buffering=0)
            f.write(b"* OK ready\r\n")
            while True:
                line = f.readline(65536).decode("utf-8", "replace").rstrip("\r\n")
                if not line:
                    return
                tag, _, rest = line.partition(" ")
                if rest.upper() == "CAPABILITY":
                    f.write(f"* CAPABILITY IMAP4rev1\r\n{tag} OK done\r\n".encode())
                    continue
                if rest.upper() == "LOGOUT":
                    f.write(f"* BYE bye\r\n{tag} OK done\r\n".encode())
                    return
                if rest.upper().startswith("LOGIN"):
                    self.logins += 1
                    if self.mode == "no":
                        f.write(f"{tag} NO [AUTHENTICATIONFAILED] {rest}\r\n".encode())
                    elif self.mode == "bad":
                        f.write(f"{tag} BAD {rest}\r\n".encode())
                    elif self.mode == "bye":
                        f.write(f"* BYE {rest}\r\n".encode())
                        return
                    elif self.mode == "untagged":
                        f.write(f"* NO {rest}\r\n{tag} NO login\r\n".encode())
                    elif self.mode == "echo_then_hangup":
                        f.write(f"* NO {rest}\r\n".encode())
                        return
                    elif self.mode == "garbage":
                        f.write(f"{rest} {rest}\r\n".encode())
                        return
                    continue
                f.write(f"{tag} BAD\r\n".encode())
        except (OSError, ValueError):
            return
        finally:
            raw.close()


def _client_ctx(cafile: Path) -> ssl.SSLContext:
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    c.load_verify_locations(cafile=str(cafile))
    c.minimum_version = ssl.TLSVersion.TLSv1_2
    return c


def _run_imap(
    tmp_path: Path, cert: tuple[Path, Path], mode: str, secret: str, *, login_reaches_server: bool = True
) -> BaseException:
    pw = tmp_path / "imap-pw.txt"
    pw.write_text(secret + "\n", encoding="utf-8")
    srv = _EchoImap(cert[0], cert[1], mode)
    try:
        s = ImapSettings(
            HOST,
            "reader-user",
            pw,
            port=srv.port,
            folders=("INBOX",),
            timeout_seconds=3.0,
            ssl_context=_client_ctx(cert[0]),
        )
        caught = _catch(lambda: counts_by_key(s, "RUN1-"))
    finally:
        srv.close()
    if login_reaches_server:  # not vacuous: the server really read the LOGIN line it then echoed
        assert srv.logins >= 1, f"the test server never read a LOGIN line (mode {mode})"
    return caught


@pytest.mark.parametrize("secret", [PLAIN, QUOTED, SLASHED], ids=["plain", "quoted", "backslash"])
@pytest.mark.parametrize("mode", ["no", "bad", "bye", "untagged", "echo_then_hangup", "garbage"])
def test_n1_a_refused_mailbox_login_leaves_the_password_nowhere(
    tmp_path: Path,
    cert: tuple[Path, Path],
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
    mode: str,
    secret: str,
) -> None:
    caplog.set_level(logging.DEBUG)
    exc = _run_imap(tmp_path, cert, mode, secret)
    assert isinstance(exc, ImapCountError)
    assert exc.__cause__ is None and exc.__context__ is None
    seen = capsys.readouterr()
    _assert_clean(secret, exc, [caplog.text, seen.out, seen.err, str(exc)])


@pytest.mark.parametrize(
    "boom",
    [lambda data: OSError(data), lambda data: RuntimeError(data), lambda data: ValueError(data)],
    ids=["os", "runtime", "value"],
)
def test_n1_an_error_in_the_middle_of_the_login_leaves_the_password_nowhere(
    tmp_path: Path, cert: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, boom: Callable[[str], BaseException]
) -> None:
    real_send = imap_count._BoundedImap.send

    def send(self: Any, data: bytes) -> None:
        if b" LOGIN " in data:
            raise boom(data.decode("utf-8", "replace"))
        real_send(self, data)

    monkeypatch.setattr(imap_count._BoundedImap, "send", send)
    exc = _run_imap(tmp_path, cert, "no", PLAIN, login_reaches_server=False)  # the client stops before the wire
    assert isinstance(exc, ImapCountError), type(exc)  # an odd error type becomes the fixed refusal too
    _assert_clean(PLAIN, exc)


def test_n1_imaplib_abort_during_login_leaves_the_password_nowhere(
    tmp_path: Path, cert: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    import imaplib

    def login(self: Any, user: str, password: str) -> None:
        raise imaplib.IMAP4.abort(f"command: LOGIN {user} {password}")

    monkeypatch.setattr(imaplib.IMAP4, "login", login)
    exc = _run_imap(tmp_path, cert, "no", PLAIN, login_reaches_server=False)  # login is replaced: nothing is sent
    assert isinstance(exc, ImapCountError)
    _assert_clean(PLAIN, exc)


# --------------------------------------------------------------------------------------- N1: smtp, live, crm


def _smtp_with_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_with: str) -> BaseException:
    from test_r7f_findings import _provider
    from test_smtp_outbox import SUBJECT, TO

    box = _provider(tmp_path, 9, ssl.create_default_context())
    monkeypatch.setattr(box, "_connect", lambda b: types.SimpleNamespace(close=lambda: None))

    def command(conn: Any, budget: Any, buf: Any, text: str) -> int:
        if text.startswith("AUTH PLAIN "):
            raise OSError(f"server echoed: {text}")
        return 250

    from lead_desk import smtp_provider

    monkeypatch.setattr(smtp_provider, "_command", command)
    monkeypatch.setattr(smtp_provider, "_read_reply", lambda *a, **k: 220)
    monkeypatch.setattr(box, "_wrap", lambda sock, b: sock)
    return _catch(lambda: box.send("RUN1-L-001", TO, SUBJECT, "Hi", 2.0))


def test_n1_smtp_login_error_leaves_the_password_and_the_auth_blob_nowhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exc = _smtp_with_failure(tmp_path, monkeypatch, "auth")
    assert isinstance(exc, Exception) and exc.__cause__ is None and exc.__context__ is None
    _assert_clean(FAKE_PASSWORD, exc)


def test_n1_a_model_key_is_in_no_error_after_a_failed_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from lead_desk import live_claude

    key = "sk-" + "canary-" + "key-0004"
    q: Any = object.__new__(live_claude.LiveQualifier)
    q.s = types.SimpleNamespace(timeout_seconds=2.0, base_url="http://127.0.0.1:9", api_version="x")

    def opener(req: Any, timeout: float | None = None) -> Any:
        raise RuntimeError(f"request headers {dict(req.header_items())}")

    monkeypatch.setattr(live_claude._OPENER, "open", opener)
    exc = _catch(lambda: q._post(b"{}", key))
    assert exc.__cause__ is None and exc.__context__ is None
    _assert_clean(key, exc)


def test_n1_a_crm_token_is_in_no_error_after_a_failed_call(monkeypatch: pytest.MonkeyPatch) -> None:
    from lead_desk import crm_hubspot

    token = "tok-" + "canary-" + "0005"
    crm: Any = object.__new__(crm_hubspot.HubspotCrm)
    crm.s = types.SimpleNamespace(timeout_seconds=2.0, base_url="http://127.0.0.1:9")

    def request(req: Any, left: float, deadline: float) -> Any:
        raise RuntimeError("echo " + req.get_header("Authorization"))

    monkeypatch.setattr(crm, "_request", request, raising=False)
    exc = _catch(lambda: crm._once("GET", "/x", None, time.monotonic() + 5, token))
    assert exc.__cause__ is None and exc.__context__ is None
    _assert_clean(token, exc)


def test_n1_a_secret_file_refusal_holds_no_chain(tmp_path: Path) -> None:
    from lead_desk.regfile import FileRefused, read_secret_line

    bad = tmp_path / "k.txt"
    bad.write_bytes(b"\xff\xfe" + PLAIN.encode())
    exc = _catch(lambda: read_secret_line(bad, "key", "key"))
    assert isinstance(exc, FileRefused) and exc.__context__ is None and exc.__cause__ is None
    _assert_clean(PLAIN, exc, [str(tmp_path)])


# ------------------------------------------------------------------------------------ N1: the repo-wide guard

_READERS = {"read_secret_line", "read_secret_file", "_read_secret_text", "_read_key"}
_KEY_METHOD = "_key"  # `self._key()` reads the vendor key; the module function `_key(name)` of tools/ does not
_LOGINS = {"login", "authenticate", "login_cram_md5"}  # imaplib / smtplib ways to send a secret to a server
_AUTH_TEXT = re.compile(
    r"^(AUTH |Bearer |Basic )|x-api-key|x-n8n-api-key|x-auth-token|^api-key$|proxy-authorization|^authorization$",
    re.IGNORECASE,
)
_SECRET_PATH = re.compile(
    r"password|passwd|passphrase|secret|key_file|token|api_key|pw_file|credential|private_key", re.IGNORECASE
)
_OPENERS = {"open", "open_regular", "read_text", "read_bytes"}
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def _call_name(node: ast.Call, aliases: dict[str, str]) -> str:
    """The name a call goes by: `f(...)`, `m.f(...)`, `getattr(m, "f")(...)`; an alias gives the name it stands for."""
    f = node.func
    if isinstance(f, ast.Name):
        return aliases.get(f.id, f.id)
    if isinstance(f, ast.Attribute):
        return f.attr
    if (
        isinstance(f, ast.Call)
        and isinstance(f.func, ast.Name)
        and f.func.id == "getattr"
        and len(f.args) >= 2  # noqa: PLR2004
        and isinstance(f.args[1], ast.Constant)
        and isinstance(f.args[1].value, str)
    ):
        return f.args[1].value
    return ""


def _touches_secret(fn: ast.AST, aliases: dict[str, str]) -> bool:
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            name = _call_name(n, aliases)
            if name in _READERS or name in _LOGINS:
                return True
            if name == _KEY_METHOD and isinstance(n.func, ast.Attribute) and not n.args:
                return True
            if name in _OPENERS and any(
                _SECRET_PATH.search(ast.unparse(a)) for a in [*n.args, *[k.value for k in n.keywords]]
            ):
                return True
            if (
                isinstance(n.func, ast.Attribute)
                and name in _OPENERS
                and _SECRET_PATH.search(ast.unparse(n.func.value))
            ):
                return True
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and _AUTH_TEXT.search(n.value):
            return True
    return False


def _live_calls(fn: ast.AST) -> Iterator[ast.Call]:
    """The calls in `fn` that are not under an `if` with a constant false test (`if False:` is dead code)."""

    def walk(node: ast.AST) -> Iterator[ast.Call]:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Constant) and not node.test.value:
            for child in node.orelse:
                yield from walk(child)
            return
        if isinstance(node, ast.Call):
            yield node
        for child in ast.iter_child_nodes(node):
            yield from walk(child)

    yield from walk(fn)


def _guarded(fn: ast.AST, defined_here: set[str]) -> bool:
    """True for a function with the decorator `secret_boundary` or a live call of `scrub_error`. A function of the same
    name defined in the file under test does not count (it is not the one in lead_desk.scrub)."""
    if "secret_boundary" not in defined_here:
        for d in getattr(fn, "decorator_list", []):
            target = d.func if isinstance(d, ast.Call) else d
            if (isinstance(target, ast.Name) and target.id == "secret_boundary") or (
                isinstance(target, ast.Attribute) and target.attr == "secret_boundary"
            ):
                return True
    return "scrub_error" not in defined_here and any(_call_name(c, {}) == "scrub_error" for c in _live_calls(fn))


def _aliases(tree: ast.AST) -> dict[str, str]:
    """`import x as y` and `y = x` for a name or a dotted name, followed to the name last used."""
    out: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.asname:
                    out[a.asname] = a.name
        elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = n.value
            if isinstance(v, ast.Name):
                out[n.targets[0].id] = out.get(v.id, v.id)
            elif isinstance(v, ast.Attribute):
                out[n.targets[0].id] = v.attr
    return out


def _sites(source: str) -> tuple[list[str], list[str]]:
    """(unguarded, guarded) names of the outermost functions in `source` that touch a secret."""
    tree = ast.parse(source)
    aliases = _aliases(tree)
    defined_here = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    bad: list[str] = []
    good: list[str] = []

    def visit(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _FUNCTIONS) and _touches_secret(child, aliases):
                (good if _guarded(child, defined_here) else bad).append(getattr(child, "name", "<lambda>"))
            else:
                visit(child)  # a function that touches nothing may hold an inner one that does

    visit(tree)
    return bad, good


def unguarded_sites(source: str) -> list[str]:
    """Names of functions in `source` that touch a secret and neither use `secret_boundary` nor call `scrub_error`.
    A TRIPWIRE, not a proof: it reads names, so a new way of touching a secret it does not know is not seen."""
    return _sites(source)[0]


def guarded_sites(source: str) -> list[str]:
    return _sites(source)[1]


def _guard_files() -> list[Path]:
    """Every Python file of the places that run with a secret, in sub-packages too."""
    return [
        p
        for top in ("src/lead_desk", "scripts", "load_tools", "tools")
        for p in sorted((REPO / top).rglob("*.py"))
        if "__pycache__" not in p.parts
    ]


def test_n1_every_function_that_touches_a_secret_uses_the_one_scrub_helper() -> None:
    assert (REPO / "src" / "lead_desk" / "scrub.py").is_file()
    found = {p.relative_to(REPO).as_posix(): unguarded_sites(p.read_text(encoding="utf-8")) for p in _guard_files()}
    assert {k: v for k, v in found.items() if v} == {}


def test_n1_the_guard_finds_a_planted_site() -> None:
    plain = "def f(m, p):\n    m.login('u', p)\n"
    assert unguarded_sites(plain) == ["f"]
    ok = "@secret_boundary(E, 'x')\ndef f(m, p):\n    m.login('u', p)\n"
    assert unguarded_sites(ok) == []
    ok2 = "\n".join(
        [
            "def f(m, p):",
            "    try" + ":",
            "        m.login('u', p)",
            "    except Exception as e" + ":",
            "        scrub_error(e)",
            "        raise",
            "",
        ]
    )
    assert unguarded_sites(ok2) == []
    alias = "from lead_desk.regfile import read_secret_file as rsf\ndef g(p):\n    return rsf(p)\n"
    assert unguarded_sites(alias) == ["g"]
    raw = "def h(cfg):\n    return open(cfg.password_file).read()\n"
    assert unguarded_sites(raw) == ["h"]
    raw2 = "def h(cfg):\n    return cfg.key_file.read_text()\n"
    assert unguarded_sites(raw2) == ["h"]
    hdr = "def h(k):\n    return {'Authorization': 'Bearer ' + k}\n"
    assert unguarded_sites(hdr) == ["h"]
    unrelated = "def h(a):\n    return open(a.report_file).read()\n"
    assert unguarded_sites(unrelated) == []


def test_n1_scrub_error_drops_cause_context_and_frame_locals() -> None:
    from lead_desk.scrub import scrub_error

    def inner() -> None:
        secret_local = PLAIN
        raise RuntimeError(secret_local)

    try:
        try:
            inner()
        except RuntimeError as first:
            raise ValueError("fixed") from first
    except ValueError as outer:
        scrub_error(outer)
        assert outer.__cause__ is None and outer.__context__ is None and outer.__suppress_context__
        for e in _chain(outer):
            for frame, _ in traceback.walk_tb(e.__traceback__):
                if frame.f_code.co_name == "inner":
                    assert "secret_local" not in frame.f_locals


def test_n1_secret_boundary_turns_an_odd_error_into_the_fixed_text_and_keeps_ours() -> None:
    from lead_desk.scrub import secret_boundary

    @secret_boundary(ImapCountError, "fixed text")
    def odd() -> None:
        raise RuntimeError(PLAIN)

    @secret_boundary(ImapCountError, "fixed text")
    def ours() -> None:
        raise SendRefused("a fixed refusal")

    e = _catch(odd)
    assert type(e) is ImapCountError and str(e) == "fixed text" and e.__context__ is None and e.__cause__ is None
    _assert_clean(PLAIN, e)
    e2 = _catch(ours)
    assert type(e2) is SendRefused and str(e2) == "a fixed refusal"


# ------------------------------------------------------------------------- M9-70, M9-71: the banner of the real check


def _banner_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, **over: str
) -> str:
    """The real `main` up to the Start question, answered n; returns what it printed."""
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import run_real_check as rrc
    finally:
        sys.path.pop(0)
    from test_real_check_dry import _valid_config

    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert rrc.main(["--config", str(_valid_config(tmp_path, **over))]) == rrc.EXIT_STOPPED
    return capsys.readouterr().out


@pytest.mark.parametrize(("calls", "sends", "readback"), [(7, 3, 6), (11, 5, 9)])
def test_m9_70_71_the_banner_counts_every_desk_process(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    calls: int,
    sends: int,
    readback: int,
) -> None:
    """Two desk processes run (the second after the crash) and each counts its own caps in memory: the worst case the
    owner reads is two times the per-process figure. Different numbers for calls, mails and read-back, so a wrong
    variable, a missing factor or a +1 cannot give the same line."""
    out = _banner_lines(
        tmp_path,
        capsys,
        monkeypatch,
        DESK_HUBSPOT_MAX_CALLS=str(calls),
        DESK_SMTPP_MAX_SENDS=str(sends),
        REAL_HUBSPOT_READBACK_MAX_CALLS=str(readback),
    )
    assert "desk processes: 2 (one crash)" in out
    assert f"worst case HubSpot calls: {calls * 2} by the desk + {readback} read-back = {calls * 2 + readback}\n" in out
    assert f"worst case mails: {sends * 2}, all to your own inboxes" in out


# --------------------------------------------------------------------------------- r7l reviewer killers (A, B, C)


def test_a14_ehlo_after_starttls_refused_stops_before_the_password(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_r7l_findings import WIRE, _prov_on, _Rec

    sock: Any = _Rec([b"220 ok\r\n", b"250 ok\r\n", b"220 go\r\n", b"554 no\r\n", b"235 ok\r\n", b"250 ok\r\n"])
    box = _prov_on(tmp_path, monkeypatch, sock, "starttls")
    with pytest.raises(SendRefused):
        dialogue: Any = box._dialogue
        dialogue(sock, _Budget(2.0), FAKE_PASSWORD, "inbox-a@example.test", WIRE)
    assert not any(d.startswith(b"AUTH") for d in sock.sent())


def test_s13r_a_byte_after_the_total_limit_ends_the_drain_quietly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "DRAIN_TOTAL_SECONDS", 0.2)
    a, b = socket.socketpair()

    class R:
        timed_out_in = "x"

        def arm(self, *x: Any) -> None:
            pass

    class F:
        def read1(self, n: int) -> bytes:
            time.sleep(0.3)
            return b"x"

    h = types.SimpleNamespace(_reader=R(), connection=a, rfile=F())
    drain: Any = server._Handler._drain
    drain(h, 100)
    assert h._reader.timed_out_in == ""
    a.close()
    b.close()


def test_a17_a_reply_whose_headers_used_up_the_limit_writes_no_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "REPLY_WRITE_TIMEOUT_SECONDS", 0.2)
    a, b = socket.socketpair()
    wrote: list[bytes] = []

    class W:
        def write(self, data: bytes) -> None:
            if data.startswith(b"HTTP/"):
                time.sleep(0.4)
            else:
                wrote.append(data)

        def flush(self) -> None:
            pass

    h: Any = object.__new__(server._Handler)
    h.request_version, h.command, h.requestline = "HTTP/1.0", "GET", "GET / HTTP/1.0"
    h.connection = a
    h.wfile = W()
    h.close_connection = False
    h._slot = types.SimpleNamespace(release=lambda: None)
    h._send_bytes(200, b"{}", "application/json")
    assert wrote == []
    a.close()
    b.close()


def test_a19_finish_stops_at_the_byte_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "DRAIN_TOTAL_SECONDS", 0.5)
    calls: list[int] = []

    class C:
        def settimeout(self, t: Any) -> None:
            pass

        def shutdown(self, h: Any) -> None:
            pass

        def recv(self, n: int) -> bytes:
            calls.append(n)
            return b"x" * n

    h: Any = object.__new__(server._Handler)
    h.connection = C()
    h.wfile = types.SimpleNamespace(flush=lambda: None, close=lambda: None, closed=True)
    h.rfile = types.SimpleNamespace(close=lambda: None, closed=True)
    h.finish()
    assert sum(calls) <= server.DRAIN_MAX_BYTES + 65536 and len(calls) < 1000


def test_a22_drain_stops_at_the_byte_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server, "DRAIN_TOTAL_SECONDS", 0.5)
    a, b = socket.socketpair()
    got: list[int] = []

    class R:
        timed_out_in = ""

        def arm(self, *x: Any) -> None:
            pass

    class F:
        def read1(self, n: int) -> bytes:
            got.append(n)
            return b"x" * n

    h = types.SimpleNamespace(_reader=R(), connection=a, rfile=F())
    drain: Any = server._Handler._drain
    drain(h, 10**9)
    assert sum(got) <= server.DRAIN_MAX_BYTES + 65536 and len(got) < 1000
    a.close()
    b.close()


def test_a9_the_stats_file_holds_sent_after_a_send(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from test_r7f_findings import _provider
    from test_smtp_outbox import SUBJECT, TO

    stats = tmp_path / "stats.json"
    box = _provider(tmp_path, 9, ssl.create_default_context(), stats_file=stats)
    monkeypatch.setattr(box, "_connect", lambda b: types.SimpleNamespace(close=lambda: None))
    monkeypatch.setattr(box, "_dialogue", lambda *a: None)
    assert box.send("RUN1-L-001", TO, SUBJECT, "Hi", 2.0) == "SENT"
    assert json.loads(stats.read_text(encoding="utf-8")) == {"attempts": 1, "sent": 1}


def test_n1_scrub_error_cuts_a_chain_three_deep_made_by_implicit_contexts() -> None:
    from lead_desk.scrub import scrub_error

    held: list[BaseException] = []

    def deep(password: str) -> None:
        raise RuntimeError(password)

    def boom() -> None:
        try:
            try:
                deep(PLAIN)
            except RuntimeError as inner:
                held.append(inner)  # someone else may still hold the inner error
                raise OSError("second") from None
        except OSError as middle:
            held.append(middle)
            raise ValueError("third") from None

    exc = _catch(boom)
    assert exc.__context__ is not None and exc.__context__.__context__ is not None  # the chain exists (a context)
    scrub_error(exc)
    assert all(e.__context__ is None and e.__cause__ is None for e in _chain(exc))
    # the walk follows the context too: an inner error that is held elsewhere is cut and its frames are emptied
    assert all(e.__context__ is None for e in held)
    inner_frames = []
    tb = held[0].__traceback__
    while tb is not None:
        inner_frames.append(tb.tb_frame)
        tb = tb.tb_next
    assert not any("password" in f.f_locals for f in inner_frames)
    _assert_clean(PLAIN, exc)


# ------------------------------------------------------------------ M9-43: the reserve and the cost lines


def _exact_body_len(model: str, max_tokens: int, effort: str, question: str) -> int:
    """Written out here, not taken from the program: the JSON the call sends."""
    from lead_desk.live_claude import SYSTEM_TEXT

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": SYSTEM_TEXT,
        "output_config": {"effort": effort},
        "messages": [{"role": "user", "content": question}],
    }
    return len(json.dumps(body).encode("utf-8"))


def test_m9_43_the_reserve_counts_every_byte_of_the_request_body(tmp_path: Path) -> None:
    from decimal import Decimal

    from lead_desk.config import LiveSettings
    from lead_desk.live_claude import LiveQualifier, worst_case_usd

    key = tmp_path / "k.txt"
    key.write_text("made-up-key-for-tests-only\n", encoding="utf-8")
    s = LiveSettings(
        model="m" * 700,  # a long model name makes the body far larger than the question
        key_file=key,
        price_in_per_mtok=Decimal("1000"),
        price_out_per_mtok=Decimal("5000"),
        price_date="2026-01-01",
        cap_run_usd=Decimal("1000"),
        cap_total_usd=Decimal("2000"),
        ledger_path=tmp_path / "ledger.jsonl",
        run_id="run-a",
        timeout_seconds=2.0,
    )
    q = LiveQualifier(s)
    reserved: list[Decimal] = []
    sent: list[int] = []
    real_reserve = q.ledger.reserve

    def reserve(settings: Any, usd: Decimal, wait_seconds: float | None = None) -> str:
        reserved.append(usd)
        return real_reserve(settings, usd, wait_seconds)

    def post(body: bytes, k: str, timeout: float) -> dict[str, Any]:
        sent.append(len(body))
        return {"content": [{"type": "text", "text": "hot"}], "usage": {"input_tokens": 1, "output_tokens": 1}}

    qa: Any = q
    qa.ledger.reserve = reserve
    qa._post = post
    assert q.qualify("L000000000001", "made.up.1@example.test") == "hot"
    question = "lead id: L000000000001\nemail: made.up.1@example.test\nAnswer: hot, warm or cold?"
    exact = _exact_body_len(s.model, s.max_tokens, s.effort, question)
    assert sent == [exact] and exact > len(question) + 700
    assert reserved == [worst_case_usd(s, exact)]


def test_m9_43_the_cost_lines_of_both_check_scripts_use_the_exact_request_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from decimal import ROUND_CEILING, Decimal

    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import run_live_check as rlc
        import run_real_check as rrc
    finally:
        sys.path.pop(0)
    from test_real_check_dry import _valid_config

    from lead_desk.constants import LIVE_DEFAULT_EFFORT, LIVE_DEFAULT_MAX_TOKENS

    model = "m" * 800
    key = tmp_path / "k"
    key.write_text("made-up-key-for-tests-only\n", encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    # run_live_check: the longest question of 2 leads, 1 run, one model at US$100 in and US$10 out per million
    code = rlc.main(
        ["--key-file", str(key), "--ledger", str(tmp_path / "led"), "--cap-run", "100", "--cap-total", "200",
         "--price-date", "2026-01-01", "--model", f"{model}=100,10", "--leads", "2", "--runs", "1"]
    )  # fmt: skip
    out = capsys.readouterr().out
    assert code == rlc.EXIT_STOPPED, out
    longest = max(
        _exact_body_len(
            model,
            LIVE_DEFAULT_MAX_TOKENS,
            LIVE_DEFAULT_EFFORT,
            f"lead id: {lid}\nemail: {em}\nAnswer: hot, warm or cold?",
        )
        for lid, em in rlc._emails(2)
    )
    one = (Decimal(100) * longest + Decimal(10) * LIVE_DEFAULT_MAX_TOKENS) / 1_000_000 * 2
    assert f"US${one.quantize(Decimal('0.0001'), rounding=ROUND_CEILING)} (caps" in out
    # run_real_check: the same, with the model name from the config
    live = {
        "DESK_LIVE_MODEL": model,
        "DESK_LIVE_KEY_FILE": str(key),
        "DESK_LIVE_PRICE_IN_PER_MTOK": "100",
        "DESK_LIVE_PRICE_OUT_PER_MTOK": "10",
        "DESK_LIVE_PRICE_DATE": "2026-01-01",
        "DESK_LIVE_CAP_RUN_USD": "50",
        "DESK_LIVE_CAP_TOTAL_USD": "60",
        "DESK_LIVE_LEDGER_PATH": str(tmp_path / "ledger"),
        "DESK_LIVE_RUN_ID": "r1",
    }
    monkeypatch.setattr(rrc, "new_tag", lambda: "rabcdef")  # r7q: the banner counts the addresses the run will send
    assert rrc.main(["--config", str(_valid_config(tmp_path, **live)), "--live-model"]) == rrc.EXIT_STOPPED
    banner = capsys.readouterr().out
    found = re.search(r"people: (\d+) \+ a twin", banner)
    assert found is not None
    persons = int(found.group(1))
    half = persons // 2
    addresses = [f"rabcdef-p{i}@{rrc.EMAIL_DOMAIN}" for i in range(1, persons + 1)]
    addresses.append(f"rabcdef-p{half}.second@{rrc.EMAIL_DOMAIN}")  # the twin: the longest
    body = max(
        _exact_body_len(
            model,
            LIVE_DEFAULT_MAX_TOKENS,
            LIVE_DEFAULT_EFFORT,
            f"lead id: L000000000000\nemail: {em}\nAnswer: hot, warm or cold?",
        )
        for em in addresses
    )
    cost = (Decimal(100) * body + Decimal(10) * LIVE_DEFAULT_MAX_TOKENS) / 1_000_000 * 3 * (persons + 3) * 2
    assert f"worst case model cost: US${cost:.4f} " in banner


# ------------------------------------------------------------------ M9-54: one path segment per email


@pytest.mark.parametrize(
    ("email", "segment"),
    [
        ("a/b@x.test", "a%2Fb%40x.test"),
        ("../x@y.test", "..%2Fx%40y.test"),
        ("q?r=1#f@x.test", "q%3Fr%3D1%23f%40x.test"),
    ],
)
def test_m9_54_set_fields_sends_the_email_as_exactly_one_path_segment(tmp_path: Path, email: str, segment: str) -> None:
    """Mutant M54: `quote(email)` (safe='/') leaves '/' in the path, so the email adds path parts."""
    from support import HOST, stop_within

    from demo_only import fake_hubspot as fh
    from lead_desk.crm_hubspot import CrmRefused, HubspotCrm, HubspotSettings

    key_file = tmp_path / "key.txt"
    key_file.write_text("k" + "e" * 15 + "-for-tests-0002\n", encoding="utf-8")
    state = fh.HubspotState("k" + "e" * 15 + "-for-tests-0002", "ok")
    srv, th, url = fh.serve(state, HOST)
    try:
        crm = HubspotCrm(HubspotSettings(key_file, 50, base_url=url, timeout_seconds=2.0, allow_any_base_url=True))
        with pytest.raises(CrmRefused):  # no such contact: the fake answers 404, which is not the point here
            crm.set_fields("L1", email, "", "NEW")
    finally:
        stop_within(lambda: fh.stop(srv, th, state), "fake HubSpot server")
    patches = [p for m, p in state.calls if m == "PATCH"]
    assert patches == [f"/crm/v3/objects/contacts/{segment}?idProperty=email"]


# ------------------------------------------------------------------ M9-17 and M9-55 (pass 11)


@pytest.mark.parametrize("to", ["é@x.test", "a@x.test".replace("x", "х"), "ａ@x.test"])
def test_m9_17_send_refuses_a_non_ascii_recipient_before_the_password_or_any_socket(tmp_path: Path, to: str) -> None:
    """Mutant M17: the `isascii()` test is dropped from the recipient check in SmtpProviderOutbox.send."""
    from lead_desk.contract import SendRefused
    from lead_desk.smtp_provider import ProviderSettings, SmtpProviderOutbox

    settings = ProviderSettings(
        host="127.0.0.1",
        port=1,
        user="u",
        password_file=tmp_path / "no-such-password-file",  # a password read would fail with another message
        mail_from="sender@example.test",
        recipients=("in1@example.test",),
        max_sends=3,
        security="ssl",
        timeout_seconds=1.0,
    )
    with pytest.raises(SendRefused, match="recipient is not a plain address"):
        SmtpProviderOutbox(settings).send("RUN1-L1", to, "subject", "body", 1.0)


@pytest.mark.parametrize("word", ["no", "0", "false", "y", "off", "yes please", "1"])
def test_m9_55_only_the_word_yes_switches_the_vendor_host_check_off(word: str) -> None:
    """Mutant M55: any non-empty text in DESK_HUBSPOT_ALLOW_ANY_BASE_URL switches the check off."""
    from lead_desk.crm_hubspot import HubspotSettings

    env = {
        "DESK_HUBSPOT_KEY_FILE": "key.txt",
        "DESK_HUBSPOT_MAX_CALLS": "5",
        "DESK_HUBSPOT_BASE_URL": "https://example.test",
        "DESK_HUBSPOT_ALLOW_ANY_BASE_URL": word,
    }
    with pytest.raises(ValueError):  # the vendor-domain refusal (SettingRefused is a ValueError)
        HubspotSettings.from_env(env)
    env["DESK_HUBSPOT_ALLOW_ANY_BASE_URL"] = " YeS "
    assert HubspotSettings.from_env(env).allow_any_base_url is True


# ---------------------------------------------------------------- order pollution: k15 fakes leaked into the next test


def test_the_driver_tests_leave_no_fake_flags_behind_for_a_later_test_file() -> None:
    """On r7m the k15 tests (tests/test_r7k_findings.py) left a fake error counter in `load_driver`, so a later
    `test_real_check_dry.py` test died with `no attribute 'get_lock'`. Both files run in one process, in both orders."""
    import os
    import sys

    from support import run_program

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    k15 = "tests/test_r7k_findings.py"
    dry = "tests/test_real_check_dry.py"
    for first, second in ((k15, dry), (dry, k15)):
        done = run_program(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", first, second]
            + ["-k", "k15 or dry_fakes_run_end_to_end"],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
        assert done.returncode == 0, (first, second, done.stdout[-1500:])
        assert "get_lock" not in done.stdout


# ---------------------------------------------------------------- M9-81: a value that holds or overlaps another


def _scrub() -> Any:
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import run_real_check as rrc
    finally:
        sys.path.remove(str(REPO / "scripts"))
    return rrc.scrub


@pytest.mark.parametrize(
    ("text", "values", "want"),
    [
        ("x abcdEFGH1234 y", ["abcd", "abcdEFGH1234"], "x <value> y"),
        ("x abcdEFGH1234 y", ["abcdEFGH1234", "abcd"], "x <value> y"),
        ("x abcd y wxyz z", ["abcd", "wxyz"], "x <value> y <value> z"),  # equal length: both hidden
        ("k abcdefghijkl k", ["abcdefgh", "efghijkl"], "k <value> k"),  # overlap, not holding: no tail left
        ("k abcdefghijkl k", ["efghijkl", "abcdefgh"], "k <value> k"),
        ("no value here", ["abcd"], "no value here"),
        ("abc", ["abc"], "abc"),  # under 4 characters: not a value
    ],
)
def test_m9_81_scrub_hides_a_value_that_holds_or_overlaps_another(text: str, values: list[str], want: str) -> None:
    scrub = _scrub()
    env = {f"N{i}": v for i, v in enumerate(values)}
    assert scrub(text, env) == want
    assert scrub(text, dict(reversed(list(env.items())))) == want


# ------------------------------------------------------------------ M9-13: a zero time budget is refused everywhere


def test_m9_13_every_time_budget_setting_refuses_zero_and_takes_a_small_positive_number(tmp_path: Path) -> None:
    from decimal import Decimal

    from lead_desk.crm_hubspot import HubspotSettings
    from lead_desk.envnum import SettingRefused
    from lead_desk.imap_count import ImapSettings
    from lead_desk.live_claude import LiveSettings
    from lead_desk.smtp_outbox import SmtpSettings
    from lead_desk.smtp_provider import ProviderSettings

    pw = tmp_path / "pw"
    base_provider = {
        "host": "127.0.0.1",
        "port": 465,
        "user": "u",
        "password_file": pw,
        "mail_from": "a@x.test",
        "recipients": ("b@x.test",),
        "max_sends": 1,
    }

    def live(t: float) -> LiveSettings:
        return LiveSettings(
            model="m" * 5,
            key_file=pw,
            price_in_per_mtok=Decimal(1),
            price_out_per_mtok=Decimal(1),
            price_date="2026-11-04",
            cap_run_usd=Decimal(1),
            cap_total_usd=Decimal(1),
            ledger_path=tmp_path / "ledger",
            run_id="R1",
            timeout_seconds=t,
        )

    makers: dict[str, Any] = {
        "smtp provider": lambda t: ProviderSettings(**base_provider, timeout_seconds=t),
        "smtp outbox": lambda t: SmtpSettings(timeout_seconds=t),
        "hubspot": lambda t: HubspotSettings(pw, 1, timeout_seconds=t),
        "imap step": lambda t: ImapSettings("h.test", "u", pw, timeout_seconds=t),
        "imap total": lambda t: ImapSettings("h.test", "u", pw, total_seconds=t),
        "live model": live,
    }
    for name, make in makers.items():
        for bad in (0, 0.0, -1.0, float("nan"), float("inf")):
            with pytest.raises((ValueError, SettingRefused)):
                make(bad)
        make(0.001)  # accepted
    env_provider = {
        "DESK_SMTPP_HOST": "127.0.0.1",
        "DESK_SMTPP_USER": "u",
        "DESK_SMTPP_PASSWORD_FILE": str(pw),
        "DESK_SMTPP_FROM": "a@x.test",
        "DESK_SMTPP_RECIPIENTS": "b@x.test",
        "DESK_SMTPP_MAX_SENDS": "1",
    }
    with pytest.raises((ValueError, SettingRefused)):
        ProviderSettings.from_env(env_provider | {"DESK_SMTPP_TIMEOUT_SECONDS": "0"})
    assert ProviderSettings.from_env(env_provider | {"DESK_SMTPP_TIMEOUT_SECONDS": "0.001"}).timeout_seconds == 0.001
    with pytest.raises((ValueError, SettingRefused)):
        SmtpSettings.from_env({"DESK_SMTP_TIMEOUT_SECONDS": "0"})
    assert SmtpSettings.from_env({"DESK_SMTP_TIMEOUT_SECONDS": "0.001"}).timeout_seconds == 0.001
    hub = {"DESK_HUBSPOT_KEY_FILE": str(pw), "DESK_HUBSPOT_MAX_CALLS": "1"}
    with pytest.raises((ValueError, SettingRefused)):
        HubspotSettings.from_env(hub | {"DESK_HUBSPOT_TIMEOUT_SECONDS": "0"})
    assert HubspotSettings.from_env(hub | {"DESK_HUBSPOT_TIMEOUT_SECONDS": "0.001"}).timeout_seconds == 0.001


# ------------------------------------------------------------ r7k F3: the thread that ends AFTER the start failure


class _StartsThenFailsAtOnce(threading.Thread):
    """start() begins a thread that waits for a release, and then raises: the failure path gives the place back
    FIRST, and the thread ends LATER (the order of the real race)."""

    release = threading.Event()
    begun: list[threading.Thread] = []

    def start(self) -> None:
        gate = threading.Thread(target=lambda: (_StartsThenFailsAtOnce.release.wait(5), self.run()), daemon=True)
        _StartsThenFailsAtOnce.begun.append(gate)
        gate.start()
        raise RuntimeError("after start")


def test_r7k_f3_a_look_up_thread_that_ends_after_the_start_failure_does_not_give_the_place_back_twice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant O07: `if not state["released"]:` in `work` replaced by `if True:` (the count goes to -1)."""
    from lead_desk import netconnect

    deadline = time.monotonic() + 10
    while netconnect.hung_lookups() != 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    assert netconnect.hung_lookups() == 0
    _StartsThenFailsAtOnce.release.clear()
    _StartsThenFailsAtOnce.begun.clear()
    monkeypatch.setattr(
        netconnect,
        "threading",
        types.SimpleNamespace(Thread=_StartsThenFailsAtOnce, Event=threading.Event, Lock=threading.Lock),
    )
    monkeypatch.setattr(
        netconnect,
        "socket",
        types.SimpleNamespace(
            getaddrinfo=lambda *_a, **_k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 9))],
            SOCK_STREAM=socket.SOCK_STREAM,
        ),
    )
    with pytest.raises(RuntimeError):
        netconnect.resolve_bounded("name.example.test", 9, 1.0)
    assert netconnect.hung_lookups() == 0  # given back by the failure path
    _StartsThenFailsAtOnce.release.set()
    for gate in _StartsThenFailsAtOnce.begun:
        gate.join(5)
    assert netconnect.hung_lookups() == 0  # the late end of the thread gives nothing back a second time


# ------------------------------------------------------------------ M9-25: a reply line that is not a code


@pytest.mark.parametrize("line", [b"abc", b"2x0", b"25", b"2 0", b"", b"+25", b"12a", b"250x", b"xyz abc"])
def test_m9_25_a_reply_line_that_is_not_a_code_is_the_fixed_unreadable_reply_error(line: bytes) -> None:
    """Mutants M25a/M25b: `line.isdigit()` dropped from the bare code check or `line[:3].isdigit()` from the other, so
    `int(...)` raises a raw ValueError that holds the line text. smtp_provider reads replies with this same function."""
    from lead_desk.smtp_outbox import _Budget, _Closed, _read_reply

    a, b = socket.socketpair()
    try:
        b.sendall(line + b"\r\n")
        with pytest.raises(_Closed) as caught:
            _read_reply(a, _Budget(2.0), bytearray())
        assert str(caught.value) == "unreadable reply"
    finally:
        a.close()
        b.close()


@pytest.mark.parametrize("greeting", [b"abc\r\n", b"2x0\r\n", b"25\r\n"])
def test_m9_25_the_outbox_turns_an_odd_greeting_into_its_own_error_and_not_a_value_error(greeting: bytes) -> None:
    from lead_desk.contract import SendAmbiguous, SendRefused, SendUnreachable
    from lead_desk.smtp_outbox import SmtpOutbox, SmtpSettings

    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def serve() -> None:
        conn, _ = srv.accept()
        with conn:
            conn.sendall(greeting)
            time.sleep(0.5)

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    try:
        box = SmtpOutbox(SmtpSettings(host="127.0.0.1", port=srv.getsockname()[1], timeout_seconds=3.0))
        with pytest.raises((SendUnreachable, SendRefused, SendAmbiguous)) as caught:
            box.send("RUN1-L1", "a@x.test", "subject", "body", 3.0)
        assert not isinstance(caught.value, ValueError)
        assert greeting.strip().decode() not in str(caught.value)
    finally:
        t.join(3)
        srv.close()


# ------------------------------------------------------------------ M9-77: one login too many in the mailbox poll


def test_m9_77_the_mailbox_poll_never_logs_in_more_than_the_banner_says(tmp_path: Path) -> None:
    """Mutant M77: `logins >= IMAP_LOGINS_MAX` becomes `>`: one more login than the banner's worst case. A real
    loopback mailbox that never holds the mail, a far time limit, no real sleeping: the logins the SERVER saw must be
    exactly the limit plus the one last poll, and never above the banner figure (limit plus POLL_EXTRA_LOGINS)."""
    from demo_only.fake_imap import FakeImap

    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import run_real_check as rrc
    finally:
        sys.path.remove(str(REPO / "scripts"))
    from lead_desk.imap_count import ImapSettings

    made = make_cert(tmp_path, HOST)
    if made is None:
        pytest.skip("the openssl program is not installed, so no test certificate can be made")
    cert, key = made

    ctx = ssl.create_default_context(cafile=str(cert))
    srv = FakeImap(cert, key, HOST, {"INBOX": []})
    pw = tmp_path / "pw"
    pw.write_text(srv.password + "\n", encoding="utf-8")
    try:
        box = ImapSettings(HOST, srv.user, pw, port=srv.port, folders=("INBOX",), timeout_seconds=3.0, ssl_context=ctx)
        _got, logins, failed = rrc.poll_mailboxes(
            [box], {"L1"}, [{"L1"}], 1, 10_000.0, 0.0, sleep=lambda _s: None, sent_ids={"L1"}
        )
    finally:
        srv.close()
    assert failed is False
    assert len(srv.logins) == rrc.IMAP_LOGINS_MAX + 1 == logins
    assert len(srv.logins) <= rrc.IMAP_LOGINS_MAX + rrc.POLL_EXTRA_LOGINS


# ------------------------------------------------------------------ M9-73: the refusal line for any error class


@pytest.mark.parametrize(
    "make",
    [lambda t: OSError(t), lambda t: PermissionError(13, t), lambda t: ArithmeticError(t), lambda t: ValueError(t)],
)
def test_m9_73_a_setting_reader_error_prints_the_fixed_line_unless_it_is_a_value_error_naming_a_setting(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, make: Any
) -> None:
    """Mutant M73: the scrubbed text of ANY error class is printed (an OSError text holds a path). Only a ValueError
    (our own setting messages, which name a setting and never a value) may print its text; the rest print the fixed
    line."""
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import run_real_check as rrc
    finally:
        sys.path.remove(str(REPO / "scripts"))
    from test_real_check_dry import _valid_config

    marker = "/home/" + "someone/secret-dir/key-file.txt"  # a made-up path, built from parts
    is_value = isinstance(make("x"), ValueError)

    def boom(*_a: Any, **_k: Any) -> None:
        raise make(f"cannot read {marker}")

    monkeypatch.setattr(rrc, "check_secret_files", boom)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert rrc.main(["--config", str(_valid_config(tmp_path))]) == rrc.EXIT_REFUSED
    out = capsys.readouterr().out
    if is_value:
        assert out.startswith("refused: cannot read ")  # our own message text may be shown (scrubbed)
    else:
        assert "refused: the config or a setting cannot be used" in out
        assert marker not in out and "cannot read" not in out


# ------------------------------------------------------------------ M9-57: a 408 is not "nothing stored"


def _status_server(status: int) -> tuple[Any, str]:
    import http.server

    class H(http.server.BaseHTTPRequestHandler):
        def answer(self) -> None:
            n = int(self.headers.get("Content-Length") or 0)
            if n:
                self.rfile.read(n)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *_a: Any) -> None:
            return None

    for verb in ("do_GET", "do_POST", "do_PATCH", "do_DELETE"):
        setattr(H, verb, H.answer)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


@pytest.mark.parametrize(
    ("status", "stored_nothing"),
    [(400, True), (404, True), (422, True), (425, True), (408, False), (500, False), (502, False), (503, False)],
)
@pytest.mark.parametrize("call", ["put", "set_fields"])
def test_m9_57_the_status_table_of_the_crm_write_calls(
    tmp_path: Path, call: str, status: int, stored_nothing: bool
) -> None:
    """Mutant M57: 408 is dropped from the exception in `_fail`, so a request time-out is called a refusal (nothing
    stored) though HubSpot may have stored the write. Refusals (4xx but 408/409/429) say nothing was stored; 408 and
    5xx are `CrmError` that does NOT say so (the desk must not ask again as if nothing happened)."""
    from lead_desk.adapters import CrmError, CrmNothingStored
    from lead_desk.crm_hubspot import HubspotCrm, HubspotSettings

    key = tmp_path / "k"
    key.write_text("k" + "e" * 15 + "-for-tests-0003\n", encoding="utf-8")
    srv, url = _status_server(status)
    try:
        crm = HubspotCrm(HubspotSettings(key, 20, base_url=url, timeout_seconds=2.0, allow_any_base_url=True))
        with pytest.raises(CrmError) as caught:
            if call == "put":
                crm.put(
                    "L-1", {"name": "Ada", "email": "a@x.test", "company": "C", "source": "form", "ai_label": "hot"}
                )
            else:
                crm.set_fields("L-1", "a@x.test", "", "NEW")
    finally:
        srv.shutdown()
        srv.server_close()
    assert isinstance(caught.value, CrmNothingStored) is stored_nothing
