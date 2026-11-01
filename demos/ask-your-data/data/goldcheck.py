"""Loader and checker for the Lumen Goods gold and adversarial data (standard library only; no database driver).

Files next to this module:
  gold.jsonl                70 items: 30 `dev`, 40 `test` (the sealed split)
  adversarial.jsonl         30 items: 14 deterministic (`ci`) and 16 live (`test`, sealed)
  adversarial.dev.jsonl     12 items (`dev`): the prompt is tuned against these, never against the 16 sealed ones
  exemplars.jsonl           prompt exemplars, copied from DEV gold items only
  dataset_contract.json               the planted-row registry plus the dataset facts the gold SQL depends on
  manifest.json             SHA-256 of the sealed items, written by `python goldcheck.py --freeze`

`validate_all()` checks structure and the dev/test discipline without a database. `check_execution()` takes two
callables (one per seed database) that run a SELECT and return `(columns, rows)`; it checks that the two independent
formulations of every gold query agree on BOTH databases. The callables are injected, so this module never imports a
driver (the demo's lock-in test allows the driver only in `askdata/pgsource.py`). Run it against the real seeds with
`PgSource`; the test-suite runs it against a stand-in generator.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

DATA = Path(__file__).resolve().parent
KINDS = {"answerable", "ambiguous", "abstain", "refuse"}
OUTCOME = {
    "answerable": "answered",
    "ambiguous": "answered_or_clarified",
    "abstain": "abstained",
    "refuse": "refused",
}
LEVELS = ("easy", "medium", "hard", "glossary", "ambiguous", "out_of_scope", "refuse")
# design 12.1: (dev, test) per level
COMPOSITION = {"easy": (8, 10), "medium": (8, 8), "hard": (3, 7), "glossary": (3, 5), "ambiguous": (3, 5),
               "out_of_scope": (3, 3), "refuse": (2, 2)}  # fmt: skip
TRAPS = {
    "uk_gb",
    "cryptic_flag",
    "revenue_definitions",
    "nulls",
    "orphans",
    "relative_dates",
    "line_price_vs_list",
}
GROUPS = {"direct_write": "refused_no_exec", "restricted": "no_restricted_value",
          "resource_abuse": "bounded_resources", "sql_trick": "no_unsafe_statement",
          "data_injection": "answers_match_clean"}  # fmt: skip
GOLD_FIELDS = {"id", "tier", "level", "kind", "question", "expect_outcome", "gold_sql", "gold_sql_alt",
               "formulation", "params", "order_matters", "order_columns", "scale", "accepted_interpretations",
               "traps", "glossary_keys", "planted_row_ids", "exemplar", "authored_by", "notes"}  # fmt: skip
ADV_FIELDS = {"id", "tier", "group", "kind", "question", "needs_llm", "expect_outcome", "pass_rule",
              "fixed_reply_sql", "forbidden_strings", "plant_ids", "clean_pair_id", "notes"}  # fmt: skip
INTERP_FIELDS = {
    "id",
    "label",
    "assumption_tag",
    "gold_sql",
    "gold_sql_alt",
    "scale",
    "order_columns",
}
VIEWS = {
    "customers_v",
    "products_v",
    "orders_v",
    "order_items_v",
    "payments_v",
    "refunds_v",
    "support_tickets_v",
}
AS_OF = "2026-10-15"
WORDS = re.compile(r"[a-z0-9]+")


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def canonical(item: dict) -> str:
    return json.dumps(item, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def digest(items: list[dict]) -> str:
    """SHA-256 over the canonical JSON of the items sorted by id (key order and file order do not matter)."""
    body = "\n".join(canonical(i) for i in sorted(items, key=lambda i: i["id"]))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def load_all(root: Path = DATA) -> dict:
    return {
        "gold": read_jsonl(root / "gold.jsonl"),
        "adversarial": read_jsonl(root / "adversarial.jsonl"),
        "adversarial_dev": read_jsonl(root / "adversarial.dev.jsonl"),
        "exemplars": read_jsonl(root / "exemplars.jsonl"),
        "plants": json.loads((root / "dataset_contract.json").read_text(encoding="utf-8")),
        "manifest": json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if (root / "manifest.json").exists() else None,
    }  # fmt: skip


def compute_manifest(data: dict) -> dict:
    gold = data["gold"]
    return {
        "sealed_test_sha256": digest([g for g in gold if g["tier"] == "test"]),
        "dev_sha256": digest([g for g in gold if g["tier"] == "dev"]),
        "adversarial_sha256": digest(data["adversarial"]),
        "adversarial_dev_sha256": digest(data["adversarial_dev"]),
        "exemplars_sha256": digest(data["exemplars"]),
        "counts": {"gold_dev": sum(g["tier"] == "dev" for g in gold), "gold_test": sum(g["tier"] == "test" for g in gold),
                   "adversarial": len(data["adversarial"]), "adversarial_dev": len(data["adversarial_dev"])},
        "rule": "Sealed items are frozen. A change to any `test` gold item or to adversarial.jsonl needs "
                "`python goldcheck.py --freeze` AND a recorded reason in the PR; derived result hashes live outside "
                "this file so filling them in never touches the seal.",
    }  # fmt: skip


def _norm_sql(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def sql_problems(sql: str, label: str) -> list[str]:
    """Static rules every gold statement must satisfy (single SELECT over exposed views only, no restricted column)."""
    out = []
    if not isinstance(sql, str) or not sql.strip():
        return [f"{label}: empty SQL"]
    low = _norm_sql(sql)
    if ";" in low:
        out.append(f"{label}: contains a semicolon")
    if not (low.startswith(("select ", "with "))):
        out.append(f"{label}: does not start with SELECT or WITH")
    if re.search(r"\bshop\.|\bpg_|information_schema|\bemail\b", low):
        out.append(f"{label}: touches a non-exposed object or the restricted email column")
    ctes = set(re.findall(r"(?:\bwith|,)\s+(\w+)\s+as\s*\(", low))
    for rel in re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_.]*)", low):
        if rel in ctes:
            continue
        if not (rel.startswith("analytics.") and rel[len("analytics.") :] in VIEWS):
            out.append(f"{label}: relation {rel!r} is not an exposed view")
    return out


def _tokens(text: str) -> set[str]:
    return set(WORDS.findall(text.lower()))


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0


def _sqls(item: dict) -> list[tuple[str, str]]:
    """(label, sql) for every statement an item carries."""
    out = []
    if item["kind"] == "answerable":
        out += [
            (f"{item['id']}.gold_sql", item["gold_sql"]),
            (f"{item['id']}.gold_sql_alt", item["gold_sql_alt"]),
        ]
    for it in item["accepted_interpretations"]:
        out += [
            (f"{item['id']}.{it['id']}.gold_sql", it["gold_sql"]),
            (f"{item['id']}.{it['id']}.gold_sql_alt", it["gold_sql_alt"]),
        ]
    return out


def _gold_item_problems(g: dict) -> list[str]:
    gid = g.get("id", "?")
    out = []
    if set(g) != GOLD_FIELDS:
        return [
            f"{gid}: fields differ: missing {sorted(GOLD_FIELDS - set(g))} extra {sorted(set(g) - GOLD_FIELDS)}"
        ]
    if (
        g["tier"] not in ("dev", "test")
        or not re.fullmatch(r"[DT]\d{2}", g["id"])
        or g["id"][0] != g["tier"][0].upper()
    ):
        out.append(f"{gid}: id and tier disagree (dev items are D##, sealed test items are T##)")
    if g["level"] not in LEVELS:
        out.append(f"{gid}: bad level {g['level']!r}")
    if g["kind"] not in KINDS or g["expect_outcome"] != OUTCOME.get(g["kind"]):
        out.append(f"{gid}: kind/expect_outcome mismatch")
    if not g["question"].strip() or len(g["question"]) > 500:
        out.append(f"{gid}: question empty or over 500 characters")
    if not isinstance(g["order_matters"], bool) or not isinstance(g["exemplar"], bool):
        out.append(f"{gid}: order_matters and exemplar must be booleans")
    if g["exemplar"] and g["tier"] != "dev":
        out.append(f"{gid}: only DEV items may be exemplars")
    if not set(g["traps"]) <= TRAPS:
        out.append(f"{gid}: unknown trap {set(g['traps']) - TRAPS}")
    kind, interps = g["kind"], g["accepted_interpretations"]
    if kind == "answerable":
        if interps or g["level"] in ("ambiguous", "out_of_scope", "refuse"):
            out.append(f"{gid}: answerable item with interpretations or a non-answerable level")
        if (
            g["gold_sql_alt"] is None
            or g["gold_sql"] is None
            or _norm_sql(g["gold_sql"]) == _norm_sql(g["gold_sql_alt"])
        ):
            out.append(f"{gid}: the two formulations are missing or identical")
        if not g["formulation"] or len(set(g["formulation"])) < 2:
            out.append(f"{gid}: formulation must name two different styles")
        if not isinstance(g["scale"], list) or not g["scale"]:
            out.append(
                f"{gid}: scale must be a non-empty list (decimals per output column, null for non-numeric)"
            )
    elif kind == "ambiguous":
        if g["level"] != "ambiguous" or not 2 <= len(interps) <= 3:
            out.append(
                f"{gid}: ambiguous items need level 'ambiguous' and 2 or 3 accepted interpretations"
            )
        if g["gold_sql"] is not None or g["gold_sql_alt"] is not None:
            out.append(f"{gid}: ambiguous items keep their SQL inside accepted_interpretations")
        tags = [i.get("assumption_tag") for i in interps]
        if len(set(tags)) != len(tags) or not all(tags):
            out.append(f"{gid}: every interpretation needs its own non-empty assumption_tag")
        for it in interps:
            if set(it) != INTERP_FIELDS:
                out.append(f"{gid}: interpretation fields differ {sorted(set(it) ^ INTERP_FIELDS)}")
            elif _norm_sql(it["gold_sql"]) == _norm_sql(it["gold_sql_alt"]):
                out.append(f"{gid}.{it['id']}: identical formulations")
    else:
        if (
            g["gold_sql"] is not None
            or g["gold_sql_alt"] is not None
            or interps
            or g["order_matters"]
        ):
            out.append(f"{gid}: abstain/refuse items carry no SQL, interpretations or ordering")
        if g["level"] != ("out_of_scope" if kind == "abstain" else "refuse"):
            out.append(f"{gid}: level does not match kind")
    for label, sql in _sqls(g) if kind in ("answerable", "ambiguous") else []:
        out += sql_problems(sql, label)
    if kind == "answerable":
        blob = (g["gold_sql"] or "") + (g["gold_sql_alt"] or "")
        for key, val in g["params"].items():
            if str(val) not in blob:
                out.append(f"{gid}: param {key}={val} does not appear in the SQL")
        if g["order_matters"] != bool(g["order_columns"]):
            out.append(f"{gid}: order_matters and order_columns must go together")
    return out


def validate_gold(gold: list[dict]) -> list[str]:
    out = []
    ids = [g["id"] for g in gold]
    if len(ids) != len(set(ids)):
        out.append("duplicate gold ids")
    for g in gold:
        out += _gold_item_problems(g)
    tally = Counter((g["tier"], g["level"]) for g in gold)
    for level, (dev, test) in COMPOSITION.items():
        if (tally[("dev", level)], tally[("test", level)]) != (dev, test):
            out.append(
                f"composition of {level}: got {tally[('dev', level)]}/{tally[('test', level)]}, want {dev}/{test}"
            )
    if (sum(g["tier"] == "dev" for g in gold), sum(g["tier"] == "test" for g in gold)) != (30, 40):
        out.append("gold must be 30 dev and 40 test items")
    seen = {t for g in gold for t in g["traps"]}
    if seen != TRAPS:
        out.append(f"traps not covered: {sorted(TRAPS - seen)}")
    return out


def validate_adversarial(items: list[dict], plants: dict, *, dev: bool) -> list[str]:
    out = []
    ids = [a["id"] for a in items]
    if len(ids) != len(set(ids)):
        out.append("duplicate adversarial ids")
    plant_ids = set(plants["plants"])
    for a in items:
        aid = a.get("id", "?")
        if set(a) != ADV_FIELDS:
            out.append(f"{aid}: fields differ {sorted(set(a) ^ ADV_FIELDS)}")
            continue
        if (
            a["group"] not in GROUPS
            or a["pass_rule"] != GROUPS[a["group"]]
            or a["kind"] != "adversarial"
        ):
            out.append(f"{aid}: group, kind and pass_rule disagree")
        if not a["question"].strip():
            out.append(f"{aid}: empty question")
        det = a["group"] in ("direct_write", "restricted", "resource_abuse")
        if a["needs_llm"] == det:
            out.append(
                f"{aid}: needs_llm must be false exactly for direct_write, restricted and resource_abuse"
            )
        want = "dev" if dev else ("ci" if det else "test")
        if a["tier"] != want:
            out.append(f"{aid}: tier {a['tier']!r} should be {want!r}")
        if det and not a["fixed_reply_sql"]:
            out.append(
                f"{aid}: deterministic items need fixed_reply_sql (the reply a compromised model would give)"
            )
        if not det and a["fixed_reply_sql"] is not None:
            out.append(f"{aid}: live items carry no fixed reply")
        if not set(a["plant_ids"]) <= plant_ids:
            out.append(f"{aid}: unknown plant id")
        if a["group"] == "data_injection":
            if not a["plant_ids"] or not a["clean_pair_id"]:
                out.append(f"{aid}: data_injection needs plant_ids and clean_pair_id")
        elif a["plant_ids"] or a["clean_pair_id"]:
            out.append(f"{aid}: only data_injection items carry plants")
        if a["group"] == "restricted" and "@example.com" not in a["forbidden_strings"]:
            out.append(f"{aid}: restricted items must forbid '@example.com'")
        if a["group"] == "data_injection" and not a["forbidden_strings"]:
            out.append(
                f"{aid}: data_injection needs forbidden_strings (payload fragments that must not reach the SQL)"
            )
    groups = Counter(a["group"] for a in items)
    want_groups = ({"direct_write": 2, "restricted": 2, "sql_trick": 3, "data_injection": 5} if dev else
                   {"direct_write": 6, "restricted": 4, "resource_abuse": 4, "sql_trick": 6, "data_injection": 10})  # fmt: skip
    if dict(groups) != want_groups:
        out.append(f"adversarial groups {dict(groups)} != {want_groups}")
    if not dev and (sum(not a["needs_llm"] for a in items), sum(a["needs_llm"] for a in items)) != (
        14,
        16,
    ):
        out.append("sealed adversarial must be 14 deterministic and 16 live")
    return out


def validate_plants(plants: dict) -> list[str]:
    out, seen = [], set()
    for pid, p in plants["plants"].items():
        if set(p) != {"table", "pk", "column", "planted", "purpose"}:
            out.append(f"plant {pid}: bad fields")
            continue
        key = (p["table"], p["pk"], p["column"])
        if key in seen:
            out.append(f"plant {pid}: row/column planted twice")
        seen.add(key)
        if "@" in p["planted"] and "example.com" not in p["planted"]:
            out.append(f"plant {pid}: a real-looking address")
    if len(plants["plants"]) != 12:
        out.append(
            "expected 12 plants (10 text plants + 2 terminal-control plants, design 11.6 and A-11)"
        )
    return out


def validate_exemplars(exemplars: list[dict], gold: list[dict]) -> list[str]:
    out = []
    by_id = {g["id"]: g for g in gold}
    if not 8 <= len(exemplars) <= 10:
        out.append("8 to 10 exemplars are required")
    test_q = [g["question"] for g in gold if g["tier"] == "test"]
    for e in exemplars:
        if set(e) != {"id", "source_dev_id", "question", "sql"}:
            out.append(f"exemplar {e.get('id')}: bad fields")
            continue
        src = by_id.get(e["source_dev_id"])
        if src is None or src["tier"] != "dev" or src["kind"] != "answerable":
            out.append(f"exemplar {e['id']}: source must be a DEV answerable item")
            continue
        if not src["exemplar"] or e["question"] != src["question"] or e["sql"] != src["gold_sql"]:
            out.append(
                f"exemplar {e['id']}: must equal its dev item and that item must be flagged exemplar"
            )
        for q in test_q:
            if jaccard(e["question"], q) > 0.8:
                out.append(f"exemplar {e['id']}: too similar to a sealed test question ({q!r})")
    flagged = {g["id"] for g in gold if g["exemplar"]}
    if flagged != {e["source_dev_id"] for e in exemplars}:
        out.append("the dev items flagged exemplar differ from the exemplars file")
    return out


def validate_all(root: Path = DATA) -> list[str]:
    d = load_all(root)
    out = (
        validate_gold(d["gold"])
        + validate_plants(d["plants"])
        + validate_exemplars(d["exemplars"], d["gold"])
    )
    out += validate_adversarial(d["adversarial"], d["plants"], dev=False)
    out += validate_adversarial(d["adversarial_dev"], d["plants"], dev=True)
    clash = {a["id"] for a in d["adversarial"]} & {a["id"] for a in d["adversarial_dev"]}
    if clash:
        out.append(f"adversarial ids shared between dev and sealed: {sorted(clash)}")
    if d["manifest"] is None:
        out.append("manifest.json is missing (run python goldcheck.py --freeze)")
    else:
        want = compute_manifest(d)
        for k, v in want.items():
            if k != "rule" and d["manifest"].get(k) != v:
                out.append(
                    f"manifest {k} does not match the files (sealed or dev data changed after freeze?)"
                )
    return out


# ---------------------------------------------------------------------------------------------- execution checks

Runner = Callable[[str], tuple[list[str], list[tuple]]]


def _cell(v: object, scale: int | None) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float, Decimal)):
        d = Decimal(str(v))
        if scale is not None:
            d = d.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_EVEN)
        else:
            d = d.normalize()
        return format(d, "f") if d != d.to_integral() else format(d.quantize(Decimal(1)), "f")
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return str(v)


def normalise(rows: list[tuple], scale: list[int | None] | None, *, ordered: bool) -> list[tuple]:
    sc = scale or []
    norm = [tuple(_cell(v, sc[i] if i < len(sc) else None) for i, v in enumerate(r)) for r in rows]
    return norm if ordered else sorted(norm)


def result_hash(rows: list[tuple], scale: list[int | None] | None, *, ordered: bool) -> str:
    body = json.dumps(normalise(rows, scale, ordered=ordered), separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _tie_probe(sql: str) -> str:
    return re.sub(
        r"limit\s+(\d+)\s*$",
        lambda m: f"LIMIT {int(m.group(1)) + 1}",
        sql.strip(),
        flags=re.IGNORECASE,
    )


def check_execution(gold: list[dict], run_a: Runner, run_b: Runner) -> dict:
    """Run every answerable and ambiguous statement on both databases. Returns {'problems': [...], 'executed': n,
    'hashes': {label: {'a': h, 'b': h}}}. `executed` counts statements actually sent."""
    problems, hashes, executed = [], {}, 0
    for g in gold:
        if g["kind"] == "answerable":
            variants = [(g["id"], g["gold_sql"], g["gold_sql_alt"], g["scale"], g["order_columns"])]
        elif g["kind"] == "ambiguous":
            variants = [
                (
                    f"{g['id']}.{i['id']}",
                    i["gold_sql"],
                    i["gold_sql_alt"],
                    i["scale"],
                    i["order_columns"],
                )
                for i in g["accepted_interpretations"]
            ]
        else:
            continue
        per_interp: list[dict[str, str]] = []
        for label, sql1, sql2, scale, order_cols in variants:
            ordered = bool(order_cols)
            hs = {}
            for side, run in (("a", run_a), ("b", run_b)):
                c1, r1 = run(sql1)
                c2, r2 = run(sql2)
                executed += 2
                if len(c1) != len(c2):
                    problems.append(
                        f"{label}[{side}]: formulations return {len(c1)} vs {len(c2)} columns"
                    )
                    continue
                if scale is not None and len(scale) != len(c1):
                    problems.append(
                        f"{label}[{side}]: scale has {len(scale)} entries for {len(c1)} columns"
                    )
                n1, n2 = (
                    normalise(r1, scale, ordered=ordered),
                    normalise(r2, scale, ordered=ordered),
                )
                if n1 != n2:
                    problems.append(
                        f"{label}[{side}]: the two formulations disagree ({len(n1)} vs {len(n2)} rows)"
                    )
                if not r1:
                    problems.append(f"{label}[{side}]: empty result (a vacuous check)")
                hs[side] = result_hash(r1, scale, ordered=ordered)
                if ordered and re.search(r"limit\s+\d+\s*$", sql1.strip(), re.IGNORECASE):
                    _, probe = run(_tie_probe(sql1))
                    executed += 1
                    limit = len(r1)
                    if len(probe) > limit and all(
                        _cell(probe[limit - 1][c], None) == _cell(probe[limit][c], None)
                        for c in order_cols
                    ):
                        problems.append(
                            f"{label}[{side}]: tie at the LIMIT cut on the order columns"
                        )
            hashes[label] = hs
            per_interp.append(hs)
        if g["kind"] == "ambiguous":
            for side in ("a", "b"):
                got = [h.get(side) for h in per_interp]
                if len(set(got)) != len(got):
                    problems.append(
                        f"{g['id']}[{side}]: two interpretations return the same result (the ambiguity is vacuous)"
                    )
    return {"problems": problems, "executed": executed, "hashes": hashes}


def main(argv: list[str]) -> int:
    if "--freeze" in argv:
        d = load_all()
        (DATA / "manifest.json").write_text(
            json.dumps(compute_manifest(d), indent=2) + "\n", encoding="utf-8"
        )
        print("manifest.json written")
    problems = validate_all()
    print("\n".join(problems) if problems else "gold and adversarial data: structure OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
