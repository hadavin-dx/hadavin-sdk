"""Builds ../CORE-PR-HANDOFF-v22-other-tracks.md from the v21 file (round 9; readiness M7, m6). Asserted replacements."""
import re
s = open("../CORE-PR-HANDOFF-v21-other-tracks.md").read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90]); s = s.replace(old, new)
rep("# Core hardening hand-off v21, other tracks", "# Core hardening hand-off v22, other tracks")
rep("Companion of `CORE-PR-HANDOFF-v21.md` (the spend track). **Changes from v20 in this file (v21): the title, the companion name, and one block that says which gate script and which pass rule the PRs of this file use (below, \"Gate for every PR of this file\"); no content of any PR changed, and no command was run on the PRs of this file.**",
    "Companion of `CORE-PR-HANDOFF-v22.md` (the spend track). **Changes from v21 in this file (v22; readiness major M7 and minor m6 of the v21 review): the title, the companion name, the output folder and the row E0-O1 (it still named the v14 script `gate4.sh` and \"all five rc=0\", which cannot hold on the tree as it stands: pytest has two known failures; it now names `gate4_v22.sh` and the pass rule of the gate block), and the sentence about `tests/test_g4_parity.py` (it exists today and is not a PLANNED test); no content of any PR changed, and no command was run on the PRs of this file.**")
rep("Output folder: `handover/core-hardening/audit-r460/evidence-handoff-v14/` (the runner writes).", "Output folder: `handover/core-hardening/audit-r460/evidence-handoff-v22/` (the runner writes; v22 readiness major M7: v21 still named the v14 folder).")
rep("`tests/test_extract_masking.py` and `tests/test_g4_parity.py` are tests the named PR **would add** (PLANNED), and `fileguard.py` is the new K1 file (PLANNED, it exists nowhere today). `evidence-handoff-v14/gate4.sh` is carried from v14, never run.",
    "and `tests/test_extract_masking.py` are tests the named PR **would add** (PLANNED), and `fileguard.py` is the new K1 file (PLANNED, it exists nowhere today). `tests/test_g4_parity.py` EXISTS today (checked with `ls` in v22; v21 listed it both as existing and as PLANNED, readiness minor m6). The gate script is `evidence-handoff-v22/gate4_v22.sh`; the v14 `gate4.sh` is no longer used by this file.")
rep("| E0-O1 | `sh evidence-handoff-v14/gate4.sh E0-O1-<PR>` (", "| E0-O1 | `sh evidence-handoff-v22/gate4_v22.sh E0-O1-<PR>` (")
rep("each ends with `rc=`; not run by the author).", "each ends with `rc=`, then `compare_gate4.py` decides; run once by the author on the unchanged tree, see the gate block above).")
rep("| all five rc=0 at each PR's final head | exists |", "| the exit code of `compare_gate4.py` is 0 at each PR's final head: ruff, format, timing tests and bandit rc=0; pytest fails only the two tests of the saved baseline and no more failures than the baseline (NOT \"all five rc=0\": the unchanged tree has two known pytest failures, L20) | exists |")
s = re.sub(r"[A-Za-z_0-9./-]*v21[A-Za-z_0-9./-]*", lambda m: m.group(0).replace("v21", "v22") if re.search(r"\.(py|sh|md|txt)$|evidence-handoff-v21/?|-v21", m.group(0)) else m.group(0), s)
s = s.replace("**Gate for every PR of this file (v21;", "**Gate for every PR of this file (v22;")
open("../CORE-PR-HANDOFF-v22-other-tracks.md", "w").write(s); print("ok", s.count("v21"))
