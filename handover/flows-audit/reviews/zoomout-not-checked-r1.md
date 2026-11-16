# "What did we not check" (egm-zoom-out, agent a0f5061; saved condensed by flows-audit; reviewer words unverified)
Reviewer read REPORT, FIX-PLAN, QUESTIONS in full, FINDINGS lines 1-25 only (not the 45 rows). Nothing ran. Items 4 and 8 may already be answered by Q27 (items 4, 9), which it read as unanswered: check before acting.
1 Major: the script that sends the same body twice and logs both POSTs (post-twice script, run_real_check_n8n.py, n8n_api.py) is not on disk and nothing reviews it; ask a read-only review + byte-identical body check once the lead supplies it (Q27-1).
2 Major: earlier results "12 of 20" and "2 of 5" (one CRM row and one mail) unexplained; one filmed success proves little; suggest T19 run a fixed number of times with pass rate written down.
3 Major: F-002 patch is untested before the take; no fallback to unpatched real-v5 budgeted after Tue 14:00Z GO/NO-GO.
4 Major: GO rule vs F-002/F-031/F-007/F-011/F-041 being Blocker/Major (Q27-9 may answer).
5 Major: no frame-level check that the visible mail shows the lead ID and both POSTs are on screen (Q28-2 open).
6 Major: late second mail: wait time set at rehearsal; after-take recount reads the table, not the mailbox.
7 Medium: mailbox as instrument untested (no positive control: two distinct mails show as two; no dedup/filter check; clock).
8 Medium: guard risk 2-3 h and 17-step order vs one rehearsal slot.
9 Major: audit surface much larger than the claim (45 findings, 52 flows); 10 Medium: steps 3 and 9 heavy; re-rating F-011/F-041 off the take path is cheapest GO fix.
