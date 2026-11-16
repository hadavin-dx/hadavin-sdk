import re
from patch_lib import Doc
CARRY = "`evidence-handoff-v13/raw-greps-v13.txt` (carried from v13, not re-run in v14)"
for name, lines in (("CORE-PR-HANDOFF-v14.md", {19,53,74,103,104,206}), ("CORE-PR-HANDOFF-v14-other-tracks.md", {10,84})):
    d = Doc(name); L = d.t.split("\n")
    for i in lines:
        assert "`raw-greps-v14.txt`" in L[i-1], (name, i)
        L[i-1] = L[i-1].replace("`raw-greps-v14.txt`", CARRY)
    d.t = "\n".join(L); d.n = len(lines); d.save()
d = Doc("CORE-PR-HANDOFF-v14.md")
d.rep("Method now: `raw-greps-v14.txt` G1 and G1b, test lines", "Method now: `raw-greps-v14.txt` G1 (python `ast`, multi-line calls included; v13's line grep G1 and G1b are withdrawn), test lines")
d.rep("`raw-greps-v14.txt` (greps G1 to G16, method printed with each; G12, G13, G14 and G15 re-run here replace the v9 grep files that v12 named but did not carry)", "`raw-greps-v14.txt` (greps G1, G4 and G17 to G21 re-run in v14, method printed with each; G2, G3, G5 to G16 stay in `evidence-handoff-v13/raw-greps-v13.txt`, carried and not re-run)")
d.save()
