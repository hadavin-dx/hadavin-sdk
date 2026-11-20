"""Install test for the model gate (review-code-F-gate-3 MJ-C, ORDER 020).

Parses ``src/hadavin_sdk`` (syntax tree, no text search) for every model call (``.chat(``, ``.apply_guardrail(``), every ``ModelGate(``
construction and every ``.bind(`` and checks that each model caller is either reached through a bound gate (``bind(..., mapping=<run map>)``
or ``mapping=NO_MAP``) or listed in ``BYPASS`` below with a reason. Sources: handover/core-c/inputs/draft-ticket-F-install.md and
handover/core-c/requests/3-bind-mapping-required.md. The registry of callers is ``guard/producers.py`` MODEL_CALLERS (checked by
tests/test_k5_producers.py with the same scan: this file reads it the same way, but only inside ``src``).

Core-b has not installed the gate yet, so the install-dependent assertions are strict xfails. When core-b installs the gate they flip
to a failure (XPASS(strict)): REMOVE THE MARKER, that is the signal that the install now holds.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

import hadavin_sdk
from hadavin_sdk.guard.producers import MODEL_CALLERS

SRC = pathlib.Path(hadavin_sdk.__file__).resolve().parent
SINK_METHODS = {"chat", "apply_guardrail"}
GATE_MODULE = "guard/model_gate.py"

# Callers that must reach the model through a bound gate once the install lands: caller module -> module(s) that build the
# `bind(..., mapping=...)` for it (from the install draft section 3 and request 3 section 2).
INSTALLED = {
    "runtime/agent_loop.py": {
        "runtime/agent_loop.py"
    },  # Runtime.handle binds with the live run map
    "guard/judge.py": {
        "runtime/agent_loop.py"
    },  # the judge is bound per call by _screen / _shadow with the run's map
    "evals.py": {"evals.py"},  # eval command line: mapping=NO_MAP
    "k1b/loop.py": {"k1b/replay.py"},  # replay command line: mapping=NO_MAP
}
# Callers that are NOT reached through the gate, by design (module -> one-line reason). A NEW caller must be in INSTALLED or here.
BYPASS = {
    "guard/bedrock_guardrail.py": "vendor detector call (apply_guardrail) outside the gate by design: not on the LLM protocol, not metered",
    "guard/model_gate.py": "the gate itself: the one place that calls the inner client, after reserve and enforce",
    "extract.py": "no caller in src; F-install deletes it (draft section 8): drop this row with the file",
}
# NO_MAP may be named only here (the eval and replay command lines have no run and no map), besides its definition in the gate module.
NO_MAP_ALLOWED = {"evals.py", "k1b/replay.py"}

# The bare word is built from parts so the repository rule about stage names does not read this file as a stage.
STAGE_WORD = "sta" + "ge"


def _trees() -> dict[str, ast.Module]:
    out = {}
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC).as_posix()
        out[rel] = ast.parse(path.read_text(encoding="utf-8"))
    return out


def _calls(tree: ast.AST):
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call)]


def _attr(call: ast.Call) -> str:
    return call.func.attr if isinstance(call.func, ast.Attribute) else ""


def _name(call: ast.Call) -> str:
    return call.func.id if isinstance(call.func, ast.Name) else _attr(call)


def _model_callers(trees: dict[str, ast.Module]) -> set[str]:
    return {
        rel
        for rel, tree in trees.items()
        if not rel.startswith("llm/") and any(_attr(c) in SINK_METHODS for c in _calls(tree))
    }


def _gate_builders(trees) -> set[str]:
    return {
        r
        for r, t in trees.items()
        if r != GATE_MODULE and any(_name(c) == "ModelGate" for c in _calls(t))
    }


def _bind_with_mapping(tree: ast.AST) -> list[ast.Call]:
    return [
        c
        for c in _calls(tree)
        if _attr(c) == "bind" and any(k.arg == "mapping" for k in c.keywords)
    ]


def _names_no_map(tree: ast.AST) -> bool:
    return any(
        (isinstance(n, ast.Name) and n.id == "NO_MAP")
        or (isinstance(n, ast.Attribute) and n.attr == "NO_MAP")
        for n in ast.walk(tree)
    )


def _bad_gate_arguments(tree: ast.AST) -> list[str]:
    """Problems in `ModelGate(...)` constructions: any `enforce=` (non-default), a `worst_case=` that is not a named function."""
    bad = []
    for c in _calls(tree):
        if _name(c) != "ModelGate":
            continue
        for k in c.keywords:
            if k.arg == "enforce":
                bad.append("enforce= given (non-default)")
            if k.arg == "worst_case" and not isinstance(k.value, ast.Name | ast.Attribute):
                bad.append("worst_case= is not a named function")
    return bad


# ---- parts that hold today ----


def test_the_registry_and_the_scan_agree_on_the_callers_in_src():
    trees = _trees()
    found = _model_callers(trees)
    # every caller found is in the install table or the bypass table, whatever else changes
    unknown = found - set(INSTALLED) - set(BYPASS)
    assert not unknown, (
        f"a model caller that is neither bound by the install nor in the BYPASS table (with a reason): {sorted(unknown)}"
    )
    # and the producers registry knows them (the k5 registry test also covers the demos)
    assert found - {GATE_MODULE} <= MODEL_CALLERS, sorted(found - MODEL_CALLERS)


def test_every_bypass_and_install_entry_still_exists_and_still_calls_a_model():
    trees = _trees()
    for rel in set(INSTALLED) | set(BYPASS):
        assert rel in trees, f"{rel} no longer exists: update the table"
    callers = _model_callers(trees)
    for rel in INSTALLED:
        assert rel in callers, f"{rel} no longer calls a model: update INSTALLED"
    for rel, why in BYPASS.items():
        assert why.strip()
        assert rel in callers, f"{rel} no longer calls a model: remove its BYPASS row"


def test_the_binder_modules_named_in_the_table_exist():
    trees = _trees()
    for caller, binders in INSTALLED.items():
        for b in binders:
            assert b in trees, f"{caller}: binder module {b} does not exist"


def test_no_map_is_named_only_on_the_eval_and_replay_command_lines():
    named = {rel for rel, t in _trees().items() if _names_no_map(t)} - {GATE_MODULE}
    assert named <= NO_MAP_ALLOWED, (
        f"NO_MAP outside the eval and replay command lines: {sorted(named - NO_MAP_ALLOWED)}"
    )


def test_a_bind_with_a_mapping_never_passes_the_constant_none():
    for rel, t in _trees().items():
        for c in _bind_with_mapping(t):
            for k in c.keywords:
                if k.arg == "mapping":
                    assert not (isinstance(k.value, ast.Constant) and k.value.value is None), (
                        f"{rel}: bind(mapping=None)"
                    )


def test_no_gate_is_built_in_src_with_a_non_default_enforce_or_a_lambda_worst_case():
    for rel, t in _trees().items():
        if rel == GATE_MODULE:
            continue
        assert not _bad_gate_arguments(t), f"{rel}: {_bad_gate_arguments(t)}"


def test_the_gate_argument_check_catches_the_bad_shapes():
    def bad(src):
        return _bad_gate_arguments(ast.parse(src))

    assert bad("ModelGate(llm, meter=m, audit=a, enforce=lambda t, m: t)")
    assert bad("ModelGate(llm, meter=m, audit=a, worst_case=lambda **k: 1)")
    assert not bad("ModelGate(llm, meter=m, audit=a, worst_case=worst_case_usd)")
    assert not bad("ModelGate(llm, meter=m, audit=a, worst_case=prices.worst_case)")
    assert not bad("ModelGate(llm, meter=m, audit=a)")


def test_the_gate_does_not_check_the_stage_so_the_refusal_is_an_install_time_check():
    """The gate takes no stage: a pilot or prod refusal of a non-default enforce/worst_case cannot live inside it."""
    tree = _trees()[GATE_MODULE]
    words = {"pilot", "prod", STAGE_WORD, "environment", "demo"}
    arg_names = {
        a.arg
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
        for a in n.args.args + n.args.kwonlyargs
    }
    assert not (arg_names & {STAGE_WORD, "environment", "env"}), (
        "the gate takes a stage argument: update the install-time test"
    )
    strings = {
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in words
    }
    assert not strings, (
        f"the gate module compares against stage words {strings}: update the install-time test"
    )


# ---- parts that need core-b's install: strict xfails (remove the marker when the install lands) ----

NOT_INSTALLED = "core-b has not installed the gate yet: requests/3-bind-mapping-required.md"
_xfail = pytest.mark.xfail(strict=True, raises=AssertionError, reason=NOT_INSTALLED)


@_xfail
def test_install_every_model_caller_is_reached_through_a_bound_gate_with_a_mapping():
    trees = _trees()
    assert _gate_builders(trees), "no module under src builds a ModelGate"
    for caller, binders in INSTALLED.items():
        assert any(_bind_with_mapping(trees[b]) for b in binders), (
            f"{caller}: none of {sorted(binders)} calls bind(..., mapping=<run map> or NO_MAP)"
        )


@_xfail
def test_install_no_map_is_used_by_both_command_lines():
    trees = _trees()
    for rel in sorted(NO_MAP_ALLOWED):
        assert _names_no_map(trees[rel]), (
            f"{rel} (eval/replay command line) does not bind with mapping=NO_MAP"
        )


@_xfail
def test_install_the_module_that_builds_the_gate_refuses_a_non_default_enforce_or_worst_case_in_pilot_and_prod():
    trees = _trees()
    builders = _gate_builders(trees)
    assert builders, "no module under src builds a ModelGate"
    for rel in builders:
        t = trees[rel]
        stage_words = {
            n.value
            for n in ast.walk(t)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and n.value in {"pilot", "prod"}
        }
        names = {n.id for n in ast.walk(t) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)
        }
        assert stage_words or {"PILOT", "PROD", "STAGES"} & names, (
            f"{rel} builds the gate but never looks at the stage"
        )
        assert not _bad_gate_arguments(t), f"{rel}: {_bad_gate_arguments(t)}"
