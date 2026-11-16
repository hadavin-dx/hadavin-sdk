# Fix log tcfp16: answer to reviews/stranger-plan-r21.md (22 findings: B1, B2, M1 to M20)

Files edited: RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md (all in handover/flows-audit). Nothing committed. Nothing run against n8n or Postgres. Reviewer words were treated as unverified: each finding was checked against the lines first.

## What was NOT verified (read first)
- Every changed command was checked with `bash -n` only (30 changed code spans and the Block R3 block: 0 syntax errors). Three small pieces were also run in a scratch folder on made-up data: the reviewer-line test (a good line continues, a PLACEHOLDER line stops), the repeat-sha rule (first write, same sha, new sha; the last line wins when sourced) and the password-file check and body-file chain (the body parsed as JSON). The full chains were never run.
- `stat -c %a` (the password-file mode check) is the GNU form; not tried on the lead's system.
- The clock minutes of steps 6 to 8 and step 16 were not measured. The "about 11 minutes" for a by-hand gate is step 24's own figures (15 against 4), not a measurement.
- QUESTIONS.md was not edited (not in my file set). Q31 item 55 still says Wed 05:45Z for the gate script, which now disagrees with the proposal below; the lead must update item 55 or reject the proposal.
- The wording of the activation-probe answer ("did you mean") is still UNVERIFIED, as in FIX-PLAN Step 8a.
- RUNBOOK line 76 (named in the earlier plan as a SHA_EVIDENCE description) was not edited; I did not find text there that the M1 change makes false. Not checked beyond a grep.

## Per finding: confirmed or wrong, and the fix
- B1 CONFIRMED (RUNBOOK 4b (e) and step 13 (d) grepped the whole pin file). Fix: both chains now take the reviewer line (`RL="$(grep '^# reviewed by:' PINFILE)"`) and test only it, with a here-string, no pipe. FIX-PLAN Step 4 and TAKE-CHECKLIST Pin procedure step 4 say the same.
- B2 CONFIRMED (nothing set BODY content, ADDR or KEYS). Fix: step 16 now holds one typed chain that sets KEY, ADDR, KEYS, picks the field from HOOK_URL, writes `$BODY` and prints `body-written`. Gate (a)/(b) of step 24 and (6a) of step 17 now start with `. "$ENVSH" && need_set ... KEYS ...`. Block R5e's header points to the chain.
- M1 CONFIRMED. The evidence sha lines were appended before pytest ran. Fix: Block R3 appends them in a new last line, only if `recorded rc=0` appears exactly once, `same-head` and the equal-head line are in `$EVLOG.git`; otherwise `NOT WRITTEN` and exit 1. Text updated in TAKE-CHECKLIST row 3 and block header, RUNBOOK step 1, FIX-PLAN Step R3.
- M2 CONFIRMED. Step 3 (RUNBOOK) and Step 2 (FIX-PLAN) now test the generator's own exit (`generator-exit-0`, else `STOP`). Step 4 and FIX-PLAN Step 3 add `four-flow-files-found` and `recovery-unchanged` before the commit.
- M3 CONFIRMED. Row 3 now allows exactly one code file, `build_mainframe.py`, and adds the command `git diff --name-only $FINAL_SHA $PATCH_BRANCH -- src tests scripts`, which must print nothing (RUNBOOK step 17 (3), TAKE-CHECKLIST row 3).
- M4 CONFIRMED. Step 17 (1) now says: type Block R1 whole.
- M5 CONFIRMED. RESULT_JSON check is a chain printing `result-path-new`; the take starts only after it. The Python check exits 1 unless the value is `no`.
- M6 CONFIRMED. All sha-append chains (RUNBOOK steps 4, 4b, 6, FIX-PLAN Steps 3 and 4c-equivalent, TAKE-CHECKLIST P1c) now: same line exists -> `sha-exists-X`; name exists with another sha -> append and print `sha-written-repeat`; else `sha-written`. Last line wins when sourced. Section 4 sha rule, step 4/4b/6 pass lines, N4 and P1c pass line updated. SHA_PIN2 on step 13 already worked this way.
- M7 CONFIRMED. DB_SETUP.sh reads both passwords from `$KEEP/pg-secrets.env`, which must exist before step 8 (0b); step 8 has a `pg-secrets-ready` check (counts only); (0b) chain stops if the file is missing. Times moved to Tue 04:54Z in RUNBOOK I53 and FIX-PLAN row; one-password rule (RUNBOOK section 4) and TAKE-CHECKLIST items 4 and Needed-by updated.
- M8 CONFIRMED. Step 8 (0a) and (0b) run before step 7 when n8n uses Postgres; DB_SETUP.sh also creates n8n's own database; a `datname` check follows (0b). Downgrade B needs none of this. Minutes unchanged (they already sit in the 25 of step 8).
- M9 AUDIT PROPOSAL, lead to confirm. RUNBOOK clock wins: gate script needed Tue 04:00Z. If absent at step 16: run (a) to (e) by hand, about 11 minutes more. NOT CHECKED is never a pass: only (e), only before the scope answer; any NOT CHECKED in (a) to (d) means the gate failed. Written in RUNBOOK section 2, step 16, I57, FIX-PLAN conflict note, TAKE-CHECKLIST gate row.
- M10 AUDIT PROPOSAL, lead to confirm. Run the positive control once on Tuesday after the step 16 mailbox count (about 10 + 4 min, inside the lead's slot; clock blocks untouched); Wednesday repeats it as dated. Without it the row-5 mail count is NOT PASSED on Tuesday.
- M11 AUDIT PROPOSAL, lead to confirm. The `!!!` lines of step 4b (b) decide: only the reviewer line -> route A ((c) then (e)); any other `!!!` (including a sha256 mismatch) -> route B (P1a to P1c) only; expect route B; in doubt route B. Same sentence in FIX-PLAN Step 4 (which said "always" route B) and TAKE-CHECKLIST (Pin procedure and row 4).
- M12 CONFIRMED in part: REFUSED is the intended stop, but the way out was unclear. Now stated: Block R4r, a NEW LOG, Block R4 again; a log made under pin 2 is never counted (RUNBOOK step 5 fail action, TAKE-CHECKLIST Pin procedure step 2).
- M13 AUDIT PROPOSAL, lead to confirm; PARTLY WRONG: TAKE-CHECKLIST (Needed-by and table) and FIX-PLAN already said Tue 03:30Z; RUNBOOK 164 is the skeleton loop, not a time. Only RUNBOOK I48 said 13:50 for the shas. Fixed there to Tue 03:30Z (Q31 item 38 (b)).
- M14 CONFIRMED. FIX-PLAN Step 0 now uses `test -z "$(git status --short ...)" && echo status-clean &&`; pass line updated.
- M15 CONFIRMED. Step 4a patch commands are `&&` chains printing `patch-F003-applied` / `patch-F004-applied`; the second runs only after the first printed.
- M16 CONFIRMED. Step 4a text: 4b and later steps do not start until both applied lines (or `step3a committed`), the commit and `status-clean`.
- M17 CONFIRMED. Step 6 copy loop breaks on first REFUSED or failed `cp`; `tuesday-set-copied` shows both files. SHA_SCRIPTS command also follows the repeat rule.
- M18 CONFIRMED (probe existed only in FIX-PLAN Step 8a). Ported into RUNBOOK step 11 with its pass and fail text.
- M19 CONFIRMED. The T19 form-leg command now starts with `. "$ENVSH" && need_set WAIT_S N8N_PORT TESTLOG &&`.
- M20 CONFIRMED. Placeholder table rows added for RECORDING and TESTREC, INSERTLOG, WAIT_S, RESULT_JSON, POSTFILE and LOG3.
- Grants file number: Q31 item 88 (checked in QUESTIONS.md: 78 = DB_SETUP, 88 = DB_GRANTS). Fixed in RUNBOOK step 8 (three places), row I51, FIX-PLAN grants row, TAKE-CHECKLIST item 34; the text that said "no Q31 item yet" is removed.

## Lead-only decisions (safest written default, each labelled AUDIT PROPOSAL, lead to confirm)
M9 (gate script time and fallback), M10 (Tuesday positive control), M11 (pin 1 route rule), M13 (SHA_R20 to SHA_R23 time Tue 03:30Z), plus the M8 ordering (step 8 (0a)/(0b) before step 7).

## Checks run
See the command output in the hand-back report (check_refs, check_names, check_secrets, ruff format, clock-block diff, bash -n counts).
