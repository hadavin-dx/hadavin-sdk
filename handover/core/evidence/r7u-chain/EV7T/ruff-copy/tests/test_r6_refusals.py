"""Class (round 6): a key, a trust setting or a log must be refused at the ONE shared place, before any money is
reserved or any connection is made, with a fixed text that holds no typed value and no class name. Made-up data only;
loopback only; no real service."""

from __future__ import annotations

import ast
import io
import ssl
import sys
import types
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import http_guard

from lead_desk import constants, regfile
from lead_desk.envnum import SettingRefused
from lead_desk.imap_count import ImapCountError, ImapSettings
from lead_desk.regfile import FileRefused, read_secret_line, secret_text_ok
from lead_desk.smtp_provider import ProviderSettings, SendRefused, SmtpProviderOutbox
from load_tools import check_invariants as ci

REPO = Path(__file__).resolve().parents[1]
CANARY = "canary" + "-" * 3 + "xyz"


def _key_file(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "key.txt"
    p.write_bytes(text.encode("utf-8"))
    return p


# A: a non-ASCII key is refused by the shared reader and the shared text check, in the file and the env value alike
@pytest.mark.parametrize("secret", ["k" * 7 + "é", "k" * 9 + "​", "б" * 12, "a" * 8 + "\x7f"])
def test_non_ascii_or_control_key_refused(tmp_path: Path, secret: str) -> None:
    assert secret_text_ok(secret) is False
    with pytest.raises(FileRefused) as raised:
        read_secret_line(_key_file(tmp_path, secret), "model key", "key")
    assert str(raised.value) == "the model key file holds no key"


def test_plain_ascii_key_accepted(tmp_path: Path) -> None:
    assert read_secret_line(_key_file(tmp_path, "abcdefgh12345\n"), "model key", "key") == "abcdefgh12345"
    assert secret_text_ok("abcdefgh") and not secret_text_ok("abcdefg")


# B and C: the caller-given context is re-checked at send time; a context and a CA file together are refused
def _settings(tmp_path: Path, **kw: object) -> ProviderSettings:
    pw = tmp_path / "pw.txt"
    pw.write_text("p" * 12)
    base: dict[str, Any] = {
        "host": "127.0.0.1",
        "port": 1,
        "user": "u@example.com",
        "password_file": pw,
        "mail_from": "a@example.com",
        "recipients": ("b@example.com",),
        "max_sends": 1,
    }
    base.update(kw)
    return ProviderSettings(**base)


def test_context_weakened_after_build_is_refused_before_connecting(tmp_path: Path) -> None:
    ctx = ssl.create_default_context()
    box = SmtpProviderOutbox(_settings(tmp_path), ssl_context=ctx)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with pytest.raises(SendRefused) as raised:
        box._verifying_context()
    assert CANARY not in str(raised.value)


def test_context_and_ca_file_together_refused(tmp_path: Path) -> None:
    ca = tmp_path / "ca.pem"
    ca.write_text("x")
    s = _settings(tmp_path, ca_file=ca)
    with pytest.raises(SettingRefused) as raised:
        SmtpProviderOutbox(s, ssl_context=ssl.create_default_context())
    assert "give only one" in str(raised.value)
    assert str(ca) not in str(raised.value)


# D: the mailbox user with a control character is refused where the settings are made
@pytest.mark.parametrize("user", ["", "a@example.com\r\nA2 LOGOUT", "a\x00b"])
def test_imap_user_control_character_refused(tmp_path: Path, user: str) -> None:
    with pytest.raises(ImapCountError) as raised:
        ImapSettings(host="127.0.0.1", user=user, password_file=tmp_path / "p")
    assert str(raised.value) == "the mailbox user must be plain printable ASCII text without a space at either end"
    assert isinstance(raised.value, ValueError)  # R7: so every script main that refuses a setting also catches it


# E: the bounded secret read never reads more than the cap, whatever the file holds
def test_secret_read_is_bounded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[int] = []
    real = regfile.open_regular

    def spy(path: Any, *a: Any, **k: Any) -> Any:
        f = real(path, *a, **k)
        inner = f.read

        def read(size: int = -1) -> bytes:
            seen.append(size)
            return inner(size)

        setattr(f, "read", read)
        return f

    monkeypatch.setattr(regfile, "open_regular", spy)
    big = tmp_path / "big.txt"
    big.write_bytes(b"a" * (regfile.SECRET_FILE_MAX_BYTES * 3))
    with pytest.raises(FileRefused):
        read_secret_line(big, "model key", "key")
    assert seen and all(0 < n <= regfile.SECRET_FILE_MAX_BYTES + 1 for n in seen)


# F: no number or exit code is defined twice with a different value in constants.py
def test_constants_have_no_duplicate_names() -> None:
    tree = ast.parse((REPO / "src/lead_desk/constants.py").read_text(encoding="utf-8"))
    names = [t.target.id for t in tree.body if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)]
    names += [t.targets[0].id for t in tree.body if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name)]
    dup = sorted({n for n in names if names.count(n) > 1})
    assert dup == []


# G: no refusal or status line in the scripts prints a class name
def test_scripts_print_no_class_names() -> None:
    bad: list[str] = []
    for p in sorted((REPO / "scripts").glob("*.py")) + sorted((REPO / "demo_only").glob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print":
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Attribute) and sub.attr == "__name__":
                        bad.append(f"{p.name}:{node.lineno}")
    assert bad == []


# I: one shared bounded request-body helper
class _H:
    def __init__(self, headers: dict[str, str], body: bytes = b"") -> None:
        self.headers = headers
        self.rfile = io.BytesIO(body)
        self.connection = types.SimpleNamespace(settimeout=lambda _seconds: None)  # the reader sets a time limit


@pytest.mark.parametrize(
    ("headers", "status"),
    [
        ({"Content-Length": "-1"}, 400),
        ({"Content-Length": "+5"}, 400),
        ({"Content-Length": "٥"}, 400),
        ({"Content-Length": "9" * 5000}, 413),
        ({"Content-Length": str(constants.FAKE_BODY_MAX_BYTES + 1)}, 413),
        ({"Transfer-Encoding": "chunked"}, 411),
    ],
)
def test_request_body_refusals(headers: dict[str, str], status: int) -> None:
    assert http_guard.read_request_body(_H(headers)) == (b"", status)


def test_request_body_short_read_and_good_read() -> None:
    assert http_guard.read_request_body(_H({"Content-Length": "5"}, b"abc")) == (b"", 408)
    assert http_guard.read_request_body(_H({"Content-Length": "3"}, b"abcdef")) == (b"abc", 0)
    assert http_guard.read_request_body(_H({})) == (b"", 0)


# J: the log reader streams and stops at the row cap with its own exit code
def test_read_jsonl_row_cap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ci, "LOAD_TOTAL_MAX", 3)
    p = tmp_path / "log.jsonl"
    p.write_text("{}\n" * 5)
    with pytest.raises(ci.TooManyRowsError) as raised:
        ci.read_jsonl(p, "--requests")
    assert "--requests" in str(raised.value) and str(tmp_path) not in str(raised.value)
    assert constants.EXIT_LOG_TOO_LONG == 4


# L: exit codes that share a number do so on purpose and the pairs are pinned
def test_shared_exit_code_pairs_are_pinned() -> None:
    codes = {
        "check failed": constants.EXIT_CHECK_FAILED,
        "refused": constants.EXIT_REFUSED,
        "unreachable": constants.EXIT_UNREACHABLE,
        "bad setting or path": constants.EXIT_BAD_SETTING_OR_PATH,
        "stopped by the person": constants.EXIT_STOPPED,
        "adapters unreachable": constants.EXIT_ADAPTERS_UNREACHABLE,
    }
    assert codes == {
        "check failed": 1,
        "refused": 2,
        "unreachable": 3,
        "bad setting or path": 4,
        "stopped by the person": 6,
        "adapters unreachable": 7,
    }
    assert len(set(codes.values())) == len(codes)  # R7: no number carries two meanings in the script codes


def test_start_poll_constants_are_positive() -> None:
    assert constants.START_CHECK_TRIES > 0 and constants.START_CHECK_PAUSE_SECONDS > 0
