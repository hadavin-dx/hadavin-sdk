# fix-tcfp17 (round 22, plan files; fixer log)

## Not verified (first)
- Nothing was run against a real n8n, database, mailbox or the real take. Every new command was written, then tested only in a scratch folder (keysave, keyload, stepjudge, step 11b chain) or by `bash -n` (syntax only).
- The edited step 9 (a2) cell, the step 4a wait rule and the Wednesday WARN reader row are text; no one has confirmed them. All are marked AUDIT PROPOSAL, lead to confirm.
- The new times in the 4a rule (04:46Z, 06:21Z, 05:51Z, 08:59Z, 09:59Z) are arithmetic from the existing clock (04:16 + 30 min, and the old latest-start values minus 30 min); not measured.
- No review round was run on the result; reviewer words were re-read against the files, not independently re-reviewed.

## Findings
1 Blocker (step 8 before 7): holds; fixed (order 6, 8, 7, 9 in the order paragraph, step rows, "Cannot run before" cells incl. step 9 (a2), clock row). Minutes unchanged, sum 269.
2 Blocker (two fills): holds; fixed (step 9 (a) five values by 05:00Z, (a2) three credential ids after step 8 and 7, (c) adds SUB_WORKFLOW_ID).
3 Major (one key count): holds; 5, 8, 9 everywhere; leftover "exactly 8 keys" in step 18 removed.
4 Blocker (keys across shells): holds; `keysave WORD` / `keyload WORD` in the skeleton, used in steps 16-19, 24, 26 (file mode 600, names printed only, refuses to overwrite).
5 Major (saved records): holds; `stepjudge` plus saved lines for steps 29, 25, 22, 24 (g)(h) and sign-off, 13 (b) (`$LOG2.bang` and reader line), 26 (`$POSTLOG.counts`, `.mail`, `.mail2`, outcome line), mailbox counts in steps 19a, 21, 23 read from `$TESTLOG`.
6 Major (step 4a): holds; ONE rule (wait to 04:46Z, then commit what was supplied, missing items written as open); clock row 4a and "latest start" sentence changed identically in FIX-PLAN and TAKE-CHECKLIST; section 6 note added.
7 Major (Wednesday WARN reader): holds; new who-needs row in FIX-PLAN and TAKE-CHECKLIST, RUNBOOK roles row, Case B text, step 22 text, TAKE-CHECKLIST item 14.
8 Major (time statements): holds; ORDERS values kept; the five conflicts named once in RUNBOOK section 8 ("Time statements that disagree"); pointers in FIX-PLAN line 1 and TAKE-CHECKLIST (two places).
9 Major (FIX-PLAN steps 1 and 2): holds; both are now pointers to RUNBOOK steps 1, 2 and 3; the operator rule moved to FIX-PLAN line 1; RUNBOOK "as in FIX-PLAN Step 1" now "as in RUNBOOK step 1".
10 Major ($EXPORT): holds; new RUNBOOK row 11b (new empty folder outside the repository, 1 min inside step 12's 15); step 12 "Cannot run before" now names 11b.

## Citations
- Item 49: due Tue 07:00Z, fixed in TAKE-CHECKLIST and in FIX-PLAN's "Not Tuesday blockers" sentence.
- FINDINGS.md line numbers cited by the reviewer (116/119) and the checker are both wrong for the file today (F-008 140, F-011 141, F-041 144); RUNBOOK now cites by row id.
- FIX-PLAN Step 12's 08:33Z comes from RUNBOOK I20 (rehearsal 1 from 07:48Z, 45 min), not item 56: fixed.
- FIX-PLAN Step 14: points to the Round 21 M9 conflict; item 55 not updated.

## Relay item 1
Block R6 awk pattern changed to `/GO row 6: (studio )?lead decides/`. Test on made-up lines: old pattern matched only F-902; new matched F-901, F-902, F-906. On the real LEDGER-ROWS.md old gives 0 hits, new gives 1 (F-003, Blocker, OPEN).

## Verification (commands run from handover/flows-audit unless shown)
- `diff <(sed -n 14,47p FIX-PLAN.md) <(sed -n 8,41p TAKE-CHECKLIST.md)`: no output (CLOCK-SAME printed after it).
- From repo root: `python3 handover/flows-audit/tools/check_refs.py` PASS 5176 references; `check_names.py` PASS 655 rows; `check_secrets.py` PASS 0 hits in 2061 files.
- `ruff format --check .`: 772 files already formatted.
- `bash -n`: 22 blocks (the skeleton fence and 21 inline command spans touched this round), 0 failed. Syntax only.

## Open for the lead (not edited here)
- Time conflicts of finding 8 (re-pin Mon 23 Nov 07:00Z against the arithmetic; rehearsal end 09:30 against 09:25/09:37; recording-ready 12:00Z against 12:22Z; Block R3 runtime; merges about 04:00Z against step 1). Lead picks which value governs.
- Order change on Tuesday (6, 8, 7, 9) and the 4a wait (up to 30 min, not in the 269).
- Q31 changes needed: item 61 split into five values by 05:00Z and three credential ids as a second fill after step 7; items 35 and 79 (no time change); item 49 and item 8 (e) both Tue 07:00Z; item 55 against M9 not updated; item 24 (JUDGE_WHO) is now also needed by stepjudge; I18 take program must read $KEY/$ADDR after keyload.
- Relay items for other agents (not done): item 92 text, the item 89 UNVERIFIED sentence, item 26 adding the F-003 line.
