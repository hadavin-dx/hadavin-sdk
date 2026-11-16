# Report: FIX-PLAN fixes for reader round 64 (static; nothing run; nothing marked passed)
## Unverified / not done first
- No new command was run except `bash -n` and a two-case test of self-check item 7 (both outputs as expected: `gate-pass-e-not-checked`, `gate-pass`). Pass words of RUNBOOK steps are "taken as written".
- M16 was not fixed line by line: I added a general rule (line 35) and named times only in Steps 10, 12, 13; other LEAD FILLS lines (Steps 5, 6, 8, 8b, items 5, 7, 8) have no own time and rely on the rule. M17 likewise only partly pair-checked: lines 94, 105, 217, 221, 224 not re-read after edits. Round/finding labels were NOT all moved out of FIX-PLAN.md; the changelog covers my new text only.
- M10: the last-section table still has 5 columns, not the reviewer's two-word-column layout; I made the intro truthful and put step words in the "How each step passes" table. Items 10(a), 38(d) not given new rows.
## Checks run
- Frozen block md5 of FIX-PLAN 37-84 = dfd844ddb7085082534434075814e131 = TAKE-CHECKLIST 32-79; head still 36 lines.
- check_refs PASS 5190, check_names PASS 655, check_secrets PASS 0 hits, check_counts PASS 52 files, ruff format 1129 formatted.
## Cross-file points for the lead (TAKE-CHECKLIST untouched)
- RUNBOOK step 24 must treat `gate-pass-e-not-checked` as FAIL; step 24 must write `stepjudge 24 signoff signed`.
- The lead's mail-count tool must take LABEL and expected count and print `mail-count-ok-LABEL` / `mail-count-WRONG-LABEL`.
- TAKE-CHECKLIST Block R3 must refuse if shas.env is missing; its PIN_NAME / JUDGE_WHO times must stay 03:30Z (09:00 IST) / 04:00Z (09:30 IST).
- New LEAD DECIDES: take-folder path by Mon 22:00Z (Tue 03:30 IST), proposal 03:00Z (08:30 IST); Step 10 runner commands by Wed 05:45Z (11:15 IST); fallback by Wed 06:00Z (11:30 IST).
