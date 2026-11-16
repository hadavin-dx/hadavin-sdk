# Fix report for reviews/plan-files-reader-r37.md (FIXER, sole editor of RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md)

Not committed. No sub-agents. No spend. EGM review of this result is the lead's step; I did not replace it with my own review.

## What I did NOT do or check (first)
- Item 10 ("commands first" rewrite of the eight long step cells) is only PARTLY done: history labels and old-form sentences were moved out into reviews/runbook-history-cells.md (about 92.5k to 89k characters in the cells). The commands are not yet moved to the front of each cell. I stopped because the history is woven into the prose and an unverified restructure could orphan references or delete pass lines. Needs the lead's decision (below).
- Nothing was run against a real n8n, Postgres or mailbox. The files are static. Only shell lines were tested, with `bash -n` and tiny fake-data runs: need_new, step 11b, step 9(a), step 18 first line, step (1b), TC check 7.
- My last extra test (keysave/keyload words 19a, 21, 23 in a scratch folder) was NOT run: the command was blocked by the safety check on `rm -rf` and I did not retry. The keysave word list edit (RUNBOOK line 195) is read-checked only.
- Q31 items 25 and 50 are append-only and were not edited. QUESTIONS.md, ORDERS.md, REVIEW.md and flow-check/ untouched.
- The reviewer's line numbers came from an older snapshot; I re-found every item by text.

## Checks (run from handover/flows-audit, final run)
- `python3 -I tools/check_refs.py`: PASS 5184 references
- `python3 -I tools/check_names.py`: PASS 655 rows
- `python3 -I tools/check_secrets.py`: PASS 0 hits in 2834 files
- `python3 -I tools/check_counts.py`: PASS 52 files / 655 nodes
- `ruff format --check .`: 959 files already formatted
- Clock block: FIX-PLAN lines 37-84 and TAKE-CHECKLIST lines 8-55 identical (CLOCK-SAME)
- TC check 7 new command: `bash -n` ok; fake run with a run sheet that holds "approval" printed `FOLDER-OK`, the hit line, `grep exit 0` (a hit, correctly not a pass); with REPO empty it printed `REFUSED: REPO` and no `grep exit`.

## Changes per Major (all re-found by grep first)
1. Pin commit blocks without reviewer-line guard: TC P1c (about line 424) and P2c (about 462) now carry the same `# reviewed by: NAME, YYYY-MM-DD, pin sha256 XXXXXXXX` guard as RUNBOOK steps 4b(d) and 13 (reject PLACEHOLDER, session, "lead to confirm").
2. n8n_api.py due time: RUNBOOK step 6 (about line 218) now has one statement with roles: file check at 04:54Z (10:24 IST) is the due check; 06:59Z (12:29 IST) is the first use by ARGUMENTS (section 10(b)). Whether a missing file at 04:54 stops only the steps that use it is a lead decision (below).
3. WAIT_S due time: one due time per input stated per RUNBOOK section 10 (g)/(h); steps 16 and 18 say "last time to change"; step 18 WAIT_S due 08:29Z (13:59 IST) as in the clock block. The other times (TC row 5(f) 06:00Z, step 18 Wed 05:45Z, 10(g) 04:00Z) were given roles, not changed.
4. NO-GO governing time: RUNBOOK lines about 285, 327, 331 and TC about 130 name the governing time per Case A and Case B, with UTC and IST. Marked AUDIT PROPOSAL, lead to confirm. New item (6) added to the "Time statements that disagree" list.
5. Keysave words: RUNBOOK line 195 list extended with 19a, 21 and 23; rows 240, 242, 244 say "Keys first: keysave 19a/21/23" and how to get two keys before 19a.
6. NOT CHECKED uses: TC line 6 now lists every allowed use (Tuesday, step 19 Wednesday gate (e), Row 4 (d), step 18 start-up line, R3c, check 4). RUNBOOK 17.6 wording matched.
7. Labels: "TAKE-CHECKLIST item 24 / 17" qualified; "Pin procedure point N" is the new label (was "item/step 3-5"); "FIX-PLAN Step N" capitalised everywhere; bare "Step 3a" qualified; step 18 pass lines renamed "T19 pass line 1..3" and "T21 command (N)".
8. UTC/IST labels added at RUNBOOK 207, 218, 229 (16.11), 247, 285, 331(1). Values unchanged.
9. Dated-schedule times (TC 6 "09:50Z", TC 381 "about 10:00Z / 11:00Z"): corrected to say "dated schedule" and added to the disagree list; per-case clock times from section 6 are the governing ones.
10. Partly done (see top). Also fixed: unbalanced `**` in row 229 (`**2, 2, 2, 1**`), "(6a)" pasted onto 17.14 is now its own block `17.14a`, paren depth 0; row 215 "FILE1 FILE2" now FILES and its unclosed `**`; row 219 stray double backtick; row 187 [step log] wrapper statement now also covers steps 1, 3, 4.
11. Step 18 (1b): `input_ready SECOND_ADMIN >> "$TESTLOG" 2>&1`, so the ready line is read from the saved log.

Minor guard gaps (all fixed): need_new (line 174) refuses empty (`REFUSED: $V is empty; type a NEW $V in the call`; empty returns 1, new path 0, existing path 1); step 11b `need_set REPO EXPORT TESTLOG`; step 18 first line guarded; step 9(a) prints `values-file-made` only if the subshell write succeeded, else `REFUSED: the values file was not made`.

## Coordinator extra item: TC check 7
The old one-line `cd "$REPO" && grep ...` form is replaced by the fail-closed form of FINDINGS.md F-042/F-043: `. "$ENVSH" && need_set REPO && test -n "$REPO" && test -f "$REPO/handover/demo/VIDEO-RUNSHEET.md" && echo FOLDER-OK && { grep -n -i ... ; echo "grep exit $?"; }`. Pass needs `FOLDER-OK` first and `grep exit 1`; `grep exit 2` or no FOLDER-OK is not a pass. Positive control `grep -c -i -e "a person decides"` must print 2. Tested as above.

## Decisions for the lead
1. WAIT_S due time: the header rule "earlier time wins" gives 04:00/06:00Z, but section 10(h) and the clock block give 08:29Z. I kept 08:29Z; confirm or change the rule.
2. Is a missing n8n_api.py at 04:54Z a stop for all steps or only for the steps that use it (I wrote the second, narrower reading as a proposal)?
3. Per-case NO-GO governing times (Case A 06:53 + 307 min = 12:00; Case B about 12:55Z; repeat of flow files +146 min later) and which rule gives way to the 12:00 slip limit. Case B overruns 12:00 and needs your ruling.
4. Dated versus gated times (items 9 and the new disagree item 6).
5. The 19a address form (how the second key is obtained).
6. New labels: "Pin procedure point N" and new block number 17.14a.
7. Approve or refuse a manual commands-first rewrite of the eight cells (4a, 4b, 6, 8, 9, 13, 16, 18); history archive is in reviews/runbook-history-cells.md.
8. Q31 items 25 and 50 hold the old wording and are append-only; they need a lead-written correction line if wanted.
9. EGM review of this result (egm:* reviewers, then resolve) is yours to run; non-security path, round beyond 2 means only Blockers and Majors.

## Files changed
RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md (line 33 words list and Step capitalisation only; clock block untouched), reviews/runbook-history-cells.md (new), reviews/fix-planfiles37.md (this file). Scratch copies of the originals (RUNBOOK.orig, TC.orig, FP.orig) are in the scratchpad.

## Token use
Not measured by me; the earlier part of the session was long and was compacted once. I cannot give a number.
