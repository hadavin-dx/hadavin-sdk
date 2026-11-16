# Citation check, plan files, round 21 (static; nothing run)

## Could not check
- Counts and times from the fix log that are the fixer's own arithmetic or measurement: "30 changed code spans" with 0 bash -n errors, "about 11 minutes" (15 against 4), "10 + 4 min" positive control, 22 findings. I re-checked only the sum of RUNBOOK section 6 (269 min = 4 h 29 min) and its Tuesday step clock: both correct.
- The git shas named in the three files (nothing to compare them with on disk).
- Whether `stat -c %a`, here-strings and the chains behave as claimed (not run).
- All 163 "Q31 item N" cites were checked by title and time; the quoted claim text beyond the title and time was read for the 60 or so cites in changed places, not every sentence.

## MISMATCH rows
| cite | claimed | found | verdict |
|---|---|---|---|
| TAKE-CHECKLIST.md:118 "item 49 ... is due Wed 05:45Z, the earlier governs" | Q31 item 49 due Wed 05:45Z | QUESTIONS.md item 49: ANSWER BY Tue 17 Nov 07:00Z, "the earlier wording gave ... Wed 05:45Z; it is dropped (fix-q31-7)" | MISMATCH (stale; item 49 and item 8 (e) are both Tue 07:00Z) |
| RUNBOOK.md:15 "FINDINGS.md lines 115 and 118 say 'stays Major until a fix and a test'" | F-011 and F-041 on lines 115 and 118 | F-011 is line 116, F-041 line 119 (115 is F-008, 118 not checked as a row head); wording "stays Major until a fix and a test exist" is on 116 and 119 | MISMATCH (off by one) |
| FIX-PLAN.md:106 (Step 12) "by Wed 08:33Z (14:03 IST), after pass A (QUESTIONS Q31 item 56)" | item 56 sets the 08:33Z time | Item 56 has only Tue 04:00Z (decision) and Wed 05:45Z (commands); 08:33Z comes from RUNBOOK I20 (rehearsal 1 sends from 07:48, 45 min) | MISMATCH (time not in the cited item) |
| FIX-PLAN.md:108 (Step 14) "by Wed 05:45Z (QUESTIONS Q31 item 55); on Tuesday check (e) is NOT CHECKED" | consistent with round 21 M9 | Item 55 does say Wed 05:45Z, but M9 (RUNBOOK I47/I57, FIX-PLAN:197) says the gate script is needed Tue 04:00Z and NOT CHECKED is allowed only for (e) before the scope answer. Step 14 itself was not updated; the conflict is stated only at FIX-PLAN:197 and is marked AUDIT PROPOSAL | NOTE: open conflict, not a wrong cite; QUESTIONS.md item 55 still not updated (fix log says so) |
| RUNBOOK.md:225 (step 21) vs section 6 Wednesday | rehearsal 1 starts 07:40 in section 6 (07:30 block, positive control 07:30-07:40) | step 21 and I20 say 07:44 start, first send 07:48, end 08:33 (with gate); section 6 text says the same for the gated case and 07:40 for the dated one | NOTE: consistent as written (two cases), listed because four numbers appear |

## MATCH rows (Q31 item numbers and what the plan files claim)
| cite | claimed | found | verdict |
|---|---|---|---|
| item 88 (RUNBOOK:204 x3, I51, FIX-PLAN grants row, TAKE-CHECKLIST:92) | DB_GRANTS.sh and the take owner login's right to create the table; due Tue 04:54Z | QUESTIONS.md line 608: same title, Tue 04:54Z | MATCH |
| item 78 (RUNBOOK:34,204,393; FIX-PLAN:96; TAKE-CHECKLIST:90) | DB_SETUP.sh only; due Tue 04:54Z | line 598, Tue 04:54Z, "item 88" not yet mentioned there but item 88 says "item 78 asks for DB_SETUP.sh only" | MATCH |
| item 52 / 60 / 37 (insert text, names and password route, SELECT-only login) | Tue 04:54Z | 501, 509: Tue 04:54Z; 492 (item 37): 04:54Z | MATCH |
| item 59 (shas.env names), 48 (PIN_NAME), 38 (a) 03:00Z, 38 (b) 03:30Z, 38 (c) 06:00Z, 38 (f) desk doors | Tue 03:30Z / 03:30Z / 03:00Z / 03:30Z / 06:00Z; (f) = two entry points | 508, 497, 493: same | MATCH |
| item 61 (values file 05:00Z), 77 (address, 05:00Z), 62 (05:54Z), 63 (06:24Z), 64 and 65 (06:39Z), 47 (06:59Z), 35 and 79 (05:14Z), 69/80/81 (04:16Z) | as cited | 510, 597, 511, 512 ff, 496, 490, 599, 584, 600, 601: same times | MATCH |
| item 25 (06:00Z), 53 (06:00Z), 50 (Wed 05:45Z), 54, 55, 57, 82 (Wed 05:45Z) | as cited | same | MATCH |
| item 70 (branch Tue 09:00Z, answer 07:00Z), 58 (09:00Z, supersedes Wed 05:45Z), 67 (10:30Z), 71 (Wed 05:45Z; run_real_check_n8n.py 09:00Z), 72 (Wed 08:25Z) | as cited | 585, 507, 582, 586, 587 | MATCH |
| item 10 (a) 03:00Z, (b)(c) 06:15Z; item 11 07:00Z; item 26 07:00Z (route item 10 (a) 03:00Z); item 8 and 49 Tue 07:00Z; item 32 Mon 22:00Z; item 27 Mon 21:00Z; item 30 Mon 20:30Z; item 33 Tue 04:00Z; item 51 Tue 03:00Z; item 56 Tue 04:00Z (decision) | as cited | same in QUESTIONS.md | MATCH |
| item 83 to 87 "new, not step 4a inputs"; item 86 (loop same file as post-twice script?), item 87 (positive-control script, I32) | as cited | 184 to 188 | MATCH |
| item 66 "group D" (TAKE-CHECKLIST:109) | one answer covers several items | item 66 text says group D names the governing time | MATCH |
| every other "Q31 item N" (163 cites in all) | item exists | all 163 resolve to an existing item (1 to 93); items 40 to 46 sit under "Q31 additions" at lines 667 to 673, after the History heading (live list, labelled so); item 94 does not exist and is not cited | MATCH |

## Times against ORDERS.md (Q26 line 147, Q27 line 156, Q28 166, Q29 167, Q30 170-171, 14:35Z note line 159-160)
- Re-pin done about 08:00Z, short re-smoke about 1 h, done about 09:30Z, GO/NO-GO Tue 14:00Z: MATCH (lines 147, 160).
- Wed practice 06:00Z, T19-T21 at its end about 07:00Z, Row 4 after, rehearsal about 07:30Z, F-031/F-007 re-read by Wed 06:00Z: MATCH (line 171).
- Rehearsal ends 09:30Z, take 10:00Z, GO if counts proof green and scene 4 inside 3 min, slip allowed to Mon 23 Nov 12:00Z, NO-GO latest re-pin Mon 23 Nov 07:00Z, credits stop Mon 23 Nov 18:29Z, post Wed 18 Nov 15:00Z / Wed 25 Nov 15:00Z: MATCH (lines 147, 156 items 6, 7).
- "if still open at Wed 07:30Z the take is NO-GO" (Q27 item 9): MATCH (line 156).
- ORDERS line numbers cited: 132 (Q21), 135 (Q22a), 138 (Q22b), 141 (Q23/24), 144 (Q25), 147 (Q26), 156 (Q27), 159-160 (14:35Z note), 166 (Q28), 167 (Q29), 170-171 (Q30), 176-177 (ORDER 037), ORDERS.md:20: all MATCH. The Q26 time stamp slip (line 170) is stated correctly in the files.
- Round 21 times: step 1 at 04:00Z gives step 2 04:03 ... step 15 08:14, end 08:29: MATCH to the 269-minute sum. Wednesday block 06:00, 07:00, 07:30, 07:40, 08:25, 08:40, 09:25, 09:50: arithmetic MATCH. Audit-planned times (03:30Z, 04:54Z, and so on) are not in ORDERS and are labelled audit proposals.

## RUNBOOK cites into handover/demo and flows-audit files
- N8N-START.md lines 15 to 27 hold the saved-runs "off" sentences: MATCH.
- PLAN-4-NLITE-FROM-LEAD.md:106 (up to 3 HubSpot contacts archived) and :196 (execution data until cleanup): MATCH.
- ORDERS.md:20 (one database wording) and QUEUE.md:8 (one server, two databases): MATCH.
- DESIGN-A-README.md line 23 (MF_CRM_URL, MF_STAGE_URL): MATCH. mf.py:45 (CREATE TABLE of mf_leads): MATCH.
- fill_flows/README.md line 245 (clean-up item 3, saved executions): MATCH.
- take_check.sh:60 and README:240 are named only in ORDERS.md line 144; take_check.sh line 60 is empty in the current file: CANNOT-CHECK what was meant (not cited by the plan files).
- FINDINGS.md lines 115 and 118: see MISMATCH above.

Files: /home/user/hadavin-sdk/handover/flows-audit/reviews/citation-plan-files-r1.md (this file). Nothing else edited.
