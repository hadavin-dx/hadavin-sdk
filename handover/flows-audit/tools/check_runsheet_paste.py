"""check_runsheet_paste.py: static checker for flows-audit/RUNSHEET-WORDING.md (round 5).
Usage: python3 -I check_runsheet_paste.py RUNSHEET-WORDING.md [CLAIMS-TABLE.md]
Reads the files only; writes nothing; exit 0 = all checks pass, 1 = a check failed.
Checks: (1) every table row has the right number of cells (a pipe sign inside a cell breaks this);
(2) every Paste-this cell is NO PASTE, DELETE, or ONE string in double quotes with no quote mark,
no apostrophe, no pipe sign and no backtick inside; (3) the banned words (approval, audit trail,
one database) appear in no paste cell; (4) row ids are unique; (5) row counts per section;
(6) with CLAIMS-TABLE.md given: every A-/B- claim id there has a row here (by number, letters ignored)."""
import re
import sys

BANNED = ("approval", "audit trail", "one database")


def main(argv):
    text = open(argv[1], encoding="utf-8").read().split("\n")
    sec, rows, bad, ids = "", {}, [], {}
    for n, line in enumerate(text, 1):
        if line.startswith("## "):
            sec = line[3:].split(".")[0].strip()[:12]
        if not (line.startswith("| ") and not line.startswith("| id") and not line.startswith("|---") and not line.startswith("| card line")):
            continue
        cells = [c.strip() for c in line.strip()[1:-1].split(" | ")]
        rid = cells[0]
        if len(cells) not in (4, 6):
            if len(cells) == 3:
                continue
            bad.append(f"line {n} {rid}: {len(cells)} cells")
            continue
        paste = cells[1] if len(cells) == 4 else cells[3]
        ok = paste in ("NO PASTE", "DELETE")
        if not ok:
            m = re.fullmatch(r'"([^"]*)"', paste)
            if not m:
                bad.append(f"line {n} {rid}: paste cell is not one quoted string")
            else:
                inner = m.group(1)
                if "'" in inner or "`" in inner or "|" in inner:
                    bad.append(f"line {n} {rid}: apostrophe, backtick or pipe in paste")
                low = inner.lower()
                for w in BANNED:
                    if w in low:
                        bad.append(f"line {n} {rid}: banned words {w!r} in paste")
        if rid in ids:
            bad.append(f"line {n}: duplicate id {rid} (first at line {ids[rid]})")
        ids[rid] = n
        rows.setdefault(sec, []).append(rid)
    for s, r in rows.items():
        print(f"section {s!r}: {len(r)} rows")
    print("total rows:", sum(len(r) for r in rows.values()))
    if len(argv) > 2:
        have = {re.match(r"([AB])-(\d+)", i).groups() for i in ids if re.match(r"[AB]-\d+", i)}
        want = set()
        for line in open(argv[2], encoding="utf-8"):
            m = re.match(r"\| ([AB])-(\d+)", line)
            if m:
                want.add(m.groups())
        miss = sorted(want - have)
        extra = sorted(have - want)
        print("claim ids in CLAIMS-TABLE.md:", len(want), "| with no row here:", [f"{a}-{b}" for a, b in miss])
        print("row ids here that are not A/B claim ids there:", [f"{a}-{b}" for a, b in extra])
        if miss:
            bad.append("claim ids missing")
    for b in bad:
        print("FAIL:", b)
    print("RESULT:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


sys.exit(main(sys.argv))
