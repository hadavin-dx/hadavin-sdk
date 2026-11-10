"""P10 step 7 check: _drop_targets == the old _IMAGE / _MDLINK regexes on 300,000 random strings. PYTHONPATH=<tree>/src"""
import re, random
from hadavin_sdk.approvals import gate
L = gate._LABEL
OLD_IMG = re.compile(r"!" + L + r"\([^)]*\)"); OLD_LNK = re.compile(L + r"\(\s*[^)\s]+[^)]*\)")
random.seed(7); bad = 0; n = 300000
for _ in range(n):
    s = "".join(random.choice(["!", "[", "]", "(", ")", " ", "a", "\\", "\n", "](", "![", "x.com", "\t"]) for _ in range(random.randint(0, 14)))
    a = OLD_LNK.sub(r"\1 [link removed]", OLD_IMG.sub("[image removed]", s))
    b = gate._drop_targets(gate._MDLINK_HEAD, gate._drop_targets(gate._IMAGE_HEAD, s, lambda m: "[image removed]", True), lambda m: m.group(1) + " [link removed]", False)
    if a != b:
        bad += 1
        if bad < 4: print("DIFF", repr(s), repr(a), repr(b))
print("strings", n, "different", bad)
