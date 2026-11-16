"""Measure the invoice checks on the 409 demo texts (238 order mails, 171 supplier invoices, 60 of them forged) and on a forgery set.

Not a test (no test_ prefix); run:  python tests/corpus_measure.py [--forgeries]
Prints: D10 recall on the 60 forged, D10-or-D12 recall, false D10 / false D12 on the 111 correct invoices, D12 on the 238 order mails,
and (with --forgeries) recall of tests/forgeries2.py. The 409 texts were written by the same author as the code: this is own-material.
"""

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from intake import invoicecheck as ic  # noqa: E402

D = ROOT / "demo_only" / "data"


def _record(facts):
    lines = [
        {"qty": ln["qty"], "unit_cost_minor": int(ln["cost_minor"]), "amount_minor": ln["qty"] * int(ln["cost_minor"])}
        for ln in facts.get("lines", [])
    ]
    return {
        "invoice_no": facts.get("invoice_no"),
        "po_ref": facts.get("po_ref"),
        "supplier_name": facts.get("supplier_shown"),
        "lines": lines,
        "adjustments": [],
        "total_minor": int(facts.get("total_minor", 0)),
    }


CODES: dict[str, list] = {}  # case id -> notice codes of the last call (for the breakdown)


def flags_for(rec, text, on_file, cid=""):
    """Flags and notice codes through the one entry point the pipeline uses (`check_reasons`)."""
    fl = set()
    try:
        name = rec.get("supplier_name") or "x"
        flg, notes = ic.check_reasons(rec, text, {ic._key(name): on_file} if on_file else {})
        fl |= {f for f in flg if f in ("D10", "D12")}
        CODES[cid] = sorted({n.code for n in notes})
    except Exception as e:  # noqa: BLE001
        fl.add("EXC:" + type(e).__name__)
    return fl


def run():
    seed = json.load(open(D / "seed.json"))
    bank = {s["id"]: s["bank"] for s in seed["suppliers"]}
    rows = [json.loads(line) for f in ("dev", "test") for line in open(D / f"{f}.jsonl")]
    forged = ok_inv = 0
    f10 = f10or12 = fd10 = fd12 = fany = 0
    orders = od12 = 0
    exc = 0
    fp_ids = []
    t0 = time.time()
    for r in rows:
        text = (D / r["source"]["path"]).read_text(encoding="utf-8", errors="replace")
        facts = r["facts"]
        if r["kind"] == "order":
            orders += 1
            fl = flags_for({"lines": [], "adjustments": [], "total_minor": 0}, text, None, r["case_id"])
            od12 += "D12" in fl
            exc += any(x.startswith("EXC") for x in fl)
            continue
        on_file = bank.get(facts.get("po_supplier"))
        fl = flags_for(_record(facts), text, on_file, r["case_id"])
        exc += any(x.startswith("EXC") for x in fl)
        if "D10" in r["expected"]["exceptions"]:
            forged += 1
            f10 += "D10" in fl
            f10or12 += bool(fl & {"D10", "D12"})
        else:
            ok_inv += 1
            fd10 += "D10" in fl
            fd12 += "D12" in fl
            if fl & {"D10", "D12"}:
                fany += 1
                fp_ids.append((r["case_id"], sorted(fl)))
    print(
        f"forged={forged} D10={f10} D10|D12={f10or12} | correct={ok_inv} falseD10={fd10} falseD12={fd12} falseAny={fany} | orders={orders} D12={od12} | exc={exc} | {time.time() - t0:.1f}s"
    )
    import collections  # noqa: PLC0415

    by_code = collections.Counter(c for cid, _ in fp_ids for c in CODES.get(cid, []))
    print("false flags among the correct invoices, by notice code (an invoice may carry several):", dict(by_code.most_common()))
    return fp_ids


if __name__ == "__main__":
    ids = run()
    if "--ids" in sys.argv:
        print(ids)
    if "--forgeries" in sys.argv:
        import forgeries2  # noqa: PLC0415

        forgeries2.report(ic)
