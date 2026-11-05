"""Checks of the test split: reference agreement, structure, overlap with dev. Aggregates and agreement only; no test answer is pinned."""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import reference as ref

DATA = ROOT / "demo_only" / "data"
SCENARIO_ONLY = {"R-REF-001", "R-REF-013", "R-REF-016", "R-REF-019", "R-REF-025", "R-REF-027"}


def _cases(split):
    return [json.loads(x) for x in (DATA / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]


def test_files_match_the_manifest_hashes():
    m = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))["files"]
    for name in ("test.jsonl", "world_test.json"):
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == m[name]


def test_reference_agrees_with_the_test_gold():
    world, cases = ref.load("test")
    for c in cases:
        for s in c.get("steered", []):
            assert ref.evaluate(c, world, s) == (s["expect_deny"], None), (c["case_id"], s["expect_deny"])
        e = c["expected"]
        if e["action"] in ("refund", "cancel", "reship", "goodwill"):
            assert ref.evaluate(c, world, ref.correct_call(c)) == (None, e["tier"]), c["case_id"]
        if e["outcome"] == "refuse":
            assert e["deny_code"] in {ref.evaluate(c, world, s)[0] for s in c["steered"]}


def test_test_split_has_the_same_builders_deny_codes_vectors_and_hard_zeros_as_dev():
    dev, test = _cases("dev"), _cases("test")
    codes = lambda cs: (
        {s["expect_deny"] for c in cs for s in c.get("steered", [])}
        | {c["expected"]["deny_code"] for c in cs if c["expected"]["deny_code"]}
    )
    vec = lambda cs: {c["injection"]["vector"] for c in cs if "injection" in c}
    hz = lambda cs: {k for c in cs for k in c["expected"]["hard_zero_keys"]}
    assert codes(test) == codes(dev) and vec(test) == vec(dev) and hz(test) == hz(dev)
    assert Counter(c["bucket"] for c in dev) == Counter(c["bucket"] for c in test)
    assert Counter(c["expected"]["outcome"] for c in dev) == Counter(c["expected"]["outcome"] for c in test)
    ids = lambda w: {o["order_id"] for o in w["orders"]}
    wd, wt = (
        json.loads((DATA / "world.json").read_text(encoding="utf-8")),
        json.loads((DATA / "world_test.json").read_text(encoding="utf-8")),
    )
    assert not ids(wd) & ids(wt)


def test_every_demo_side_rule_has_a_test_split_case_except_scenario_only_rules():
    import re

    rules = set(re.findall(r"^\| (R-REF-\d{3}) \|", (ROOT / "gate_rules.md").read_text(encoding="utf-8"), re.MULTILINE))
    seen = {r for c in _cases("test") for r in c["expected"]["rule_ids"] + [s["rule_id"] for s in c.get("steered", [])]}
    assert rules - SCENARIO_ONLY <= seen, rules - SCENARIO_ONLY - seen


def test_the_same_eleven_deny_codes_appear_in_gold_in_both_splits():
    codes = {s: {c["expected"]["deny_code"] for c in _cases(s)} - {None} for s in ("dev", "test")}
    assert len(codes["dev"]) == len(codes["test"]) == len(codes["dev"] | codes["test"]) == 11


def test_the_test_split_files_name_no_other_demo_and_no_outside_path():
    for name in ("test.jsonl", "world_test.json"):
        text = (DATA / name).read_text(encoding="utf-8")
        for token in ("apex" + "c", "inta" + "ke", "deal" + "desk", "ask-your" + "-data", "C:" + chr(92), "/home/"):
            assert token not in text, (name, token)
