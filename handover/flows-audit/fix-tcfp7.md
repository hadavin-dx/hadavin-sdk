# fix-tcfp7: TAKE-CHECKLIST.md and FIX-PLAN.md, round 16Z section B (M1 to M10 and smaller items), ORDER 037 item 3, coordinator extras and citation r7

Fixer log. Static edits only. Nothing was run in n8n and nothing was run on the real tree except the five allowed check commands and `bash -n flow-check/take_check.sh`. Backups: `bak-tcfp7-take.md` and `bak-tcfp7-fixplan.md` in the scratchpad. No commit.

## What was changed (finding, then fix)
- M1 pass rule: new "Pass rule" paragraph in TAKE-CHECKLIST.md (Form 1 command plus pass line; Form 2 a JUDGED line in `$JUDGELOG`). "NOT CHECKED" and "a GO would be a judgement by the lead" removed. Rows 2, 6, 7 end in a recorded judgement.
- M2 pin procedure: rewritten with Blocks P1a, P1b, P1c (output kept in `"$LOG.pin1"`, count of `NEW PIN WRITTEN to`, python3 reviewer-line writer, commit, `SHA_PIN1`); pin 2 uses the same blocks. FIX-PLAN steps 4 and 9 no longer send the pin run to /dev/null.
- M3 sha names: the RUNBOOK four (`SHA_FOLDER`, `SHA_PIN1`, `SHA_PIN`, `SHA_SCRIPTS`); `$FINAL_SHA` became `SHA_EVIDENCE` and is said not to be one of the four.
- M4 branches: each GO row names its branch; row 3 runs on `$BRANCH`, rows 4 and 7 on `$PATCH_BRANCH`; `git status` limited to `-- src tests`; `test ! -e "$EVLOG"` added; pytest exit code in a sub-shell.
- M5: `<new folder>` replaced by `$NEW` and `$FLOWS`; `'^!!!'` single-quoted; take_check run as `bash "$REPO/..."` with a separate `test ! -e "$LOG" && echo "log path is new"`.
- M6: GO rows 1, 4, 5, 6, 7 have command blocks R1, R4, R4b, R5e, R5f, R6, R7 with counts as pass lines (RUNBOOK step 5 counts).
- M7: export check (exactly four files, JSON parse, take_check on `$EXPORT`, pin 2) added to row 4 as Block R4b.
- M8, M9: one identical Clock block (Tuesday table, Wednesday table, who is needed when) in both files, taken from RUNBOOK section 6. "about 08:00Z" for the WARN reader replaced by 04:26Z and 07:14Z. "Same day" replaced by times. Slot table of FIX-PLAN corrected: the re-smoke is RUNBOOK step 16 and does not repeat steps 5 to 13.
- M10: reviewer line limits written (ASCII only, whole stand-in list, text "session" or "lead to confirm" anywhere, date real, not future, not older than the pin's date line).
- Smaller: Step 0 uses `--show-toplevel` equal to `$REPO`; `ACCEPTED` grep uses only the prefix.
- ORDER 037 item 3: Inputs item 9 marked settled; re-smoke and rehearsal definitions fixed; "default no" fixed; FIX-PLAN lines 1, 10, 22, 23, 26, 32 fixed; new Inputs item 19 (contacts left in the real trial account, number of Step D messages, credits ceiling).
- Coordinator extras: FIX-PLAN step 7 DESK_ALERT_TO check; step 17 SELECT-only count of rows in review/unknown/failed; T19 and T21 pass wording; step 10b named as F-018's pass line; item 7 F-004 note; item 8 downgrade evidence; TAKE-CHECKLIST check 7 Blocker-if-said greps; GO row 6 computed from the LEDGER-ROWS flag; GO row 7 and check 12 point to the FINDINGS downgrade evidence.
- Citation r7: (1) PLAN-4-NLITE-FROM-LEAD.md line 106 holds no such wording; cite changed to line 196 ("until cleanup", not "deleted"). (2) S9-2 and S9-3 cited by the table row that begins "S9-2, S9-3" in QUESTIONS.md, not by line numbers. (3) inputs/DECISIONS-2026-11-16.md here is a 13-line copy that does not define S9-2 or S9-3; the original is in the studio folder; said so. (4) Q28 item 4 (line 166) gives the list without times; only Q27 item 10 (line 156) says "with times"; fixed in Inputs item 15.

## Tested in scratch (made-up data, scratchpad/tcfp7)
Step 0, the row 1 loop and unset guard, the pin-edit python3 program (ok, bad date refused, line break refused, two reviewer lines refused), the commit block (git scratch repo), the post-twice loop with sha before and after (2 HTTP, 2 sha256, 1 distinct), the export check, the DESK_ALERT_TO test (prints the line when different, nothing and exit 1 when same or empty). The row 6 awk filter and the F-041 Part A and Part B greps were run read-only on the real tree: Part A no hit (exit 1), Part B lists only handover/demo/n8n-rerun/R2-tables.md, the awk lists F-037, F-008, F-011, F-029, F-041, F-018 (OPEN) and F-003 (lead decides).

## Check outputs (from handover/flows-audit)
secrets rc=0 (PASS 0 hits in 1803 files); refs rc=0 (PASS 5160 references); counts rc=0 (PASS 52 files / 655 nodes); ruff check rc=0; ruff format --check rc=0 (519 files already formatted); bash -n take_check.sh rc=0.

## Not done or uncertain
- The GO commands on the real tree were never run (no values exist). Mutation command, import, post-twice script, mailbox tool, T7b runner: still LEAD FILLS; those rows are NOT PASSED until written.
- Row 6 reads LEDGER-ROWS.md in this repository; the real ledger is in the studio folder.
- The python3 pin writer was not run against a real pin from take_check.sh.

## RUNBOOK doubts (RUNBOOK.md not edited)
- Step 4b and 13 use `sed -i` with `<LEAD FILLS: NAME>` text; a name such as O'Brien breaks it. The python3 block here is safer.
- Step 14 (c) `grep -F ... | grep -o '[0-9]' | wc -l` prints 0 when the sentence is missing (false pass).
- RUNBOOK still carries "decision 4" wording, which take_check.sh and check_flows.py print and test.

## Files with stale text for the lead's REPORT.md list (ORDER 037)
Edited here: TAKE-CHECKLIST.md, FIX-PLAN.md. Not mine and may still carry the stand-in or "rehearsal not in real HubSpot" text: QUEUE.md, ORDERS.md (line 20), REPORT.md, STATUS-BOARD.md, OWNER-STEPS-q16-rows.md, PLAN-005.md, fill_flows/README.md, flow-check/README.md.

## Round 9 (TAKE-CHECKLIST.md and FIX-PLAN.md only; static text edits; not committed)
Inputs checked against files and flow-check/take_check.sh first: tc-r8-commands-findings B1 (true: unanchored `RESULT: 0 FAIL` count is 3 on a correct run; the "two greps" explanation was wrong and is dropped), T21 REVOKE CONNECT (invalid, PUBLIC holds CONNECT), findings-r9-codebase Major 3. Backups in the scratchpad (bak-tc9-*.md).
Changed: anchored FINAL greps; separate judge blocks R2j/R6j/R7j and R8 decision; chained guarded commits (FP step 3, P1c); R3 with SHA_EVIDENCE check, R3c leftovers check; R4/R4r/R4b-1/R4b-2 with LOG3 and counts files; R5e counts; R7 single command and pass line (same in FP 8b); exit echoes on "prints nothing" greps; T21 method, T19 provisional, T20 extra case; guarded FP step 2; needed-by table; ENVSH, LOG3, FINAL_SHA rows; evidence file list; items 20-23 and item 14 QUESTION; check 1 now says "decision 4" must not be changed alone (F-008 greps the literal).
Checks, run from this folder: check_secrets exit 0 (0 hits), check_refs exit 0 (5162 refs), ruff check exit 0, ruff format --check exit 0, Clock diff exit 0.
Not run: none of the commands in the new blocks were executed on a real tree.

Extra items (coordinator): 6 RUNBOOK-fixer items applied to TAKE-CHECKLIST.md; item 5 RUNBOOK 4b(c) text not found, unverified.

## Round 10 (TAKE-CHECKLIST.md and FIX-PLAN.md only; static text edits; not committed)
Source: reviews/tc-r9-fresh-findings.md (0 Blockers, Majors 1 to 10, Nits 1 to 5). Every finding was checked against the files first; none was untrue. RUNBOOK.md, FINDINGS.md and QUESTIONS.md were not edited. Clock blocks: no clock time changed.
- Major 1: one identical gates line added after the Wednesday table in both files (dated times, no gates; with gates Case A take 10:07 to 11:07, ready about 11:27; Case B take 11:02 to 12:02, ready about 12:22; RUNBOOK section 6 wins).
- Major 2: FIX-PLAN got Step 4c (copy take scripts, RUNBOOK 6), Step 4d (start n8n, F-011 decision first, readiness check on `$N8N_PORT`) and Step 8a (activation plus a GET probe; the 404 wording is UNVERIFIED); step map and slot paragraph updated.
- Major 3: all log guards in TAKE-CHECKLIST are now chained (`test ! -e ... && ... > log; echo "exit $?"`), the `git switch` lines are chained, pin restore goes through a temp file.
- Major 4: `$ENVSH` row rewritten (`ENVSH="$TAKE_FOLDER/shas.env"`), skeleton printed, `. "${ENVSH:?unset}"` plus `:?` guards at the top of every block, rows added for `$N8N_PORT`/`$TAKE_PORT`, `$TAKE_DB`, `$PGADMIN`, `$FLOWS_ROLE`, `$FLOWS_PW` (and `$SRC_TAKE`, `$ACTLOG`, the shas); Block R3 appends `SHA_EVIDENCE` and `FINAL_SHA`.
- Major 5: Block R2 uses `"${SHA_SCRIPTS:?unset}"`. Major 6: P2a, P2b, P2c printed in full. Major 7: exit echoes added (FP steps 1 and 6) and a positive control in R6. Major 8: reader window 04:26Z to 04:51Z and 07:14Z to 07:44Z everywhere. Major 9: written as QUESTION, Inputs item 24, "planned by the audit, lead to confirm"; no JUDGED line until answered. Major 10: branch base is `$FINAL_SHA` with a printed merge-base test.
- Nits 1 to 4 applied (typed T19 to T21 pointers, T21 step 3 and INVALID line, P1b guards, key-in-body check, 16-row total). Nit 5 acknowledged, no change.
Port name: RUNBOOK says `TAKE_PORT`, FINDINGS says `N8N_PORT`; this round writes `$N8N_PORT` and defines `N8N_PORT="$TAKE_PORT"` in the skeleton.
Not run: no command was executed against n8n, Postgres or the network. The 23 fences of TAKE-CHECKLIST and the 6 new inline FIX-PLAN commands passed `bash -n`; Step 4c was run once in a scratch folder on made-up files (found, found, MISSING as expected).
Needs the lead: item 24 ($JUDGE_WHO); LOG3 and REPORT naming differences inside RUNBOOK.md (section 4 drops LOG3, input I2 names it; RUNBOOK set-once holds REPORT, here it is typed per call); port name; the mailbox count command; whether `/healthz/readiness` and the GET-404 wording hold for the take's n8n version.
