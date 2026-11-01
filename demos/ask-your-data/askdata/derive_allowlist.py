"""Derive what the gold set and the exemplars actually use, and compare it with the allowlists (design A-10).

    python -m askdata.derive_allowlist            print the derived sets
    python -m askdata.derive_allowlist --write    rewrite askdata/allowed_nodes.json (the owner-reviewed copy)

Every gold query (both formulations) and every exemplar is run through the validator with the Lumen catalog; a
statement that does not validate is an error (the allowlist can never be tighter than the gold set). The committed
`allowed_nodes.json` must equal the derived result, so a gold change that needs a new construct shows up as a diff.
This module imports no parser: the parser lives only in `validate.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from askdata.allowed import CAST_TARGETS, FUNCTIONS, LUMEN_VIEWS
from askdata.validate import describe

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
COMMITTED = HERE / "allowed_nodes.json"


def gold_statements() -> list[tuple[str, str]]:
    """(label, sql) for every gold query, alternative formulation and exemplar."""
    out: list[tuple[str, str]] = []
    for line in (DATA / "gold.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        for key in ("gold_sql", "gold_sql_alt"):
            if row.get(key):
                out.append((f"{row['id']}.{key}", row[key]))
    for line in (DATA / "exemplars.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        out.append((f"{row['id']}.sql", row["sql"]))
    return out


def derive() -> dict[str, object]:
    nodes: set[str] = set()
    funcs: set[str] = set()
    casts: set[str] = set()
    for _, sql in gold_statements():
        found = describe(sql, views=LUMEN_VIEWS)
        nodes |= set(found["nodes"])
        funcs |= set(found["functions"])
        casts |= set(found["casts"])
    return {
        "catalog": "lumen",
        "nodes": sorted(nodes),
        "functions": sorted(funcs),
        "casts": sorted(casts),
        "allowed_but_unused_by_gold": {
            "functions": sorted(FUNCTIONS - funcs),
            "casts": sorted(CAST_TARGETS - casts),
        },
    }


def main(argv: list[str]) -> int:
    text = json.dumps(derive(), indent=2, sort_keys=True) + "\n"
    if "--write" in argv:
        COMMITTED.write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
