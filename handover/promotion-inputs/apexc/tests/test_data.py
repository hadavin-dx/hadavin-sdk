"""Stage-1 checks: deterministic regeneration, gold-set shape, label oracle, doc consistency. Offline."""

import json
import re
from pathlib import Path

import gen

from apexc.classify import classify_full, cumulative_minor, tier_for

ROOT = Path(__file__).resolve().parents[1]
ALL_TYPES = (
    "price_variance",
    "quantity_variance",
    "no_receipt",
    "line_mismatch",
    "duplicate_exact",
    "duplicate_near",
    "bank_change",
    "new_vendor",
    "tax_total_mismatch",
    "currency",
    "unknown_currency",
    "vendor_master_recent_edit",
    "contact_change",
    "vendor_mismatch",
    "vendor_inactive",
    "submitter_not_authorised",
    "unknown_vendor",
    "po_not_found",
    "no_po",
    "ambiguous_po",
    "extraction_disagreement",
    "invalid_amount",
    "bank_change_cooling",
    "vendor_master_unverified_edit",
    "payee_collision",
    "tax_id_collision",
    "cross_vendor_duplicate",
    "po_line_overbilled",
)
DATA = ROOT / "demo_only" / "data"


def test_regeneration_is_byte_identical():
    for name, content in gen.outputs().items():
        assert (DATA / name).read_bytes() == content, name


def test_generation_is_independent_of_run():
    a, b = gen.outputs(), gen.outputs()
    assert a == b


def test_shape_and_counts(cases):
    assert len(cases) == 256  # acceptance.md item 4: 128 dev + 128 test
    assert len({c["case_id"] for c in cases}) == len(cases)
    for split in ("dev", "test"):
        for bucket in ("easy", "hard", "trap", "abstain"):
            assert any(c["split"] == split and c["bucket"] == bucket for c in cases), (split, bucket)
    assert sum(1 for c in cases if c["split"] == "dev") == sum(1 for c in cases if c["split"] == "test") == 128
    assert sum(1 for c in cases if c["injection"]) == 28  # acceptance.md: 28 injection cases
    assert all(re.fullmatch(r"apexc-[ehta]-\d{3}", c["case_id"]) for c in cases)


def test_every_exception_type_and_tier_in_both_splits(cases):
    for split in ("dev", "test"):
        types = {t for c in cases if c["split"] == split for t in c["expected"]["exception_types"]}
        assert types >= {
            "price_variance",
            "quantity_variance",
            "no_receipt",
            "duplicate_exact",
            "duplicate_near",
            "bank_change",
            "new_vendor",
            "tax_total_mismatch",
            "currency",
            "vendor_master_recent_edit",
            "vendor_mismatch",
            "unknown_vendor",
            "po_not_found",
            "no_po",
            "ambiguous_po",
            "extraction_disagreement",
        }, split
        tiers = {c["expected"]["tier"] for c in cases if c["split"] == split}
        assert tiers >= {"none", "human", "four_eyes", "four_eyes_over_max", "blocked"}, split


def test_labels_match_reference_classifier(cases, pol):
    for c in cases:
        got, ev = classify_full(c, pol)
        assert sorted(got) == c["expected"]["exception_types"], c["case_id"]
        assert sorted(ev) == c["expected"]["evidence_types"], c["case_id"]
        inv = c["invoice"]
        assert tier_for(got, inv["currency"], cumulative_minor(c, pol), pol) == c["expected"]["tier"], c["case_id"]


def test_traps_are_not_flagged_as_duplicates(cases):
    for c in cases:
        if c["recipe"] in ("rent", "weekly_service", "rejected_valid", "partial_prior"):
            assert c["expected"]["exception_types"] == [], c["case_id"]


def test_no_float_money_and_integer_strings(cases):
    def walk(o, path=""):
        if isinstance(o, float):
            raise AssertionError(f"float at {path}")
        if isinstance(o, dict):
            for k, v in o.items():
                if k.endswith("_minor") and v is not None:
                    assert isinstance(v, str) and re.fullmatch(r"-?\d+", v), (path, k, v)
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")

    for c in cases:
        walk(c, c["case_id"])
    walk(json.loads((DATA / "seed.json").read_text(encoding="utf-8")), "seed")


def test_reserved_domains_only(cases):
    blob = (
        (DATA / "seed.json").read_text(encoding="utf-8")
        + (DATA / "dev.jsonl").read_text(encoding="utf-8")
        + (DATA / "test.jsonl").read_text(encoding="utf-8")
    )
    for dom in re.findall(r"@([A-Za-z0-9.-]+)", blob):
        assert dom.endswith((".example.com", ".example.org", ".example.net", "example.com")), dom


def test_failure_modes_first_provenance(cases):
    md = (ROOT / "failure_modes.md").read_text(encoding="utf-8")
    declared = set(re.findall(r"^\| (FM-\d\d) \|", md, re.M))
    gold_rows = {m.group(1) for m in re.finditer(r"^\| (FM-\d\d) \|.*\| gold \|$", md, re.M)}
    used = {fm for c in cases for fm in c["failure_modes"]}
    assert used <= declared, used - declared
    assert gold_rows <= used, f"failure modes marked gold with no case: {sorted(gold_rows - used)}"
    hz_declared = set(re.findall(r"^\| (HZ-\d\d) \|", md, re.M))
    assert {h for c in cases for h in c["hard_zero_keys"]} <= hz_declared


def test_rule_ids_cited_exist():
    rules = (ROOT / "gate_rules.md").read_text(encoding="utf-8")
    defined = set(re.findall(r"^\| (R-APEXC-\d{3}) \|", rules, re.M))
    assert len(defined) == 37  # R-APEXC-001 to 037 (README)
    cited = set()
    for f in (
        "failure_modes.md",
        "scoping.md",
        "demo_only/demo_script.md",
        "acceptance.md",
        "src/apexc/tools.py",
        "src/apexc/classify.py",
        "src/apexc/normalise.py",
    ):
        cited |= set(re.findall(r"R-APEXC-\d{3}", (ROOT / f).read_text(encoding="utf-8")))
    assert cited <= defined, sorted(cited - defined)


def test_demo_script_cases_exist(cases):
    ids = {c["case_id"] for c in cases}
    demo = json.loads((DATA / "demo_cases.json").read_text(encoding="utf-8"))
    assert len(demo) == 5 and all(d["case_id"] in ids for d in demo)
    by_id = {c["case_id"]: c for c in cases}
    assert any(by_id[d["case_id"]]["expected"]["tier"] == "blocked" for d in demo)
    assert any(by_id[d["case_id"]]["expected"]["outcome"] == "abstain" for d in demo)


def test_manifest_hashes_match_files():
    m = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    import hashlib

    for name, h in m["sha256"].items():
        path = ROOT / name if "/" in name else DATA / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == h, name


def test_label_check_is_a_second_reader_check_on_the_current_data_and_says_what_it_is_not():
    import hashlib

    d = json.loads((DATA / "labels_check.json").read_text(encoding="utf-8"))
    assert d["kind"] == "second-reader consistency check" and d["stale_for_current_data"] is False
    assert d["applied_to_test_sha256"] == hashlib.sha256((DATA / "test.jsonl").read_bytes()).hexdigest()  # it was run on THIS data
    assert d["n"] == 128 and d["agree"] == 128 and d["disagreements"] == [] and d["agents_marked_unsure"]
    assert "NOT independent" in d["limits"] and "tuned" in d["limits"] and "not evidence of accuracy" in d["limits"]


def test_there_is_no_sealed_claim_anywhere(cases):
    import re

    for f in (
        "README.md",
        "scoping.md",
        "acceptance.md",
        "gate_rules.md",
        "failure_modes.md",
        "eval-contract.md",
        "demo_only/data/dataset_contract.json",
    ):
        text = (ROOT / f).read_text(encoding="utf-8")
        for line in text.splitlines():
            if re.search(r"sealed", line, re.I):
                assert re.search(r"not sealed|no sealed|nothing here is|never .?sealed|not .sealed|only meaning|backwards", line, re.I), (
                    f,
                    line[:120],
                )


def test_counts_in_the_docs_come_from_code():
    """m10: stale counts were a recurring defect, so the numbers the docs state are checked against the code and the data."""
    import importlib.util
    import re

    root = ROOT
    spec = importlib.util.spec_from_file_location("mutation_check", root / "mutation_check.py")
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    rules = sorted(int(n) for n in re.findall(r"\| R-APEXC-(\d{3}) \|", (root / "gate_rules.md").read_text(encoding="utf-8")))
    readme, acceptance = (root / "README.md").read_text(encoding="utf-8"), (root / "acceptance.md").read_text(encoding="utf-8")
    assert f"R-APEXC-001 to {rules[-1]:03d}" in readme and rules == list(range(1, rules[-1] + 1))
    assert f"{len(mc.M)} mutants" in acceptance
    n_dev, n_test = (sum(1 for _ in (DATA / f"{s}.jsonl").open(encoding="utf-8")) for s in ("dev", "test"))
    assert f"`dev.jsonl` ({n_dev})" in readme and f"`test.jsonl` ({n_test})" in readme
    unsure = len(json.loads((DATA / "labels_check.json").read_text(encoding="utf-8"))["agents_marked_unsure"])
    assert f"marked {unsure} cases unsure" in acceptance
    assert "reverts 20 fixes" not in readme


def test_the_test_count_and_the_failure_mode_counts_in_the_docs_are_real():
    """The suite size, the failure modes and the invariants the docs state are counted from the code, not typed."""
    import os
    import re
    import subprocess
    import sys

    root = ROOT
    fm = (root / "failure_modes.md").read_text(encoding="utf-8")
    n_fm, n_hz = len(set(re.findall(r"\| (FM-\d+) \|", fm))), len(set(re.findall(r"\| (HZ-\d+) \|", fm)))
    docs = "".join((root / f).read_text(encoding="utf-8") for f in ("README.md", "acceptance.md", "scoping.md"))
    assert f"{n_fm} failure modes" in docs and f"{n_hz} invariants" in docs
    if os.environ.get("APEXC_COUNTING"):  # the collection subprocess does not recurse
        return
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=root, capture_output=True, text=True,
                         env={**os.environ, "APEXC_COUNTING": "1"}).stdout  # fmt: skip
    n = int(re.search(r"(\d+) tests? collected", out).group(1))
    assert f"{n} tests" in (root / "acceptance.md").read_text(encoding="utf-8"), n
