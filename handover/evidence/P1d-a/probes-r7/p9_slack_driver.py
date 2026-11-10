"""P9: the new registry driver for SlackChannel._blocks, run over the SPELLINGS of tests/test_k5_round9.py on a tree.
Usage: PYTHONPATH=<tree>/src python p9_slack_driver.py   (run from the repo root so `tests` imports)"""
import hashlib, pathlib, sys, types
import hadavin_sdk
from hadavin_sdk.approvals import slack_channel
sys.path.insert(0, ".")
from tests import test_k5_round9 as r9
src = pathlib.Path(hadavin_sdk.__file__).parent
print("tree", hashlib.sha256(b"".join(p.read_bytes() for p in sorted(src.rglob("*.py")))).hexdigest()[:12] if False else hadavin_sdk.__file__)
def drv(s):
    ch = slack_channel.SlackChannel.__new__(slack_channel.SlackChannel)
    ch.max_card_chars = 2900
    req = types.SimpleNamespace(summary=f"a {s} b", current_step=0, steps=[1], approval_id="a", status="PENDING")
    return ch._blocks(req, None)[0]["text"]["text"]
bad = 0
for k, v in sorted(r9.SPELLINGS.items()):
    out = drv(v)
    leak = [n for n in r9.NEEDLES if n in out]
    ph = bool(r9.PLACEHOLDER.search(out))
    if leak or not ph:
        bad += 1
    print(k, "LEAK" if leak else "ok", "ph" if ph else "NO-PH", out[:70].replace("\n", "\\n"))
print("bad", bad, "of", len(r9.SPELLINGS))
