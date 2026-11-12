"""Issue 10: the clean-corpus count. `tests/record_prh_main.py` CORPUS holds ordinary text with ordinary hidden items (colour codes,
tabs, joiners, overstrike). Run it through the tool and error paths with a handed-out secret that is NOT in the text, and each
text again with one masked copy of the secret added after it. The number of withheld results must be 0.
Usage (from the repo root): python -I handover/evidence/PRH/b7/clean_corpus.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tests import record_prh_main as rec

from hadavin_sdk import tools

HAND = "Qx7mLp" + "-9vRtzKw2"


def withheld(o: str) -> bool:
    return o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "" or "withheld" in o


def main() -> int:
    n = bad = 0
    for name, text in sorted(rec.CORPUS.items()):
        for variant, t, expect_marker in (
            ("plain", text, False),
            ("with-one-copy", text + "\n" + HAND, True),
        ):
            for path, out in (
                ("tool", tools.prepare_output(t, {}, 4000, [HAND])),
                ("error", tools.error_reason(ValueError(t), [HAND])),
            ):
                n += 1
                if expect_marker:
                    ok = (
                        HAND not in out
                        and tools.MARKER in out
                        and not out.startswith(tools.MARKER + tools.TRUNCATED)
                    )
                else:
                    ok = not withheld(out)
                if not ok:
                    bad += 1
                    print("WITHHELD-OR-WRONG", name, variant, path, repr(out)[:100])
    print(f"clean corpus: {len(rec.CORPUS)} texts, {n} runs, withheld or wrong: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
