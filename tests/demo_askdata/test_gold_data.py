"""Gold and adversarial data for the Lumen Goods demo: structure, dev/test discipline, the seal, and the checker itself.

No database is needed here; `test_gold_exec.py` executes the SQL.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
from pathlib import Path

import pytest
import sqlglot
from sqlglot.optimizer.qualify import qualify

from tests.demo_askdata.conftest import DEMO
from tests.demo_askdata.gold_runner import load_goldcheck

DATA = DEMO / "data"
gc = load_goldcheck()


@pytest.fixture(scope="module")
def data() -> dict:
    return gc.load_all()


def test_the_shipped_data_is_valid():
    assert gc.validate_all() == []


def test_counts_and_composition(data):
    gold = data["gold"]
    assert (sum(g["tier"] == "dev" for g in gold), sum(g["tier"] == "test" for g in gold)) == (
        30,
        40,
    )
    assert len(data["adversarial"]) == 30 and len(data["adversarial_dev"]) == 12
    sealed = data["adversarial"]
    assert (
        sum(a["needs_llm"] for a in sealed) == 16 and sum(not a["needs_llm"] for a in sealed) == 14
    )
    definite = [g for g in gold if g["tier"] == "test" and g["kind"] == "answerable"]
    assert len(definite) == 30  # the denominator of the coverage gate (design 12.5)


def test_every_trap_has_an_item_and_every_ambiguous_item_has_tagged_interpretations(data):
    assert {t for g in data["gold"] for t in g["traps"]} == gc.TRAPS
    for g in data["gold"]:
        if g["kind"] == "ambiguous":
            assert 2 <= len(g["accepted_interpretations"]) <= 3
            assert all(i["assumption_tag"] for i in g["accepted_interpretations"])


def test_all_sql_parses_as_one_postgres_select_and_every_column_exists(data):
    views = data["plants"]["contract"]["views"]
    assert set(views) == gc.VIEWS
    schema = {"analytics": {v: dict.fromkeys(cols, "text") for v, cols in views.items()}}
    n = 0
    for g in data["gold"]:
        for label, sql in gc._sqls(g):
            tree = sqlglot.parse(sql, dialect="postgres")
            assert len(tree) == 1, label
            qualify(
                tree[0],
                schema=schema,
                dialect="postgres",
                validate_qualify_columns=True,
                quote_identifiers=False,
            )
            n += 1
    assert n >= 120  # 52 answerable x 2 plus the interpretations x 2


def test_the_restricted_email_column_is_in_no_exposed_view_and_no_gold_sql(data):
    assert all("email" not in cols for cols in data["plants"]["contract"]["views"].values())
    assert not any("email" in sql.lower() for g in data["gold"] for _, sql in gc._sqls(g))


def test_data_files_carry_no_real_address_and_no_raw_control_byte():
    for path in DATA.glob("*.json*"):
        text = path.read_text(encoding="utf-8")
        assert not any(ord(c) < 32 and c not in "\n\r\t" for c in text), path.name
        for address in re.findall(r"[\w.+-]*@[\w.-]+", text):
            assert address.endswith("@example.com"), (path.name, address)


# ------------------------------------------------------------------------------ the seal and the dev/test wall
def _copy_data(tmp_path: Path) -> Path:
    dst = tmp_path / "data"
    shutil.copytree(DATA, dst, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


def _rewrite(path: Path, edit) -> None:
    rows = gc.read_jsonl(path)
    edit(rows)
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + "\n", encoding="utf-8"
    )


def test_manifest_matches_the_files():
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == gc.compute_manifest(gc.load_all())


def test_changing_a_sealed_test_item_fails_until_refrozen(tmp_path):
    root = _copy_data(tmp_path)

    def edit(rows):
        next(r for r in rows if r["id"] == "T05")["question"] += " Please."

    _rewrite(root / "gold.jsonl", edit)
    problems = gc.validate_all(root)
    assert any("sealed_test_sha256" in p for p in problems)


@pytest.mark.parametrize("name", ["adversarial.jsonl", "adversarial.dev.jsonl"])
def test_changing_adversarial_items_fails_until_refrozen(tmp_path, name):
    root = _copy_data(tmp_path)
    _rewrite(root / name, lambda rows: rows[-1].update(question=rows[-1]["question"] + " Thanks."))
    assert any("sha256" in p for p in gc.validate_all(root))


def test_the_seal_is_order_and_key_order_independent():
    items = [{"id": "T01", "b": 1, "a": 2}, {"id": "T02", "z": 0}]
    assert gc.digest(items) == gc.digest([{"z": 0, "id": "T02"}, {"a": 2, "b": 1, "id": "T01"}])


def test_a_test_item_cannot_be_an_exemplar_or_be_copied_into_the_exemplars(tmp_path, data):
    bad = copy.deepcopy(data["gold"])
    next(g for g in bad if g["id"] == "T01")["exemplar"] = True
    assert any("only DEV items" in p for p in gc.validate_gold(bad))
    ex = copy.deepcopy(data["exemplars"])
    t = next(g for g in data["gold"] if g["id"] == "T01")
    ex[0].update(source_dev_id="T01", question=t["question"], sql=t["gold_sql"])
    assert any("DEV answerable item" in p for p in gc.validate_exemplars(ex, data["gold"]))


def test_an_exemplar_too_close_to_a_sealed_question_is_refused(data):
    ex = copy.deepcopy(data["exemplars"])
    d = next(g for g in data["gold"] if g["id"] == ex[0]["source_dev_id"])
    gold = copy.deepcopy(data["gold"])
    next(g for g in gold if g["id"] == "T01")["question"] = d["question"] + " now"
    assert any("too similar" in p for p in gc.validate_exemplars(ex, gold))


def test_exemplars_are_dev_items_only(data):
    ids = {g["id"]: g for g in data["gold"]}
    assert all(ids[e["source_dev_id"]]["tier"] == "dev" for e in data["exemplars"])
    assert not {e["source_dev_id"] for e in data["exemplars"]} & {
        g["id"] for g in data["gold"] if g["tier"] == "test"
    }


def test_plants_are_referenced_consistently(data):
    known = set(data["plants"]["plants"])
    used = {p for a in data["adversarial"] + data["adversarial_dev"] for p in a["plant_ids"]}
    assert used <= known
    assert {"CUST-ESC-1", "TICKET-ESC-1"} <= used  # the two terminal-control plants are exercised
    assert all(a["clean_pair_id"] for a in data["adversarial"] if a["group"] == "data_injection")


# ------------------------------------------------------------------------------ the validators reject bad input
def test_validators_reject_bad_items(data):
    gold = copy.deepcopy(data["gold"])
    d = next(g for g in gold if g["id"] == "D01")
    d["gold_sql_alt"] = d["gold_sql"]
    assert any("identical" in p for p in gc.validate_gold(gold))
    gold = copy.deepcopy(data["gold"])
    next(g for g in gold if g["id"] == "D01")["gold_sql"] = "SELECT email FROM shop.customers"
    assert any("non-exposed" in p for p in gc.validate_gold(gold))
    gold = copy.deepcopy(data["gold"])
    next(g for g in gold if g["id"] == "D02")["tier"] = "test"
    assert any("id and tier disagree" in p for p in gc.validate_gold(gold))
    adv = copy.deepcopy(data["adversarial"])
    adv[0]["needs_llm"] = True
    assert any("needs_llm" in p for p in gc.validate_adversarial(adv, data["plants"], dev=False))


def test_sql_static_rules():
    assert gc.sql_problems("SELECT 1 FROM analytics.orders_v", "x") == []
    assert gc.sql_problems("DELETE FROM analytics.orders_v", "x")
    assert gc.sql_problems("SELECT 1 FROM analytics.orders_v; SELECT 2", "x")
    assert gc.sql_problems("SELECT 1 FROM shop.orders", "x")
    assert (
        gc.sql_problems("WITH t AS (SELECT 1 FROM analytics.orders_v) SELECT * FROM t", "x") == []
    )


# ------------------------------------------------------------------------------ the execution checker, with fake databases
def _item(**kw):
    base = {
        "id": "D99",
        "kind": "answerable",
        "gold_sql": "SELECT 1 LIMIT 2",
        "gold_sql_alt": "SELECT 2",
        "scale": [0],
        "order_matters": False,
        "order_columns": [],
        "accepted_interpretations": [],
    }
    return {**base, **kw}


def _runner(table: dict[str, list[tuple]]):
    return lambda sql: (["c"], table[sql])


def test_check_execution_passes_when_formulations_agree_and_normalises_numbers():
    from decimal import Decimal

    run = _runner({"SELECT 1 LIMIT 2": [(Decimal("2.500"),)], "SELECT 2": [(2.5,)]})
    out = gc.check_execution([_item(scale=[2])], run, run)
    assert out["problems"] == [] and out["executed"] == 4


def test_check_execution_catches_disagreement_empty_results_and_tied_cuts():
    agree = _runner({"SELECT 1 LIMIT 2": [(1,)], "SELECT 2": [(2,)]})
    assert any("disagree" in p for p in gc.check_execution([_item()], agree, agree)["problems"])
    empty = _runner({"SELECT 1 LIMIT 2": [], "SELECT 2": []})
    assert any("empty" in p for p in gc.check_execution([_item()], empty, empty)["problems"])
    top = _item(
        order_matters=True, order_columns=[0], gold_sql="SELECT 1 LIMIT 1", gold_sql_alt="SELECT 2"
    )
    tied = _runner(
        {"SELECT 1 LIMIT 1": [(5,)], "SELECT 1 LIMIT 2": [(5,), (5,)], "SELECT 2": [(5,)]}
    )
    assert any(
        "tie at the LIMIT cut" in p for p in gc.check_execution([top], tied, tied)["problems"]
    )
    clean = _runner(
        {"SELECT 1 LIMIT 1": [(5,)], "SELECT 1 LIMIT 2": [(5,), (4,)], "SELECT 2": [(5,)]}
    )
    assert gc.check_execution([top], clean, clean)["problems"] == []


def test_check_execution_flags_a_vacuous_ambiguity_and_only_one_side_failing():
    interp = [
        {
            "id": i,
            "gold_sql": f"A{i}",
            "gold_sql_alt": f"B{i}",
            "scale": [0],
            "order_columns": [],
            "label": "",
            "assumption_tag": i,
        }
        for i in "ab"
    ]
    amb = _item(kind="ambiguous", accepted_interpretations=interp, gold_sql=None, gold_sql_alt=None)
    same = _runner({"Aa": [(1,)], "Ba": [(1,)], "Ab": [(1,)], "Bb": [(1,)]})
    assert any("vacuous" in p for p in gc.check_execution([amb], same, same)["problems"])
    ok = _runner({"Aa": [(1,)], "Ba": [(1,)], "Ab": [(2,)], "Bb": [(2,)]})
    bad_b = _runner({"Aa": [(1,)], "Ba": [(9,)], "Ab": [(2,)], "Bb": [(2,)]})
    problems = gc.check_execution([amb], ok, bad_b)["problems"]
    assert problems and all("[b]" in p for p in problems)


def test_result_hash_ignores_row_order_unless_ordered():
    rows = [(1, "a"), (2, "b")]
    assert gc.result_hash(rows, None, ordered=False) == gc.result_hash(
        rows[::-1], None, ordered=False
    )
    assert gc.result_hash(rows, None, ordered=True) != gc.result_hash(
        rows[::-1], None, ordered=True
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: next(r for r in rows if r["id"] == "T07").update(
            gold_sql="SELECT 1 FROM analytics.orders_v"
        ),
        lambda rows: next(r for r in rows if r["id"] == "T07").update(tier="dev"),
        lambda rows: rows.append({**rows[-1], "id": "T41"}),
    ],
)
def test_other_sealed_mutations_are_caught(tmp_path, mutate):
    root = _copy_data(tmp_path)
    _rewrite(root / "gold.jsonl", mutate)
    assert gc.validate_all(root)


def test_changing_the_dataset_contract_after_freeze_is_caught(tmp_path):
    root = _copy_data(tmp_path)
    path = root / "dataset_contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    contract["plants"]["ORD-NOTE-1"]["pk"] = 999
    path.write_text(json.dumps(contract), encoding="utf-8")
    assert any("contract_sha256" in p for p in gc.validate_all(root))


def test_no_sealed_sql_equals_a_dev_or_exemplar_sql(data):
    def sqls(tier):
        return {gc._norm_sql(s) for g in data["gold"] if g["tier"] == tier for _, s in gc._sqls(g)}

    assert not sqls("dev") & sqls("test")
    assert not {gc._norm_sql(e["sql"]) for e in data["exemplars"]} & sqls("test")


def test_dev_and_sealed_adversarial_items_share_no_question_and_few_plants(data):
    sealed, dev = data["adversarial"], data["adversarial_dev"]
    for d in dev:
        for s in sealed:
            assert gc.jaccard(d["question"], s["question"]) < 0.8, (d["id"], s["id"])
    pairs = {
        (tuple(d["plant_ids"]), tuple(s["plant_ids"]))
        for d in dev
        for s in sealed
        if d["plant_ids"]
    }
    assert all(
        dp != sp for dp, sp in pairs
    )  # no dev item uses exactly the plant set of a sealed item


def test_most_injection_items_expose_the_planted_text(data):
    inj = [a for a in data["adversarial"] if a["group"] == "data_injection"]
    assert sum(a["exposure"] != "none" for a in inj) >= 5
