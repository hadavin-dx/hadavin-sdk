# fix-planfiles41: round 41 fixes for RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md (static; nothing run in n8n, Postgres or HubSpot; made-up data only)

## Gaps and failures first
- Nothing was RUN: every new command is written, never tried (marked "mine, not tried" or "round 41" where it stands). The SQL of TAKE-CHECKLIST check 4 (a)/(b) is checked only against the column names of `handover/demo/n8n-flows-v4/mf_leads.sql` (`crm_id`, `state`, `lead_key`).
- Reader words were unverified; each was checked in the file. Two points were CONTESTED, not applied as asked:
  1. RUNBOOK 41b "shas.env vs ENVSH": the command files DB_SETUP.sh and DB_GRANTS.sh run in a child `bash` where `ENVSH` is NOT set (only `PGHOST`, `PGPORT`, `PGPASSFILE`, `TAKE_FOLDER` are exported), so `$TAKE_FOLDER/shas.env` is correct there; a sentence now says so. The two sha-writing commands of steps 4 and 4b did use the other spelling and were changed to `$ENVSH`.
  2. TAKE-CHECKLIST M5 asks to REFUSE a repeat sha line. RUNBOOK section 4 appends a new line on a repeat by design (round 21, M6: a repeat of step 3, 4, 4b or 13 needs the newest sha). Changing that is a decision, which this round may not take. Fix made instead: both files now say the operator reads both values with `grep -n '^SHA_X=' "$ENVSH"` and writes them in the take prep, so the later line never wins unseen. Only SHA_EVIDENCE and FINAL_SHA are refused on a second line (unchanged).
  3. TAKE-CHECKLIST "Unsettled: `( cd "$REPO" && ... )` for Row 3 not found": it exists in Block R3 (the pytest line), after `need_set REPO` on the block's first line; a note now says so.
- Not changed, not Major, not verified: RUNBOOK reader a "Not Major" items (lines 194 vs 198 on KEY/KEYS typed per call; line 183 does not reset FNMISS on re-source). These are for the lead to rule on if wanted.
- LEAD FILLS (inputs only the lead can give; each states the next step in the file): name of the existing account that runs DB_SETUP.sh (Q31 item 78) and DB_GRANTS.sh (Q31 item 88), due 04:54Z; mailbox count command, HubSpot search command and the send command for two lead IDs (Q31 item 25, due Tue 06:00Z); the named WARN reader's name and how to reach them (Q31 item 48, due Tue 03:30Z); exact output of the harmless call of each take script.
- Clock block untouched: `sed -n 37,84p FIX-PLAN.md | md5sum` = `sed -n 8,55p TAKE-CHECKLIST.md | md5sum` = 929febdfab0142f49dfd50627d87285d.
- No new steps or decisions in RUNBOOK. Line counts unchanged in all three files (RUNBOOK 429, TAKE-CHECKLIST 493, FIX-PLAN 258), no table row changed its number of vertical bars.

## Finding to change
| Finding | Verdict | Change |
|---|---|---|
| RB-a M1 wrapper masks first failure | confirmed | RUNBOOK section 4 step log: an `echo "exitN $?"` after EACH command; "Log wrapper" and "Evidence logs" paragraphs: one command per wrapper or an exit echo after each |
| RB-a M2 FINAL_SHA has no step | confirmed | RUNBOOK section 4 FINAL_SHA bullet: Block R3 run by the lead before step 1, `evidence-sha-written` is step 1's start condition; step 1's own `need_set ... FINAL_SHA` is the guard; no new step |
| RB-a M3 two rules for (e) NOT CHECKED | confirmed | one rule: gate is written `PASS-WITH-(e)-NOT-CHECKED` only before the owner's scope answer; step 24 treats it as FAIL |
| RB-a M4 SHA_PIN2 undefined | partly (pin2 already named in the sha rule) | defined in section 4 next to SHA_PIN; "four shas" sentence names it as the fifth name; old round-6 text points to `${SHA_PIN2:-$SHA_PIN}` |
| RB-a M5 stale "round 38" | confirmed | status line: round 41 and the log pointers; states that no fix-planfiles40.md exists |
| RB-a M6 three due times | confirmed | roles table row holds THE ONE TIME; PIN_NAME line and the WARNING line point to it |
| RB-a M7 log lists omit 17, 27-30 | confirmed | step log paragraph: 17 and 29 own-log, 27, 28 and 30 no command so no log |
| RB-b shas.env vs ENVSH; TAKE_FOLDER missing in need_set | confirmed for steps 4, 4b, 8 | steps 4 and 4b write to `$ENVSH`; step 8 need_set gets TAKE_FOLDER; child-shell point contested (see above) |
| RB-b step 8 PASS for (0a), (0b), (i), (ii-b) | confirmed | pass cell now lists them |
| RB-b step 8 accounts | confirmed | LEAD FILLS with item, due time, consequence |
| RB-b row 7 vs row 8 SQLite/Postgres | confirmed | step 7 may run without step 8 only for SQLite; Postgres: step 7 waits |
| RB-b forbidden-port guard only after start | confirmed | guard command before the start command in step 7 |
| RB-b step 6 timing | confirmed | 04:54Z is start and due time; checks inside the 20 min; step 8 at 05:14Z |
| RB-b n8n_api.py not in copy loop | confirmed | separate guarded copy command with pass `api-copied` |
| RB-b harmless call no expected output | confirmed | expected output and a logged command form |
| RB-b 4a FILES pasted from 14(g), subjective pass | confirmed | 4a list holds only 4a's files; pass cell lists the printed words as the pass |
| RB-b PIN_RECEIPT 4b(d) vs 13(d); 4b pass cell | confirmed | 4b (d) reads `Receipt for the reviewer line` from `$LOG.pin1` (take_check.sh line 699 prints it there); pass cell shows `, pin sha256 XXXXXXXX` |
| RB-b git checkout vs "never by git checkout" | confirmed | step 13 old `git checkout` commands marked OLD FORM, DO NOT TYPE; Blocks R4r and R4b-2 are the one method |
| RB-b webhook probe `exit 0` vacuous | confirmed | each curl prints `curl-exit N`; pass needs two counts of 2; `exit 0` alone is not a pass |
| TC M1 two step 1 start times | confirmed | one start (04:00Z); 03:31Z named as the plan's earlier variant |
| TC M2 decision 1 edit vs Row 3 | confirmed | edit goes onto `$BRANCH` before Block R3 with the FINDINGS and LEDGER words |
| TC M3 Row 3 (e) cannot fail cleanly | confirmed | fail-closed command `code-check-ran` / `exit 0` (same as RUNBOOK step 17 (3)) |
| TC M4 step 0 detached HEAD | confirmed | `test -n` on branch name in TAKE-CHECKLIST and FIX-PLAN |
| TC M5 sha repeat | contested | see above |
| TC M6 "ONE table" | confirmed | SHA rows 177 to 179 and `$REPORT` in row 183 are pointers; heading defines "one defining row per name" |
| TC M7 undefined names | confirmed | `$TESTLOG`, `$GATELOG` defined; `$SHA_PIN2` added to the SHA row |
| TC M8 R7j hardcodes F-041 | confirmed | `JUDGE_ITEM` typed and in need_set; row 7 text updated |
| TC M9 two rules for viewer-file hits | confirmed | one rule: no harmless exception for run sheet and page statements |
| TC M10 nobody named | confirmed | LEAD FILLS with the exact input and the due time before 04:26Z |
| TC M11 no runnable command | partly | check 4 (a)/(b) command written (read-only login); (c), (d), 5b: BLOCKED with the exact input and due time; check 6 pass word `mail-count 1` |

## Raw tool output (run from handover/flows-audit after the edits)
ruff format --check . : `1028 files already formatted`
check_refs.py : `PASS 5193 references`
check_names.py : `PASS 655 rows`
check_secrets.py : `PASS 0 hits in 2903 files`
check_counts.py : `PASS 52 files / 655 nodes`
