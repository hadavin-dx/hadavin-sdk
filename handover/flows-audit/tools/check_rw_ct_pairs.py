"""check_rw_ct_pairs.py: compare the paste strings of RUNSHEET-WORDING.md with CLAIMS-TABLE.md.
Usage (run from handover/flows-audit): python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md [--list]
Reads both files, writes nothing. For every row of RUNSHEET-WORDING.md whose paste cell is one
double-quoted string, reports the rows whose string is not found word for word in CLAIMS-TABLE.md.
Exit 0 = every string is found, 1 = at least one is not, 2 = wrong usage or unreadable file.
With --list the unmatched rows are printed in full (id, line, string)."""

import re
import sys

USAGE = "usage: python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md [--list]"


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def paste_strings(text):
    """Yield (line number, row id, paste string) for each row with a quoted paste cell."""
    for n, line in enumerate(text.split("\n"), 1):
        if not line.startswith("| ") or line.startswith(("| id", "|---", "| card line")):
            continue
        cells = [c.strip() for c in line.strip()[1:-1].split(" | ")]
        if len(cells) not in (4, 6):
            continue
        paste = cells[1] if len(cells) == 4 else cells[3]
        m = re.fullmatch(r'"([^"]*)"', paste)
        if m:
            yield n, cells[0], m.group(1)


def main(argv):
    args = [a for a in argv[1:] if a != "--list"]
    if len(args) != 2:
        print(USAGE)
        return 2
    try:
        rw = read_text(args[0])
        ct = read_text(args[1])
    except OSError as exc:
        print(f"cannot read a file: {exc.strerror}")
        print(USAGE)
        return 2
    rows = list(paste_strings(rw))
    missing = [r for r in rows if r[2] not in ct]
    print(f"paste strings in RW: {len(rows)} | found word for word in CT: {len(rows) - len(missing)}")
    print(f"not found in CT: {len(missing)}")
    for n, rid, s in missing:
        shown = s if "--list" in argv else s[:70]
        print(f"  RW line {n} {rid}: {shown}")
    return 1 if missing else 0


sys.exit(main(sys.argv))
