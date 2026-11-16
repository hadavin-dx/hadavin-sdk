# fix-tcfp9: round 13 fixes to RUNBOOK.md, TAKE-CHECKLIST.md, FIX-PLAN.md (fixer, started 13:51Z, written 14:03Z)
Nothing here was run in n8n, Postgres or HubSpot. All new command blocks are WRITTEN, NOT RUN. Originals: scratchpad bak-tcfp9/.
Checkpoint 13:56Z: guards applied to TAKE-CHECKLIST (bash -n 25 blocks OK). Checkpoint 14:01Z: RUNBOOK, FIX-PLAN and QUESTIONS edited.

## What failed or is not done (first)
- Not every "LEAD FILLS" cell is rewritten one by one. A blanket rule (TAKE-CHECKLIST "Blanket rule" paragraph, FIX-PLAN Read-first bullet) covers the rest; about 25 FIX-PLAN occurrences still read "LEAD FILLS" (grep shows them). Partial for B4.
- RUNBOOK pass-line cells of steps 18 to 26 are not each edited to say which log they read. I added the citation to the step-title cell of rows 7, 8, 16, 18, 19, 19a, 21, 23, 24, 26 (10 rows) and the "Evidence logs" rule in section 4. The `| tee -a` is NOT added inside each T19-T21 command (those commands live in FINDINGS.md F-002, outside my files). Partial for M4.
- No wrong cite found at RUNBOOK:204 (now 207). It cites OWNER-STEPS item 5 (exists). Every "ORDERS.md line 132" cite (RUNBOOK 15, 184, 358; TC 70, 167) is Q21 item 3 and line 132 holds that text and "never downgrade by counting". The literal "132 item 13" does not occur in the three files.
- check_secrets.py prints FAIL 2 hits: flow-check/raw/test-take-check.txt:177 (the known hit) and flow-check/evidence-f8-r8.md:55 (a made-up reviewer line, file modified 13:58, not by me, I did not edit it; not checked whether it is new).
- ClaimStuck, MailClaim, desk doors are not defined in QUESTIONS GLOSSARY; I wrote my reading (marked "lead to confirm", Q31 item 38). Stage service, the challenge, Qualify ARE in the glossary.
- Step 0a: the awk command that makes shas.env was syntax-checked and the extraction of the skeleton was run in scratch (64 lines, bash -n OK). The command inside FIX-PLAN was not run as written.
- Time box: finished inside 40 min but review quality of each rewritten cell is untested; a stranger read is needed.

## Findings -> change -> check
- Consistency M1 (silent guards): TAKE-CHECKLIST 19 guard lines (R1, R2.., R3 line 193, R4, R4b, R4f, R5e, R5f, R6, R7, P1a, P1b, P2a) now `if test -e X; then echo "REFUSED: ..."; ... fi`; each counts/cat read is guarded on the log it reads; RUNBOOK steps 4b(d), 5, 6 (ROW1), 13 (a)(c)(e)(counts) and values file/filled guards; FIX-PLAN step 4, 2, 8a, 9. Check: `bash -n` on the 25 TC code blocks printed no error; 22+4 inline if/fi spans of RUNBOOK and FIX-PLAN pass bash -n (after I fixed one misplaced parenthesis).
- M2 (step 13 repeat): RUNBOOK 13(a)(c)(d)(e) use `$LOG2`, `$EXPORT_PIN`, `$LOG2.final`; `SHA_PIN_N` removed, repeat prints `SHA_PIN_REPEAT`, appended nothing; `.final2` removed from RUNBOOK 159, 183, TC 313, FP step 9 (RUNBOOK:33 history kept). Check: grep final2 shows only RUNBOOK:33 history text and the sentence that says there is none.
- M3 (JUDGELOG): skeleton `JUDGELOG="${JUDGELOG:-...}"`, TESTLOG and GATELOG added, per-run list extended in RUNBOOK and TC, Pass rule has a NEW JUDGELOG example. Check: skeleton bash -n OK.
- M4: see "not done" above (partial).
- M5: `<the take's keys>` etc. replaced by `$KEYS`/`$KEY` (grep: none left); TC check 3b variable list now has PGADMIN_PW, KEYF, KEYH; pins use `$EXPORT_PIN`; "shas.env and $ENVSH are one file" stated in RUNBOOK section 4 paragraph.
- Stranger B1: FIX-PLAN Step 0a has the making command (awk skeleton, chmod 600, REFUSED if exists) and the mandated line for the folder (Q31 item 34). B2: FIX-PLAN "Step R3". B3: FIX-PLAN steps 9b to 9e and mapping paragraph updated. B4: mandated line used for n8n start (Q31 35), sub-workflow id/values loop/import/export (36), SELECT-only SQL (37), take script and others (38); Step 6 now has a guarded command to append SUB_WORKFLOW_ID. B5: TC "Example lines" table; "type exactly" note in RUNBOOK step 3 and FP step 2. B6: FP Read-first start-time line (default 04:00Z, Q31 32).
- M1 words: TC "One word, one meaning" paragraph. M2: S9-2, S9-3, Step D explained in the shared Clock/Who text. M3: not restructured (one procedure per job) beyond the repeat scheme; not done in full. M5 jargon: shared block edits (warning lines, HubSpot key, S9-2/3, Step D). M6 times: Clock "moved" row now has a decision deadline; re-pin end 08:29Z, T19-T21 and 07:30Z rule check, Wednesday order are in the TC blanket paragraph.
- QUESTIONS.md Q31: items 32 to 38 appended after item 31 (append only).
- Clock block: `diff <(sed -n '/^## Clock/,/| the owner | posts |/p' TAKE-CHECKLIST.md) <(same on FIX-PLAN.md)` printed nothing.
- check_refs.py: PASS 5168 references. check_secrets.py: FAIL 2 hits (see above).
