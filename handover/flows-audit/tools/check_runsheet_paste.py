"""check_runsheet_paste.py: static checker for flows-audit/RUNSHEET-WORDING.md (round 6).
Usage: python3 -I check_runsheet_paste.py RUNSHEET-WORDING.md [CLAIMS-TABLE.md]
Reads the files only; writes nothing; exit 0 = all checks pass, 1 = a check failed, 2 = wrong usage or file not readable.
Checks: (1) every table row has the right number of cells (a pipe sign inside a cell breaks this);
(2) every Paste-this cell is NO PASTE, DELETE, or ONE string in double quotes with no quote mark,
no apostrophe, no pipe sign and no backtick inside; (3) the banned words (approval, audit trail,
one database) appear in no paste cell; (4) row ids are unique; (5) row counts per section;
(6) with CLAIMS-TABLE.md given: every A-/B- claim id there has a row here (by number, letters ignored)."""

import re
import sys

BANNED = ("approval", "audit trail", "one database")


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


USAGE = "usage: python3 -I check_runsheet_paste.py RUNSHEET-WORDING.md [CLAIMS-TABLE.md]"
FLAGGED = re.compile(r"(UNSUPPORTED|OVERSTATED|DELETE|STALE)")


def main(argv):
    if len(argv) not in (2, 3):
        print(USAGE)
        return 2
    try:
        text = read_text(argv[1]).split("\n")
    except OSError as exc:
        print(f"cannot read {argv[1]}: {exc.strerror}")
        print(USAGE)
        return 2
    sec, rows, bad, ids = "", {}, [], {}
    for n, line in enumerate(text, 1):
        if line.startswith("## "):
            sec = line[3:].split(".")[0].strip()[:12]
        if not (
            line.startswith("| ")
            and not line.startswith("| id")
            and not line.startswith("|---")
            and not line.startswith("| card line")
        ):
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
        want, untraced = set(), set()
        try:
            table = read_text(argv[2]).split("\n")
        except OSError as exc:
            print(f"cannot read {argv[2]}: {exc.strerror}")
            print(USAGE)
            return 2
        for line in table:
            m = re.match(r"\| ([AB])-(\d+) ", line)
            if not m:
                continue
            c = [x.strip() for x in line.strip()[1:-1].split(" | ")]
            if len(c) < 7:
                continue
            # the verdict is found by its words in the cells after the claim text (cells 4 to 6),
            # not at a fixed cell number, so a moved or added column does not hide a verdict
            verdict = next(
                (
                    x
                    for x in c[3:7]
                    if re.match(r"(UNSUPPORTED|OVERSTATED|DELETE|STALE|UNTRACED|SUPPORTED)", x)
                ),
                "",
            )
            if FLAGGED.match(verdict):
                want.add(m.groups())
            elif verdict.startswith("UNTRACED"):
                untraced.add(m.groups())
        want -= set()
        miss = sorted(want - have)
        print(
            "claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md:",
            len(want),
            "| with no row here:",
            [f"{a}-{b}" for a, b in miss],
        )
        print(
            "claim ids marked UNTRACED there:",
            len(untraced),
            "| with no row here:",
            len(untraced - have),
            "(scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)",
        )
        if miss:
            bad.append("claim ids missing")
    for b in bad:
        print("FAIL:", b)
    print("RESULT:", "FAIL" if bad else "PASS")
    return 1 if bad else 0


sys.exit(main(sys.argv))
