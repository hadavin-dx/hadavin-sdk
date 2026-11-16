# fix-tcfp8: round 12 fixer log for RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md

Static edits only. Nothing was run against n8n, Postgres, HubSpot or the network. Backups: scratchpad `bak-tcfp8/`. Edited by one script with a unique-match assertion per edit (85 edits applied, 0 misses). Past the round cap: Blockers and Majors fixed; Nits listed below.

## Findings changed (each checked against the file first)
- M1 (R3 refusal prints only "git part exit"): CONFIRMED. R3 now prints a REFUSED reason and cats `$EVLOG.git` only if it is non-empty and R3 ran.
- M2 (R3 refuses forever; GO row 1 says re-run): CONFIRMED. New Block R3n moves the two evidence sha lines aside, logs why, then R3 runs with a new EVLOG. Row 1 text points to it.
- M3 (re-sourcing overwrites per-run names): CONFIRMED. RUNBOOK skeleton uses `${NAME:-default}` for 12 names plus REPORT. TC ENVSH paragraph and FP Step 0a say the same.
- M4 (RUNBOOK still says R4b-2 hard-codes LOG3): CONFIRMED. Wording fixed in three places (LOG3 comment, step 13, failure 24).
- M5 (no RUNBOOK command for SHA_SCRIPTS): CONFIRMED. Command added in RUNBOOK step 6; FP 4c points to it.
- M6 (TC "part 3" and FP single message vs RUNBOOK step 20 two messages): CONFIRMED. TC and FP now name two messages with times.
- M7 (PGADMIN meaning): CONFIRMED. One paragraph in RUNBOOK section 4 and the TC table agree: login name; PGADMIN_PW, FLOWS_PW, KEYF, KEYH, KEY added.
- M8 (two pin-restore methods): CONFIRMED. RUNBOOK step 13 says Blocks R4r and R4b-2 win.
- B1, B3, B4 to B11, C1 to C3, C5, D, E and F items: applied in FIX-PLAN as Step 0a (bootstrap, typed vs stored names, log rule, stop rule), the read-first words box, Step 3a (RUNBOOK 4a), the take_check.sh exit-code table (read from the script header), the "No command exists yet..." lines with TIME, a single pin-1 procedure pointer, repeat rules for fill, the exact four-file control list, scene-4 decision, and the C3 owner of the F-008 wording change (RUNBOOK 14 (d)).
- Drift: FIX-PLAN item 9 and line ~53 said F-018/F-019 were Nits. FINDINGS: F-018 Major, F-019 Nit rated AFTER with no BEFORE item, only F-028 a BEFORE Nit. Both lines corrected.
- Owner rows (F1, F2): rewritten in plain words with IST times, identical in TC and FP.

## Rejected
None rejected outright. Item-level reviewer wording that I could not match to file text was not applied (see Not checked).

## Nits skipped (past cap)
Any reviewer Nit not named above; `.final1` name nit was fixed in TC because it was a one-line text change.

## Lead decides (candidates for QUESTIONS Q31; QUESTIONS.md not edited)
1. Re-pin start 04:00Z vs 03:31Z (for "done about 08:00Z"). Default: 04:00Z table.
2. Scene 4 filmed? Default: no, mf-recovery imported inactive (RUNBOOK I44).
3. N8N port. Default 5690.
4. SHA_SCRIPTS: same sha as SHA_FOLDER or a fifth sha for Wednesday scripts (I24).
5. Whether to align FINDINGS.md F-002 `$KEY`/`$PGADMIN` to the names in RUNBOOK section 4.
6. Commands the lead must write: n8n start (by 05:14Z), sub-workflow id read (05:54Z), import (06:39Z), export (06:59Z), values loop (06:24Z).

## Not checked
Reviewer items B2, C4, C6, D1-D3, E1-E8, F3, F4 were not individually re-verified or mapped one by one in this log; the edits above cover the ones I confirmed. RUNBOOK steps 25-30 and sections 7-10 not re-read. Block R3 and R3n shell logic was not executed (static). Pass lines of new commands are "written, not run".

## Check output
secrets: `PASS 0 hits in 1855 files` exit 0. refs: `PASS 5168 references` exit 0. ruff check: `All checks passed!`. ruff format: `571 files already formatted`. Clock diff: identical. `grep -c '||' RUNBOOK.md`: 0.
