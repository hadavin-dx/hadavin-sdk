"""Registry test: every producer of model-bound text goes through the redaction choke point (`guard/producers.py`).
The checks are on the syntax tree of the IMPORTED package, so a mutated copy is seen."""

from __future__ import annotations

import ast
import pathlib

import pytest

import hadavin_sdk
from hadavin_sdk.guard.producers import (
    CHOKE_FAMILY,
    CHOKE_POINT,
    MODEL_CALLERS,
    OUTSIDE_THE_CHOKE_POINT,
    PRODUCERS,
)

ROOT = pathlib.Path(hadavin_sdk.__file__).resolve().parent
REPO = ROOT.parents[1]
SINK_METHODS = {"chat", "apply_guardrail"}


def _tree(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _functions(tree: ast.AST, name: str) -> list[ast.AST]:
    return [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == name
    ]


def _called_names(fn: ast.AST) -> set[str]:
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    return out


@pytest.mark.parametrize("row", PRODUCERS, ids=[r[0] for r in PRODUCERS])
def test_each_producer_calls_its_redaction_function(row):
    name, rel, func, chokes = row
    fns = _functions(_tree(ROOT / rel), func)
    assert fns, f"{name}: {rel}:{func} does not exist"
    assert any(_called_names(f) & chokes for f in fns), (
        f"{name}: {func} no longer calls any of {sorted(chokes)}"
    )


def _call_graph(rels: set[str]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for rel in rels:
        for fn in ast.walk(_tree(ROOT / rel)):
            if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                graph.setdefault(fn.name, set()).update(_called_names(fn))
    return graph


@pytest.mark.parametrize("fn", sorted(CHOKE_FAMILY))
def test_every_redaction_function_reaches_the_one_choke_point(fn):
    graph = _call_graph(set(CHOKE_FAMILY.values()))
    seen, todo = set(), [fn]
    while todo:
        cur = todo.pop()
        if cur in seen:
            continue
        seen.add(cur)
        todo.extend(graph.get(cur, ()))
    assert CHOKE_POINT in seen, f"{fn} does not reach {CHOKE_POINT}"


def _sink_callers() -> set[str]:
    callers = set()
    roots = [(ROOT, ""), (REPO / "demos", "demos/")]
    for base, prefix in roots:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            rel = prefix + path.relative_to(base).as_posix()
            if rel.startswith("llm/"):  # the adapters ARE the sink
                continue
            for n in ast.walk(_tree(path)):
                if (
                    isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr in SINK_METHODS
                ):
                    callers.add(rel)
    return callers


def test_every_module_that_calls_a_model_is_registered():
    callers = _sink_callers()
    assert callers <= MODEL_CALLERS, f"unregistered model caller: {sorted(callers - MODEL_CALLERS)}"
    registered = {r[1] for r in PRODUCERS}
    unexplained = {
        c for c in MODEL_CALLERS if c not in registered and c not in OUTSIDE_THE_CHOKE_POINT
    }
    assert not unexplained, (
        f"a model caller with no producer row and no reviewed reason: {sorted(unexplained)}"
    )


def _is_str_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"str", "repr"}
    )


def test_no_message_is_cut_with_a_slice_before_it_is_redacted():
    """A cut of exception or message text (`str(x)[:N]`, or a name assigned from `str(x)` and then sliced) is the
    cut-before-redact bug class: use `safe_head`. The check follows one assignment (`m = str(exc)` ... `m[:N]`)."""
    bad = []
    for path in ROOT.rglob("*.py"):
        tree = _tree(path)
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            strs = {
                t.id
                for n in ast.walk(fn)
                if isinstance(n, ast.Assign) and _is_str_call(n.value)
                for t in n.targets
                if isinstance(t, ast.Name)
            }
            for n in ast.walk(fn):
                if (
                    isinstance(n, ast.Subscript)
                    and isinstance(n.slice, ast.Slice)
                    and n.slice.lower is None
                ):
                    v = n.value
                    if _is_str_call(v) or (isinstance(v, ast.Name) and v.id in strs):
                        bad.append(f"{path.relative_to(ROOT).as_posix()}:{n.lineno}")
    # `tools.error_reason` slices a message that was ALREADY redacted into `message` (assigned from redact_bounded)
    assert not [b for b in bad if not b.startswith("tools.py:")], bad


REDACTORS = {
    "redact_text",
    "redact_untrusted",
    "redact_bounded",
    "redact_value",
    "redact_layered",
    "safe_head",
    "clean",
    "redact_for_people",
}


def _is_redactor_value(node: ast.AST) -> bool:
    """A call to a redaction function, possibly indexed (`redact_bounded(...)[0]`) or `.replace`d."""
    while isinstance(node, ast.Subscript | ast.Attribute):
        node = node.value
    if isinstance(node, ast.Call):
        f = node.func
        name = f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")
        if name in REDACTORS:
            return True
        if isinstance(f, ast.Attribute):  # `safe_head(...).replace(...)`
            return _is_redactor_value(f.value)
    return False


def test_in_producer_functions_a_head_slice_only_follows_a_redaction():
    """Data-flow aware AND ordered: in every registered producer function a head slice `x[:N]` must slice a value that
    was assigned from a redaction function (or from a slice of such a name) on an EARLIER line. A slice inside the very
    statement that assigns the name (`m = redact(m[:150])`) is a cut before redaction. A digest prefix
    (`plan.hash()[:12]`) is not text."""
    bad = []
    for name, rel, func, _chokes in PRODUCERS:
        for fn in _functions(_tree(ROOT / rel), func):
            redacted_after: dict[
                str, int
            ] = {}  # name -> the line after which it holds redacted text
            for _ in range(
                3
            ):  # a small fixed point: names derived from a redacted name stay redacted
                for n in ast.walk(fn):
                    if not isinstance(n, ast.Assign):
                        continue
                    src = n.value
                    derived = (
                        isinstance(src, ast.Subscript)
                        and isinstance(src.value, ast.Name)
                        and src.value.id in redacted_after
                        and src.lineno > redacted_after[src.value.id]
                    )
                    if _is_redactor_value(src) or derived:
                        for t in n.targets:
                            if isinstance(t, ast.Name):
                                redacted_after[t.id] = min(
                                    redacted_after.get(t.id, 10**9), n.end_lineno or n.lineno
                                )
            for n in ast.walk(fn):
                if (
                    isinstance(n, ast.Subscript)
                    and isinstance(n.slice, ast.Slice)
                    and n.slice.lower is None
                ):
                    v = n.value
                    is_hash = isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "hash"
                    after = (
                        isinstance(v, ast.Name)
                        and v.id in redacted_after
                        and n.lineno > redacted_after[v.id]
                    )
                    if not (is_hash or _is_redactor_value(v) or after):
                        bad.append(f"{name}: {rel}:{n.lineno}")
    assert not bad, bad
