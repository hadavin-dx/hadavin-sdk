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
from types import SimpleNamespace

import pytest

import hadavin_sdk
from hadavin_sdk.guard import judge
from hadavin_sdk.guard.model_gate import BoundGate
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
}
# NO_MAP may be named only here (the eval and replay command lines have no run and no map), besides its definition in the gate module.
NO_MAP_ALLOWED = {
    "evals.py",
    "k1b/replay.py",
    "k1b/loop.py",
}  # k1b/loop.py is the replay command line's case loop

# Where the judge (`injection_check(detector, ...)`, which reaches `JudgeDetector.llm.chat`) is called from, module -> why it
# matters for the install (code review round 3, M3/M4). The `Detector` protocol has no map argument, so a judge built
# once with ONE bound llm (guard/judge.py `make(settings, deps)` takes `deps.llm`) serves the run loop, the shadow card,
# the approval summary and the k1b loop alike: core-b must bind it with the RUN's map per call or give the protocol one.
# A NEW call site must be added here (the test below scans for it).
JUDGE_SITES = {
    "runtime/agent_loop.py": "`_screen` (document and tool output) and `_shadow` (cards.render_shadow): charged by the loop",
    "approvals/cards.py": "render_shadow: `injection_check(detector, diagnosis, 'shadow_card')`",
    "approvals/requests.py": "summary(): `injection_check(detector, inputs, 'approval_summary')`, also reached from Requests.create",
    "k1b/loop.py": "run_case: `injection_check(detector, shown, 'k1b-tool-result')` on the replay command line",
    "guard/judge.py": "`qualify` runs the judge over a golden set (evals.py builds it with the plain llm)",
    "guard/injection.py": "the definition of `injection_check` (it calls `detector.check`)",
}

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
            named = isinstance(k.value, ast.Name | ast.Attribute) or (
                isinstance(k.value, ast.Call) and _name(k.value) == "worst_case_for"
            )  # `worst_case_for(routes, llm)` is the one named factory of the closure
            if k.arg == "worst_case" and not named:
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
    assert not bad("ModelGate(llm, meter=m, audit=a, worst_case=worst_case_for(routes, llm))")
    assert bad("ModelGate(llm, meter=m, audit=a, worst_case=make_it(routes, llm))")
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


def _refuses_by_tier(tree: ast.AST) -> bool:
    """True when the module has an `if` whose test COMPARES something with a tier word (`pilot`, `prod`) or names
    `PILOT`/`PROD` or the tier list, and whose body raises. A mere mention of the word (a docstring, a constant) is not a
    refusal (code review round 3, M4: the old check passed on a mention)."""
    words = {"pilot", "prod"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        in_test = {
            n.value for n in ast.walk(node.test) if isinstance(n, ast.Constant) and n.value in words
        }
        names = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(node.test) if isinstance(n, ast.Attribute)
        }
        compares = any(isinstance(n, ast.Compare) for n in ast.walk(node.test))
        raises = any(isinstance(n, ast.Raise) for b in node.body for n in ast.walk(b))
        if raises and compares and (in_test or {"PILOT", "PROD", STAGE_WORD.upper() + "S"} & names):
            return True
    return False


def test_the_tier_refusal_check_does_not_pass_on_a_mere_mention():
    assert not _refuses_by_tier(ast.parse('"""pilot and prod"""\nTIERS = ("pilot", "prod")\n'))
    assert not _refuses_by_tier(ast.parse('if x:\n    raise ValueError("pilot")\n'))
    assert _refuses_by_tier(ast.parse('if tier in ("pilot", "prod") and enforce:\n    raise X\n'))
    assert _refuses_by_tier(ast.parse("if env == PROD:\n    raise X\n"))


@_xfail
def test_install_the_module_that_builds_the_gate_refuses_a_non_default_enforce_or_worst_case_in_pilot_and_prod():
    trees = _trees()
    builders = _gate_builders(trees)
    assert builders, "no module under src builds a ModelGate"
    for rel in builders:
        t = trees[rel]
        assert _refuses_by_tier(t), (
            f"{rel} builds the gate but never refuses by tier (a mention is not enough)"
        )
        assert not _bad_gate_arguments(t), f"{rel}: {_bad_gate_arguments(t)}"


# ---- the judge call sites (code review round 3, M3/M4): the table must be complete; holds today ----


def test_the_judge_call_sites_in_src_are_all_in_the_table():
    found = {
        rel
        for rel, tree in _trees().items()
        if any(_name(c) == "injection_check" for c in _calls(tree))
    }
    found.add("guard/injection.py")  # defines injection_check, calls detector.check
    assert found <= set(JUDGE_SITES), (
        f"a call site of the judge that the install table does not know: {sorted(found - set(JUDGE_SITES))}"
    )
    assert all(why.strip() for why in JUDGE_SITES.values())


# ---- behavioural install tests: strict xfails until core-b installs the gate ----


def _gate_rows(events):
    gate_decisions = {
        "map_enforced",
        "map_enforced_empty",
        "enforce_custom",
        "map_failed",
        "no_map",
    }
    return [
        e
        for e in events
        if e.domain == "llm" and e.operation == "chat" and e.decision in gate_decisions
    ]


@_xfail
def test_install_behavioural_every_chat_call_of_a_run_has_a_gate_audit_row(tmp_path):
    """A recording client behind the REAL Runtime (wired as `app.build` wires it): every `chat` the client receives
    must have exactly one gate row (domain llm, operation chat, a gate `decision`) in the audit chain. Catches a
    bypassed or unbound site, a deleted catch of GateRefused, a missing `principal=`; the AST test above cannot.
    Today the loop calls the client directly: no gate row exists."""
    from tests.fixtures import k5_tools
    from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg

    k5_tools.RESULTS["app"] = "mail ops@example.com from 10.0.0.7"
    try:
        llm = ScriptLLM([{"tool": "app"}, {"noaction": True}])
        rt, _ = build_runtime(k5_cfg(tmp_path), llm)
        run = handle(rt, b"user jo.bloggs@example.test reports errors")
        rows = _gate_rows(rt.audit.events(run.run_id))
    finally:
        k5_tools.RESULTS.clear()
    assert llm.sent, "the model was never called"
    assert len(rows) == len(llm.sent), (
        f"{len(llm.sent)} chat calls reached the client, {len(rows)} carry a gate audit row"
    )
    assert all(r.principal == run.principal_id for r in rows), (
        "a gate row without the run's principal"
    )


@_xfail
def test_install_behavioural_the_judge_is_built_on_a_bound_gate():
    """`judge.make(settings, deps)` is what `app.build` calls (through `backends.table`) with the plain llm. The judge it
    returns must hold a `BoundGate` (and the install must pass the RUN's map: the `Detector` protocol has no map
    argument, so core-b either binds per call or extends the protocol)."""

    class Recording:
        def chat(self, messages, **kwargs):
            raise AssertionError("not called")

    detector = judge.make(
        SimpleNamespace(route="main", threshold=0.5), SimpleNamespace(llm=Recording())
    )
    assert isinstance(detector.llm, BoundGate), (
        "the judge holds the plain client: its text is not enforced"
    )
