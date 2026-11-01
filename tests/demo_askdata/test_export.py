"""The export adapter: the mapping, the schema (a small validator for the subset the schema uses), the audit chain
the console recomputes, the honesty rules, the CLI. Offline: scripted model, SQLite stand-ins, no network."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

import pytest
from askdata import audit, export
from askdata.fixtures import Step
from askdata.ledger import QueryLedger

from .kit import COUNT_ORDERS
from .make_export_example import EXAMPLE, build
from .test_audit import write_config
from .test_eval_harness import Rig, gold

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "demo_export_v1.schema.json").read_text(
        "utf-8"
    )
)


def check(value, schema, path="$") -> list[str]:
    """Validate against the JSON-Schema subset in use: type, enum, const, pattern, minimum, required, properties,
    additionalProperties (bool or schema), items, anyOf. Returns the list of problems."""
    errs: list[str] = []
    if "anyOf" in schema:
        if not any(not check(value, s, path) for s in schema["anyOf"]):
            errs.append(f"{path}: no alternative matches")
        return errs
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: not {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in enum")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}
    t = schema.get("type")
    if t == "integer":
        ok = isinstance(value, int) and not isinstance(value, bool)
    elif t == "number":
        ok = isinstance(value, int | float) and not isinstance(value, bool)
    else:
        ok = t is None or isinstance(value, types[t])
    if not ok:
        return [*errs, f"{path}: not a {t}"]
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        errs.append(f"{path}: {value!r} does not match the pattern")
    if isinstance(value, int | float) and "minimum" in schema and value < schema["minimum"]:
        errs.append(f"{path}: below minimum")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        errs += [f"{path}.{k}: missing" for k in schema.get("required", []) if k not in value]
        for k, v in value.items():
            if k in props:
                errs += check(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}.{k}: unknown key")
            elif isinstance(schema.get("additionalProperties"), dict):
                errs += check(v, schema["additionalProperties"], f"{path}.{k}")
    if isinstance(value, list) and "items" in schema:
        for i, v in enumerate(value):
            errs += check(v, schema["items"], f"{path}[{i}]")
    return errs


@pytest.fixture(scope="module")
def exp(tmp_path_factory):
    return build(tmp_path_factory.mktemp("export"), core_commit="a" * 40)


def test_the_export_validates_and_unknown_keys_are_rejected(exp):
    assert check(exp, SCHEMA) == []
    bad = copy.deepcopy(exp)
    bad["cases"][0]["surprise"] = 1
    bad["scorecard"]["verdict"] = "great"
    del bad["scorecard"]["false_abstain"]
    errs = check(bad, SCHEMA)
    assert any("surprise: unknown key" in e for e in errs)
    assert any("verdict" in e for e in errs)
    assert any("false_abstain: missing" in e for e in errs)


def test_the_committed_example_validates_and_is_the_scripted_run():
    ex = json.loads(EXAMPLE.read_text("utf-8"))
    assert check(ex, SCHEMA) == []
    assert ex["run"]["model"] == "scripted" and ex["run"]["mode"] == "scripted"
    assert ex["audit"]["verify"]["ok"]


def test_cases_rules_reasons_and_hashes_are_mapped(exp):
    cases = {c["case_id"]: c for c in exp["cases"]}
    assert set(cases) >= {
        "askdata-e-001",
        "askdata-h-001",
        "askdata-a-001",
        "askdata-t-001",
        "askdata-t-002",
    }
    ok = cases["askdata-e-001"]
    run = next(s for s in ok["steps"] if s["name"] == "run_select")
    assert re.fullmatch(r"[0-9a-f]{64}", run["args_summary"]["sql_sha256"])
    assert ok["outcome"] == "auto_allowed"
    refused = cases["askdata-t-002"]
    assert [s["rule_id"] for s in refused["steps"] if s["name"] == "validator"] == ["V03"] * 3
    assert refused["expected"]["outcome"] == "refuse"
    assert refused["steps"][-1]["decision"] == "deny"
    abstained = cases["askdata-a-001"]
    assert abstained["outcome"] == "abstained"
    assert "out_of_scope" in abstained["steps"][-1]["reason"]
    blocked = cases["askdata-t-001"]
    assert blocked["outcome"] == "blocked" and "write_request" in blocked["steps"][-1]["reason"]
    wrong = cases["askdata-e-002"]
    assert wrong["wrong_confident"] and not wrong["correct"]


def test_scorecard_carries_every_required_number(exp):
    sc = exp["scorecard"]
    assert sc["label"] == "smoke"
    assert "scripted model" in sc["disclaimer"] and "synthetic data" in sc["disclaimer"]
    assert sc["confident_wrong"]["x"] == 1 and sc["confident_wrong"]["items"] == ["g3"]
    assert sc["confident_wrong"]["upper_bound"] is not None
    assert sc["false_abstain"] == {"x": 1, "n_should_answer": 4, "rate": 0.25}
    assert sc["wrong_and_allowed"] == {"x": 1, "n": 3}
    assert sc["coverage"] == {"answered_correct": 2, "definite": 4}
    assert sc["verdict"] == "not_demonstrated" and "not demonstrated" in sc["verdict_text"]
    assert {d["key"] for d in sc["hard_zero_defs"]} == set(sc["hard_zeros"])
    assert all(d["meaning"] for d in sc["hard_zero_defs"])
    assert sc["thresholds"] == {"green_max_upper": 0.1, "amber_max_upper": 0.15}


def test_the_audit_chain_recomputes_and_verify_counts_match(exp):
    prev = "0" * 64
    for e in exp["audit"]["events"]:
        keys = ("seq", "event_id", "ts", "type", "actor", "case_id", "summary")
        text = json.dumps({k: e[k] for k in keys}, sort_keys=True, separators=(",", ":"))
        assert e["prev_sha256"] == prev
        prev = hashlib.sha256((prev + "\n" + text).encode("ascii")).hexdigest()
        assert e["sha256"] == prev
    v = exp["audit"]["verify"]
    assert v["events"] == v["matched"] == len(exp["audit"]["events"]) and v["ok"]
    assert v["text"].startswith("local integrity check: ")
    ids = {i for c in exp["cases"] for i in c["audit_event_ids"]}
    assert ids and ids <= {e["event_id"] for e in exp["audit"]["events"]}


def test_honesty_no_accuracy_claim_no_vendor_strings_no_control_characters(exp):
    text = json.dumps(exp).lower()
    for word in (
        "postgres",
        "sqlite",
        "anthropic",
        "claude",
        "bedrock",
        "openai",
        "gemini",
        "psycopg",
    ):
        assert word not in text, word
    assert not re.search(r"accura(te|cy) of \d|\d+ ?% accura", text)
    assert exp["banner"] == "prototype, sample data" and exp["honesty"]["synthetic"] is True
    assert exp["approvals"] == [] and exp["adapter_calls"] == []
    assert not re.search(r"[\x00-\x08\x0b-\x1f\x7f]", json.dumps(exp, ensure_ascii=False))
    markup = next(c for c in exp["cases"] if "<img" in c["input_summary"])
    assert markup["outcome"] == "blocked"  # inert text; the console renders it with textContent


def test_a_damaged_ledger_makes_verify_not_ok(tmp_path):
    r = Rig(tmp_path)
    r.script("How many orders are there", Step(sql=COUNT_ORDERS))
    r.kit.pipeline.ask("How many orders are there")
    assert audit.verify(r.kit.ledger, r.kit.sink).ok
    data = r.kit.ledger.path.read_bytes()
    r.kit.ledger.path.write_bytes(data.replace(b'"outcome":"answered"', b'"outcome":"refused"'))
    assert not audit.verify(QueryLedger(r.kit.ledger.path), r.kit.sink).ok


def test_cli_writes_export_json_from_a_run_folder(tmp_path, capsys):
    r = Rig(tmp_path)
    it = gold("g1", "answerable", "How many orders are there", COUNT_ORDERS)
    r.script(it.question, Step(sql=COUNT_ORDERS))
    recs = r.harness.run_gold([it])
    rep = r.harness.report(recs, [], split="dev", meta={"model_id": "fake-model-1"})
    run = r.kit.tmp / "runs" / "r1"  # paths.runs_dir of write_config
    run.mkdir(parents=True)
    (run / "report.json").write_text(json.dumps(rep), "utf-8")
    (run / "results.jsonl").write_text("\n".join(json.dumps(asdict(x)) for x in recs), "utf-8")
    cfg = write_config(r.kit)
    assert export.main(["--config", cfg, "--run", "r1"]) == 0
    out = json.loads((run / "export.json").read_text("utf-8"))
    assert check(out, SCHEMA) == [] and out["run"]["run_id"] == "r1"
    assert export.main(["--config", cfg, "--run", "missing"]) == 4
    assert export.main(["--config", cfg, "--run", "../r1"]) == 4  # a name, never a path
    capsys.readouterr()


def test_only_this_runs_events_and_lines_are_exported_and_a_live_model_is_refused(tmp_path):
    r = Rig(tmp_path)
    r.script("An older question", Step(sql=COUNT_ORDERS))
    r.kit.pipeline.ask("An older question")  # another run in the same ledger and audit folder
    it = gold("g1", "answerable", "How many orders are there", COUNT_ORDERS)
    r.script(it.question, Step(sql=COUNT_ORDERS))
    recs = r.harness.run_gold([it])
    rep = r.harness.report(recs, [], split="dev", meta={"model_id": "fake-model-1"})
    kw = {
        "ledger": r.kit.ledger,
        "sink": r.kit.sink,
        "results": [asdict(x) for x in recs],
        "run_id": "r",
    }
    out = export.build_export(report=rep, **kw)
    assert len(out["audit"]["events"]) == 2 and out["audit"]["verify"]["events"] == 4
    assert all(e["case_id"] == "askdata-e-001" for e in out["audit"]["events"])
    with pytest.raises(ValueError, match="scripted"):
        export.build_export(report={**rep, "model_id": "some-live-model"}, **kw)
