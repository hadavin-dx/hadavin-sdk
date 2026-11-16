# fix-f5-r4: round 4 log for RUNSHEET-WORDING.md (RECREATED by flows-audit main session)
Failure first: the original log written by the F5 round 4 fixer was deleted by mistake by the claims round 4 fixer (`rm -f` of an untracked file, reported by that fixer). This file is rebuilt from the fixer's hand-back text only; it is shorter than the original and not independent. The run sheet itself (RUNSHEET-WORDING.md, 331 lines) was not touched.
## Still UNCHECKED (fixer's list)
- Whether take scripts do the flow-set switch (scripts not in checkout, FAILED-TAKE-NOTE.md:20; QUEUE.md:24 says the switch is manual with scripts/n8n_api.py, also absent). Note: lead decision 2026-11-16 item 1 makes the take real-v5 only, so the switch is no longer in this video.
- Whether run_mf.py starts all three stand-ins (dn1_common.py:85 starts only smtp_catcher.py).
- What step 9.2 answer checks return; which model the stage uses on filming day; whether the 80 stop tests were one lead each; the old sentences at R:4, R:75, R:51, R:79, PLAN:194; the real-v5 vs film-v5 difference; Q-A to Q-E open (section 5).
## Decision changed
D1 and D3 now go to the coordinator (CLAIMS-TABLE.md lines 27, 52). Hat LEAD renamed COORDINATOR; "Goes where" LEAD renamed FILE EDIT.
## Finding both reviewers missed
A-088 in CLAIMS-TABLE.md is the sentence at P:156 (round 3 called it A-075b). Round 3's row A-088 was a guessed sentence at R:90 and was deleted; A-075b renamed A-088.
## Disagreed with reviewers
"Nested quotes" were in old-sentence columns, not paste cells; DESIGN-A-README lines crm 26, mail 27, stage 28; B-189 split in two rows.
## Changes
Step 9 / N-8 false "not in this checkout" reason removed; real start commands and ports (crm_stub.py 8771, stage_server.py 8770, smtp_catcher.py 8791; read, not run). Addresses A-005/A-084 reconciled; "real CRM cannot refuse" lines reworded; closing card one table; quote and fragment rows fixed; gate lists built by script; rows added A-012, B-017, B-024, B-051, B-067, B-078, B-091, B-189(b), B-214, B-215, X-5, X-6; words defined in section 0-words; Q-A/Q-B raised.
## Script self-check on the final file (fixer's claim, not rerun by me)
141 rows (65/3/17/56); every paste cell NO PASTE, DELETE or one double-quoted string; no "one database", "audit trail", "approval", "UNCHECKED" in paste cells; every claim id has a row.
