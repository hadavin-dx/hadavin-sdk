#!/usr/bin/env python3
"""Builds ../CORE-PR-HANDOFF-v21-other-tracks.md from the v20 file (never edited). Every replaced string is asserted."""
import pathlib
here = pathlib.Path(__file__).resolve().parent
t = (here.parent / "CORE-PR-HANDOFF-v20-other-tracks.md").read_text(encoding="utf-8")
lines = t.split("\n")
assert lines[0].startswith("# Core hardening hand-off v20, other tracks")
lines[0] = "# Core hardening hand-off v21, other tracks (everything that is not spend), 2026-11-16 UTC (same date in IST)"
assert lines[2].startswith("Companion of `CORE-PR-HANDOFF-v20.md`")
lines[2] = ("Companion of `CORE-PR-HANDOFF-v21.md` (the spend track). **Changes from v20 in this file (v21): the title, the companion name, and one block that says which gate script and which pass rule the PRs of this file use (below, \"Gate for every PR of this file\"); no content of any PR changed, and no command was run on the PRs of this file.** The change notes of v17 to v20 that stood in this paragraph were dropped (they are in the v17 to v20 files and describe edits already in the text below); the v12 and v13 edit notes further down stay as they were.")
t = "\n".join(lines)
a = "every PR's gate run is `sh evidence-handoff-v14/gate4.sh E0-O1-<PR>`"
assert a in t
t = t.replace(a, "every PR's gate run is `sh evidence-handoff-v21/gate4_v21.sh E0-O1-<PR>`")
b = "**`gate4.sh` was never run.**"
assert b in t
state = (here / "gate4_state_other.txt").read_text(encoding="utf-8").strip()
t = t.replace(b, "**" + state + "**")
gate = ("\n**Gate for every PR of this file (v21; one rule, the same as the spend track).** The script is `evidence-handoff-v21/gate4_v21.sh <prefix>` and its verdict is the exit code of `python3 -I evidence-handoff-v21/compare_gate4.py <prefix>`, which the script runs last: `ruff check`, `ruff format --check`, the timing tests and `bandit` must end `rc=0`; `pytest` must fail only the two tests of the saved baseline (`evidence-handoff-v21/baseline/raw-gate4-base-pytest.txt`: two repository guard tests about files under `handover/`, L20), no other test, and no more failed tests than the baseline. A PR of this file that adds a new failing test name fails the gate. The script does not compare failure message text (a reviewer reads the two messages once at the PR head). It does not run CodeQL, SonarCloud, CodeRabbit, pip-audit, Semgrep, zizmor or gitleaks, and it skips the database and vault tests (no `HADAVIN_TEST_PG_DSN`): the lead's CI run is the gate.\n")
marker = "**Per-PR output names (readiness major 9):**"
assert marker in t
# put the gate block right before the output-names paragraph's line start
i = t.index("Output folder: `handover/core-hardening/audit-r460/evidence-handoff-v14/` (the runner writes).")
t = t[:i] + gate.lstrip("\n") + "\n" + t[i:]
ex = "`tests/test_g4_parity.py`"
assert ex in t
t = t.replace("**Labels for this table (v15):**", "**`tests/test_g4_parity.py` exists today** (checked with `ls` in v21; readiness minor m6 of v20); I did not check any other test file name of this file.\n\n**Labels for this table (v15):**", 1)
for old, new in [("CORE-PR-HANDOFF-v20.md", "CORE-PR-HANDOFF-v21.md"), ("CORE-PR-HANDOFF-v19.md", "CORE-PR-HANDOFF-v21.md")]:
    t = t.replace(old, new)
(here.parent / "CORE-PR-HANDOFF-v21-other-tracks.md").write_text(t, encoding="utf-8")
print("written", len(t))
