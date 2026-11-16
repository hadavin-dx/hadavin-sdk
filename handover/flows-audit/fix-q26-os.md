# fix-q26-os (OWNER-STEPS rows and QUESTIONS, lead answer Q26, ORDERS.md lines 146-147)
Failures and doubts first:
- Nothing was run; static edits only. Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os-q26/
- T2 (no 10 s reply), T3 (3-minute cut, no timer) and the Step A text were already fixed by the Q25 pass (fix-q25-os.md); only the leftovers below were still stale.
- The citation note named T9 (FIX-PLAN cites T9 for the A-016f change; in OWNER-STEPS the right row is T12). T9 in OWNER-STEPS is correct, so it is unchanged; FIX-PLAN line 15 is another agent's file and still needs T12.
- Pipe count: every T row still has 5 pipe signs (4 cells), as before; none added.
Changes:
1. New section "Schedule: two paths" (GO / NO-GO test, UTC and IST, "the lead moves the times", "agent-time estimate, not a promise", named open risk n8n single-instance guard +2 to 3 h, r20/r21/r22 in plain words, scene 4 only if rehearsal shows takeover inside 3 minutes, Row 4 first after re-pin and practice run).
2. T6: n8n_api.py, run_real_check_n8n.py, n8n_drive.py = "lead provides at re-pin".
3. T4 pointer to CLAIMS-TABLE "Checks" section line 138 (was "line 30", which is now the tags item).
4. T12/T13: "Q25-2, line 143" -> "Q25 item 2, line 144" (143 is the heading); T12 "Q24-5" -> "Q24 item 5, ORDERS.md line 141".
5. Row 4 intro: "not the owner's Step A or Step D" -> "not the owner's Step D, the owner's only step".
6. Glossary and order step 1: r20/r21/r22 now point to the plain words (was "lead fills in").
7. Footer: tenth rewrite line. QUESTIONS.md: Q26 heading marked ANSWERED (13:00Z) with a one-line summary; nothing deleted.
Check: python3 -I handover/flows-audit/tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> RESULT: PASS (159 rows, exit 0).
