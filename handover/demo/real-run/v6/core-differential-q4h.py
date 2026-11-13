"""Old-code against new-code differential for the three core key readers (made-up data, no network, nothing written
outside a temporary folder).

  python core-differential-q4h.py run  TREE OUT.json   # run the 1512 generated key files through the three readers of TREE
  python core-differential-q4h.py compare OLD.json NEW.json

TREE is a checkout (its src/ is used and its tests/test_core_key_readers.py supplies the 1512 files, the same on every
run). `compare` prints, per reader, how many files were accepted by both, refused by both, accepted by one only, and
how many refusal TEXTS changed. The rule it checks: the hubspot and smtp readers accept exactly the same files (only the
text of a refusal may change); the live reader differs only by refusing a key that has more than one line."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


def run(tree: str, out: str) -> None:
    root = Path(tree)
    sys.path[:0] = [str(root / "src"), str(root / "tests")]
    import test_core_key_readers as t  # the generator and the three readers

    result: dict[str, list[list[str | None]]] = {}
    with tempfile.TemporaryDirectory(prefix="core-diff-") as tmp:
        for reader in t.READERS:
            rows: list[list[str | None]] = []
            for raw in t.CASES:
                got, msg = t.outcome(reader, raw, Path(tmp))
                rows.append([got, msg or None])
            result[reader] = rows
    Path(out).write_text(json.dumps(result), encoding="utf-8")
    print(f"{tree}: {sum(len(v) for v in result.values())} readings written")


def compare(old: str, new: str) -> int:
    a = json.loads(Path(old).read_text(encoding="utf-8"))
    b = json.loads(Path(new).read_text(encoding="utf-8"))
    bad = 0
    for reader in a:
        both_ok = both_no = only_old = only_new = text_changed = 0
        for (go, mo), (gn, mn) in zip(a[reader], b[reader], strict=True):
            if go is not None and gn is not None:
                both_ok += 1
                bad += go != gn  # the accepted secret itself must be the same
            elif go is None and gn is None:
                both_no += 1
                text_changed += mo != mn
            elif go is not None:
                only_old += 1  # accepted before, refused now
            else:
                only_new += 1  # refused before, accepted now
        print(
            f"{reader}: {len(a[reader])} files; accepted by both {both_ok}; refused by both {both_no} "
            f"(text changed in {text_changed}); accepted only by the OLD code {only_old}; accepted only by the NEW code {only_new}"
        )
        if reader != "live":
            bad += only_old + only_new
        else:
            bad += only_new
    print("RESULT:", "differences outside the allowed ones" if bad else "no difference outside the allowed ones")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3])
    else:
        sys.exit(compare(sys.argv[2], sys.argv[3]))
