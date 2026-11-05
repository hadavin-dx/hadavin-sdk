"""C18a: a failing detector's exception text must not reach the log with the values it carries.

Fake secrets only (example.com addresses, the public test IBAN, a key built from parts).
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest

from hadavin_sdk.guard.injection import injection_check

LOGGER = "hadavin_sdk.guard"
EMAIL, IBAN = "bob@example.com", "GB82WEST12345698765432"
KEY = "sk-" + "a" * 30
SEEDS = ("bob", "example.com", "bob@exa", IBAN, "GB82WEST", KEY, "hunter2abc")


class Boom:
    """A detector that fails with the given exception."""

    backend = "boom"

    def __init__(self, exc: BaseException) -> None:
        self.exc = exc

    def check(self, text: str, source: str):
        raise self.exc


def _run(exc: BaseException, caplog):
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        verdict = injection_check(Boom(exc), "a document", "doc")
    return verdict, caplog.text


def _no_seed(text: str) -> None:
    for seed in SEEDS:
        assert seed not in text, f"{seed!r} reached the log: {text!r}"


def test_detector_error_log_has_no_values(caplog):
    verdict, text = _run(ValueError(f"contact {EMAIL} iban {IBAN}"), caplog)
    assert "ValueError" in text  # still diagnosable
    _no_seed(text)
    assert verdict.flagged is True and verdict.reason_code == "guard_unavailable"


def test_value_straddling_300_cut_masked(caplog):
    verdict, text = _run(ValueError("x" * 290 + " " + EMAIL), caplog)
    assert "ValueError" in text
    _no_seed(text)
    assert "bob@exa" not in text
    assert verdict.flagged is True


def test_custom_str_not_logged(caplog):
    class Custom(Exception):
        def __str__(self) -> str:
            return f"document says {EMAIL} and {KEY}"

    verdict, text = _run(Custom(), caplog)
    assert "Custom" in text
    _no_seed(text)
    assert verdict.reason_code == "guard_unavailable"


def test_broken_str_does_not_break_the_handler(caplog):
    class Broken(Exception):
        def __str__(self) -> str:
            raise RuntimeError("str failed " + EMAIL)

    verdict, text = _run(Broken(), caplog)  # must not raise out of the fail-closed path
    _no_seed(text)
    assert verdict.flagged is True and verdict.reason_code == "guard_unavailable"


def test_verdict_stays_guard_unavailable(caplog):
    for exc in (
        ValueError("x"),
        RuntimeError(EMAIL),
        KeyError(IBAN),
        TypeError("password=hunter2abc"),
    ):
        verdict, text = _run(exc, caplog)
        assert (verdict.flagged, verdict.score, verdict.backend, verdict.reason_code) == (
            True,
            1.0,
            "boom",
            "guard_unavailable",
        )
        _no_seed(text)
        assert "detector Boom failed" in text  # the log line itself still exists


def test_password_assignment_masked(caplog):
    _, text = _run(ValueError("login failed, password=hunter2abc for the user"), caplog)
    assert "ValueError" in text
    _no_seed(text)


@pytest.mark.parametrize(
    "exc", [ConnectionError(f"cannot reach db {EMAIL}"), OSError(f"disk {IBAN}")]
)
def test_connection_and_os_errors_withheld(caplog, exc):
    verdict, text = _run(exc, caplog)
    assert type(exc).__name__ in text
    _no_seed(text)
    assert "cannot reach" not in text and "disk" not in text  # withheld, not just masked
    assert verdict.reason_code == "guard_unavailable"


# --- the class guard: no log call in src may carry a raw exception ---------------------------------------

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
_LEVELS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
_LOGGERS = {"_LOG", "LOG", "log", "logger", "_logger", "logging"}


def _is_log_call(node: ast.Call) -> bool:
    f = node.func
    if not (isinstance(f, ast.Attribute) and f.attr in _LEVELS):
        return False
    base = f.value
    if isinstance(base, ast.Name):
        return base.id in _LOGGERS
    # logging.getLogger(...).warning(...)
    return isinstance(base, ast.Call) and getattr(base.func, "attr", "") == "getLogger"


def _is_safe_wrapper(node: ast.AST) -> bool:
    """safe_message(...) or type(<x>).__name__ / <x>.__class__.__name__."""
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "safe_message":
        return True
    if isinstance(node, ast.Attribute) and node.attr == "__name__":
        v = node.value
        if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "type":
            return True
        if isinstance(v, ast.Attribute) and v.attr == "__class__":
            return True
    return False


def _uses_raw(node: ast.AST, name: str) -> bool:
    if _is_safe_wrapper(node):
        return False
    if isinstance(node, ast.Name) and node.id == name:
        return True
    return any(_uses_raw(c, name) for c in ast.iter_child_nodes(node))


def find_raw_exc_logs(source: str) -> list[tuple[int, str]]:
    """(line, why) for every log call inside `except X as <name>` that gets the raw exception."""
    found: list[tuple[int, str]] = []
    for handler in ast.walk(ast.parse(source)):
        if not (isinstance(handler, ast.ExceptHandler) and handler.name):
            continue
        for stmt in handler.body:
            for call in ast.walk(stmt):
                if not (isinstance(call, ast.Call) and _is_log_call(call)):
                    continue
                if call.func.attr == "exception":
                    found.append((call.lineno, "_LOG.exception logs the traceback"))
                for kw in call.keywords:
                    if kw.arg == "exc_info" and not (
                        isinstance(kw.value, ast.Constant) and kw.value.value in (False, None)
                    ):
                        found.append((call.lineno, "exc_info"))
                parts = [*call.args, *(kw.value for kw in call.keywords if kw.arg != "exc_info")]
                if any(_uses_raw(a, handler.name) for a in parts):
                    found.append((call.lineno, f"raw {handler.name} in a log call"))
    return found


def test_no_raw_exc_in_log_calls_ast():
    bad = []
    for path in sorted(SRC.rglob("*.py")):
        for line, why in find_raw_exc_logs(path.read_text(encoding="utf-8")):
            bad.append(f"{path.relative_to(SRC)}:{line}: {why}")
    assert not bad, "raw exception text in a log call (use safe_message):\n" + "\n".join(bad)


_HEAD = "try:\n pass\nexcept Exception as e:\n "


@pytest.mark.parametrize(
    "call",
    [
        "_LOG.warning('x %s', e)",
        "_LOG.warning(f'x {e}')",
        "_LOG.warning('x {}'.format(e))",
        "_LOG.warning('x %s', str(e)[:300])",
        "_LOG.warning('x', exc_info=True)",
        "_LOG.exception('x')",
        "logging.getLogger('a').error('x %s', e.args)",
    ],
)
def test_ast_checker_flags_bad_shapes(call):
    assert find_raw_exc_logs(_HEAD + call + "\n"), call


@pytest.mark.parametrize(
    "call",
    [
        "_LOG.warning('x %s', type(e).__name__)",
        "_LOG.warning('x %s', e.__class__.__name__)",
        "_LOG.warning('x %s', safe_message(e, 300))",
        "_LOG.warning('x')",
    ],
)
def test_ast_checker_passes_good_shapes(call):
    assert not find_raw_exc_logs(_HEAD + call + "\n"), call
