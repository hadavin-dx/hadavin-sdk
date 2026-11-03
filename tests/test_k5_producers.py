"""Registry test: every producer of model-bound text goes through the redaction choke point (`guard/producers.py`)."""

from __future__ import annotations

import ast
import pathlib

import pytest

from hadavin_sdk.guard.producers import MODEL_CALLERS, PRODUCERS

ROOT = pathlib.Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"


def _tree(rel: str) -> ast.Module:
    return ast.parse((ROOT / rel).read_text(encoding="utf-8"))


def _called_names(fn: ast.AST) -> set[str]:
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", ""))
    return out


@pytest.mark.parametrize("row", PRODUCERS, ids=[r[0] for r in PRODUCERS])
def test_each_producer_calls_its_choke_point(row):
    name, rel, func, chokes = row
    fns = [
        n
        for n in ast.walk(_tree(rel))
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == func
    ]
    assert fns, f"{name}: {rel}:{func} does not exist"
    assert any(_called_names(f) & chokes for f in fns), (
        f"{name}: {func} no longer calls any of {sorted(chokes)}"
    )


def test_every_module_that_calls_a_model_is_registered():
    callers = set()
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("llm/"):  # the adapters ARE the sink
            continue
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "chat"
            ):
                callers.add(rel)
    assert callers <= MODEL_CALLERS, (
        f"unregistered model caller: {sorted(callers - MODEL_CALLERS)}; add its producer rows"
    )
    registered = {r[1] for r in PRODUCERS}
    # every caller is a producer row itself, or (k1b/loop.py) sends only what the k1b bundle row masked
    assert {c for c in MODEL_CALLERS if c not in registered} <= {"k1b/loop.py"}


def test_no_message_is_cut_with_a_slice_before_it_is_redacted():
    """`str(exc)[:N]` is the cut-before-redact bug class (a cut splits a secret): use `safe_head`."""
    bad = []
    for path in ROOT.rglob("*.py"):
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(n, ast.Subscript)
                and isinstance(n.slice, ast.Slice)
                and n.slice.lower is None
                and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Name)
                and n.value.func.id == "str"
            ):
                bad.append(f"{path.relative_to(ROOT).as_posix()}:{n.lineno}")
    assert not bad, bad
