# Citation check r14: RUNBOOK, FIX-PLAN, TAKE-CHECKLIST (agent ae44a70). Saved by flows-audit, condensed. Checker words unverified. Cites mean flows-audit/ORDERS.md (186 lines), not handover/demo/ORDERS.md (671 lines). ~75 ORDERS cites (71 MATCH), 21 other file:line (14 MATCH), ~105 Q31 item cites (all items exist with right topic except below). Files were edited during the check (a185caa); recheck 1-6 after its push.
1 MISMATCH RUNBOOK:310 "ORDERS.md line 132 item 13": line 132 = Q21 items 1-3; item 13 is on line 144 (Q25).
2 MISMATCH RUNBOOK:310, FIX-PLAN:112/113/124, TAKE-CHECKLIST:404 fill_flows/README.md "line 240": clean-up item 3 is on line 245 (heading 242); line 240 holds the 1e999/Infinity text. ORDERS line 144 also says README:240 (lead's cite off by 5).
3 MISMATCH RUNBOOK:15 "FINDINGS.md lines 115 and 117": 115 = F-011, 117 = F-029, F-041 = 118 -> should be 115 and 118.
4 MISMATCH RUNBOOK:202, FIX-PLAN:125 demo/n8n-flows/DESIGN-A-README.md "line 23" saved-runs sentence: line 23 is MF_CRM_URL/MF_STAGE_URL; grep for saved runs finds nothing in that file.
5 MISMATCH FIX-PLAN:113 flow-check/README.md "line 31" shows --accept-no-save: line 31 is "Test hooks of run_all.sh"; flag is on line 55.
6 MISMATCH FIX-PLAN:101 input I24 "(QUESTIONS Q31 item 32)": item 32 = re-pin start time (Mon 22:00Z); no Q31 item asks the I24 question.
7 SOFT RUNBOOK:316, FIX-PLAN:113 "QUEUE.md:8 old one database wording": QUEUE.md:8 already says one server with two databases; what is stale there is "executions saved ON ... deleted at clean-up". ORDERS.md:20 holds the old wording.
8 SOFT RUNBOOK:349 item 25 06:00Z vs items 38(c)/53 08:00Z: two deadlines for "the same answer".
9 SOFT TAKE-CHECKLIST:108, FIX-PLAN:177 item 49 "Wed 05:45Z": item 49 says item 8(e) due Tue 07:00Z and the earlier governs.
Notes: RUNBOOK:3 "lines 105 to 171": 105-108 blank, answers start 109 (harmless). Not checked: quoted claim text against every target; OWNER-STEPS row cites.
