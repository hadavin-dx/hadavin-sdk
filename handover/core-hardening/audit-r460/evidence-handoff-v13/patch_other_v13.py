import re, sys
sys.path.insert(0, "/home/user/hadavin-sdk/handover/core-hardening/audit-r460/evidence-handoff-v13")
from patch_lib import Doc
d = Doc("CORE-PR-HANDOFF-v13-other-tracks.md")
d.line("# Core hardening hand-off v12, other tracks", "# Core hardening hand-off v13, other tracks (everything that is not spend), 2026-11-16 UTC (same date in IST)")
d.rep("Companion of `CORE-PR-HANDOFF-v12.md` (the spend track).", "Companion of `CORE-PR-HANDOFF-v13.md` (the spend track).")
d.rep("1. Nothing was run except small read-only programs (`evidence-handoff-v9/` and `evidence-handoff-v12/`). No test suite, no `ruff`, no `bandit`, no Postgres.",
"1. Nothing in this file was run except small read-only programs (`evidence-handoff-v9/` and `evidence-handoff-v13/`). No test suite, no `ruff`, no `bandit`. (The v13 builder did run a throwaway Postgres 16.15 for the spend file only; nothing of this file touches it.)")
d.after_line("- **v12 edits (nothing else changed):**",
"""- **v13 edits (nothing else changed; every other-track PR is carried with no change of content, which is the lead's brief for v13):** (1) paths, companion names and evidence names renamed to v13; (2) **H-0 must also rename `dev` to `demo` in the new spend tests and fixtures** of the spend track (spend file, section 1: `Config.environment` is still `dev` until H-0, `src/hadavin_sdk/config.py:317`), and locate every line it edits by its text, because S-2a moves line numbers in `runtime/agent_loop.py` (spend file, 7.1 hot-file column, which now lists every file H-0 and H-1 edit, readiness major 5); (3) **names that do not exist in `src/` yet are planned names, not present facts:** `restore_kinds`, `hash_chain_ok`, `anchored_checkpoints`, `anchor_supplied`, `signing_key_location` and `masking_damage` each have 0 files in `src/` (grep run on 2026-11-16; `evidence-handoff-v13/raw-greps-v13.txt` does not hold this one, the 6-line check is in `v13-CHANGES.md`); wherever the text below writes one of them in the present tense, read "the PR adds"; (4) the spend track now has five PR ids (S-1, S-2a, S-2b, DB-1, DB-2), so the combined merge order has 14 ids (spend file, 7.1); the other-track order is unchanged; (5) the citation file of this file is `evidence-handoff-v13/raw-cite-check-v13-other.txt` (it exists, section 8 of the spend file).""")
t = d.t
t = t.replace("evidence-handoff-v12/", "evidence-handoff-v13/")
t = re.sub(r"(raw-[a-z-]+)-v12", r"\1-v13", t)
t = t.replace("CORE-PR-HANDOFF-v12.md", "CORE-PR-HANDOFF-v13.md")
d.t = t
d.save()
