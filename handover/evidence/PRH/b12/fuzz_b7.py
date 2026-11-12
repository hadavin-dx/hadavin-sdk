"""EVIDENCE for PR H batch 11: the seeded fuzz of tests/test_prh_b7.py (`_fuzz_texts`, 3000 texts) through the tool path of one tree.
Usage: python fuzz_b7.py gen <texts.json>   (writes the 3000 texts, using THIS repo's tests folder and source)
       python fuzz_b7.py <tree-root> <texts.json>   (runs them against <tree-root>/src, which may be a tree without the new modules)
Prints counts only: strict withheld (marker + truncated, or the note), readable 8-character windows of the handed-out secret, exceptions.
No readable value is printed."""

import json, sys
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
HAND = "Qx7mLp" + "-9vRtzKw2"
if sys.argv[1] == "gen":
    sys.path.insert(0, str(repo / "src"))
    sys.path.insert(1, str(repo))
    from tests import test_prh_b7 as b7

    Path(sys.argv[2]).write_text(json.dumps(list(b7._fuzz_texts(3000))))
    print("wrote", len(json.loads(Path(sys.argv[2]).read_text())), "texts")
    raise SystemExit(0)
tree = sys.argv[1]
sys.path.insert(0, tree + "/src")
from hadavin_sdk import tools  # noqa: E402


def stands(out, secret, size=8):
    return any(secret[i : i + size] in out for i in range(len(secret) - size + 1))


n = withheld = readable = exc = 0
for t in json.loads(Path(sys.argv[2]).read_text()):
    n += 1
    try:
        o = tools.prepare_output(t, {}, 4000, [HAND])
    except Exception:  # noqa: BLE001
        exc += 1
        continue
    withheld += "withheld" in o or o.startswith(tools.MARKER + tools.TRUNCATED)
    readable += stands(o, HAND)
print(
    f"tree {tree} | texts {n} | strict withheld {withheld} | readable windows {readable} | exceptions {exc}"
)
