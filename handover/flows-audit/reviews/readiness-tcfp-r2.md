# Readiness review of TAKE-CHECKLIST.md and FIX-PLAN.md, round 2 (egm-implementation-readiness, agent ae8642b12fa73d84c)
Saved by flows-audit, condensed. Reviewer words unverified; it ran no commands. Verdict: NOT ready for a stranger to run Tuesday's GO test command by command. Verified by me: take_check.sh:274 prints sha text between "status N." and "RESULT" (Blocker 1 confirmed); OWNER-STEPS line 63 is the delete-step paragraph, "not found" sentence is at line 74.
B1 FIX-PLAN step 4 (~L15) pass grep '^FINAL: take_check exit status 0\. RESULT: 0 FAIL' can never match; fix: two greps (status 0\. and RESULT: 0 FAIL).
B2 TAKE-CHECKLIST L48-54 GO rows 1,2,3,5 have no runnable command (LEAD FILLS); only row 4 runnable (needs pin edit), row 6 needs ledger_check.py not in tree; row 5 short re-smoke has no executable steps.
M1 row 6 ledger pass line may exit non-zero on Tuesday because F-002/F-031/F-007 stay Blocker (not in Tuesday's test); say which rows count or filter by take-path code.
M2 FIX-PLAN L70 "rehearsal ending 09:30Z (12:30 to 15:00 IST; start 07:30Z)": 07:30Z is 13:00 IST; TAKE-CHECKLIST L40 right.
M3 TAKE-CHECKLIST L27 cites OWNER-STEPS lines 83 and 120-123 for practice run (really 119, 84, 94, 125); row 10 (L71) "not found" at 63 should be 74; fix-tcfp2.md L6 says it read line 63.
M4 FIX-PLAN step 1 (L12): git diff --stat pass breaks if lead edits (take_check.sh, check_flows.py, F-031 text) are uncommitted; restrict the diff to a path or commit first.
M5 steps 0-3 and GO row 1 rely on a git clone ($REPO); no .git seen in this tree.
Minor: run_all.sh --diff-base cite line 57 not 56; check 7 "card line holds no digit" no command (grep -c counts lines); row 13/item 7 old F-007 phrase also in handover/demo REPORT.md:49; r23 as GO condition is the fixer's reading (ORDERS names r20-r22); fixer's check_secrets/check_refs pass says nothing about correctness.
Not checked: any command; pin WARN set vs patched copy; patch contents; remaining ORDERS lines; take scripts.
