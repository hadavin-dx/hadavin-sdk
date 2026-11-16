# Fix report, plan files round 28 (RUNBOOK, FIX-PLAN, TAKE-CHECKLIST)

Static audit; nothing ran in n8n; made-up data. No git commits. QUESTIONS.md not touched.

## Failures and uncertainty first
- Not run on the real tree: every changed command is written, not run there. `bash -n` was run on 9 extracted spans (all rc 0; list below) and the guard stop (REFUSED on empty REPO, SRC_TAKE, KEEP) was run on 4 of them with a stand-in `need_set`. NOT extracted and not `bash -n` checked: the one-line prefixes added to RUNBOOK step 3 (`. "$ENVSH" && need_set REPO NEW && if ...`), the two RUNBOOK 4a apply chains, and the RUNBOOK 4b (d) group (a plain `( ... )` wrap).
- I did not read every line of the three files; the sibling sweep used grep (below). About 20 other `cd "$REPO" && grep ...` and `psql "$PG..."` lines remain without their own need_set; I judged each as not a false pass (an empty variable makes the command fail or print an error, and the pass line needs a printed positive line or a non-empty hit list), so left them. This is a judgement, not a run.
- FIX-PLAN item 8 line holds a stray fragment ": the spend ledger and the stage journal are ONE exception made of two files; owner studio lead." after "(lead decision 2026-11-16 item 10)." It looks like a paste error from another item. I did not touch it (not in the findings; meaning unclear). Next step: the lead or the next reader decides whether to delete it.

## Findings -> result
1. need_set missing (psql, REPO, LOG): FIXED. TAKE-CHECKLIST check 2: every command is now a `( . "$ENVSH" && need_set ... || exit 1; ... )` group; new first gate `db-is-take-db` (current_database() equals `$TAKE_DB`) must print before mf_leads.sql runs; pass cell says REFUSED or psql error = stop. RUNBOOK 4a: both `git apply --check` chains start with `. "$ENVSH" && need_set REPO`. RUNBOOK 4b (b) and (d) are groups with `need_set REPO NEW LOG` (and NEW_PIN). Class sweep: the pattern `if test -z "$(git -C "$REPO" status ...)"; then echo status-clean` was a real false pass (git error prints nothing, so `status-clean`); fixed at all 8 occurrences (RUNBOOK 7: step 3, 4a x2, 4b, 4b/pin, 5-ish and 15 rows; FIX-PLAN 1) with `need_set REPO [NEW]` plus `git -C "$REPO" rev-parse --is-inside-work-tree > /dev/null &&`. RUNBOOK step 3 `if test ! -e "$REPO/..."` got `. "$ENVSH" && need_set REPO NEW &&`. RUNBOOK step 6 SHA_SCRIPTS text now names the guard.
2. FIX-PLAN Step 6 `$KEEP`: FIXED. One chain `need_set KEEP TOOL FILLED && ... delete ... && test -n "$KEEP" && test ! -e "$KEEP/filled" && echo gone`; no `gone` = stop; same for `$FILLED1`.
3. FIX-PLAN Step 4c "status prints NOTHING": FIXED. Now a guarded chain with positive line `scripts-committed` (else `scripts-DIRTY` or an error = stop). RUNBOOK step 6 text got the `true`-line-first wording.
4. Two due times: (a) I12 04:54 / 06:59: CONTESTED, one time each for two different things (file at the step 6 row start 04:54; arguments at step 12 export 06:59, matching the clock slot table), no change. (b) FIXED: FIX-PLAN Step 14 inputs now Tue 04:00Z (09:30 IST), as Q31 item 55 and RUNBOOK I47/I57 (Wed 05:45Z kept only as the latest-use note). (c) FIXED: F-011 route one time, Tue 03:00Z (08:30 IST), Q31 item 10 (a), in FIX-PLAN item 8 (was 04:00Z); TAKE-CHECKLIST GO row 3 (c) mutation command now Tue 03:00Z (Q31 item 38 (a)) instead of 04:00Z. (d) FIXED: FIX-PLAN I24 now Tue 04:26Z (09:56 IST) as RUNBOOK I24. (e) FIXED: TAKE-CHECKLIST item 8 now F-018 loop before 06:24Z (RUNBOOK step 10) and import method before 06:39Z (RUNBOOK step 11), matching FIX-PLAN slots. No time set by the lead was changed; Q31 items 15, 48, 51 untouched and read only.
5. Bare "step N": FIXED where ambiguous. RUNBOOK RC8 now "RUNBOOK step 10 prints 0 problem(s) (... FIX-PLAN Step 6 holds the same check)" (the reviewer's reading that it is a FIX-PLAN step is wrong: RUNBOOK row 10 is the fill check; wording made explicit). TAKE-CHECKLIST: Pin procedure references now "Pin procedure item 3/4/5"; 12 other bare RUNBOOK step references now carry "RUNBOOK" (sha names, step 13 repeat, step 8/7, 19a, 1 to 15, 5 to 13, before step 1). Remaining bare ones are already qualified ("Pin procedure, step N", "FIX-PLAN item 3 step N", "Step 0 of the GO test").
6. "desk doors": FIXED. TAKE-CHECKLIST now defines it as FIX-PLAN does (the old entry flows desk-form-door and desk-webhook-door, F-019).
7. I51 "about 05:50 (11:20)": was stale (step 8 row starts 05:14; first use inside it about 05:29 = 10:59 IST, as TAKE-CHECKLIST item 31). FIXED in RUNBOOK I51.
8. $LOG guard form: FIXED. TAKE-CHECKLIST Placeholder row now gives the same REFUSED form as P1a, P2a, R4.
9. EXPORT_PIN grep count: FIXED. Now `grep -v '^#' "$EXPORT_PIN" | grep -c -E '@|[0-9a-f]{16}'` must print 0. Checked on the committed pin: the old form matched 2 comment lines (two 64-hex sha lines); the new form prints 0.
10. Check 14 "checks 4 and 5b read-only forms": FIXED, now names check 4 (c), (d) and check 5b counts, no sending.
11. "contains one of 3 or more letters": FIXED to "a stand-in word of 3 or more letters" (2 places); added what a person with a surname such as Lead, Ai or Code does (no override; write another name or another reader). Marked "read in the script, not run".
12. Scratch-run claim: FIXED. Text now says the final P1b/P2b text with `re.ASCII` was NOT run.

## Lead's extra item (fix A cannot close on Tuesday)
One sentence "Fix A cannot close on Tuesday as things stand (FINDINGS.md F-011, cell STATE OF FIX A ON 2026-11-16: no import command and no Postgres T7b exist in the tree)" added at TAKE-CHECKLIST needed-by paragraph (item 11/12 part, line 59), Inputs-list item 22 (line 81), GO row 7 (line 203); FIX-PLAN Step 4d (line 96), item 8 (A) (line 130) and item 8b (line 131). No time changed; (B) is named the only route that can clear GO row 7 as things stand, as FINDINGS says.

## RUNBOOK edits (frozen file; pure guard/wording/consistency)
1. 4a: need_set on both `git apply --check` chains. 2. 4b (b) and (d): guard groups. 3. All 7 `status-clean` forms: guard plus work-tree check. 4. Step 3: guard prefix. 5. Step 6 SHA_SCRIPTS wording (guard). 6. RC8: "RUNBOOK step 10". 7. I51 time 05:50 -> 05:29 (10:59 IST). A backup of the pre-edit files is in the scratchpad (RUNBOOK.bak, FIX-PLAN.bak, TC.bak).

## Raw outputs
```
diff <(sed -n 14,47p FIX-PLAN.md) <(sed -n 8,41p TAKE-CHECKLIST.md)   -> (empty), rc=0
diff <(sed -n 49,61p FIX-PLAN.md) <(sed -n 43,55p TAKE-CHECKLIST.md)  -> (empty), rc=0
bash -n: tc-check2-a, -b, -c, fp-step6-gone, fp-step4c, status-form, rb-4b-b, tc-expin, tc-log-form: all rc 0
python3 -I tools/check_refs.py    -> PASS 5171 references
python3 -I tools/check_names.py   -> PASS 655 rows
python3 -I tools/check_secrets.py -> PASS 0 hits in 2681 files
ruff format --check .             -> 829 files already formatted
```
Guard test with a stand-in need_set and empty REPO / SRC_TAKE / KEEP: `REFUSED: SRC_TAKE`, `REFUSED: REPO`, `REFUSED: KEEP`, `REFUSED: REPO` (the four commands stopped before any git or psql call).
