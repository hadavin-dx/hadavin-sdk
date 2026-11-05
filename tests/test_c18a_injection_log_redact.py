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
        caplog.clear()
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


def test_huge_message_bounded_and_masked(caplog):
    """A 200k-character exception message is capped before masking: bounded time, nothing leaks."""
    import time

    t0 = time.perf_counter()
    verdict, text = _run(ValueError(("word " * 40_000) + EMAIL), caplog)
    assert (
        time.perf_counter() - t0 < 2.0
    )  # budget: the cap makes this milliseconds; 2 s is generous
    _no_seed(text)
    assert verdict.reason_code == "guard_unavailable"


@pytest.mark.parametrize("fail", [ValueError("boom"), RecursionError("deep"), MemoryError()])
def test_redact_failure_fails_closed(caplog, monkeypatch, fail):
    def broken(text):
        raise fail

    monkeypatch.setattr("hadavin_sdk.guard.safe_message.redact", broken)
    verdict, text = _run(ValueError(f"contact {EMAIL}"), caplog)
    _no_seed(text)
    assert "(message unavailable)" in text
    assert verdict.flagged is True and verdict.reason_code == "guard_unavailable"


def test_injection_check_does_not_swallow_redaction_error():
    """Skipped until C1a lands `RedactionError`; C1c adds the re-raise in injection_check. Then this must pass."""
    mod = pytest.importorskip(
        "hadavin_sdk.guard.redactor",
        reason="LOUD: RedactionError does not exist before C1a; this test must be un-skipped by C1c",
    )

    class Redacting:
        backend = "r"

        def check(self, text, source):
            raise mod.RedactionError("x")

    with pytest.raises(mod.RedactionError):
        injection_check(Redacting(), "t", "doc")


# --- the class guard: no log call or print in src may carry a raw exception ------------------------------

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
_LEVELS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log", "fatal"}
_TRACE = {"format_exc", "format_exception", "print_exc", "print_exception", "format_tb", "print_tb"}
_SAFE_CALLS = {"safe_message", "safe_text"}

# Operator-terminal output that deliberately shows the exception: (file, unparsed call) -> reason.
_OPERATOR = (
    "ConfigError / StoreUnavailable text printed to the operator's own terminal (never a log or a store): "
    "it is written by us or echoes the operator's own config file, and the secrets kind keeps secret "
    "values out of config. Masking would also collapse the multi-line validation report the operator needs."
)
WAIVERS: dict[tuple[str, str], str] = {
    ("cli.py", "print(f'refused: {exc}', file=sys.stderr)"): _OPERATOR,
    ("cli.py", "print(f'could not verify: {exc}', file=sys.stderr)"): _OPERATOR,
    ("cli.py", "print(f'tick: {exc}', file=sys.stderr)"): _OPERATOR,
    ("cli.py", "print(f'tick: config error: {exc}', file=sys.stderr)"): _OPERATOR,
    (
        "cli.py",
        "traceback.print_exc()",
    ): "opt-in HADAVIN_DEBUG=1 traceback to the operator's terminal only",
}


def _chain(node: ast.AST) -> list[str]:
    """Identifiers of a Name/Attribute chain, outermost first: self._log.warning -> [self, _log, warning]."""
    out: list[str] = []
    while isinstance(node, ast.Attribute):
        out.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        out.append(node.id)
    elif isinstance(node, ast.Call):
        out.append(f"{''.join(_chain(node.func)[-1:])}()")
    return out[::-1]


def _is_logger(base: ast.AST) -> bool:
    ids = _chain(base)
    if not ids:
        return False
    last = ids[-1].lower()
    return last.endswith(("log", "logger")) or last in {"logging", "getlogger()"}


def _is_safe_wrapper(node: ast.AST) -> bool:
    """safe_message(...) / safe_text(...) or type(<x>).__name__ / <x>.__class__.__name__."""
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") in _SAFE_CALLS:
        return True
    if isinstance(node, ast.Attribute) and node.attr == "__name__":
        v = node.value
        if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "type":
            return True
        if isinstance(v, ast.Attribute) and v.attr == "__class__":
            return True
    return False


def _uses_raw(node: ast.AST, names: set[str]) -> bool:
    if _is_safe_wrapper(node):
        return False
    if isinstance(node, ast.Name) and node.id in names:
        return True
    return any(_uses_raw(c, names) for c in ast.iter_child_nodes(node))


def _truthy(node: ast.AST) -> bool:
    return not (isinstance(node, ast.Constant) and node.value in (False, None))


def find_leaks(source: str) -> list[tuple[int, str, str]]:
    """(line, why, unparsed call) for every leak of exception text inside any `except` handler."""
    found: list[tuple[int, str, str]] = []
    for handler in ast.walk(ast.parse(source)):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        names = {handler.name} if handler.name else set()
        calls = [n for st in handler.body for n in ast.walk(st)]
        for _ in range(2):  # aliases: m = str(exc) makes m raw too
            for n in calls:
                raw = isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None
                if raw and _uses_raw(n.value, names):
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                    names |= {t.id for t in targets if isinstance(t, ast.Name)}
        for call in calls:
            if not isinstance(call, ast.Call):
                continue
            ids = _chain(call.func)
            text = ast.unparse(call)

            def flag(why: str, call=call, text=text) -> None:
                found.append((call.lineno, why, text))

            if (ids[:1] == ["traceback"] and ids[-1] in _TRACE) or ids == ["sys", "exc_info"]:
                flag("traceback / exc_info in a handler")
                continue
            is_log = (
                isinstance(call.func, ast.Attribute)
                and call.func.attr in _LEVELS
                and _is_logger(call.func.value)
            )
            is_out = (
                ids == ["print"]
                or ids == ["warnings", "warn"]
                or (len(ids) >= 2 and ids[-1] == "write" and ids[-2] in {"stderr", "stdout"})
            )
            if not (is_log or is_out):
                continue
            if is_log and call.func.attr == "exception":
                flag("_LOG.exception logs the traceback")
            for kw in call.keywords:
                if kw.arg == "exc_info" and _truthy(kw.value):  # exc_info branch
                    flag("exc_info")
            parts = [*call.args, *(kw.value for kw in call.keywords if kw.arg != "exc_info")]
            if any(_uses_raw(a, names) for a in parts):
                flag(f"raw exception text in {'a log call' if is_log else ids[-1]}")
    return found


def test_no_raw_exc_in_log_calls_ast():
    bad, used = [], set()
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        for line, why, text in find_leaks(path.read_text(encoding="utf-8")):
            if (rel, text) in WAIVERS:
                used.add((rel, text))
            else:
                bad.append(f"{rel}:{line}: {why}: {text[:90]}")
    assert not bad, "raw exception text in a log/print (use safe_message):\n" + "\n".join(bad)
    assert used == set(WAIVERS), f"stale waivers: {sorted(set(WAIVERS) - used)}"


_HEAD = "try:\n pass\nexcept Exception as e:\n "
_BARE = "try:\n pass\nexcept Exception:\n "


@pytest.mark.parametrize(
    "src",
    [
        _HEAD + "_LOG.warning('x %s', e)",
        _HEAD + "_LOG.warning(f'x {e}')",
        _HEAD + "_LOG.warning('x {}'.format(e))",
        _HEAD + "_LOG.warning('x %s', str(e)[:300])",
        _HEAD + "_LOG.warning('x', exc_info=True)",
        _HEAD + "_LOG.warning('x', exc_info=e)",
        _HEAD + "_LOG.exception('x')",
        _HEAD + "logging.getLogger('a').error('x %s', e.args)",
        _HEAD + "_LOG.warning('x', extra={'v': str(e)})",
        _HEAD + "self._log.error('x %s', e)",
        _HEAD + "self.logger.error('x %s', e)",
        _HEAD + "LOGGER.error('x %s', e)",
        _HEAD + "m = str(e)\n _LOG.warning('x %s', m)",
        _HEAD + "print(f'refused: {e}')",
        _HEAD + "sys.stderr.write(str(e))",
        _HEAD + "warnings.warn(str(e))",
        _HEAD + "traceback.print_exc()",
        _HEAD + "x = traceback.format_exc()",
        _HEAD + "x = sys.exc_info()",
        _BARE + "_LOG.exception('x')",
        _BARE + "_LOG.warning('x', exc_info=True)",
        _BARE + "traceback.print_exc()",
        _BARE + "x = sys.exc_info()",
        _BARE + "self._log.exception('x')",
    ],
)
def test_ast_checker_flags_bad_shapes(src):
    assert find_leaks(src + "\n"), src


@pytest.mark.parametrize(
    "src",
    [
        _HEAD + "_LOG.warning('x %s', type(e).__name__)",
        _HEAD + "_LOG.warning('x %s', e.__class__.__name__)",
        _HEAD + "_LOG.warning('x %s', safe_message(e, 300))",
        _HEAD + "_LOG.warning('x %s', safe_text(e, 300))",
        _HEAD + "m = safe_message(e)\n _LOG.warning('x %s', m)",
        _HEAD + "print(type(e).__name__)",
        _HEAD + "_LOG.warning('x')",
        _BARE + "_LOG.warning('x')",
        _BARE + "print('could not verify')",
        _HEAD + "_LOG.warning('x', exc_info=False)",
    ],
)
def test_ast_checker_passes_good_shapes(src):
    assert not find_leaks(src + "\n"), src
