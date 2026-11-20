"""Ticket E14: a memory cap on the redactor's finder build (`defaults.MAX_FINDER_CHARS`, trie nodes of the first trie) and a
run-level character cap on the map (`evidence.max_map_chars`, ends `document_too_complex`).

Every assertion message starts with its id and a space (`E14-Tn ...`): the mutants of `tests/e14_mutants.py` expect it.
`v(c, n)` is the character `c` followed by n-1 random letters and digits (a fixed seed): distinct first characters share no node.
"""

from __future__ import annotations

import importlib
import random
import string
import sys
import time

import pytest
from pydantic import ValidationError

from hadavin_sdk import defaults
from hadavin_sdk.config import EvidenceSettings
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import RunState as S
from tests.fixtures import k5_tools
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

_ALPHA = string.ascii_letters + string.digits


def _fail(msg):
    raise AssertionError(
        msg
    ) from None  # an assertion, not pytest.Failed: the mutant runner judges the reason


def v(c: str, n: int) -> str:
    rng = random.Random(f"{c}{n}")
    return c + "".join(rng.choices(_ALPHA, k=n - 1))


def test_t1_a_build_over_the_cap_is_refused(monkeypatch):
    monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", 1000, raising=False)
    red = R._Redactor({"<SECRET_1>": v("a", 600), "<SECRET_2>": v("b", 600)})
    try:
        red.sweep("x")
    except runmap.InputTooLarge as exc:
        assert "FinderMemoryTooMuch" in str(exc), f"E14-T1 wrong refusal: {exc!r}"
    else:
        _fail("E14-T1 the build over the cap was accepted")


def test_t2_the_boundary_is_the_constant(monkeypatch):
    va, vb = v("a", 500), v("b", 500)
    rules = {"<SECRET_1>": va, "<SECRET_2>": vb}
    monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", 1000, raising=False)
    try:
        out = R._Redactor(dict(rules)).sweep("q " + va + " q")
    except runmap.InputTooLarge:
        _fail("E14-T2 exactly 1,000 nodes at cap 1,000 was refused")
    assert out == "q <SECRET_1> q", f"E14-T2 the build at the cap did not mask: {out!r}"
    monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", 999, raising=False)
    with pytest.raises(runmap.InputTooLarge, match="FinderMemoryTooMuch"):
        R._Redactor(dict(rules)).sweep("x")


def test_t3_nodes_not_characters(monkeypatch):
    p = v("p", 500)
    rules = {
        "<SECRET_1>": p + "x" * 300,
        "<SECRET_2>": p + "y" * 300,
    }  # 1,100 nodes, 1,600 characters
    monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", 1100, raising=False)
    try:
        R._Redactor(dict(rules)).sweep("x")
    except runmap.InputTooLarge:
        _fail(
            "E14-T3 a build of 1,100 nodes at cap 1,100 was refused (characters counted, not nodes)"
        )
    monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", 1099, raising=False)
    with pytest.raises(runmap.InputTooLarge, match="FinderMemoryTooMuch"):
        R._Redactor(dict(rules)).sweep("x")


def test_t4_refuse_never_skip(monkeypatch):
    va, vb = v("a", 600), v("b", 600)
    m = runmap.RunMap()
    runmap.redact_untrusted("password=" + va, m)
    assert any(x == va for x in m.values()), "E14-T4 setup: the first value was not planted"
    before, cache = dict(m), {k: id(x) for k, x in m.redact_cache.items()}
    monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", 1000, raising=False)
    with pytest.raises(runmap.InputTooLarge, match="FinderMemoryTooMuch"):
        runmap.redact_untrusted("password=" + vb + " and " + va, m)
    assert dict(m) == before, "E14-T4 the refused call changed the run's map"
    assert {k: id(x) for k, x in m.redact_cache.items()} == cache, (
        "E14-T4 the refused call changed the cache"
    )
    mine = dict(before)
    with pytest.raises(runmap.InputTooLarge, match="FinderMemoryTooMuch"):
        R.redact_many(["password=" + va, "password=" + vb], mine)
    assert mine == before, "E14-T4 redact_many changed the caller's dict on a refusal"


def test_t5_the_gate_refuses_too(monkeypatch):
    va, vb = v("a", 600), v("b", 600)
    m = runmap.RunMap({"<SECRET_1>": va, "<SECRET_2>": vb})
    monkeypatch.setattr(defaults, "MAX_FINDER_CHARS", 1000, raising=False)
    with pytest.raises(runmap.InputTooLarge, match="FinderMemoryTooMuch"):
        runmap.enforce_map("x " + va, m)
    assert runmap.enforce_map("x", {}) == "x", "E14-T5 an empty map must stay free"


NINE = " ".join(f"10.1.1.{i}" for i in range(1, 10)).encode()  # 9 IPv4 values of 8 characters: 72


def test_t6_document_path_boundary(tmp_path):
    outcomes = {}
    for cap in (72, 71):
        cfg = k5_cfg(tmp_path / str(cap), config={"evidence": {"max_map_chars": cap}})
        rt, _ = build_runtime(cfg, ScriptLLM([{"noaction": True}]))
        run = handle(rt, document=NINE)
        outcomes[cap] = (run.state, run.reason_code)
        if cap == 71:
            assert all(e.caught_by is None for e in rt.audit.events(run.run_id)), (
                "E14-T6 a refusal must not be a catch"
            )
    assert outcomes[72] == (S.NO_ACTION, outcomes[72][1]), (
        f"E14-T6 cap 72 must accept: {outcomes[72]}"
    )
    assert outcomes[71] == (S.NEEDS_PERSON, "document_too_complex"), (
        f"E14-T6 cap 71 must stop: {outcomes[71]}"
    )


def test_t7_tool_path_boundary(tmp_path):
    k5_tools.RESULTS["app"] = " ".join(f"10.2.2.{i}" for i in range(1, 10))
    cfg = k5_cfg(
        tmp_path / "base", config={"evidence": {"max_map_chars": defaults.MAX_FINDER_CHARS}}
    )
    rt, _ = build_runtime(cfg, ScriptLLM([{"noaction": True}]))
    run = handle(rt)
    held = sum(
        map(len, set(rt.store.get_redaction_map(run.run_id).values()))
    )  # the default document alone
    results = {}
    for name, cap in (("tight", held + 71), ("loose", held + 200)):
        cfg = k5_cfg(tmp_path / name, config={"evidence": {"max_map_chars": cap}})
        rt, _ = build_runtime(cfg, ScriptLLM([{"tool": "app"}, {"noaction": True}]))
        run = handle(rt)
        results[name] = (run.state, run.reason_code)
    assert results["tight"] == (S.NEEDS_PERSON, "document_too_complex"), (
        f"E14-T7 tool path at the cap: {results}"
    )
    assert results["loose"][1] != "document_too_complex", (
        f"E14-T7 tool path under the cap stopped: {results}"
    )


def test_t8_config():
    assert EvidenceSettings().max_map_chars == defaults.MAX_MAP_CHARS, "E14-T8 default"
    assert (
        EvidenceSettings(max_map_chars=defaults.MAX_FINDER_CHARS).max_map_chars
        == defaults.MAX_FINDER_CHARS
    ), "E14-T8 the build cap itself must be accepted"
    for bad in (0, defaults.MAX_FINDER_CHARS + 1):
        try:
            EvidenceSettings(max_map_chars=bad)
        except ValidationError:
            continue
        _fail(f"E14-T8 max_map_chars={bad} was accepted")


def test_t9_derivation_pin():
    assert defaults.MAX_MAP_CHARS == 2 * defaults.MAX_REDACT_CHARS == 524_288, (
        "E14-T9 MAX_MAP_CHARS"
    )
    assert (
        defaults.MAX_FINDER_CHARS == defaults.MAX_MAP_CHARS + defaults.MAX_REDACT_CHARS == 786_432
    ), "E14-T9 MAX_FINDER_CHARS"


@pytest.mark.perf
def test_t10_e14_shape_is_refused():
    items = ["password=" + v(c, 260_000) for c in "abcdefgh"]
    t0 = time.thread_time()
    try:
        R.redact_many(items)
    except runmap.InputTooLarge as exc:
        assert "FinderMemoryTooMuch" in str(exc), f"E14-T10 wrong refusal {exc!r}"
    else:
        _fail("E14-T10 8 x 260,000 plain values were accepted")
    assert time.thread_time() - t0 < 20, "E14-T10 the refusal took too long"


@pytest.mark.perf
def test_t11_the_real_constant():
    vals = [v(c, 262_144) for c in "abc"]
    assert defaults.MAX_FINDER_CHARS == 3 * 262_144, "E14-T11 constant drifted"
    red = R._Redactor({f"<SECRET_{i}>": x for i, x in enumerate(vals, 1)})
    try:
        red.sweep("x")
    except runmap.InputTooLarge:
        _fail("E14-T11 exactly 786,432 nodes was refused at the real constant")
    red = R._Redactor(
        {f"<SECRET_{i}>": x for i, x in enumerate([vals[0] + "z", vals[1], vals[2]], 1)}
    )
    with pytest.raises(runmap.InputTooLarge, match="FinderMemoryTooMuch"):
        red.sweep("x")


def test_t12_honest_sizes_stay_far_under():
    m = runmap.RunMap()
    runmap.redact_untrusted(" ".join(f"10.{i // 250}.{i % 250}.7" for i in range(1500)), m)
    for i in range(40):
        runmap.redact_value({f"k{j}": f"value {i} {j} 10.9.9.{j}" for j in range(5)}, m)
    held = sum(map(len, set(m.values())))
    assert held < defaults.MAX_MAP_CHARS // 30, (
        f"E14-T12 an honest k5-size run holds {held} characters"
    )
    assert 8_571 < defaults.MAX_MAP_CHARS // 30, (
        "E14-T12 the property corpus' worst build is not far under"
    )
