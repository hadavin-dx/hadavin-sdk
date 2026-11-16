# fix-tcfp11 (round 15 fixer). Edited RUNBOOK.md, FIX-PLAN.md, TAKE-CHECKLIST.md only. Backups in the scratchpad bk/ folder. Not committed.
One time per input (all three files): re-smoke command, test list, wait value = Tue 06:00Z, Q31 item 25 (38 (c), 53 same answer); F-011 route = Tue 03:00Z, evidence standard = Tue 06:15Z (item 10); SELECT-only login = Tue 04:54Z (items 60, 52); post-twice script = Q31 item 58, Wed 05:45Z; if absent by Tue 09:00Z GO row 2 prints BLOCKED and the answer is NO-GO (no script invented); T21 failure rule = Tue 07:00Z (item 8 (e) governs item 49).
PIN_NAME and JUDGE_WHO: read only from shas.env, never typed. REPLACE_ME_I## -> REPLACE_ME_Q31_nn. FIX-PLAN table rows 40-46 -> 59-65. bootstrap-ok loop now 8 names (item 59); database names and PGADMIN/FLOWS_ROLE moved to the "set later" loop.
Step log paragraph added (RUNBOOK section 4), steps marked; step 12 and the step 16 refusal write $TESTLOG; FIX-PLAN wrapper list extended. Sha rule: grep -q guard on every append; repeat of step 13 appends SHA_PIN2; restores read ${SHA_PIN2:-$SHA_PIN} (tested in a scratch shell). 3a/4a either-or note in both. Citation fixes 1-6 and soft 7-9 applied.
## BLOCKED (exact input needed; QUESTIONS.md is not mine)
1. No Q31 item holds the list of review report files ($REPORT, GO row 2): skeleton tag REPLACE_ME_Q31_NONE.
2. No Q31 item asks input I24 (are four shas accepted).
3. Text wording of RUNBOOK 4a (1) is due before step 5 (04:51Z) but Q31 item 11 is due 07:00Z; no item holds the wording.
4. Post-twice script: item 58 due Wed 05:45Z, GO row 2 needs it and its reviews by Tue 14:00Z: the lead must give a Tue 09:00Z time for the script branch or accept NO-GO on row 2.
5. Q31 answer-by table and count line stop at item 31 (QUESTIONS.md, other agent).
## Raw output (cd handover/flows-audit)
bash -n on the shas.env skeleton: ok. python3 tools/check_refs.py: PASS 5166 references. ruff format --check .: 637 files already formatted. Clock diff (FIX-PLAN vs TAKE-CHECKLIST, sed range): empty, "CLOCK-SAME" (47 lines each; RUNBOOK has no "## Clock" heading, section 6 holds it). check_secrets.py: FAIL 1 hits: flow-check/raw/test-take-check.txt:178 token-like (length 47) (in flow-check/, not mine).
Not checked: full-text re-read of all three files after edits; ORDERS.md/DECISIONS/OWNER-STEPS-q16-rows full-path minor: see below.
