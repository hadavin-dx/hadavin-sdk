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

## Round 11 (TAKE-CHECKLIST.md and FIX-PLAN.md only; static text edits; not committed)
Source: reviews/tcfp-r11-findings.md (M1 to M10, Nits) plus the coordinator's contacts item. Checked against the files first; reviewer claims all held, except: the Nit "Words box starts line 84" cites no text I could find (no "line 84" in either file; no change); M10 database time: 04:54Z is already earlier than the 05:14Z n8n start, so it stands (a note was added). RUNBOOK.md, QUESTIONS.md, FINDINGS.md not edited. Clock blocks: the sed range through "| the owner | posts |" is byte-identical (diff exit 0); no clock time changed. Own slip: my first edit run deleted Blocks R5e to R8 by a bad slice; I restored both files from backup and reran with a fixed slice; all Blocks R1 to R8 are present (checked by listing).
- M1 (TC/FP side): TC no longer prints a skeleton; it points to RUNBOOK section 4 and lists the names it needs; TAKE_PORT row is now a single N8N_PORT row (value "5690"); FP points to RUNBOOK section 4.
- M2 (TC side): Block R3 refuses if SHA_EVIDENCE or FINAL_SHA is already in $ENVSH (prints "ENVSH holds no evidence sha yet" first).
- M3: FP Step 4c has mkdir -p -m 700 first; SHA_SCRIPTS is made in its own && chain from `git -C "$SRC_TAKE" rev-parse HEAD`, stops if $SRC_TAKE is not a git work tree.
- M4: FP slot sentence relabelled (FP step with its RUNBOOK step in brackets) and the step map now covers FP 0 to 9 and 10 to 17 and RUNBOOK 4a, 14 to 17 (the Wednesday mapping is my reading; RUNBOOK wins).
- M5: FP step 4 starts with "FIRST do RUNBOOK 4b = P1a, P1b, P1c"; "(or always ...)" removed, exit 4 is stated certain (reviewer line names a session); Block R4 split into part 1 (pin lines) and part 2 (take_check).
- M6: verified RUNBOOK step 13 (e) writes $LOG2.final and says R4b-2 is not used. $LOG3 row and sentences dropped; row 4, Raw output files, Pin procedure steps 2 and 5, FP step 9 use $LOG2.final; new Block R4f counts $LOG2.final; Block R4b-2 now only restores pin 2 and says it is not used on Tuesday for row 4.
- M8: FP step 0 uses RUNBOOK step 1's path scope and requires HEAD = $FINAL_SHA before check_patches.sh.
- M9: Wednesday token-scopes row in both Clock blocks marked "may be moved to Tue 05:54Z; lead decides (QUESTIONS Q31 items 27 and 30)".
- M10: export script "before 06:59Z".
- Contacts (coordinator): Inputs items 19 and 23, Words box Step D, schedule row, Row 4/10/11 text, Clock Step D rows and FIX-PLAN 10b and schedule now follow RUNBOOK (10 contacts with the hook leg, 9 without; message 1 lists 7 or 6, message 2 lists 3; message 1 after the two sends of step 19a); hook leg marked lead to confirm; the conflict with OWNER-STEPS "one message per contact" is flagged, not decided.
- Nits applied: FP step 5 CREATE DATABASE and current_database(); FP step 7 control for the placeholder-name grep; "Inputs item 21" cites fixed (4d, port row); FP 8a webhook paths read from the files (mf-form, mf-hook) with a note; Block R2 split so SHA_SCRIPTS is needed only in new Block R2s; `scripts\n8n_api.py` now `scripts/n8n_api.py`.
Checks, from this folder: check_secrets exit 0 (0 hits), check_refs exit 0 (5168 refs), ruff check exit 0, ruff format --check exit 0, Clock diff exit 0, bash -n on all 17 TC fences and FP fences exit 0 and on the three new FP inline commands (4c two commands, step 0) exit 0.
Not run: nothing against n8n, Postgres or the network; no new command was executed.
What RUNBOOK must contain (for the RUNBOOK fixer): one superset section 4 skeleton with VALUES, FILLED1, FILLED, SRC_TAKE, ACTLOG and N8N_PORT="5690" besides what it holds; no SHA_EVIDENCE and no FINAL_SHA line in it (R3 appends both and now refuses if either exists); LOG3 dropped from section 4 and I2; && chains in step 4, step 4b (e) and step 13 (d) so a failed commit never writes the old sha (SHA_FOLDER=... only after the commit succeeded); step 1 status scope stays as is (TC/FP now copy it); step 13 (e) and its counts stay the one source for row 4's second run; "Step D message 1" timing and contact counts already RUNBOOK's.
