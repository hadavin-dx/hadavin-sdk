# fix-tcfp3 (fixer; edited only TAKE-CHECKLIST.md and FIX-PLAN.md; backup in /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-tcfp3/)

## Failures, gaps and things not checked (first)
- No command written in the two files was run, except two: `git -C /home/user/hadavin-sdk rev-parse --is-inside-work-tree` (printed `true` on the audit machine; says nothing about the lead's laptop) and `check_secrets` / `check_refs` (below). take_check.sh, check_patches.sh, fill_flows, psql, n8n: not run.
- Still LEAD FILLS and cannot be written by the audit: the four round head shas and `$BRANCH`; review report paths and their closing words; the take repository's test and mutation commands; the T7b / import-test runner; the allowed places for "one database"; the take scripts (`n8n_start.sh`, `n8n_kill.py`, `run_real_check_n8n.py`, `n8n_drive.py`, `scripts/n8n_api.py`, the post-twice script: all absent from this tree, named in the rows); mailbox tool; connection strings.
- Row 6 (ledger) is now a LEAD QUESTION: the audit never saw `ledger_check.py` (not in the tree), so it does not know whether it can filter by id. Proposed pass line is the audit's own. Also asked: does F-003 (text-fix Blocker, not named in Q30) count on Tuesday.
- Reviewer's claim "no .git seen": my one check printed `true` for this tree; the lead must still run Step 0 on the laptop.
- F-007 grep widened to REPORT.md; I searched only the three files, not all of handover/demo (stated in the file). REPORT.md:49 quotes the phrase as allowed wording for K3, so a person decides that hit.
- fix-tcfp2.md (old log) still says it read line 63 of OWNER-STEPS; not edited (not my file). TAKE-CHECKLIST and FIX-PLAN now cite that file by heading or quoted words only.
- Row 3 uses the core repo's pytest gate as an example; whether it is the take repo's gate is marked LEAD FILLS.

## Fixed (each confirmed against the files first)
- B1: confirmed at take_check.sh:274 (sha text sits between "status N." and "RESULT"). FIX-PLAN step 4, check 1 and GO row 4 now use two greps (`^FINAL: take_check exit status 0\.` and `RESULT: 0 FAIL`); expected FINAL line text corrected.
- B2: GO rows 1, 2, 3, 5 now have commands with named placeholders ($REPO, $BRANCH, $SHA_R20..R23, $FLOWS, $LOG, $EVLOG, $PGCONN ...) and where each value comes from, or an exact LEAD FILLS naming the ORDERS line (Q26 item 1, Q27 items 1 and 4, Q29 item 4). Row 5 is a step list (take_check, mf_leads.sql via psql, n8n_start.sh [missing], fill_flows commands from its README, import [missing], post-twice script [missing], count proof). Row 4 now starts with a pin check (`grep -n '^# reviewed by:'`), since the committed pin line makes take_check exit 4. Row 6: see above. Row 7: grep command and scope written; runner missing.
- M1: ledger pass line rewritten (which rows count, why exit 0 cannot be the Tuesday line), also in FIX-PLAN GO bullet.
- M2: FIX-PLAN "12:30 to 15:00 IST; start 07:30Z" became 07:30Z = 13:00 IST to 09:30Z = 15:00 IST. Other IST pairs re-checked: correct.
- M3: OWNER-STEPS cites by heading/quoted words (practice run; "not found" item).
- M4: step 1 pass line restricted to `git diff --stat -- handover/demo/n8n-mainframe`.
- M5: Step 0 with its own check in both files (`git -C "$REPO" rev-parse --is-inside-work-tree` prints `true`); Inputs item 1 points to it.
- Minors: run_all.sh line 57 (its `patched)` case, read); card-line digit test (`grep -F ... | grep -o '[0-9]' | wc -l` prints 0); F-007 grep widened; r23 as GO condition marked as the audit's reading of ORDERS (schedule table, FIX-PLAN).

## Evidence
`python3 -I tools/check_secrets.py` -> `PASS 0 hits in 1756 files`
`python3 tools/check_refs.py` -> `PASS 5147 references`
These say nothing about whether the commands are correct. Nothing committed. EGM: this is a fix of an EGM review (egm-implementation-readiness r2); the result review of the new text is the lead's step.
