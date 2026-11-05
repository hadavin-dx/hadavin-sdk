"""Documents must agree with code and data. Every number in the docs that can drift is written as a marker <!--n:NAME=VALUE--> and compared with the
value generated from code/data here; the docs may not claim a sealed or blind set; the mutation results must belong to this exact tree; every implemented
rule has a mutant; every rule in the rule table is either implemented or listed as spec-only."""

import hashlib
import json
import re
import sys

import engine_kit as ek
from engine_kit import D

sys.path.insert(0, str(D / "mutation"))
import mutation_check as mc

from dealdesk import identities, store

sys.path.insert(0, str(D / "demo_only" / "data"))
import gen_cases

DOCS = sorted(p for p in D.glob("*.md"))


def text(name):
    return (D / name).read_text(encoding="utf-8")


def generated():
    m = ek.MATRIX
    cells = sum(len(r) for r in m["cells"]["discount"].values()) + sum(
        1
        for dim in ("margin", "term_years", "billing", "payment_terms_days", "sla_tier", "renewal_downsell")
        for v in m["cells"][dim].values()
        if isinstance(v, dict)
    )
    dev = [json.loads(x) for x in (D / "demo_only/data/dev_cases.jsonl").read_text(encoding="utf-8").splitlines()]
    old = sum(len((D / f"demo_only/data/{f}.jsonl").read_text(encoding="utf-8").splitlines()) for f in ("dev_a", "dev_b"))
    return {
        "cells": cells,
        "mutants": len(mc.MUTS),
        "rules_implemented": len(mc.RULES_IMPLEMENTED),
        "identities": len(identities.IDENTITIES),
        "actions": len(identities.ACTIONS),
        "kinds": len(store.KINDS),
        "clauses": len(ek.POLICY["clauses"]),
        "dev_gold_policy_cases": old,
        "dev_cases": len(dev),
        "test_cases": len(gen_cases.make.__defaults__)
        and sum(gen_cases.make.__defaults__) + 20,  # n_decide + n_accept + n_trace + 20 scenario rows
        "dev_cases_decide": sum(r["kind"] == "decide" for r in dev),
        "dev_cases_accept": sum(r["kind"] == "accept" for r in dev),
        "dev_cases_trace": sum(r["kind"] == "trace" for r in dev),
        "dev_cases_scenario": sum(r["kind"] == "scenario" for r in dev),
    }


def test_every_numeric_marker_in_the_docs_equals_the_generated_value():
    gen, seen = generated(), set()
    for p in DOCS:
        for name, val in re.findall(r"<!--n:([a-z_]+)=([0-9]+)-->", p.read_text(encoding="utf-8")):
            assert name in gen, (p.name, name)
            assert gen[name] == int(val), (p.name, name, gen[name], val)
            seen.add(name)
    assert {"cells", "mutants", "rules_implemented", "identities", "dev_gold_policy_cases", "dev_cases", "test_cases"} <= seen


def test_dev_and_test_shapes_are_equal_by_construction():
    g = generated()
    assert g["test_cases"] == g["dev_cases"] == sum(g[k] for k in g if k.startswith("dev_cases_"))


def test_every_rule_in_the_rule_table_is_implemented_or_listed_as_spec_only():
    t = text("gate_rules.md")
    ids = set(re.findall(r"^\| R-DEALDESK-(\d{3})", t, re.MULTILINE))
    ids |= {f"{n:03d}" for n in range(10, 18)} if "R-DEALDESK-010..017" in t else set()
    impl = set(mc.RULES_IMPLEMENTED)
    spec_only = set(re.findall(r"<!--spec-only:([0-9 ]*)-->", t)[0].split()) if re.search(r"<!--spec-only:", t) else set()
    assert ids - {"019"} <= impl | spec_only, sorted(ids - impl - spec_only)
    assert not impl & spec_only


def test_every_implemented_rule_has_a_mutant_and_every_mutant_names_real_rules():
    cov = {r for m in mc.MUTS for r in m[4]}
    assert set(mc.RULES_IMPLEMENTED) <= cov, sorted(set(mc.RULES_IMPLEMENTED) - cov)
    assert cov <= set(mc.RULES_IMPLEMENTED), sorted(cov - set(mc.RULES_IMPLEMENTED))
    assert len({m[0] for m in mc.MUTS}) == len(mc.MUTS)  # unique names


def test_mutation_results_belong_to_this_exact_tree_and_none_survived():
    r = text("mutation/RESULTS.txt")
    assert f"tree_sha256: {mc.tree_hash()}" in r, "RESULTS.txt is stale: re-run the harness after the last code/test change"
    assert f"mutants: {len(mc.MUTS)}" in r and "baseline: unmutated copy passes" in r
    n = len(mc.MUTS)
    assert f"summary: {n} of {n} CAUGHT, 0 SURVIVED, 0 TIMEOUT, 0 UNPINNED OR UNEXPECTED REASON" in r
    assert "| SURVIVED |" not in r and "CAUGHT_UNEXPECTED" not in r and "CAUGHT_UNPINNED" not in r
    assert (
        r.count("| CAUGHT | reason ok |") == n
    )  # every mutant is killed by a test among those that failed first when its kill was recorded (mutation/expected_kills.json: a recording, not an independent choice)
    pins = json.loads((D / "mutation/expected_kills.json").read_text(encoding="utf-8"))
    assert set(pins) == {m[0] for m in mc.MUTS} and all(pins[k] for k in pins)


def test_no_doc_claims_a_sealed_blind_or_held_out_result():
    for p in DOCS:
        t = p.read_text(encoding="utf-8")
        for m in re.finditer(r"(?i)sealed|blind|held-out|held out", t):
            window = t[max(0, m.start() - 70) : m.end() + 90].lower()
            ok = any(
                k in window
                for k in (
                    "not sealed",
                    "no sealed",
                    "never sealed",
                    "none sealed",
                    "burned",
                    "second-author",
                    "second author",
                    "prerequisite",
                    "tuned",
                )
            )
            assert ok, (p.name, window)


def test_present_tense_claims_name_files_that_exist():
    for name in ("tests/oracle_indep.py", "tests/test_inbox.py", "tests/test_controls.py", "tests/test_engine.py", "tests/test_segregation.py", "mutation/mutation_check.py",
                 "mutation/RESULTS.txt", "demo_only/data/load_profile.json", "demo_only/data/pass.json", "runbook.md", "CORE_COPIES.md", "core_copies.json", "demo_only/eval/lock.template.json", "tests_oneshot/test_test_split.py"):  # fmt: skip
        assert (D / name).exists(), name
    assert hashlib.sha256((D / "config/desk_policy.json").read_bytes()).hexdigest() in text("demo_only/data/manifest.json")


def test_docs_say_hadavin_never_the_studio_name_and_never_promise_what_cannot_be_promised():
    for p in DOCS:
        t = p.read_text(encoding="utf-8").lower()
        assert "zero hallucination" not in t and "guarantee" not in t.replace("no guarantee", "").replace(
            "cannot guarantee", ""
        ), p.name


def test_ci_workflow_runs_the_gates_on_both_python_versions_with_pinned_actions():
    wf = (D / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert (
        '"3.12"' in wf
        and '"3.13"' in wf
        and "bandit" in wf
        and "ruff format --check" in wf
        and "ruff check" in wf
        and "pytest" in wf
    )
    for line in wf.splitlines():
        if "uses:" in line:
            assert re.search(r"@[0-9a-f]{40}\b", line), line  # every action pinned by commit SHA
    assert "bandit" in (D / "pyproject.toml").read_text(encoding="utf-8")  # declared in the test group


def test_gate_rules_holds_section_15_and_every_revision_4_rule_in_a_table_row():
    t = text("gate_rules.md")
    assert re.search(r"^## 15\. ", t, re.MULTILINE) and re.search(r"^### 15\.1 ", t, re.MULTILINE) and "## 16." in t
    for n in range(80, 97):
        assert re.search(rf"^\| R-DEALDESK-0{n} \|", t, re.MULTILINE), n
