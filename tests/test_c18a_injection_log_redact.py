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


# --- the class guard: no log, print, store or re-raise in a handler may carry raw exception text -----------

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
_LEVELS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log", "fatal"}
_TRACE = {"format_exc", "format_exception", "print_exc", "print_exception", "format_tb", "print_tb"}
_SAFE_CALLS = {"safe_message", "safe_text"}
_SINK_KW = {"errors", "last_error", "error_code", "message", "detail", "error", "reason"}
_SINK_METHODS = {"append", "extend", "add"}
_LOGGER_NAMES = {"lg", "audit", "logging"}

_OPERATOR = (
    "ConfigError / StoreUnavailable text printed to an interactive operator's terminal (never a log or a "
    "store; CI captures the output of these commands, which is why the unattended `tick` prints are NOT "
    "waived): it is written by us or echoes the operator's own config file, and the secrets kind keeps "
    "secret values out of config. Masking would also collapse the multi-line validation report."
)
_RAISE = (
    "builds a ConfigError from a pydantic/yaml/SDK error at config load; the text is the operator's own "
    "config and only ever reaches an interactive print (waived above) or the tick print, which masks it "
    "with safe_message (see test_tick_config_error_secret_masked)."
)
_DESCRIBE = (
    "llm.retry.describe() builds the text from the class name, the HTTP status and the kind's own error code, "
    "never from the SDK message (pinned by test_with_retry_error_text_never_has_sdk_message)."
)
# (file, enclosing function, unparsed statement) -> (reason, expected count). A second identical statement in
# the same function is NOT waived silently: the count must match exactly.
WAIVERS: dict[tuple[str, str, str], tuple[str, int]] = {
    ("cli.py", "main", "print(f'refused: {exc}', file=sys.stderr)"): (_OPERATOR, 1),
    ("cli.py", "_main", "print(f'could not verify: {exc}', file=sys.stderr)"): (_OPERATOR, 1),
    ("config.py", "_one", "raise ConfigError(f'backends.{cap} ({kind}): {exc}') from exc"): (
        _RAISE,
        1,
    ),
    ("config.py", "load_config", "raise ConfigError(str(exc)) from exc"): (_RAISE, 1),
    ("registry.py", "load_registry", "raise ConfigError(str(exc)) from exc"): (_RAISE, 1),
    (
        "llm/anthropic.py",
        "client",
        "raise ConfigError(f\"backend llm 'anthropic' ({settings.platform}): {exc}\") from exc",
    ): (_RAISE, 1),
    (
        "llm/retry.py",
        "with_retry",
        "raise ProviderError(f'{label}: {describe(exc, detail)}') from exc",
    ): (_DESCRIBE, 1),
    (
        "llm/retry.py",
        "with_retry",
        "raise ProviderExhausted(f'{label}: {describe(exc, detail)} after {max_attempts} attempts') from exc",
    ): (_DESCRIBE, 1),
    ("cli.py", "main", "traceback.print_exc()"): (
        "opt-in HADAVIN_DEBUG=1 traceback to the interactive operator's terminal only",
        1,
    ),
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
    if isinstance(base, ast.Call):
        f = base.func
        if isinstance(f, ast.Attribute) and f.attr == "getChild":  # _LOG.getChild("x")
            return _is_logger(f.value)
        return getattr(f, "attr", getattr(f, "id", "")) == "getLogger"
    ids = _chain(base)
    last = ids[-1].lower() if ids else ""
    return last.endswith(("log", "logger")) or last in _LOGGER_NAMES


def _is_safe_wrapper(node: ast.AST, exc: str | None) -> bool:
    """safe_message(<exc>, ...) / safe_text(<exc>, ...) with the exception object itself as first argument
    (safe_message(str(e)) is NOT safe), or type(<x>).__name__ / <x>.__class__.__name__."""
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") in _SAFE_CALLS:
        a = node.args[0] if node.args else None
        return isinstance(a, ast.Name) and a.id == exc
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") in {"isinstance", "type"}:
        return True  # a class test or the class object: no message text
    if isinstance(node, ast.Attribute) and node.attr == "__name__":
        v = node.value
        if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "type":
            return True
        if isinstance(v, ast.Attribute) and v.attr == "__class__":
            return True
    return False


def _uses_raw(node: ast.AST, names: set[str], exc: str | None) -> bool:
    if _is_safe_wrapper(node, exc):
        return False
    if isinstance(node, ast.Name) and node.id in names:
        return True
    if isinstance(node, (ast.Attribute, ast.Subscript)) and ast.unparse(node) in names:
        return True
    return any(_uses_raw(c, names, exc) for c in ast.iter_child_nodes(node))


def _truthy(node: ast.AST) -> bool:
    return not (isinstance(node, ast.Constant) and node.value in (False, None))


def _target_names(t: ast.AST) -> set[str]:
    if isinstance(t, (ast.Tuple, ast.List)):
        return set().union(*(_target_names(e) for e in t.elts)) if t.elts else set()
    if isinstance(t, ast.Name):
        return {t.id}
    if isinstance(t, (ast.Attribute, ast.Subscript)):
        return {ast.unparse(t)}
    return set()


def _enclosing(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return "<module>"


def find_leaks(source: str) -> list[tuple[int, str, str, str]]:
    """(line, why, unparsed statement, enclosing function) for every leak of exception text in a handler."""
    tree = ast.parse(source)
    parents = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    found: list[tuple[int, str, str, str]] = []
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        exc = handler.name
        names = {exc} if exc else set()
        nodes = [n for st in handler.body for n in ast.walk(st)]
        for _ in range(3):  # aliases: x = str(e), self.x = ..., a, b = ..., (m := ...)
            for n in nodes:
                if isinstance(n, ast.Assign) and _uses_raw(n.value, names, exc):
                    for t in n.targets:
                        names |= _target_names(t)
                elif (
                    isinstance(n, ast.AnnAssign)
                    and n.value
                    and _uses_raw(n.value, names, exc)
                    or isinstance(n, ast.NamedExpr)
                    and _uses_raw(n.value, names, exc)
                ):
                    names |= _target_names(n.target)
        fn = _enclosing(handler, parents)

        def flag(node: ast.AST, why: str, fn: str = fn) -> None:
            found.append((node.lineno, why, ast.unparse(node), fn))

        for n in nodes:
            if isinstance(n, ast.Raise):
                c = n.exc
                if isinstance(c, ast.Call) and any(
                    _uses_raw(a, names, exc) for a in [*c.args, *(k.value for k in c.keywords)]
                ):
                    flag(n, "raise carries raw exception text")
                continue
            if not isinstance(n, ast.Call):
                continue
            ids = _chain(n.func)
            if (ids[:1] == ["traceback"] and ids[-1] in _TRACE) or ids == ["sys", "exc_info"]:
                flag(n, "traceback / exc_info in a handler")
                continue
            recv = _chain(n.func.value) if isinstance(n.func, ast.Attribute) else []
            recv_last = recv[-1].lower() if recv else ""
            is_log = (
                isinstance(n.func, ast.Attribute)
                and _is_logger(n.func.value)
                and (n.func.attr in _LEVELS or recv_last == "audit")
            )
            is_bare = isinstance(n.func, ast.Name) and any(
                k in n.func.id.lower() for k in ("log", "warn", "emit")
            )
            is_out = (
                is_bare
                or ids == ["print"]
                or ids == ["warnings", "warn"]
                or (len(ids) >= 2 and ids[-1] == "write" and ids[-2] in {"stderr", "stdout"})
            )
            kw_vals = [(k.arg, k.value) for k in n.keywords]
            if is_log or is_out:
                if is_log and n.func.attr == "exception":
                    flag(n, "_LOG.exception logs the traceback")
                for arg, val in kw_vals:
                    if arg == "exc_info" and _truthy(val):  # exc_info branch
                        flag(n, "exc_info")
                parts = [*n.args, *(v for a, v in kw_vals if a != "exc_info")]  # kwargs branch
                if any(_uses_raw(p, names, exc) for p in parts):
                    flag(n, "raw exception text in a log/print")
                continue
            if any(a in _SINK_KW and _uses_raw(v, names, exc) for a, v in kw_vals):  # store branch
                flag(n, "raw exception text stored in a keyword field")
            elif (
                isinstance(n.func, ast.Attribute)
                and n.func.attr in _SINK_METHODS
                and any(_uses_raw(a, names, exc) for a in n.args)
            ):
                flag(n, "raw exception text stored via append/extend/add")
    return found


def test_no_raw_exc_in_log_calls_ast():
    from collections import Counter

    bad, used = [], Counter()
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        for line, why, text, fn in find_leaks(path.read_text(encoding="utf-8")):
            if (rel, fn, text) in WAIVERS:
                used[(rel, fn, text)] += 1
            else:
                bad.append(f"{rel}:{line} in {fn}(): {why}: {text[:100]}")
    assert not bad, "raw exception text leaks (use safe_message or the class name):\n" + "\n".join(
        bad
    )
    assert dict(used) == {k: v[1] for k, v in WAIVERS.items()}, (
        "waiver counts differ (stale or extra)"
    )


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
        _HEAD + "lg.error('x %s', e)",
        _HEAD + "audit.write(e)",
        _HEAD + "_LOG.getChild('a').error('x %s', e)",
        _HEAD + "m = str(e)\n _LOG.warning('x %s', m)",
        _HEAD + "self.err = str(e)\n _LOG.warning('x %s', self.err)",
        _HEAD + "a, b = str(e), 1\n _LOG.warning('x %s', a)",
        _HEAD + "if (m := str(e)):\n  _LOG.warning('x %s', m)",
        _HEAD + "print(f'refused: {e}')",
        _HEAD + "sys.stderr.write(str(e))",
        _HEAD + "warnings.warn(str(e))",
        _HEAD + "_safe_log('x %s', e)",
        _HEAD + "emit(e)",
        _HEAD + "warn_user(str(e))",
        _HEAD + "audit_log('x %s', e)",
        _HEAD + "_LOG.warning('x %s', safe_message(str(e)))",
        _HEAD + "Row(errors=[str(e)])",
        _HEAD + "Row(last_error=str(e))",
        _HEAD + "write(message=f'{e}')",
        _HEAD + "errors.append(f'{e}')",
        _HEAD + "errors.extend([str(e)])",
        _HEAD + "raise ConfigError(str(e))",
        _HEAD + "raise ConfigError(f'bad {e}')",
        _HEAD + "raise X(e)",
        _HEAD + "raise X(msg=str(e))",
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
        _HEAD + "_safe_log('x %s', type(e).__name__)",
        _HEAD + "errors.append(safe_message(e, 300, S))",
        _HEAD + "Row(last_error=safe_text(e))",
        _HEAD + "raise ConfigError('x') from e",
        _HEAD + "raise ConfigError(safe_message(e))",
        _HEAD + "raise",
        _BARE + "_LOG.warning('x')",
        _BARE + "print('could not verify')",
        _HEAD + "_LOG.warning('x', exc_info=False)",
    ],
)
def test_ast_checker_passes_good_shapes(src):
    assert not find_leaks(src + "\n"), src


def test_waiver_is_keyed_on_function_and_count():
    """A second identical print, or the same print in another function, is not waived by the first."""
    one = "def f():\n try:\n  pass\n except Exception as e:\n  print(f'refused: {e}')\n"
    two = one + "  print(f'refused: {e}')\n"
    other = one.replace("def f", "def g")
    assert [(w, f) for _, _, w, f in find_leaks(one)] == [("print(f'refused: {e}')", "f")]
    assert len(find_leaks(two)) == 2 and find_leaks(other)[0][3] == "g"
