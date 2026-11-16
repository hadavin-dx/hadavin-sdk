# Round 30 fix log: RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md (source: reviews/plan-files-reader-r29.md)
Fixer: one agent, 2026-11-16. Non-security path beyond round 2: 8 Majors, the stray fragment (9) and the Nits. Nothing was committed. Nothing was run in n8n or on the real tree. STUDIO-PREAMBLE v1 / EGM-GATE v1 read.

## Failures, uncertainty and what I did not do (first)
1. NOT CHANGED, lead-owned: the Nit "gated Wednesday times (rehearsal block ends 09:37, take 10:07) imply a gate gap before rehearsal 2". The brief says change no time the lead set. RUNBOOK section 6 does name the gates (10 + 4 + 45 + 4 + 15 + 45 + 4 = 127 min, ending 09:37), while the Clock block gives only the gated times of rehearsal 1 and the numbers row (07:48 to 08:33, 08:33 to 08:48). I left the Clock block identical in both files. Proposed Q31 text below.
2. Choices left to the lead, as the brief says: F-011 route A or B (item 3), and who names the person (item 8). For item 8 I wrote the existing audit proposal (the owner, or a human the owner picks, names the person; the lead writes the cell `PIN_NAME`) as "audit proposal, lead to confirm", not as a decision.
3. The three evidence standards stay "NOT WRITTEN: LEAD FILLS" (GO row 7, route B). I invented none. Under B the replacement wording for "one Postgres server with two databases" is still LEAD FILLS with no time of its own; it follows the evidence standard due Tue 06:15Z (Inputs-list item 12).
4. Not run: every command is written, not run on the lead's machine. The guard chains were run only with a stand-in `need_set` and stand-in `psql` (below). The real `psql`, n8n and the take folder were not touched. The `bash -n` check covers syntax, not behaviour on the real tree.
5. Spans NOT extracted for `bash -n`: the fenced blocks of TAKE-CHECKLIST (R2j, R6j, R7j, R8; I did not change them), the RUNBOOK copy loop and SHA_SCRIPTS command (unchanged), and prose-only edits.
6. I did not edit EXCEPTIONS.md or QUESTIONS.md. Row 5 of EXCEPTIONS.md (Reading A, ORDER 004) is only referenced in GO row 7: under B it no longer holds as written, and whether it is superseded is the lead's line.
7. The reviewer's words were checked by text before editing; no finding was contested. Two details differ from the reviewer's wording: (a) FIX-PLAN 4c's chain already had `rev-parse` before status, so the true gap was only that RUNBOOK step 6 used "must print NOTHING"; (b) the reviewer wrote item 3 "six places": found exactly six (FIX-PLAN 96, 130, 131; TAKE-CHECKLIST 59, 81, 203).

## Finding to result
| # | Finding | What I checked in the text | Result (where) |
|---|---|---|---|
| 1 | step 6 check passes on empty output; two copy commands | confirmed: RUNBOOK step 6 said "must print NOTHING"; FIX-PLAN 4c held a different group command (`found`/`bash-n-ok`, `cp` overwrites) and a stale `! grep -q '^SHA_SCRIPTS='` claim | RUNBOOK step 6: one chain, pass word `scripts-committed` (`scripts-DIRTY` or REFUSED is a stop); pass cell lists `tuesday-set-copied` and `scripts-committed`. FIX-PLAN 4c: older group command removed, RUNBOOK's mkdir/copy loop/check loop/`bash -n` named as the typed ones; sha sentence now says three-branch, pass words `sha-written`, `sha-written-repeat`, `sha-exists-SHA_SCRIPTS` |
| 2 | no database-name test before the table file | confirmed: only TAKE-CHECKLIST check 2 had it; check 2 (a) said "step 5 (i)" but (i) is CREATE DATABASE; step 8 had no SELECT-only count command | RUNBOOK step 8 (ii) and FIX-PLAN Step 5 (ii): `test current_database() = $TAKE_DB && echo db-is-take-db && psql -f`; (iv) in both files is the same compare (pass `db-is-take-db`); new (v-a) SELECT-only count command in RUNBOOK step 8 pass cell, FIX-PLAN (v) uses the guard form; TAKE-CHECKLIST check 2 "(i)" corrected to "FIX-PLAN Step 5 (ii) and RUNBOOK step 8 (ii)"; note that the two spellings are one run |
| 3 | "Fix A cannot close on Tuesday" with no consequence; no B pass line | confirmed; EXCEPTIONS row 5 says Reading A decided | the one sentence "Choosing A means F-011 stays open at 14:00Z and Tuesday is NO-GO unless T7b and the import test pass by then; B needs the evidence standard (Inputs-list item 12) before it can pass." in all six places (checked: 3 per file, `grep -o` count 3 and 3). GO row 7 pass cell: route A pass line, route B pass line (written evidence file in a `JUDGED row 7 item F-011` line, standard "NOT WRITTEN: LEAD FILLS", no standard by Tue 06:15Z means NO-GO), note on EXCEPTIONS row 5 |
| 4 | JUDGED printf in the Pass rule has no `head`; pass has no minimum | confirmed (line 6 vs R2j/R6j/R7j) | Pass rule printf now has `head %s` and `"$FINAL_SHA"`; the count pass says "equal to the length of the list AND at least 1"; the same "at least 1" added to the row 2, row 6 and row 7 pass cells |
| 5 | wrong item numbers and times in the needed-by paragraph | confirmed: item 22 is the route, item 11 the ledger topic, item 12 the evidence standard; item 34 = Q31 88; item 3 says 05:00Z | TAKE-CHECKLIST needed-by: "Item 22 ... by Tue 03:00Z; Item 12 ... by Tue 06:15Z; Item 11: no time stated, audit reads it as before the GO test (lead to confirm)"; "34 = Q31 88"; item 5 address names now "by Tue 05:00Z" (same two address words as item 3, Q31 item 61) |
| 6 | none-passes an empty variable or wrong path can fake | confirmed; also found that `cd BAD && grep ...; echo "grep exit $?"` prints `grep exit 1` when the `cd` fails (a fake pass) | FIX-PLAN item 7: F-003/F-004 patch grep and F-007 grep now guarded groups with `need_set REPO`, `test -s`/`test -d`, positive `grep exit N` line; TAKE-CHECKLIST check 13 F-007 grep and the 60.8 grep (line 355) same form; Pass rule text: a none-pass needs a printed positive line and a guard |
| 7 | step 15 and step 11 passes typed with `echo` | confirmed | RUNBOOK step 15: `stepjudge 15 boxes passed`, pass read from `grep '^JUDGED step 15 check boxes ' "$JUDGELOG"`; step 11 screen look: `stepjudge 11 screen-look passed`; section 4 "Step records" and the TAKE-CHECKLIST Pass rule Form 2 list now name steps 11 and 15 |
| 8 | "lead" has two readings; RUNBOOK 44 vs item 14 | confirmed (README.md says ORDERS.md is written by the lead; item 14 says the owner names the person) | defined once in RUNBOOK section 2 (new table row), with a pointer sentence in FIX-PLAN line 6 and TAKE-CHECKLIST Words box; RUNBOOK Answer cells sentence uses it; RUNBOOK 44 now the audit proposal (owner or a human the owner picks names the person, the lead writes `PIN_NAME`). Marked "lead to confirm" |
| 9 | stray fragment in FIX-PLAN item 8 | confirmed: summary of EXCEPTIONS row 1 / ORDER 012, broke the sentence | deleted incl. leading ": "; sentence moved after "F-020" in the AFTER THE VIDEO list with "EXCEPTIONS.md row 1, ORDER 012" |
| Nit a | gate gap before rehearsal 2 | RUNBOOK section 6 names it, Clock block does not | NOT CHANGED (lead's times); proposed Q31 text |
| Nit b | RUNBOOK step 7 pass lacks `need_set N8N_PORT` and forbidden-port test | confirmed | step 7 pass command now has both, as FIX-PLAN 4d |
| Nit c | delete of filled-1 has no gone line | confirmed | `gone-filled-1` / REFUSED command added |
| Nit d | step 4b (b) no `test -s "$LOG.pin0"` | confirmed | `test -s` with `log-pin0-written` / MISSING line before the `grep '^!!!'` |

## Proposed Q31 text (QUESTIONS.md is another fixer's file; not edited)
- Q31 item 89 (proposed), who writes ORDERS.md and the Q31 answers: "RUNBOOK section 2 now says the lead (the Claude session) writes ORDERS.md and every Q31 answer, and for an owner choice asks the owner and writes the owner's reply into ORDERS.md. Is that right? Answer by Tue 04:00Z (09:30 IST). If not answered, the written reading stands."
- Q31 item 90 (proposed), F-011 B and EXCEPTIONS row 5: "If F-011 is downgraded (route B), is EXCEPTIONS.md row 5 (Reading A, ORDER 004) superseded, and what is the replacement wording for 'one Postgres server with two databases'? Answer with the evidence standard (Inputs-list item 12), by Tue 06:15Z (11:45 IST). If route B is not chosen, no answer is needed."
- Q31 item 91 (proposed), Wednesday gated clock: "The Clock block lists the gated times of rehearsal 1 and of the numbers row only; RUNBOOK section 6 adds a 4-minute gate before rehearsal 2 (block ends 09:37). Should the Clock block show the gated times of rehearsal 2 too? A time change is the lead's. Answer by Tue 14:00Z (19:30 IST)."
(Item numbers 89 to 91 are a guess: the other fixer owns QUESTIONS.md numbering.)

## Raw outputs
Diffs (find by text; line numbers did not move in FIX-PLAN and TAKE-CHECKLIST, RUNBOOK gained one line, the roles-table row):
```
diff <(sed -n 14,47p FIX-PLAN.md) <(sed -n 8,41p TAKE-CHECKLIST.md)   -> empty (printed CLOCK-EMPTY)
diff <(sed -n 49,61p FIX-PLAN.md) <(sed -n 43,55p TAKE-CHECKLIST.md)  -> empty (printed WHO-EMPTY)
```
(Block starts checked by text: "## Clock (the SAME block ..." at FIX-PLAN 14 / TAKE-CHECKLIST 8; "**Who is needed when" at FIX-PLAN 49 / TAKE-CHECKLIST 43; last rows "| the owner | posts |" at 61 / 55.)

Tools, from flows-audit (after the last edit):
```
python3 -I tools/check_refs.py     -> PASS 5171 references
python3 -I tools/check_names.py    -> PASS 655 rows
python3 -I tools/check_secrets.py  -> PASS 0 hits in 2697 files
python3 -I tools/check_counts.py   -> PASS 52 files / 655 nodes
ruff format --check .              -> 845 files already formatted
```
(Baseline before my edits: refs 5171, names 655, secrets 0 hits in 2688 files, ruff 836 files; the file counts moved because other fixers add files.)

`bash -n` on every new or changed command: 25 backtick spans containing my markers were extracted by a script into 25 files (spans 01 to 25) and `bash -n` printed OK for all 25 (the loop matched 25 blocks; names RUN = RUNBOOK, FIX = FIX-PLAN, TAK = TAKE-CHECKLIST). The changed ones are: 02 (take-tree), 03 (`scripts-committed`), 04 (step 7 port), 05 (step 8 (ii)), 06 (step 8 (iv)), 07 (SELECT-only count), 08 (gone-filled-1), 01 (4b (b)), 11 and 17 (stepjudge 11 and 15), 18 to 21 (FIX-PLAN 4d, Step 5 (ii), (iv), (v)), 22 (F-007 grep), 23 (patch grep), 24 (check 2, unchanged but same family), 25 (60.8 grep). The other spans in the 25 are existing commands that carry the same markers.

REFUSED paths, run with a stand-in `need_set` (copied from RUNBOOK section 4), a stand-in `psql` and made-up folders:
```
03 SRC_TAKE empty        -> REFUSED: SRC_TAKE is empty or still a REPLACE_ME placeholder ...   (no scripts-committed)
03 not a git tree        -> fatal: not a git repository                                        (no scripts-committed)
03 clean git tree        -> scripts-committed          03 dirty tree -> scripts-DIRTY
05 PGCONN_TAKE empty     -> REFUSED: PGCONN_TAKE is empty ...                                  (psql -f never ran)
05 database = n8n's own  -> exit 1 only (no db-is-take-db, table file not run)
05 database = take's own -> db-is-take-db, CREATE TABLE (stand-in), exit 0
06 (iv) wrong database   -> exit 1 only
04 N8N_PORT=5678         -> REFUSED: forbidden port 5678      04 empty -> REFUSED: N8N_PORT is empty ...
22 F-007 REPO empty / wrong folder / no handover/demo -> REFUSED (rc 1); clean -> grep exit 1; a hit -> hit line + grep exit 0
23 patch grep REPO empty -> REFUSED; wrong path -> stops silently, no `grep exit` line (not a pass); clean -> grep exit 1; hit -> grep exit 0
25 RUNSHEET missing      -> REFUSED: ... is missing or empty
11 stepjudge with empty JUDGE_WHO -> REFUSED; with names -> judged-line-saved, and the two pass greps each print 1
08 gone-filled-1: absent -> gone-filled-1; present -> REFUSED: ... still exists
```
Evidence of the old failure (item 6): `cd BAD && grep ...; echo "grep exit $?"` prints `grep exit 1` when the cd fails (raw run: `bash -c 'cd /nonexistent_dir_x 2>/dev/null && grep -n x /dev/null; echo "grep exit $?"'` printed `grep exit 1`).

Files changed (all in /home/user/hadavin-sdk/handover/flows-audit/): RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md, and this log. Backups of the three files as they were at the start are in the scratchpad r30 folder. Not committed.
