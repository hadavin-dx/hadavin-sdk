"""R7: a source tripwire for the common ways provider text could reach a raise, a print or a log call in ``src/hadavin_sdk/llm``.

It is NOT a proof (the later code scan is). It walks the ``ast`` of each module with these rules:

* tainted values: ``str(e)`` / ``repr(e)`` / ``format(e)`` / ``ascii(e)``, an f-string ``{e}``, the attributes ``args message msg reason
  response body text content __name__ __qualname__`` of an exception-derived name (also through ``getattr(e, "<const>")``), and
  ``e.read()``. Exception-derived: an ``except ... as e`` name, a parameter named exc/e/err/error/ex, and one level of alias.
* sinks: ``raise``, ``print``, a logging call, an argument of ``ProviderError`` / ``ProviderExhausted``; a tainted value in a sink is flagged.
* t2: ANY read of ``.__name__`` / ``.__qualname__`` on any expression is flagged, in ``describe`` too (no allow-list).
* t3: a function, parameter, class attribute or keyword named ``detail`` is flagged.
* t4: ``return`` in a function with an exception-derived parameter may not contain ``str(`` / ``repr(`` / ``format(``, ``.join(`` or an
  f-string, except in the allow-listed ``retry.describe`` and ``bedrock._code``.
* only ``retry.describe`` may call ``class_name_of``; a ``logging`` import or a ``print`` in ``llm/`` is flagged.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

LLM = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk" / "llm"
EXC_PARAMS = {"exc", "e", "err", "error", "ex"}
TAINT_ATTRS = {
    "args",
    "message",
    "msg",
    "reason",
    "response",
    "body",
    "text",
    "content",
    "__name__",
    "__qualname__",
}
STRINGIFIERS = {"str", "repr", "format", "ascii"}
CTORS = {"ProviderError", "ProviderExhausted"}
T4_ALLOW = {"retry.describe", "bedrock._code"}
# The one construction-time entry (removed when the code scan lands; the test fails once it is stale).
ENTRY = ("anthropic.client", "sink-tainted")


def _name(node) -> str | None:
    return (
        node.id
        if isinstance(node, ast.Name)
        else node.attr
        if isinstance(node, ast.Attribute)
        else None
    )


def _is_exc(node, E) -> bool:
    return isinstance(node, ast.Name) and node.id in E


def _tainted(node, E) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            f = sub.func
            if (
                isinstance(f, ast.Name)
                and f.id in STRINGIFIERS
                and sub.args
                and any(_is_exc(a, E) or _tainted(a, E) for a in sub.args)
            ):
                return True
            if (
                isinstance(f, ast.Name)
                and f.id == "getattr"
                and len(sub.args) >= 2
                and _is_exc(sub.args[0], E)
            ):
                c = sub.args[1]
                if isinstance(c, ast.Constant) and c.value in TAINT_ATTRS:
                    return True
            if isinstance(f, ast.Attribute) and f.attr == "read" and _is_exc(f.value, E):
                return True
        if isinstance(sub, ast.FormattedValue) and (_is_exc(sub.value, E)):
            return True
        if isinstance(sub, ast.Attribute) and sub.attr in TAINT_ATTRS and _is_exc(sub.value, E):
            return True
    return False


def _exc_names(fn) -> set[str]:
    E = {
        a.arg
        for a in [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]
        if a.arg in EXC_PARAMS
    }
    for node in ast.walk(fn):
        if isinstance(node, ast.ExceptHandler) and node.name:
            E.add(node.name)
    for node in ast.walk(fn):  # one level of alias
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id in E:
            E |= {t.id for t in node.targets if isinstance(t, ast.Name)}
    return E


def _is_sink(node) -> bool:
    if isinstance(node, ast.Raise):
        return True
    if isinstance(node, ast.Call):
        n = _name(node.func)
        if n in CTORS or n == "print":
            return True
        base = node.func.value if isinstance(node.func, ast.Attribute) else None
        return isinstance(base, ast.Name) and base.id.lower() in {
            "logging",
            "log",
            "logger",
            "_log",
            "_logger",
        }
    return False


def analyze(source: str, module: str) -> list[str]:
    """Flags for one module's source: ``["<module>:<line> <qualified function> <rule>"]``."""
    tree = ast.parse(source)
    flags: list[str] = []

    def flag(node, qual, rule):
        flags.append(f"{module}:{getattr(node, 'lineno', 0)} {module}.{qual} {rule}")

    # module level
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "logging" for a in node.names
        ):
            flag(node, "<module>", "logging-import")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "logging":
            flag(node, "<module>", "logging-import")
        if (
            isinstance(node, ast.Attribute)
            and node.attr in {"__name__", "__qualname__"}
            and isinstance(node.ctx, ast.Load)
        ):
            flag(node, "<any>", "t2-name-read")
        if isinstance(node, ast.Call) and _name(node.func) == "print":
            flag(node, "<any>", "print")
        if isinstance(node, ast.keyword) and node.arg == "detail":
            flag(node, "<any>", "t3-detail")
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                tgt = (
                    [t.id for t in item.targets if isinstance(t, ast.Name)]
                    if isinstance(item, ast.Assign)
                    else [item.target.id]
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
                    else []
                )
                if "detail" in tgt:
                    flag(item, node.name, "t3-detail")

    def walk(body, prefix):
        for node in body:
            if isinstance(node, ast.ClassDef):
                walk(node.body, prefix + node.name + ".")
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                qual = prefix + node.name
                if node.name == "detail" or any(
                    a.arg == "detail"
                    for a in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                ):
                    flag(node, qual, "t3-detail")
                E = _exc_names(node)
                for sub in ast.walk(node):
                    if _is_sink(sub) and _tainted(sub, E):
                        flag(sub, qual, "sink-tainted")
                    if (
                        isinstance(sub, ast.Call)
                        and _name(sub.func) == "class_name_of"
                        and qual != "describe"
                    ):
                        flag(sub, qual, "class_name_of-outside-describe")
                    if isinstance(sub, ast.Return) and sub.value is not None:
                        has_param = any(
                            a.arg in EXC_PARAMS
                            for a in [
                                *node.args.posonlyargs,
                                *node.args.args,
                                *node.args.kwonlyargs,
                            ]
                        )
                        if has_param and f"{module}.{qual}" not in T4_ALLOW:
                            for r in ast.walk(sub.value):
                                if (
                                    isinstance(r, ast.Call)
                                    and (
                                        (isinstance(r.func, ast.Name) and r.func.id in STRINGIFIERS)
                                        or (
                                            isinstance(r.func, ast.Attribute)
                                            and r.func.attr == "join"
                                        )
                                    )
                                ) or isinstance(r, ast.JoinedStr):
                                    flag(sub, qual, "t4-return-text")
                                    break
                walk(node.body, qual + ".")  # nested functions

    walk(tree.body, "")
    return flags


def _real_flags() -> list[str]:
    out: list[str] = []
    for path in sorted(LLM.glob("*.py")):
        out += analyze(path.read_text(encoding="utf-8"), path.stem)
    return out


def test_r7_the_llm_sources_have_no_unsanctioned_text_channel():
    flags = _real_flags()
    assert any(f" {ENTRY[0]} {ENTRY[1]}" in f for f in flags), (
        "the anthropic.client allow-list entry is stale: remove it (the code scan landed)"
    )
    rest = [f for f in flags if f" {ENTRY[0]} {ENTRY[1]}" not in f]
    assert rest == [], rest


PLANTED = {
    "fstring-exc": (
        "def go(exc, label):\n    raise ProviderError(f'{label}: {exc}')\n",
        "sink-tainted",
    ),
    "class-name-outside-describe": (
        "def go(exc):\n    return class_name_of(exc)\n",
        "class_name_of-outside-describe",
    ),
    "dunder-name-outside-describe": (
        "def go(exc, label):\n    raise ProviderError(f'{type(exc).__name__}')\n",
        "t2-name-read",
    ),
    "alias": ("def go(exc):\n    x = exc\n    raise ProviderError(f'{x}')\n", "sink-tainted"),
    "t2-inside-describe": ("def describe(exc):\n    return type(exc).__name__\n", "t2-name-read"),
    "t3-function": ("def detail(exc):\n    return 'x'\n", "t3-detail"),
    "t3-parameter": ("def go(exc, detail=None):\n    return 1\n", "t3-detail"),
    "t3-keyword": ("def go(exc):\n    with_retry(1, detail=2)\n", "t3-detail"),
    "t3-class-attribute": ("class K:\n    detail = None\n", "t3-detail"),
    "t4-join": (
        "def info(exc):\n    r = exc.response\n    return ' '.join(str(p) for p in (r,))\n",
        "t4-return-text",
    ),
    "t1-getattr": (
        "def go(exc):\n    raise ProviderError(getattr(exc, 'message', ''))\n",
        "sink-tainted",
    ),
    "t1-getattr-qualname": (
        "def go(exc):\n    raise ProviderError(getattr(exc, '__qualname__', ''))\n",
        "sink-tainted",
    ),
    "print": ("def go(exc):\n    print('x')\n", "print"),
    "logging-import": ("import logging\n", "logging-import"),
    "logging-call": ("def go(exc):\n    log.warning(str(exc))\n", "sink-tainted"),
    "read-call": ("def go(exc):\n    raise ProviderError(exc.read())\n", "sink-tainted"),
    "except-variable": (
        "def go():\n    try:\n        pass\n    except Exception as e:\n        raise ProviderError(repr(e))\n",
        "sink-tainted",
    ),
}


@pytest.mark.parametrize("name", PLANTED)
def test_r7_each_planted_violation_is_flagged(name):
    source, rule = PLANTED[name]
    flags = analyze(source, "planted")
    assert any(f.endswith(rule) for f in flags), (name, flags)


def test_r7_the_sanctioned_path_passes():
    good = (
        "def describe(exc, facts):\n"
        "    try:\n        class_text = class_name_of(exc)\n    except Exception:\n        class_text = 'dynamic_class'\n"
        "    parts = [class_text]\n    return ' '.join(parts)\n"
        "def with_retry(call, label, attempt):\n"
        "    try:\n        return call()\n    except Exception as exc:\n"
        "        raise ProviderError(f'{label}: {describe(exc, None)} after {attempt} attempts') from None\n"
    )
    assert analyze(good, "retry") == []
