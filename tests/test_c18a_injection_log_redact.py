"""C18a: a failing detector's exception text must not reach the log with the values it carries.

Fake secrets only (example.com addresses, the public test IBAN, a key built from parts).
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

import pytest

from hadavin_sdk.errors import ConfigError
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
    def broken(text, **kw):
        raise fail

    monkeypatch.setattr("hadavin_sdk.guard.safe_message.redact", broken)
    verdict, text = _run(ConfigError(f"contact {EMAIL}"), caplog)
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


# --- the class guard: exception text must not reach a log, print, store, call, return or raise unmasked ------
# Inverted rule (batch 5): inside every except handler, and every function that takes an exception, ANY call
# that receives text derived from the exception is a leak unless the callee is a masking helper or a pure
# string/conversion function. Waivers below are explicit and counted.

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
_LEVELS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log", "fatal"}
_TRACE = {"format_exc", "format_exception", "print_exc", "print_exception", "format_tb", "print_tb"}
_MASKING = {"safe_message", "safe_text", "safe_str", "_failure", "class_name", "locator"}
_PURE_FUNCS = {
    "str", "repr", "format", "ascii", "len", "type", "isinstance", "issubclass", "bool", "int", "float",
    "list", "tuple", "set", "frozenset", "dict", "sorted", "reversed", "enumerate", "zip", "map", "filter",
    "min", "max", "sum", "any", "all", "getattr", "hasattr", "id", "hash", "iter", "next",
}  # fmt: skip
_PURE_METHODS = {
    "format", "format_map", "join", "split", "rsplit", "splitlines", "strip", "lstrip", "rstrip", "lower",
    "upper", "replace", "encode", "decode", "startswith", "endswith", "get", "items", "keys", "values",
    "count", "index", "find", "rfind", "partition", "rpartition", "title", "capitalize", "casefold",
    "zfill", "ljust", "rjust", "center", "expandtabs", "swapcase", "translate", "removeprefix",
    "removesuffix",
}  # fmt: skip
_OBJECT_SINKS = {
    "append",
    "extend",
    "add",
    "insert",
    "put",
    "put_nowait",
    "setdefault",
    "update",
    "push",
}
_REPORTERS = {"record_exception", "capture_exception", "capture_message"}
_LOGGER_NAMES = {"lg", "audit", "logging"}
_EXC_PARAM_NAMES = {"e", "exc", "err", "error", "ex", "exception"}
_SAFE_ATTRS = {"code", "status", "status_code", "errno", "returncode", "pos", "lineno"}
_CHAIN_ATTRS = {"__cause__", "__context__"}

_RAISE_NOTE = "an error is re-raised with the original kept as __cause__ (documented; tracebacks are not printed)"
_DESCRIBE = (
    "llm.retry.describe() builds the text from the class name, the HTTP status and the kind's own error code, "
    "never from the SDK message (pinned by test_with_retry_error_text_never_has_sdk_message)."
)
_HANDOFF = (
    "k1b/loop.py hands the exception OBJECT from the worker thread to the caller thread, which re-raises it; "
    "nothing prints or stores its text here."
)
_OBJECTS = "collects or returns exception OBJECTS (no text): the callers decide what to print, through safe_message"
# (file, enclosing function, unparsed statement) -> (reason, expected count). A second identical statement in
# the same function is NOT waived silently: the count must match exactly.
WAIVERS: dict[tuple[str, str, str], tuple[str, int]] = {
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
    ("k1b/loop.py", "work", "box['exc'] = exc"): (_HANDOFF, 1),
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


def _object_expr(node: ast.AST, exc: set[str]) -> bool:
    """The exception object itself, or its __cause__ / __context__ chain."""
    while isinstance(node, ast.Attribute) and node.attr in _CHAIN_ATTRS:
        node = node.value
    return isinstance(node, ast.Name) and node.id in exc


def _is_safe_wrapper(node: ast.AST, exc: set[str], safe: set[str]) -> bool:
    """safe_message(<exc>) / safe_text(<exc>) with the exception object (or its cause chain) as first
    argument or as exc=, safe_str(<text>), type(<x>).__name__ / <x>.__class__.__name__, an isinstance / type
    test. `safe_message(str(e))` is NOT safe. A function of that name defined or imported from elsewhere in
    the module is not the masking helper."""
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") in _MASKING:
        name = node.func.id
        if name not in safe:
            return False
        if name in {"safe_str", "class_name", "locator"}:
            return True
        first = (
            node.args[0]
            if node.args
            else next((k.value for k in node.keywords if k.arg == "exc"), None)
        )
        return first is not None and _object_expr(first, exc)
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") in {"isinstance", "type"}:
        return True  # a class test or the class object: no message text
    if isinstance(node, ast.Attribute) and node.attr == "__name__":
        v = node.value
        if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "type":
            return True
        if isinstance(v, ast.Attribute) and v.attr == "__class__":
            return True
    return False


def _uses_raw(node: ast.AST, names: set[str], exc: set[str], safe: set[str]) -> bool:
    if _is_safe_wrapper(node, exc, safe):
        return False
    if (
        isinstance(node, ast.Attribute)
        and node.attr in _SAFE_ATTRS
        and _object_expr(node.value, exc)
    ):
        return False
    if isinstance(node, ast.Name) and node.id in names:
        return True
    if isinstance(node, (ast.Attribute, ast.Subscript)) and ast.unparse(node) in names:
        return True
    return any(_uses_raw(c, names, exc, safe) for c in ast.iter_child_nodes(node))


def _text_use(node: ast.AST, names: set[str], exc: set[str], safe: set[str]) -> bool:
    """Like _uses_raw, but the exception OBJECT passed along (f(exc), (x, exc)) is not text; str(exc),
    f"{exc}", .format(exc) and text aliases are."""
    if _is_safe_wrapper(node, exc, safe):
        return False
    if isinstance(node, ast.Name):
        return node.id in names and node.id not in exc
    if isinstance(node, ast.Attribute):
        if node.attr in _SAFE_ATTRS and _object_expr(node.value, exc):
            return False
        return _uses_raw(node, names, exc, safe)
    if isinstance(node, ast.FormattedValue):
        return _uses_raw(node.value, names, exc, safe)
    if isinstance(node, ast.Call):
        f = node.func
        if getattr(f, "id", "") in {"str", "repr", "format", "ascii"} or getattr(f, "attr", "") in {
            "format",
            "format_map",
            "join",
        }:
            return _uses_raw(node, names, exc, safe)
        args = [*node.args, *(k.value for k in node.keywords)]
        return any(_text_use(a, names, exc, safe) for a in args if not _object_expr(a, exc))
    return any(_text_use(c, names, exc, safe) for c in ast.iter_child_nodes(node))


def _truthy(node: ast.AST) -> bool:
    return not (isinstance(node, ast.Constant) and node.value in (False, None))


def _target_names(t: ast.AST) -> set[str]:
    """Names a store taints: the target itself and, for attribute / subscript stores, the parent object."""
    if isinstance(t, (ast.Tuple, ast.List)):
        return set().union(*(_target_names(e) for e in t.elts)) if t.elts else set()
    if isinstance(t, ast.Starred):
        return _target_names(t.value)
    if isinstance(t, ast.Name):
        return {t.id}
    if isinstance(t, (ast.Attribute, ast.Subscript)):
        root = t
        while isinstance(root, (ast.Attribute, ast.Subscript)):
            root = root.value
        return {ast.unparse(t)} | ({root.id} if isinstance(root, ast.Name) else set())
    return set()


def _pattern_names(p: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(p):
        for attr in ("name", "rest"):
            v = getattr(n, attr, None)
            if isinstance(v, str) and isinstance(n, (ast.MatchAs, ast.MatchStar, ast.MatchMapping)):
                out.add(v)
    return out


def _enclosing(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return "<module>"


def _module_info(tree: ast.AST, module: str) -> tuple[set[str], set[str], set[str], set[str]]:
    """Traceback module names, bare traceback functions, aliased log methods (w = _LOG.warning), and the
    masking helpers that really are hadavin_sdk's (not redefined or imported from elsewhere)."""
    tb_mods, tb_funcs, log_funcs = {"traceback"}, set(), set()
    foreign: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            tb_mods |= {a.asname or a.name for a in n.names if a.name == "traceback"}
        elif isinstance(n, ast.ImportFrom):
            if n.module == "traceback":
                tb_funcs |= {a.asname or a.name for a in n.names if a.name in _TRACE}
            elif n.module != "hadavin_sdk.guard.safe_message":
                foreign |= {a.asname or a.name for a in n.names}
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            foreign.add(n.name)
        elif (
            isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Attribute)
            and n.value.attr in _LEVELS
            and _is_logger(n.value.value)
        ):
            log_funcs |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    safe = set(_MASKING) if module == "guard/safe_message.py" else set(_MASKING) - foreign
    if module == "extract.py":
        safe.add("_failure")
    return tb_mods, tb_funcs, log_funcs, safe


def _is_log_getattr(f: ast.AST) -> bool:
    """getattr(_LOG, "warning")(...)"""
    return (
        isinstance(f, ast.Call)
        and getattr(f.func, "id", "") == "getattr"
        and len(f.args) >= 2
        and _is_logger(f.args[0])
        and isinstance(f.args[1], ast.Constant)
        and f.args[1].value in _LEVELS
    )


def _exc_params(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Parameters that carry an exception: named like one, or annotated with an Exception / Error type
    (quoted, Optional, Union, | all count; a Callable that takes one does not)."""
    out = []
    a = fn.args
    for p in [*a.posonlyargs, *a.args, *a.kwonlyargs, *([a.vararg] if a.vararg else [])]:
        note = ast.unparse(p.annotation) if p.annotation is not None else ""
        if "Callable" in note:
            continue
        if note:  # an annotated parameter is an exception only if its type says so
            if re.search(r"(Exception|Error)", note):
                out.append(p.arg)
        elif p.arg in _EXC_PARAM_NAMES:
            out.append(p.arg)
    return out


def _scopes(tree: ast.AST):
    """(node, exception names, body) for every except handler and every (async) function that takes an
    exception: its body is checked as a handler is."""
    for n in ast.walk(tree):
        if isinstance(n, ast.ExceptHandler):
            yield n, [n.name] if n.name else [], n.body
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = _exc_params(n)
            if params:
                yield n, params, n.body


def find_leaks(source: str, module: str = "") -> list[tuple[int, str, str, str]]:
    """(line, why, unparsed statement, enclosing function) for every leak of exception text in a handler,
    plus exception objects obtained outside a handler (future.exception(), gather(return_exceptions=True))."""
    tree = ast.parse(source)
    parents = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    tb_mods, tb_funcs, log_funcs, safe = _module_info(tree, module)
    found: list[tuple[int, str, str, str]] = []
    for n in ast.walk(tree):  # exception objects obtained outside any handler
        if isinstance(n, ast.Call):
            outside = (
                isinstance(n.func, ast.Attribute)
                and n.func.attr == "exception"
                and not n.args
                and not _is_logger(n.func.value)
            ) or any(k.arg == "return_exceptions" and _truthy(k.value) for k in n.keywords)
            if outside:
                found.append(
                    (
                        n.lineno,
                        "exception object obtained outside a handler",
                        ast.unparse(n),
                        _enclosing(n, parents),
                    )
                )
    for scope_node, excs, body in _scopes(tree):
        is_func = isinstance(scope_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        objs = set(excs)  # names bound to the exception OBJECT (e = exc, e = exc.__cause__)
        names = set(excs)
        nodes = [n for st in body for n in ast.walk(st)]
        while True:  # aliases until nothing new: x = str(e), self.x = ..., a, b = ..., for x in ..., with ... as f
            before = (len(names), len(objs))
            for n in nodes:
                if isinstance(n, ast.Assign) and _uses_raw(n.value, names, objs, safe):
                    for t in n.targets:
                        names |= _target_names(t)
                elif isinstance(n, (ast.AnnAssign, ast.NamedExpr)) and n.value is not None:
                    if _uses_raw(n.value, names, objs, safe):
                        names |= _target_names(n.target)
                elif isinstance(n, ast.AugAssign) and _uses_raw(n.value, names, objs, safe):
                    names |= _target_names(n.target)
                elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
                    if _uses_raw(n.iter, names, objs, safe):
                        names |= _target_names(n.target)
                elif isinstance(n, ast.withitem) and n.optional_vars is not None:
                    if _uses_raw(n.context_expr, names, objs, safe):
                        names |= _target_names(n.optional_vars)
                elif isinstance(n, ast.Match) and _uses_raw(n.subject, names, objs, safe):
                    for case in n.cases:
                        names |= _pattern_names(case.pattern)
                v = n.value if isinstance(n, ast.Assign) else None
                if _object_expr(v, objs) if v is not None else False:
                    objs |= {t.id for t in n.targets if isinstance(t, ast.Name)}
            if (len(names), len(objs)) == before:
                break
        fn = scope_node.name if is_func else _enclosing(scope_node, parents)
        raised = {id(n.exc) for n in nodes if isinstance(n, ast.Raise) and n.exc is not None}

        def flag(node: ast.AST, why: str, fn: str = fn) -> None:
            found.append((node.lineno, why, ast.unparse(node), fn))

        for n in nodes:
            if isinstance(n, ast.Raise):
                c = n.exc
                if isinstance(c, ast.Call) and any(
                    _uses_raw(a, names, objs, safe)
                    for a in [*c.args, *(k.value for k in c.keywords)]
                ):
                    flag(n, "raise carries raw exception text")
                continue
            if isinstance(n, (ast.Return, ast.Yield, ast.YieldFrom)) and n.value is not None:
                if (
                    is_func
                ):  # a helper that inspects an exception may return codes; handlers may not leak
                    continue
                if _object_expr(n.value, objs):
                    flag(n, "exception object returned or yielded (a caller may log it)")
                elif _text_use(n.value, names, objs, safe):
                    flag(n, "returns or yields raw exception text")
                continue
            if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and n.value is not None:
                tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                if any(isinstance(t, (ast.Attribute, ast.Subscript)) for t in tg):
                    if _object_expr(n.value, objs):
                        flag(n, "exception object stored outside the handler's scope")
                    elif _text_use(n.value, names, objs, safe):
                        flag(n, "raw exception text stored in an attribute or subscript")
                continue
            if not isinstance(n, ast.Call):
                continue
            ids = _chain(n.func)
            if (
                (ids[:1] and ids[0] in tb_mods and ids[-1] in _TRACE)
                or (len(ids) == 1 and ids[0] in tb_funcs)
                or ids == ["sys", "exc_info"]
                or (ids and ids[-1] in _REPORTERS)
            ):
                flag(n, "traceback / exc_info / reporter in a handler")
                continue
            callee = n.func.id if isinstance(n.func, ast.Name) else None
            method = n.func.attr if isinstance(n.func, ast.Attribute) else None
            if callee in _MASKING and callee in safe:
                first = (
                    n.args[0]
                    if n.args
                    else next((k.value for k in n.keywords if k.arg == "exc"), None)
                )
                text_given = first is not None and not _object_expr(first, objs)
                if (
                    callee in {"safe_message", "safe_text"}
                    and text_given
                    and _uses_raw(first, names, objs, safe)
                ):
                    flag(n, "safe_message / safe_text need the exception object, not its text")
                continue
            kw_vals = [(k.arg, k.value) for k in n.keywords]
            is_log = (
                (
                    method is not None
                    and (method in _LEVELS or (_is_logger(n.func.value) and "audit" in ids))
                )
                or (callee is not None and callee in log_funcs)
                or _is_log_getattr(n.func)
            )
            is_out = (
                ids == ["print"]
                or ids == ["warnings", "warn"]
                or (len(ids) >= 2 and ids[-1] == "write" and ids[-2] in {"stderr", "stdout"})
                or (
                    callee is not None and any(k in callee.lower() for k in ("log", "warn", "emit"))
                )
            )
            if is_log or is_out:
                if method == "exception" and is_log:
                    flag(n, "_LOG.exception logs the traceback")
                for arg, val in kw_vals:
                    if arg == "exc_info" and _truthy(val):  # exc_info branch
                        flag(n, "exc_info")
                parts = [*n.args, *(v for a, v in kw_vals if a != "exc_info")]  # kwargs branch
                if any(_uses_raw(p, names, objs, safe) for p in parts):
                    flag(n, "raw exception text in a log/print")
                continue
            if is_func or callee in _PURE_FUNCS or method in _PURE_METHODS:
                continue  # helpers: only log / print / store / raise sinks are checked
            args = [*n.args, *(v for _, v in kw_vals)]
            if method in _OBJECT_SINKS and any(_object_expr(a, objs) for a in n.args):
                flag(n, "exception object stored in a container or queue")
            elif any(_text_use(a, names, objs, safe) for a in args) and id(n) not in raised:
                flag(
                    n, "raw exception text passed to a call"
                )  # inverted rule: any unknown callee is a sink
    return found


def test_no_raw_exc_in_log_calls_ast():
    from collections import Counter

    bad, used = [], Counter()
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        for line, why, text, fn in find_leaks(path.read_text(encoding="utf-8"), rel):
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
        _HEAD + "with str(e) as f:\n  _LOG.warning('x %s', f)",
        _HEAD + "self.last_error = str(e)",
        _HEAD + "obj.attr['k'] = f'{e}'",
        _HEAD + "for line in str(e).splitlines():\n  _LOG.warning('x %s', line)",
        _HEAD + "with open(str(e)) as f:\n  _LOG.warning('x %s', f)",
        _HEAD + "match str(e):\n  case m:\n   _LOG.warning('x %s', m)",
        _HEAD + "xs = [c for c in str(e)]\n _LOG.warning('x %s', xs)",
        _HEAD + "notify(str(e))",
        _HEAD + "report(f'{e}')",
        _HEAD + "slack_post(text=str(e))",
        _HEAD + "requests.post(url, json={'text': str(e)})",
        _HEAD + "click.echo(str(e))",
        _HEAD + "typer.echo(f'{e}')",
        _HEAD + "console.print(str(e))",
        _HEAD + "out.write(str(e))",
        _HEAD + "l.error('x %s', e)",
        _HEAD + "_L.error('x %s', e)",
        _HEAD + "Row(content=str(e))",
        _HEAD + "Row(failure=str(e))",
        _HEAD + "Row(payload=str(e))",
        _HEAD + "Row(anything=str(e))",
        _HEAD + "errors.append(e)",
        _HEAD + "queue.put(e)",
        _HEAD + "return (1, str(e))",
        _HEAD + "return e",
        _HEAD + "x = e.__cause__\n return x",
        _HEAD + "seen.append(e)",
        _HEAD + "safe_message(str(e))",
        _HEAD + "c = b\n b = a\n a = str(e)\n _LOG.warning('x %s', c)",
        _HEAD + "return str(e)",
        _HEAD + "return f'failed: {e}'",
        _HEAD + "yield str(e)",
        _HEAD + "msg = ''\n msg += str(e)\n _LOG.warning('x %s', msg)",
        _HEAD + "queue.put(str(e))",
        _HEAD + "d.setdefault('k', str(e))",
        _HEAD + "store.save(f'{e}')",
        _HEAD + "d.update({'k': str(e)})",
        _HEAD + "row = Row(str(e))",
        _HEAD + "Row(note=str(e))",
        _HEAD + "Row(text=str(e))",
        _HEAD + "Row(status=str(e))",
        _HEAD + "Row(summary=str(e))",
        _HEAD + "self.err = str(e)\n store.save(self)",
        _HEAD + "d['k'] = str(e)\n store.save(d)",
        _HEAD + "a = str(e)\n b = a\n c = b\n d = c\n e2 = d\n _LOG.warning('x %s', e2)",
        "from traceback import format_exc as fe\n" + _HEAD + "x = fe()",
        "import traceback as tb\n" + _HEAD + "tb.print_exc()",
        _HEAD + "span.record_exception(e)",
        _HEAD + "sentry.capture_exception(e)",
        "w = _LOG.warning\n" + _HEAD + "w(str(e))",
        _HEAD + "getattr(_LOG, 'warning')(str(e))",
        _HEAD + "box['exc'] = e",
        _HEAD + "self.last = e",
        "def f(exc: BaseException):\n print(str(exc))\n",
        "def f(exc: ValueError | None):\n _LOG.warning('x %s', exc)\n",
        "async def f(exc: BaseException):\n print(str(exc))\n",
        "def f(e):\n _LOG.warning('x %s', e)\n",
        "def f(err: 'ValueError'):\n print(err)\n",
        "def f(exc: Optional[BaseException] = None):\n print(str(exc))\n",
        "def f(a, /, exc: Union[ValueError, None]):\n print(str(exc))\n",
        "def safe_text(e):\n return str(e)\ntry:\n pass\nexcept Exception as e:\n _LOG.warning('x %s', safe_text(e))\n",
        "from other import safe_message\ntry:\n pass\nexcept Exception as e:\n _LOG.warning('x %s', safe_message(e))\n",
        "fut.exception()",
        "asyncio.gather(*tasks, return_exceptions=True)",
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
        _HEAD + "x = e.__cause__\n _LOG.warning('x %s', safe_message(x))",
        _HEAD + "_LOG.warning('x %s', e.errno)",
        _HEAD + "_LOG.warning('x %s', safe_message(exc=e))",
        _HEAD + "_LOG.warning('x %s', safe_message(e.__cause__))",
        _HEAD + "return safe_message(e)",
        _HEAD + "return type(e).__name__",
        _HEAD + "return (e.code, None)",
        _HEAD + "return helper('set', e)",
        _HEAD + "d.update(x=1)",
        _HEAD + "Row(note='fixed')",
        _HEAD + "x = e.__cause__\n _LOG.warning('x %s', type(x).__name__)",
        "def f(exc: BaseException):\n _LOG.warning('x %s', type(exc).__name__)\n",
        "def f(detail: Callable[[BaseException], str]):\n _LOG.warning('x')\n",
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
