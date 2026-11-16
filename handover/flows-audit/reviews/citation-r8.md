# Citation check, round 8 (evidence only; no judging of whether a cited claim is wise)

Run: 2026-11-16, UTC about 13:03 to 13:08 (checks began about 12:55). Read-only on every audited file. One copy of the audited files was taken at 13:03 UTC and every check ran on that copy, because QUESTIONS.md, FINDINGS.md and OWNER-STEPS-q16-rows.md were being edited by other sessions while this ran (QUESTIONS.md grew from 473 to 484 lines during the run; the line numbers below are from the copy). If those files change again, rerun.
Audited: handover/flows-audit/QUESTIONS.md (484 lines in the copy) and RUNBOOK.md (278 lines). Cited files read: ORDERS.md (177 lines), FINDINGS.md (153), CLAIMS-TABLE.md, RUNSHEET-WORDING.md, OWNER-STEPS-q16-rows.md, EXCEPTIONS.md, QUEUE.md, SCENE-FLOW-MAP.md, inputs/, fill_flows/README.md, flow-check/take_check.sh, demo/PLAN-4-NLITE-FROM-LEAD.md, demo/n8n-flows-real-v5/mf-recovery.json.

## Counts

| class | what is checked | rows | MISMATCH | NOT CHECKABLE | NOTE | MATCH |
|---|---|---|---|---|---|---|
| A ORDERS line | "ORDERS.md line N", "lines a-b", "ORDERS.md ORDER nnn (lines a-b)", "ANSWERS 10:02Z block", "ORDERS:N", with "item m" where given | 181 | 1 | 0 | 0 | 180 |
| B ORDER nnn | bare "ORDER 0nn" (and "ORDER nnn item m") names: header exists, item exists | 67 | 0 | 0 | 0 | 67 |
| C Q item | "Q<n> item <m>": item exists in the Q section or the lead answer | 259 | 1 | 0 | 0 | 258 |
| D file:line | "file:line", "file line N", F-id to FINDINGS line pairs, row pointers in CLAIMS-TABLE and RUNSHEET-WORDING | 113 | 39 | 27 | 0 | 47 |
| E time | weekday of each "Day D Nov" (2026 calendar), UTC to IST pairs (+5:30), minute sums and clock plus duration | 541 | 0 | 0 | 1 | 540 |
| total | | 1161 | 41 | 27 | 1 | 1092 |

## How each class was checked, and what MATCH does and does not mean

- A: python3 -I read of ORDERS.md; for each cite the cited line (and for ranges both ends) was printed. A header cite (ORDER nnn, ANSWERS block) is MATCH only if that line starts with that header. A plain line cite is MATCH if the cited answer block names the same Q number as the citing sentence, or shares a distinctive term (finding id, file name, clock time, quoted phrase) with it; otherwise it was read by hand. "item m" cites were also checked for the item number on that line. MATCH means "the line exists and fits the sentence on these tests"; it is not a proof that the sentence restates the line exactly.
- B: every "ORDER nnn" header exists in ORDERS.md; "item m" exists inside that order block.
- C: item m exists as a numbered item of the Q section in QUESTIONS.md (or in the lead answer for Q19, Q20 item 4). Topic fit was compared by shared words and the weak ones (about 60) were read by hand; one partial mismatch found.
- D: FINDINGS cites were checked by finding id: line N must start with the row of the cited F-id. Other files: the cited line was printed and a key word of the claim looked for on it.
- E: python3 -I arithmetic. UTC to IST pairs: UTC + 5 h 30 min. Dates: datetime.date(2026,11,d).strftime("%a"). Sums and "clock plus duration" statements recomputed. Two rows that the pattern first marked wrong (RUNBOOK.md:60 and :217) were re-done by hand and are right (the pattern had paired a time with the wrong neighbour).

## MISMATCH rows (41)

### A ORDERS line: 1

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| ORDERS.md line 132 item 13 | RUNBOOK.md:204 | L132: 1 Env: the take's route is fill_flows literals (frozen tool, no n8n setting change), as you recommend. F-037/F-029 | MISMATCH | no item 13 on line 132 (the line holds items 1..3) |

### C Q item: 1

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| Q26 item 5 | QUESTIONS.md:132 | 5. [ANSWERED] Should Row 4 (one made-up lead through the real HubSpot trial) be the first thing done, since it | MISMATCH | the cited item 5 says only that Row 4 comes first; the 30-minute figure is in Q27 item 6 (cited next to it) |

### D file:line: 39

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| FINDINGS.md:108 (F-002) | QUESTIONS.md:108 | /---/---/---/---/---/---/---/- | MISMATCH | F-002 is on FINDINGS.md line 109 |
| FINDINGS.md:110 (F-007) | QUESTIONS.md:113 | / F-003 / Blocker / claim-not- | MISMATCH | F-007 is on FINDINGS.md line 111 |
| FINDINGS.md:128 (F-013) | QUESTIONS.md:116 | / F-009 / Nit (after the video | MISMATCH | F-013 is on FINDINGS.md line 130 |
| FINDINGS.md:111 (F-031) | QUESTIONS.md:117 | / F-007 / Blocker / inconsiste | MISMATCH | F-031 is on FINDINGS.md line 112 |
| FINDINGS.md:117 (F-041) | QUESTIONS.md:118 | / F-029 / Major / ops / take / | MISMATCH | F-041 is on FINDINGS.md line 118 |
| FINDINGS.md:150 (F-044) | QUESTIONS.md:119 | / F-039 / Nit (after the video | MISMATCH | F-044 is on FINDINGS.md line 151 |
| FINDINGS.md lines 122-125, 129-151 | QUESTIONS.md:120 | lines 122-125 hold F-043, F-001, F-005, F-006; the sentence names F-023, F-012, F-014 ... F-045 | MISMATCH | F-023 is line 126, F-012 line 127 |
| FINDINGS.md:89 | QUESTIONS.md:140 | (blank line) | MISMATCH | the BEFORE/AFTER definition is on line 88 |
| FINDINGS.md:123 (F-006) | QUESTIONS.md:203 | / F-001 / Nit (dropped) / stor | MISMATCH | F-006 is on FINDINGS.md line 125 |
| FINDINGS.md:111 (F-031) | QUESTIONS.md:203 | / F-007 / Blocker / inconsiste | MISMATCH | F-031 is on FINDINGS.md line 112 |
| FINDINGS.md:124 (F-023) | QUESTIONS.md:203 | / F-005 / Nit (for a later vid | MISMATCH | F-023 is on FINDINGS.md line 126 |
| FINDINGS.md:125 (F-012) | QUESTIONS.md:209 | / F-006 / Nit (for a later vid | MISMATCH | F-012 is on FINDINGS.md line 127 |
| FINDINGS.md:129 (F-014) | QUESTIONS.md:209 | / F-010 / Nit (after the video | MISMATCH | F-014 is on FINDINGS.md line 131 |
| FINDINGS.md:134 (F-019) | QUESTIONS.md:209 | / F-017 / Nit (after the video | MISMATCH | F-019 is on FINDINGS.md line 135 |
| FINDINGS.md:137 (F-022) | QUESTIONS.md:209 | / F-021 / Nit (after the video | MISMATCH | F-022 is on FINDINGS.md line 138 |
| FINDINGS.md:139 (F-025) | QUESTIONS.md:209 | / F-024 / Nit / ops / not in t | MISMATCH | F-025 is on FINDINGS.md line 140 |
| FINDINGS.md:146 (F-035) | QUESTIONS.md:209 | / F-034 / Nit / ops / not in t | MISMATCH | F-035 is on FINDINGS.md line 147 |
| FINDINGS.md:147 (F-036) | QUESTIONS.md:209 | / F-035 / Nit (after the video | MISMATCH | F-036 is on FINDINGS.md line 148 |
| FINDINGS.md:149 (F-039) | QUESTIONS.md:209 | / F-038 / Nit / security / tak | MISMATCH | F-039 is on FINDINGS.md line 150 |
| FINDINGS.md:150 (F-044) | QUESTIONS.md:209 | / F-039 / Nit (after the video | MISMATCH | F-044 is on FINDINGS.md line 151 |
| FINDINGS.md:151 (F-045) | QUESTIONS.md:209 | / F-044 / Nit (after the video | MISMATCH | F-045 is on FINDINGS.md line 152 |
| FINDINGS.md:122 (F-005) | QUESTIONS.md:235 | / F-043 / Nit (after the video | MISMATCH | F-005 is on FINDINGS.md line 124 |
| FINDINGS.md:117 (F-041) | QUESTIONS.md:279 | / F-029 / Major / ops / take / | MISMATCH | F-041 is on FINDINGS.md line 118 |
| FINDINGS.md:150 (F-044) | QUESTIONS.md:279 | / F-039 / Nit (after the video | MISMATCH | F-044 is on FINDINGS.md line 151 |
| FINDINGS.md:108 (F-002) | QUESTIONS.md:297 | /---/---/---/---/---/---/---/- | MISMATCH | F-002 is on FINDINGS.md line 109 |
| FINDINGS.md:110 (F-007) | QUESTIONS.md:297 | / F-003 / Blocker / claim-not- | MISMATCH | F-007 is on FINDINGS.md line 111 |
| FINDINGS.md:111 (F-031) | QUESTIONS.md:297 | / F-007 / Blocker / inconsiste | MISMATCH | F-031 is on FINDINGS.md line 112 |
| FINDINGS.md:128 (F-013) | QUESTIONS.md:297 | / F-009 / Nit (after the video | MISMATCH | F-013 is on FINDINGS.md line 130 |
| OWNER-STEPS-q16-rows.md:16 (Step D defined) | QUESTIONS.md:129 | - The chat = the one conversation where the lead's messages reach you and where you answer. The lead | MISMATCH | line 16 defines "the chat"; "Step D" is defined near line 200 |
| OWNER-STEPS-q16-rows.md line 20 (retake) | QUESTIONS.md:103 | - "re-check done": says the lead has checked the facts written in this sheet; gives the date and tim | MISMATCH | retake is defined at line 47 |
| OWNER-STEPS-q16-rows.md line 20 (retake) | QUESTIONS.md:404 | - "re-check done": says the lead has checked the facts written in this sheet; gives the date and tim | MISMATCH | retake is defined at line 47 |
| OWNER-STEPS-q16-rows.md line 227 (retake) | QUESTIONS.md:103 | - Tue 17 Nov: re-pin (the re-check is inside it) by about 08:00 UTC (13:30 IST). Then the short re-s | MISMATCH | retake is defined at line 47 |
| OWNER-STEPS-q16-rows.md line 227 (retake) | QUESTIONS.md:404 | - Tue 17 Nov: re-pin (the re-check is inside it) by about 08:00 UTC (13:30 IST). Then the short re-s | MISMATCH | retake is defined at line 47 |
| OWNER-STEPS-q16-rows.md line 33 ("money stop") | QUESTIONS.md:159 | - The take decision = the lead's own decision on Wed 18 Nov between 09:30 and 10:00 UTC (15:00 and 1 | MISMATCH | "money stop" appears only at line 233 |
| OWNER-STEPS-q16-rows.md line 53 ("money stop") | QUESTIONS.md:159 | (blank line) | MISMATCH | "money stop" appears only at line 233 |
| OWNER-STEPS-q16-rows.md line 28 (item 7, retake yes) | QUESTIONS.md:406 | - clean-up message: the lead's message that starts with the words "clean-up starts" and also holds t | MISMATCH | line 28 defines "clean-up message"; the retake decision row is item 7 of the table near line 90 |
| EXCEPTIONS.md:16 (no deletion promise) | QUESTIONS.md:283 | (blank line) | MISMATCH | line 16 is blank; the words "no deletion promise" are on line 14 |
| take_check.sh:60 (still says saved runs are deleted) | QUESTIONS.md:334 | # round 10c (Q2): sha256 of the four flow files AND of every other *.json in the folder (this script | MISMATCH | line 60 is a comment about a sha256 of flow files; no "deleted at clean-up" text on it |
| PLAN-4-NLITE-FROM-LEAD.md:106 (stale one-store text) | QUESTIONS.md:75 | 4. The notice (3 made-up people, up to 3 HubSpot contacts archived at the end, up to 3 mails, up to  | MISMATCH | line 106 holds no database/store sentence (it holds the notice text) |

## NOT CHECKABLE and NOTE rows (28)

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| inputs/plan-wp6-resmoke-v5.md line 193 (ruff format fails) | QUESTIONS.md:85 | (blank line) | NOT CHECKABLE | blank line in a plan file; a ruff format failure cannot be read from a line number without running ruff |
| inputs/plan-wp6-resmoke-v5.md line 193 (ruff format fails) | QUESTIONS.md:415 | (blank line) | NOT CHECKABLE | blank line in a plan file; a ruff format failure cannot be read from a line number without running ruff |
| scripts/run_real_check.py:993 and :1101-1107 | QUESTIONS.md | (file not present) | NOT CHECKABLE | file is in the public desk repo, not in this checkout |
| crm_hubspot.py:492-499 | QUESTIONS.md | (file not present) | NOT CHECKABLE | file is in the public desk repo, not in this checkout |
| mf.py:151-164 | CLAIMS-TABLE.md (cited inside) | (file not present) | NOT CHECKABLE | mf.py not in checkout |
| old QUESTIONS.md line 25 | QUESTIONS.md:457 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 28 | QUESTIONS.md:458 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 31 | QUESTIONS.md:459 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 37 | QUESTIONS.md:460 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 40 | QUESTIONS.md:461 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 43 | QUESTIONS.md:462 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 46 | QUESTIONS.md:463 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 49 | QUESTIONS.md:464 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 58 | QUESTIONS.md:465 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 61 | QUESTIONS.md:466 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 68 | QUESTIONS.md:467 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 75 | QUESTIONS.md:468 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 81 | QUESTIONS.md:469 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 88 | QUESTIONS.md:470 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 91 | QUESTIONS.md:471 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 99 | QUESTIONS.md:472 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 108 | QUESTIONS.md:473 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 133 | QUESTIONS.md:474 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 146 | QUESTIONS.md:475 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 153 | QUESTIONS.md:476 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 159 | QUESTIONS.md:477 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| old QUESTIONS.md line 164 | QUESTIONS.md:478 | (the old file version is not in the checkout) | NOT CHECKABLE | cites a line of a file version that no longer exists |
| Row 4 ends 07:35Z (QUESTIONS) vs Row 4 07:00 to 07:30 (RUNBOOK:152) | QUESTIONS.md:~127 vs RUNBOOK.md:152 | each is arithmetically right inside its own file; the two files give different Row 4 end times (07:35Z vs 07:30Z) | NOTE | recorded, not judged |

## MATCH rows

### A ORDERS line: 180

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| ORDERS.md lines 109-171 | QUESTIONS.md:5 | L109: ## ANSWER (lead, 10:23Z): Q13 ... L171: Q30: 1 Yes: the practice run starts about 06:00Z W | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md lines 170-171 | QUESTIONS.md:5 | L170: CORRECTION of my slip: several time stamps in my earlier ORDERS blocks (13:00Z to 15:00Z, and '13:00Z = 18:30 IST' | MATCH | Q30 named in the cited answer block |
| ORDERS.md ORDER 003 (lines 16-18 | QUESTIONS.md:9 | L16: ## ORDER 003 (lead, 2026-11-16) ANSWER to Q1: ACCEPTED as written ... L18:  | MATCH | line 16 is the header of ORDER 003; end line 18 is blank (trailing separator) |
| ORDERS.md ORDER 004 (lines 19-21 | QUESTIONS.md:10 | L19: ## ORDER 004 (lead, 2026-11-16) ANSWER to Q2 (F-011): READING A ... L21:  | MATCH | line 19 is the header of ORDER 004; end line 21 is blank (trailing separator) |
| ORDERS.md ORDER 012 (lines 54-56 | QUESTIONS.md:11 | L54: ## ORDER 012 (lead, 2026-11-16) ANSWER to Q3 (F-041) ... L56:  | MATCH | line 54 is the header of ORDER 012; end line 56 is blank (trailing separator) |
| ORDERS.md ORDER 013 (lines 57-58 | QUESTIONS.md:12 | L57: ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) ...  | MATCH | line 57 is the header of ORDER 013 |
| ORDERS.md ORDER 013 (lines 57-58 | QUESTIONS.md:13 | L57: ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) ...  | MATCH | line 57 is the header of ORDER 013 |
| ORDERS.md ORDER 013 (lines 57-58 | QUESTIONS.md:14 | L57: ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) ...  | MATCH | line 57 is the header of ORDER 013 |
| ORDERS.md ORDER 013 (lines 57-58 | QUESTIONS.md:15 | L57: ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) ...  | MATCH | line 57 is the header of ORDER 013 |
| ORDERS.md ORDER 013 (lines 57-58 | QUESTIONS.md:16 | L57: ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) ...  | MATCH | line 57 is the header of ORDER 013 |
| ORDERS.md ORDER 013 (lines 57-58 | QUESTIONS.md:17 | L57: ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) ...  | MATCH | line 57 is the header of ORDER 013 |
| ORDERS.md ANSWERS 10:02Z block (lines 94-96 | QUESTIONS.md:18 | L94: ## ANSWERS (lead, 10:02Z): all decisions are in egm/duplicate-proof-lead-desk/DECISIONS-2026-11-16.md (copy in your | MATCH | header; end line 96 is blank (trailing separator) |
| ORDERS.md ANSWERS 10:02Z block (lines 94-96 | QUESTIONS.md:19 | L94: ## ANSWERS (lead, 10:02Z): all decisions are in egm/duplicate-proof-lead-desk/DECISIONS-2026-11-16.md (copy in your | MATCH | header; end line 96 is blank (trailing separator) |
| ORDERS.md line 98 | QUESTIONS.md:20 | L98: Not blocked: D-01..D-05, D-10, S-03, L-01 belong to system-map's drift report (the system-map session writes handov | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 110 | QUESTIONS.md:21 | L110: The take uses run_real_check_n8n.py (take mode) + n8n_drive.py, NOT the desk script's archive_all path (run_real_c | MATCH | Q13 named in the cited answer block |
| ORDERS.md line 116 | QUESTIONS.md:22 | L116: Q14: YES re-rate F-005, F-006, F-023, F6B-01, F6B-13 to Nit 'for a later video' (scenes 5-11 are out) and recount  | MATCH | Q14 named in the cited answer block |
| ORDERS.md line 113 | QUESTIONS.md:24 | L113: Accept your recommendation: the take uses the v4 table file (demo/n8n-flows-v4/mf_leads.sql, the one with alert_se | MATCH | Q16 named in the cited answer block |
| ORDERS.md line 117 | QUESTIONS.md:25 | L117: Q17: 1 YES freeze fill_flows (F3) after the round now running (r7); further rounds only for an OPEN Blocker; the r | MATCH | Q17 named in the cited answer block |
| ORDERS.md line 121 | QUESTIONS.md:26 | L121: Keep exit 4 for the missing table file, zero queries read, or a missing alert column (alerts would fail on every r | MATCH | Q18 named in the cited answer block |
| ORDERS.md line 124 | QUESTIONS.md:27 | L124: Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentence on | MATCH | Q19 named in the cited answer block |
| ORDERS.md line 125 | QUESTIONS.md:28 | L125: Q20 (I could not read these facts from here; write each as 'lead verifies at re-pin', never as fact): 1 the take f | MATCH | Q20 named in the cited answer block |
| ORDERS.md line 132 | QUESTIONS.md:29 | L132: 1 Env: the take's route is fill_flows literals (frozen tool, no n8n setting change), as you recommend. F-037/F-029 | MATCH | Q21 named in the cited answer block |
| ORDERS.md line 135 | QUESTIONS.md:30 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | Q22a named in the cited answer block |
| ORDERS.md line 138 | QUESTIONS.md:31 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | Q22b named in the cited answer block |
| ORDERS.md line 141 | QUESTIONS.md:32 | L141: Q23: keep accepted, no change to the frozen tool. Q24: 1 Date X: the lead writes the re-pin time after the merge,  | MATCH | Q23 named in the cited answer block |
| ORDERS.md line 141 | QUESTIONS.md:33 | L141: Q23: keep accepted, no change to the frozen tool. Q24: 1 Date X: the lead writes the re-pin time after the merge,  | MATCH | Q24 named in the cited answer block |
| ORDERS.md line 144 | QUESTIONS.md:34 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | Q25 named in the cited answer block |
| ORDERS.md line 147 | QUESTIONS.md:35 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | Q26 named in the cited answer block |
| ORDERS.md line 156 | QUESTIONS.md:36 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block |
| ORDERS.md line 166 | QUESTIONS.md:37 | L166: Q28: 1 Yes: the caption says 'one e-mail message in the intake mailbox'. 2 Put the post-wait mailbox count and the | MATCH | Q28 named in the cited answer block |
| ORDERS.md line 167 | QUESTIONS.md:38 | L167: Q29: 1 Yes: positive control before the rehearsal (two made-up mails with different IDs show two in the intake mai | MATCH | Q29 named in the cited answer block |
| ORDERS.md lines 170-171 | QUESTIONS.md:39 | L170: CORRECTION of my slip: several time stamps in my earlier ORDERS blocks (13:00Z to 15:00Z, and '13:00Z = 18:30 IST' | MATCH | Q30 named in the cited answer block |
| ORDERS.md line 177 | QUESTIONS.md:42 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 135 | QUESTIONS.md:44 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | Q22b named in the cited answer block |
| ORDERS.md lines 109-171 | QUESTIONS.md:50 | L109: ## ANSWER (lead, 10:23Z): Q13 ... L171: Q30: 1 Yes: the practice run starts about 06:00Z W | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 160 | QUESTIONS.md:57 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | shared terms: 17 Nov, 09:30Z |
| ORDERS.md line 117 | QUESTIONS.md:61 | L117: Q17: 1 YES freeze fill_flows (F3) after the round now running (r7); further rounds only for an OPEN Blocker; the r | MATCH | Q17 named in the cited answer block |
| ORDERS.md line 144 | QUESTIONS.md:61 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | Q25 named in the cited answer block |
| ORDERS.md line 166 | QUESTIONS.md:61 | L166: Q28: 1 Yes: the caption says 'one e-mail message in the intake mailbox'. 2 Put the post-wait mailbox count and the | MATCH | Q28 named in the cited answer block |
| ORDERS.md line 138 | QUESTIONS.md:66 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | shared terms: "later" |
| ORDERS.md line 177 | QUESTIONS.md:71 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 20 | QUESTIONS.md:75 | L20: The one database means n8n's OWN state (workflows, credentials, execution history) must also be in the take's singl | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 156 item 2 | QUESTIONS.md:78 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: 07:00Z; item 2 present |
| ORDERS.md line 171 | QUESTIONS.md:84 | L171: Q30: 1 Yes: the practice run starts about 06:00Z Wed 18 Nov; the F-002 test (T19-T21) is at the end of the practic | MATCH | Q30 named in the cited answer block |
| ORDERS.md line 156 item 7 | QUESTIONS.md:88 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block; item 7 present |
| ORDERS.md line 135 item 3 | QUESTIONS.md:89 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | Q22a named in the cited answer block; item 3 present |
| ORDERS.md line 156 item 9 | QUESTIONS.md:91 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: 14:00Z; item 9 present |
| ORDERS.md lines 109-171 | QUESTIONS.md:103 | L109: ## ANSWER (lead, 10:23Z): Q13 ... L171: Q30: 1 Yes: the practice run starts about 06:00Z W | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 156 item 9 | QUESTIONS.md:108 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: F-002, T19, "F-002"; item 9 present |
| ORDERS.md lines 109-171 | QUESTIONS.md:122 | L109: ## ANSWER (lead, 10:23Z): Q13 ... L171: Q30: 1 Yes: the practice run starts about 06:00Z W | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 177 | QUESTIONS.md:131 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 160 | QUESTIONS.md:131 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 147 | QUESTIONS.md:131 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 177 | QUESTIONS.md:132 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 177 | QUESTIONS.md:133 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md lines 109-171 | QUESTIONS.md:134 | L109: ## ANSWER (lead, 10:23Z): Q13 ... L171: Q30: 1 Yes: the practice run starts about 06:00Z W | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md (line 144 | QUESTIONS.md:137 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | Q25 named in the cited answer block |
| ORDERS.md line 156 item 7 | QUESTIONS.md:139 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: 12:00Z, "credits stop", 18:29Z; item 7 present |
| ORDERS.md line 177 | QUESTIONS.md:155 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 160 | QUESTIONS.md:161 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | shared terms: 17 Nov |
| ORDERS.md line 177 | QUESTIONS.md:161 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | shared terms: 17 Nov |
| ORDERS.md line 177 | QUESTIONS.md:161 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md lines 125 and 138 | QUESTIONS.md:161 | L125: Q20 (I could not read these facts from here; write each as 'lead verifies at re-pin', never as fact): 1 the take f | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 147 | QUESTIONS.md:166 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | shared terms: "fresh three-lane review" |
| ORDERS.md line 147 | QUESTIONS.md:167 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 156 item 9 | QUESTIONS.md:169 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: F-011, F-041; item 9 present |
| ORDERS.md line 177 | QUESTIONS.md:184 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | shared terms: 12:33Z |
| ORDERS.md line 177 item 3 | QUESTIONS.md:185 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | shared terms: egm/duplicate-proof-lead-desk/wp6/LEAD-RUNBOOK-TAKE-DAY-v4.md; item 3 present |
| ORDERS.md line 144 item 10 | QUESTIONS.md:188 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | shared terms: ORDERS.md; item 10 present |
| ORDERS.md ORDER 003, lines 16-18 | QUESTIONS.md:190 | L16: ## ORDER 003 (lead, 2026-11-16) ANSWER to Q1: ACCEPTED as written ... L18:  | MATCH | line 16 is the header of ORDER 003; end line 18 is blank (trailing separator) |
| ORDERS.md ORDER 004, lines 19-21 | QUESTIONS.md:193 | L19: ## ORDER 004 (lead, 2026-11-16) ANSWER to Q2 (F-011): READING A ... L21:  | MATCH | line 19 is the header of ORDER 004; end line 21 is blank (trailing separator) |
| ORDERS.md ORDER 012, lines 54-56 | QUESTIONS.md:197 | L54: ## ORDER 012 (lead, 2026-11-16) ANSWER to Q3 (F-041) ... L56:  | MATCH | line 54 is the header of ORDER 012; end line 56 is blank (trailing separator) |
| ORDERS.md ORDER 013, lines 57-58 | QUESTIONS.md:202 | L57: ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) ...  | MATCH | line 57 is the header of ORDER 013 |
| ORDERS.md line 156 | QUESTIONS.md:212 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: F-041, F-011 |
| ORDERS.md ANSWERS 10:02Z block, lines 94-96 | QUESTIONS.md:219 | L94: ## ANSWERS (lead, 10:02Z): all decisions are in egm/duplicate-proof-lead-desk/DECISIONS-2026-11-16.md (copy in your | MATCH | header; end line 96 is blank (trailing separator) |
| ORDERS.md ANSWERS 10:02Z block, lines 94-96 | QUESTIONS.md:223 | L94: ## ANSWERS (lead, 10:02Z): all decisions are in egm/duplicate-proof-lead-desk/DECISIONS-2026-11-16.md (copy in your | MATCH | header; end line 96 is blank (trailing separator) |
| ORDERS.md line 98 | QUESTIONS.md:226 | L98: Not blocked: D-01..D-05, D-10, S-03, L-01 belong to system-map's drift report (the system-map session writes handov | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 98 | QUESTIONS.md:227 | L98: Not blocked: D-01..D-05, D-10, S-03, L-01 belong to system-map's drift report (the system-map session writes handov | MATCH | shared terms: 10:20Z, handover/system-map/decisions/D04-D05.md |
| ORDERS.md line 110 | QUESTIONS.md:229 | L110: The take uses run_real_check_n8n.py (take mode) + n8n_drive.py, NOT the desk script's archive_all path (run_real_c | MATCH | Q13 named in the cited answer block |
| ORDERS.md line 116 | QUESTIONS.md:234 | L116: Q14: YES re-rate F-005, F-006, F-023, F6B-01, F6B-13 to Nit 'for a later video' (scenes 5-11 are out) and recount  | MATCH | Q14 named in the cited answer block |
| ORDERS.md line 113 | QUESTIONS.md:242 | L113: Accept your recommendation: the take uses the v4 table file (demo/n8n-flows-v4/mf_leads.sql, the one with alert_se | MATCH | Q16 named in the cited answer block |
| ORDERS.md line 117 | QUESTIONS.md:246 | L117: Q17: 1 YES freeze fill_flows (F3) after the round now running (r7); further rounds only for an OPEN Blocker; the r | MATCH | Q17 named in the cited answer block |
| ORDERS.md line 121 | QUESTIONS.md:256 | L121: Keep exit 4 for the missing table file, zero queries read, or a missing alert column (alerts would fail on every r | MATCH | Q18 named in the cited answer block |
| ORDERS.md line 124 | QUESTIONS.md:260 | L124: Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentence on | MATCH | Q19 named in the cited answer block |
| ORDERS.md line 125 | QUESTIONS.md:269 | L125: Q20 (I could not read these facts from here; write each as 'lead verifies at re-pin', never as fact): 1 the take f | MATCH | Q20 named in the cited answer block |
| ORDERS.md line 138 | QUESTIONS.md:275 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 132 | QUESTIONS.md:278 | L132: 1 Env: the take's route is fill_flows literals (frozen tool, no n8n setting change), as you recommend. F-037/F-029 | MATCH | Q21 named in the cited answer block |
| ORDERS.md line 156 | QUESTIONS.md:280 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block |
| ORDERS.md line 135 | QUESTIONS.md:286 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | Q22a named in the cited answer block |
| ORDERS.md line 135 | QUESTIONS.md:288 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 177 | QUESTIONS.md:292 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 138 | QUESTIONS.md:296 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | Q22b named in the cited answer block |
| ORDERS.md line 138 item 1 | QUESTIONS.md:299 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | shared terms: F-031, F-007, F-002; item 1 present |
| ORDERS.md line 138 item 2 | QUESTIONS.md:300 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | shared terms: F-013; item 2 present |
| ORDERS.md line 138 item 3 | QUESTIONS.md:301 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | read by hand: cited line fits the sentence; item 3 present |
| ORDERS.md line 138 item 4 | QUESTIONS.md:302 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | read by hand: cited line fits the sentence; item 4 present |
| ORDERS.md line 138 item 5 | QUESTIONS.md:303 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | read by hand: cited line fits the sentence; item 5 present |
| ORDERS.md line 141 | QUESTIONS.md:305 | L141: Q23: keep accepted, no change to the frozen tool. Q24: 1 Date X: the lead writes the re-pin time after the merge,  | MATCH | Q23 named in the cited answer block |
| ORDERS.md line 141 | QUESTIONS.md:309 | L141: Q23: keep accepted, no change to the frozen tool. Q24: 1 Date X: the lead writes the re-pin time after the merge,  | MATCH | Q24 named in the cited answer block |
| ORDERS.md line 144 | QUESTIONS.md:319 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | Q25 named in the cited answer block |
| ORDERS.md line 156 | QUESTIONS.md:329 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block |
| ORDERS.md line 177 | QUESTIONS.md:331 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md:20 | QUESTIONS.md:335 | L20: The one database means n8n's OWN state (workflows, credentials, execution history) must also be in the take's singl | MATCH | shared terms: "deleted at clean-up" |
| ORDERS.md:20 | QUESTIONS.md:335 | L20: The one database means n8n's OWN state (workflows, credentials, execution history) must also be in the take's singl | MATCH | shared terms: "deleted at clean-up" |
| ORDERS.md line 144 | QUESTIONS.md:335 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | shared terms: ORDERS.md, QUEUE.md |
| ORDERS.md:20 | QUESTIONS.md:335 | L20: The one database means n8n's OWN state (workflows, credentials, execution history) must also be in the take's singl | MATCH | shared terms: "deleted at clean-up" |
| ORDERS.md line 147 | QUESTIONS.md:337 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | Q26 named in the cited answer block |
| ORDERS.md line 177 | QUESTIONS.md:339 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | shared terms: 17 Nov |
| ORDERS.md line 160 | QUESTIONS.md:339 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | shared terms: 09:30Z, 17 Nov, "loopback" |
| ORDERS.md line 156 | QUESTIONS.md:345 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block |
| ORDERS.md line 156 | QUESTIONS.md:346 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 166 | QUESTIONS.md:358 | L166: Q28: 1 Yes: the caption says 'one e-mail message in the intake mailbox'. 2 Put the post-wait mailbox count and the | MATCH | Q28 named in the cited answer block |
| ORDERS.md line 167 | QUESTIONS.md:367 | L167: Q29: 1 Yes: positive control before the rehearsal (two made-up mails with different IDs show two in the intake mai | MATCH | Q29 named in the cited answer block |
| ORDERS.md lines 170-171 | QUESTIONS.md:374 | L170: CORRECTION of my slip: several time stamps in my earlier ORDERS blocks (13:00Z to 15:00Z, and '13:00Z = 18:30 IST' | MATCH | Q30 named in the cited answer block |
| ORDERS.md line 170 | QUESTIONS.md:379 | L170: CORRECTION of my slip: several time stamps in my earlier ORDERS blocks (13:00Z to 15:00Z, and '13:00Z = 18:30 IST' | MATCH | shared terms: 13:00Z, "13:00Z = 18:30 IST", 15:00Z |
| ORDERS.md line 156 item 9 | QUESTIONS.md:399 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: F-002, T21; item 9 present |
| ORDERS.md line 177 | QUESTIONS.md:406 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md lines 144 and 166 | QUESTIONS.md:406 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | shared terms: ORDERS.md |
| ORDERS.md line 144 | QUESTIONS.md:406 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | Q25 named in the cited answer block |
| ORDERS.md line 160 | QUESTIONS.md:411 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | shared terms: 17 Nov |
| ORDERS.md lines 125 | QUESTIONS.md:411 | L125: Q20 (I could not read these facts from here; write each as 'lead verifies at re-pin', never as fact): 1 the take f | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 177 | QUESTIONS.md:411 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | shared terms: 17 Nov |
| ORDERS.md lines 125 | QUESTIONS.md:411 | L125: Q20 (I could not read these facts from here; write each as 'lead verifies at re-pin', never as fact): 1 the take f | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md lines 132 and 156 | QUESTIONS.md:413 | L132: 1 Env: the take's route is fill_flows literals (frozen tool, no n8n setting change), as you recommend. F-037/F-029 | MATCH | shared terms: F-011, F-041 |
| ORDERS.md line 171 | QUESTIONS.md:414 | L171: Q30: 1 Yes: the practice run starts about 06:00Z Wed 18 Nov; the F-002 test (T19-T21) is at the end of the practic | MATCH | Q30 named in the cited answer block |
| ORDERS.md line 149 | QUESTIONS.md:415 | L149: ## ORDER 030 (lead, 13:40Z): refill and ruff | MATCH | shared terms: "refill and ruff" |
| ORDERS.md line 147 | QUESTIONS.md:417 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | shared terms: "one mutation batch", "three-lane review" |
| ORDERS.md line 177 | QUESTIONS.md:418 | L177: 1 You show 6 agents with 8 open rows and low load: back to 8 now, or one reason per missing agent naming the answe | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 156 item 9 | QUESTIONS.md:419 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: F-002, T19, T21; item 9 present |
| ORDERS.md line 138 item 1 | QUESTIONS.md:420 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | shared terms: F-031; item 1 present |
| ORDERS.md line 156 item 9 | QUESTIONS.md:423 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: F-002, T19, T21; item 9 present |
| ORDERS.md line 156 item 9 | QUESTIONS.md:427 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: T19, T21; item 9 present |
| ORDERS.md line 156 item 3 | QUESTIONS.md:429 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: 15:00Z, 18 Nov; item 3 present |
| ORDERS.md line 160 | QUESTIONS.md:432 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 160 | QUESTIONS.md:432 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | shared terms: 17 Nov |
| ORDERS.md line 156 item 5 | QUESTIONS.md:433 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: F-011; item 5 present |
| ORDERS.md line 156 item 9 | QUESTIONS.md:433 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: 14:00Z, 07:00Z; item 9 present |
| ORDERS.md line 156 item 7 | QUESTIONS.md:435 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: scene 4, "else scene 4 is cut"; item 7 present |
| ORDERS.md line 156 item 7 | QUESTIONS.md:435 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | shared terms: scene 4, 07:00Z; item 7 present |
| ORDERS.md lines 146 and 147 | QUESTIONS.md:456 | L146: ## ANSWER (lead, 13:00Z Mon 16 Nov = 18:30 IST): Q26 ... L147: 1 Schedule (my agent-time estimate, not a promise; | MATCH | shared terms: n8n_drive.py, 13:00Z, run_real_check_n8n.py |
| ORDERS.md line 138 item 4 | QUESTIONS.md:467 | L138: 1 Keep Blocker for F-002, F-031, F-007 (my ORDER 007 stands; the rating note stays in REPORT). 2 F-013: accept 'en | MATCH | shared terms: 'lead verifies at re-pin'; item 4 present |
| ORDERS.md line 141 | QUESTIONS.md:470 | L141: Q23: keep accepted, no change to the frozen tool. Q24: 1 Date X: the lead writes the re-pin time after the merge,  | MATCH | Q23 named in the cited answer block |
| ORDERS.md line 141 | QUESTIONS.md:472 | L141: Q23: keep accepted, no change to the frozen tool. Q24: 1 Date X: the lead writes the re-pin time after the merge,  | MATCH | Q24 named in the cited answer block |
| ORDERS.md line 169-171 | QUESTIONS.md:478 | L169: ## ANSWER (lead, REAL clock 11:55Z Mon 16 Nov = 17:25 IST): Q30 and a time correction ... L171: Q30: 1 Yes: the pr | MATCH | Q30 named in the cited answer block |
| ORDERS.md line 98 | QUESTIONS.md:479 | L98: Not blocked: D-01..D-05, D-10, S-03, L-01 belong to system-map's drift report (the system-map session writes handov | MATCH | shared terms: handover/system-map/decisions/D04-D05.md |
| ORDERS.md line 147 | QUESTIONS.md:481 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | Q26 named in the cited answer block |
| ORDERS.md line 160 | QUESTIONS.md:481 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | shared terms: 09:30Z |
| ORDERS.md lines 146 to 171 | RUNBOOK.md:1 | L146: ## ANSWER (lead, 13:00Z Mon 16 Nov = 18:30 IST): Q26 ... L171: Q30: 1 Yes: the practice run starts about 06:00Z W | MATCH | shared terms: 17 Nov |
| ORDERS.md lines 159 to 171 | RUNBOOK.md:3 | L159: ## NOTE (lead, 14:35Z): re-smoke is now about 1 hour (owner yes) ... L171: Q30: 1 Yes: the practice run starts abo | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md lines 105 to 171 | RUNBOOK.md:3 | L105:  ... L171: Q30: 1 Yes: the practice run starts about 06:00Z W | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md lines 176 to 177 | RUNBOOK.md:3 | L176: ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure ... L177: 1 You show 6 agents wi | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 170 | RUNBOOK.md:3 | L170: CORRECTION of my slip: several time stamps in my earlier ORDERS blocks (13:00Z to 15:00Z, and '13:00Z = 18:30 IST' | MATCH | shared terms: 13:00Z, 15:00Z |
| ORDERS.md lines 159 to 171 | RUNBOOK.md:5 | L159: ## NOTE (lead, 14:35Z): re-smoke is now about 1 hour (owner yes) ... L171: Q30: 1 Yes: the practice run starts abo | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 160 | RUNBOOK.md:14 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 132 | RUNBOOK.md:15 | L132: 1 Env: the take's route is fill_flows literals (frozen tool, no n8n setting change), as you recommend. F-037/F-029 | MATCH | Q21 named in the cited answer block |
| ORDERS.md line 166 | RUNBOOK.md:17 | L166: Q28: 1 Yes: the caption says 'one e-mail message in the intake mailbox'. 2 Put the post-wait mailbox count and the | MATCH | Q28 named in the cited answer block |
| ORDERS.md line 147 | RUNBOOK.md:22 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | Q26 named in the cited answer block |
| ORDERS.md line 156 item 2 | RUNBOOK.md:22 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | read by hand: cited line fits the sentence; item 2 present |
| ORDERS.md line 135 | RUNBOOK.md:22 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | Q22 named in the cited answer block |
| ORDERS.md line 156 item 2 | RUNBOOK.md:24 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | read by hand: cited line fits the sentence; item 2 present |
| ORDERS.md line 160 | RUNBOOK.md:46 | L160: Update RUNBOOK and OWNER-STEPS times: re-pin Tue 17 Nov about 08:00Z, short loopback re-smoke (n8n start through t | MATCH | shared terms: 17 Nov |
| ORDERS.md line 132 | RUNBOOK.md:98 | L132: 1 Env: the take's route is fill_flows literals (frozen tool, no n8n setting change), as you recommend. F-037/F-029 | MATCH | shared terms: F-011, F-041, "never downgrade by counting" |
| ORDERS.md line 156 item 2 | RUNBOOK.md:99 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block; item 2 present |
| ORDERS.md line 156 item 2 | RUNBOOK.md:100 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | read by hand: cited line fits the sentence; item 2 present |
| ORDERS.md line 167 | RUNBOOK.md:107 | L167: Q29: 1 Yes: positive control before the rehearsal (two made-up mails with different IDs show two in the intake mai | MATCH | Q29 named in the cited answer block |
| ORDERS.md line 156 item 2 | RUNBOOK.md:108 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | read by hand: cited line fits the sentence; item 2 present |
| ORDERS.md line 135 | RUNBOOK.md:111 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | Q22 named in the cited answer block |
| ORDERS.md line 147 | RUNBOOK.md:115 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | Q26 named in the cited answer block |
| ORDERS.md line 166 | RUNBOOK.md:117 | L166: Q28: 1 Yes: the caption says 'one e-mail message in the intake mailbox'. 2 Put the post-wait mailbox count and the | MATCH | Q28 named in the cited answer block |
| ORDERS.md lines 176 to 177 | RUNBOOK.md:122 | L176: ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure ... L177: 1 You show 6 agents wi | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 147 | RUNBOOK.md:185 | L147: 1 Schedule (my agent-time estimate, not a promise; I tell the owner the same): Mon 16 Nov to about 04:00Z Tue (09: | MATCH | Q26 named in the cited answer block |
| ORDERS.md line 156 item 4 | RUNBOOK.md:200 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block; item 4 present |
| ORDERS.md:20 | RUNBOOK.md:210 | L20: The one database means n8n's OWN state (workflows, credentials, execution history) must also be in the take's singl | MATCH | shared terms: "one database" |
| ORDERS.md line 170 | RUNBOOK.md:212 | L170: CORRECTION of my slip: several time stamps in my earlier ORDERS blocks (13:00Z to 15:00Z, and '13:00Z = 18:30 IST' | MATCH | Q26 named in the cited answer block |
| ORDERS.md lines 176 to 177 | RUNBOOK.md:218 | L176: ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure ... L177: 1 You show 6 agents wi | MATCH | read by hand: cited line fits the sentence |
| ORDERS.md line 144 item 10 | RUNBOOK.md:218 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | Q25 named in the cited answer block; item 10 present |
| ORDERS.md line 156 item 2 | RUNBOOK.md:238 | L156: 1 n8n_start.sh, n8n_kill.py and run_real_check_n8n.py are on local take branches (merge head take/nlite-merge-m1 [ | MATCH | Q27 named in the cited answer block; item 2 present |
| ORDERS.md lines 132 and 144 | RUNBOOK.md:270 | L132: 1 Env: the take's route is fill_flows literals (frozen tool, no n8n setting change), as you recommend. F-037/F-029 | MATCH | shared terms: "up to 3" |
| ORDERS.md line 144 | RUNBOOK.md:271 | L144: 1 The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use th | MATCH | shared terms: ORDERS.md |
| ORDERS.md line 135 | RUNBOOK.md:275 | L135: 1 Scene 4: the lead stops and starts n8n with the take scripts (decision 7), the owner never does; the stopwatch i | MATCH | Q22 named in the cited answer block |

### B ORDER nnn: 67

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| ORDER 035 | QUESTIONS.md:5 | ## ORDER 035 (lead, real clock 11:58Z): per-agent status table NOW, and a standing minimum | MATCH | header at ORDERS.md line 173 |
| ORDER 037 | QUESTIONS.md:5 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176 |
| ORDER 037 item 3 | QUESTIONS.md:5 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 | QUESTIONS.md:5 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176 |
| ORDER 037 item 3 | QUESTIONS.md:42 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:71 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:71 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:78 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:131 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:132 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:133 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:155 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 023 | QUESTIONS.md:156 | ## ORDER 023 (lead, owner 2026-11-16): EGM planning skills use Fable 5.2, not Opus 5.5 | MATCH | header at ORDERS.md line 100 |
| ORDER 037 item 3 | QUESTIONS.md:161 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:161 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:161 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:170 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:170 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:175 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 | QUESTIONS.md:184 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176 |
| ORDER 037 | QUESTIONS.md:185 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176 |
| ORDER 004 | QUESTIONS.md:195 | ## ORDER 004 (lead, 2026-11-16) ANSWER to Q2 (F-011): READING A | MATCH | header at ORDERS.md line 19 |
| ORDER 012 | QUESTIONS.md:198 | ## ORDER 012 (lead, 2026-11-16) ANSWER to Q3 (F-041) | MATCH | header at ORDERS.md line 54 |
| ORDER 007 item 5 | QUESTIONS.md:198 | ## ORDER 007 (lead, 2026-11-16) BACKLOG, items 1-5 in parallel lanes | MATCH | header at ORDERS.md line 29; item 5 present |
| ORDER 002 | QUESTIONS.md:198 | ## ORDER 002 (lead, 2026-11-16) GO: proof accepted (EGM visible, models 6 opus / 64 sonnet). Start work. | MATCH | header at ORDERS.md line 11 |
| ORDER 007 item 6 | QUESTIONS.md:200 | ## ORDER 007 (lead, 2026-11-16) BACKLOG, items 1-5 in parallel lanes | MATCH | header at ORDERS.md line 29; item 6 present |
| ORDER 013 | QUESTIONS.md:204 | ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) | MATCH | header at ORDERS.md line 57 |
| ORDER 004 | QUESTIONS.md:204 | ## ORDER 004 (lead, 2026-11-16) ANSWER to Q2 (F-011): READING A | MATCH | header at ORDERS.md line 19 |
| ORDER 013 | QUESTIONS.md:205 | ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) | MATCH | header at ORDERS.md line 57 |
| ORDER 013 | QUESTIONS.md:206 | ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) | MATCH | header at ORDERS.md line 57 |
| ORDER 013 | QUESTIONS.md:207 | ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) | MATCH | header at ORDERS.md line 57 |
| ORDER 013 | QUESTIONS.md:208 | ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) | MATCH | header at ORDERS.md line 57 |
| ORDER 013 | QUESTIONS.md:209 | ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) | MATCH | header at ORDERS.md line 57 |
| ORDER 013 | QUESTIONS.md:211 | ## ORDER 013 (lead, 2026-11-16) ANSWERS Q4-Q9 and NEXT WORK (you are FINAL; this is the next order, same turn) | MATCH | header at ORDERS.md line 57 |
| ORDER 017 | QUESTIONS.md:224 | ## ORDER 017 (lead, 2026-11-16) FAILS AND GUIDANCE (owner HARD rule, bible R461 addendum 3) | MATCH | header at ORDERS.md line 75 |
| ORDER 017 | QUESTIONS.md:264 | ## ORDER 017 (lead, 2026-11-16) FAILS AND GUIDANCE (owner HARD rule, bible R461 addendum 3) | MATCH | header at ORDERS.md line 75 |
| ORDER 017 | QUESTIONS.md:282 | ## ORDER 017 (lead, 2026-11-16) FAILS AND GUIDANCE (owner HARD rule, bible R461 addendum 3) | MATCH | header at ORDERS.md line 75 |
| ORDER 037 item 3 | QUESTIONS.md:292 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 007 | QUESTIONS.md:299 | ## ORDER 007 (lead, 2026-11-16) BACKLOG, items 1-5 in parallel lanes | MATCH | header at ORDERS.md line 29 |
| ORDER 037 item 3 | QUESTIONS.md:331 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:331 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:339 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:406 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:408 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:411 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | QUESTIONS.md:411 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 030 | QUESTIONS.md:415 | ## ORDER 030 (lead, 13:40Z): refill and ruff | MATCH | header at ORDERS.md line 149 |
| ORDER 037 | QUESTIONS.md:418 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176 |
| ORDER 037 item 3 | QUESTIONS.md:434 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 004 | QUESTIONS.md:440 | ## ORDER 004 (lead, 2026-11-16) ANSWER to Q2 (F-011): READING A | MATCH | header at ORDERS.md line 19 |
| ORDER 037 item 3 | QUESTIONS.md:483 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:3 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:14 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:27 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:46 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:100 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:100 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:107 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:110 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:111 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:122 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:218 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:243 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:252 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:252 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:272 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |
| ORDER 037 item 3 | RUNBOOK.md:272 | ## ORDER 037 (lead, real clock 12:33Z): 6 agents, load 0.84; and the ruff failure | MATCH | header at ORDERS.md line 176; item 3 present |

### C Q item: 258

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| Q17 item 5 | QUESTIONS.md:25 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 3 |
| Q31 item 3 | QUESTIONS.md:25 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 3 |
| Q25 item 2 | QUESTIONS.md:27 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 1 |
| Q31 item 12 | QUESTIONS.md:40 | 12. [OPEN] FORMAT FILE (ownersteps8 item 9; known to the lead): inputs/plan-wp6-resmoke-v5.md line 193 fails r | MATCH | item at QUESTIONS.md:415; shared words: 1 |
| Q31 item 12 | QUESTIONS.md:42 | 12. [OPEN] FORMAT FILE (ownersteps8 item 9; known to the lead): inputs/plan-wp6-resmoke-v5.md line 193 fails r | MATCH | item at QUESTIONS.md:415; shared words: 3 |
| Q31 item 1 | QUESTIONS.md:42 | 1. [OPEN] SILENCE RULES (ownersteps7 item 1; ownersteps8 items 3, 7 and 8): what happens when the owner does n | MATCH | item at QUESTIONS.md:404; shared words: 4 |
| Q31 item 28 | QUESTIONS.md:42 | 28. [OPEN] L32 GO RULE: CUT SCENE 4 OR SLIP (the audit, 2026-11-16): ORDERS.md line 156 item 7 says the lead d | MATCH | item at QUESTIONS.md:435; shared words: 1 |
| Q31 item 3 | QUESTIONS.md:42 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 6 |
| Q25 item 1 | QUESTIONS.md:42 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 3 |
| Q31 item 10 | QUESTIONS.md:42 | 10. [OPEN] GATE ACTOR (the audit's own; see the GATE): who must make F-011 and F-041 fixed or downgraded with  | MATCH | item at QUESTIONS.md:413; shared words: 6 |
| Q31 item 11 | QUESTIONS.md:42 | 11. [OPEN] WHO APPLIES F-031 AND F-007 (the audit's own; Q30 item 2): ORDERS.md line 171 says the text must be | MATCH | item at QUESTIONS.md:414; shared words: 2 |
| Q31 item 8 | QUESTIONS.md:42 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 5 |
| Q31 item 10 | QUESTIONS.md:50 | 10. [OPEN] GATE ACTOR (the audit's own; see the GATE): who must make F-011 and F-041 fixed or downgraded with  | MATCH | item at QUESTIONS.md:413; shared words: 11 |
| Q31 item 10 | QUESTIONS.md:50 | 10. [OPEN] GATE ACTOR (the audit's own; see the GATE): who must make F-011 and F-041 fixed or downgraded with  | MATCH | item at QUESTIONS.md:413; shared words: 14 |
| Q31 item 8 | QUESTIONS.md:60 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 6 |
| Q17 item 5 | QUESTIONS.md:61 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 6 |
| Q25 item 1 | QUESTIONS.md:61 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 0; read by hand |
| Q28 item 3 | QUESTIONS.md:61 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 0; read by hand |
| Q17 item 5 | QUESTIONS.md:61 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 6 |
| Q17 item 5 | QUESTIONS.md:61 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 8 |
| Q25 item 1 | QUESTIONS.md:61 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 7 |
| Q28 item 3 | QUESTIONS.md:61 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 3 |
| Q31 item 3 | QUESTIONS.md:61 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 12 |
| Q17 item 5 | QUESTIONS.md:61 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 0; read by hand |
| Q31 item 6 | QUESTIONS.md:61 | 6. [OPEN] GO/NO-GO MESSAGE (ownersteps7 item 6; ownersteps8 items 2 and 3): does the lead send the owner a mes | MATCH | item at QUESTIONS.md:409; shared words: 7 |
| Q20 item 1 | QUESTIONS.md:62 | 1. Where is the take folder (the folder the take scripts and the v4 mf_leads.sql copy live in)? No input names | MATCH | item at QUESTIONS.md:272; shared words: 2 |
| Q20 item 3 | QUESTIONS.md:62 | 3. Is the intake address the RECEIVER mailbox? (I inferred it from the flow's toEmail field; the row says unco | MATCH | item at QUESTIONS.md:274; shared words: 4 |
| Q20 item 4 | QUESTIONS.md:63 | Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentenc | MATCH | item at ORDERS.md answer to Q20; shared words: 5 |
| Q31 item 8 | QUESTIONS.md:63 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 6 |
| Q31 item 14 | QUESTIONS.md:63 | 14. [OPEN] WORDS THE ORDERS DO NOT EXPLAIN (the audit's own; glossary entries marked "lead to confirm"): (a) " | MATCH | item at QUESTIONS.md:417; shared words: 3 |
| Q22a item 5 | QUESTIONS.md:65 | 5. [ANSWERED, lead action pending (the lead verifies the real-take port and n8n_api.py at re-pin)] Re-pin date | MATCH | item at QUESTIONS.md:294; shared words: 4 |
| Q27 item 1 | QUESTIONS.md:65 | 1. [ANSWERED, lead action pending (the lead copies n8n_start.sh, n8n_kill.py and run_real_check_n8n.py from th | MATCH | item at QUESTIONS.md:347; shared words: 5 |
| Q22b item 3 | QUESTIONS.md:66 | 3. [ANSWERED, lead action pending (the lead asks the owner once, in a table, for the yes to archive; what is a | MATCH | item at QUESTIONS.md:301; shared words: 6 |
| Q24 item 2 | QUESTIONS.md:67 | 2. The 45 s lease threshold N (the rehearsal step time above which recovery is off for the take) and the 'unde | MATCH | item at QUESTIONS.md:314; shared words: 3 |
| Q25 item 3 | QUESTIONS.md:67 | 3. [ANSWERED, lead action pending (the lead sets the wait and the expected attempts value at the rehearsal)] T | MATCH | item at QUESTIONS.md:324; shared words: 5 |
| Q25 item 1 | QUESTIONS.md:68 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 4 |
| Q25 item 1 | QUESTIONS.md:68 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 4 |
| Q31 item 3 | QUESTIONS.md:68 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 15 |
| Q31 item 8 | QUESTIONS.md:68 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 9 |
| Q25 item 2 | QUESTIONS.md:69 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 9 |
| Q28 item 1 | QUESTIONS.md:69 | 1. [ANSWERED] RWQ-8 (RUNSHEET-WORDING.md section 4): should the scoped caption (A-016f) say where the one mess | MATCH | item at QUESTIONS.md:361; shared words: 6 |
| Q25 item 5 | QUESTIONS.md:70 | 5. [ANSWERED, lead action pending (the lead names the mailboxes at take prep)] Which mailbox is intake, receiv | MATCH | item at QUESTIONS.md:326; shared words: 1 |
| Q31 item 8 | QUESTIONS.md:70 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 5 |
| Q25 item 10 | QUESTIONS.md:71 | 10. [PARTLY SUPERSEDED (ORDER 037 item 3, ORDERS.md line 177: the sentence "The rehearsal does NOT go into rea | MATCH | item at QUESTIONS.md:331; shared words: 11 |
| Q31 item 5 | QUESTIONS.md:71 | 5. [OPEN] NUMBER OF DELETE MESSAGES (ownersteps7 item 5): the total depends on which runs go through the real  | MATCH | item at QUESTIONS.md:408; shared words: 10 |
| Q25 item 11 | QUESTIONS.md:72 | 11. [ANSWERED, lead action pending (the lead fills in the facts)] Facts only the lead has, all left as "lead f | MATCH | item at QUESTIONS.md:332; shared words: 3 |
| Q25 item 12 | QUESTIONS.md:73 | 12. [ANSWERED, lead action pending (the lead sets the cut time after the rehearsal measures it)] Stopwatch and | MATCH | item at QUESTIONS.md:333; shared words: 3 |
| Q25 item 13 | QUESTIONS.md:74 | 13. [ANSWERED, lead action pending ((c) the lead decides at re-pin; (d) the lead corrects inputs/DECISION-one- | MATCH | item at QUESTIONS.md:334; shared words: 6 |
| Q25 item 13 | QUESTIONS.md:75 | 13. [ANSWERED, lead action pending ((c) the lead decides at re-pin; (d) the lead corrects inputs/DECISION-one- | MATCH | item at QUESTIONS.md:334; shared words: 3 |
| Q26 item 3 | QUESTIONS.md:76 | 3. [ANSWERED, lead action pending (the lead provides the runbook with real commands and places scripts/n8n_api | MATCH | item at QUESTIONS.md:341; shared words: 8 |
| Q27 item 1 | QUESTIONS.md:76 | 1. [ANSWERED, lead action pending (the lead copies n8n_start.sh, n8n_kill.py and run_real_check_n8n.py from th | MATCH | item at QUESTIONS.md:347; shared words: 8 |
| Q30 item 3 | QUESTIONS.md:76 | 3. [ANSWERED, lead action pending (the lead provides n8n_drive.py on the take branch at re-pin; whether script | MATCH | item at QUESTIONS.md:378; shared words: 3 |
| Q26 item 1 | QUESTIONS.md:77 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 2 |
| Q27 item 2 | QUESTIONS.md:78 | 2. [ANSWERED, lead action pending (the lead asks the owner once, at take prep, for the HubSpot token scopes; a | MATCH | item at QUESTIONS.md:348; shared words: 3 |
| Q31 item 27 | QUESTIONS.md:78 | 27. [OPEN] WHEN THE HUBSPOT TOKEN-SCOPES QUESTION GOES TO THE OWNER (the audit, from the same review, 2026-11- | MATCH | item at QUESTIONS.md:434; shared words: 6 |
| Q27 item 2 | QUESTIONS.md:78 | 2. [ANSWERED, lead action pending (the lead asks the owner once, at take prep, for the HubSpot token scopes; a | MATCH | item at QUESTIONS.md:348; shared words: 2 |
| Q27 item 2 | QUESTIONS.md:79 | 2. [ANSWERED, lead action pending (the lead asks the owner once, at take prep, for the HubSpot token scopes; a | MATCH | item at QUESTIONS.md:348; shared words: 6 |
| Q27 item 9 | QUESTIONS.md:80 | 9. [ANSWERED, lead action pending (F-011 and F-041 must be fixed or downgraded with evidence before Tue 17 Nov | MATCH | item at QUESTIONS.md:355; shared words: 5 |
| Q21 item 3 | QUESTIONS.md:80 | 3. Also open with no number: whether F-011 and F-041 stay Major BEFORE or are Nit AFTER (FINDINGS counts), the | MATCH | item at QUESTIONS.md:284; shared words: 2 |
| Q31 item 10 | QUESTIONS.md:80 | 10. [OPEN] GATE ACTOR (the audit's own; see the GATE): who must make F-011 and F-041 fixed or downgraded with  | MATCH | item at QUESTIONS.md:413; shared words: 12 |
| Q28 item 2 | QUESTIONS.md:81 | 2. [ANSWERED, lead action pending (the lead puts the post-wait mailbox count and the mf_leads row in frame; a  | MATCH | item at QUESTIONS.md:362; shared words: 8 |
| Q28 item 5 | QUESTIONS.md:82 | 5. [ANSWERED, lead action pending (the lead corrects DECISIONS items 1 and 7 and VIDEO-RUNSHEET rows N-9, N-10 | MATCH | item at QUESTIONS.md:365; shared words: 3 |
| Q29 item 4 | QUESTIONS.md:83 | 4. [ANSWERED, lead action pending (the lead puts the scripts on a branch; the audit reviews read-only, with a  | MATCH | item at QUESTIONS.md:372; shared words: 7 |
| Q30 item 2 | QUESTIONS.md:84 | 2. [ANSWERED, lead action pending (apply the caption and sheet text of F-031 and F-007 and re-read by Wed 18 N | MATCH | item at QUESTIONS.md:377; shared words: 6 |
| Q31 item 11 | QUESTIONS.md:84 | 11. [OPEN] WHO APPLIES F-031 AND F-007 (the audit's own; Q30 item 2): ORDERS.md line 171 says the text must be | MATCH | item at QUESTIONS.md:414; shared words: 7 |
| Q31 item 12 | QUESTIONS.md:85 | 12. [OPEN] FORMAT FILE (ownersteps8 item 9; known to the lead): inputs/plan-wp6-resmoke-v5.md line 193 fails r | MATCH | item at QUESTIONS.md:415; shared words: 10 |
| Q31 item 12 | QUESTIONS.md:85 | 12. [OPEN] FORMAT FILE (ownersteps8 item 9; known to the lead): inputs/plan-wp6-resmoke-v5.md line 193 fails r | MATCH | item at QUESTIONS.md:415; shared words: 9 |
| Q29 item 1 | QUESTIONS.md:86 | 1. [ANSWERED, lead action pending (the lead sends the two made-up mails before the rehearsal, L30)] Positive c | MATCH | item at QUESTIONS.md:369; shared words: 11 |
| Q30 item 1 | QUESTIONS.md:86 | 1. [ANSWERED] F-002 check is "Wed 07:30Z" but the rehearsal starts about 07:30Z after practice run (1 h) and R | MATCH | item at QUESTIONS.md:376; shared words: 2 |
| Q29 item 2 | QUESTIONS.md:87 | 2. [ANSWERED, lead action pending (the lead recounts the mailbox after the stated wait, L31)] Late second mail | MATCH | item at QUESTIONS.md:370; shared words: 6 |
| Q27 item 7 | QUESTIONS.md:88 | 7. [ANSWERED, lead action pending (the lead decides GO or slip about 09:30Z-10:00Z on Wed 18 Nov, L32)] A go/n | MATCH | item at QUESTIONS.md:353; shared words: 5 |
| Q31 item 28 | QUESTIONS.md:88 | 28. [OPEN] L32 GO RULE: CUT SCENE 4 OR SLIP (the audit, 2026-11-16): ORDERS.md line 156 item 7 says the lead d | MATCH | item at QUESTIONS.md:435; shared words: 8 |
| Q22a item 3 | QUESTIONS.md:89 | 3. [ANSWERED, lead action pending (L33: the lead does the check as the last step before the take)] Last check  | MATCH | item at QUESTIONS.md:292; shared words: 8 |
| Q27 item 2 | QUESTIONS.md:91 | 2. [ANSWERED, lead action pending (the lead asks the owner once, at take prep, for the HubSpot token scopes; a | MATCH | item at QUESTIONS.md:348; shared words: 5 |
| Q20 item 1 | QUESTIONS.md:91 | 1. Where is the take folder (the folder the take scripts and the v4 mf_leads.sql copy live in)? No input names | MATCH | item at QUESTIONS.md:272; shared words: 2 |
| Q20 item 3 | QUESTIONS.md:91 | 3. Is the intake address the RECEIVER mailbox? (I inferred it from the flow's toEmail field; the row says unco | MATCH | item at QUESTIONS.md:274; shared words: 2 |
| Q25 item 9 | QUESTIONS.md:96 | 9. [ANSWERED] "coordinator" or "the lead" (sweep3 Q-9; run sheet Q-W): recommendation: "the lead" everywhere.  | MATCH | item at QUESTIONS.md:330; shared words: 2 |
| Q29 item 3 | QUESTIONS.md:108 | 3. [ANSWERED] Fallback if T19/T20 fail on the patched copy: confirm whether the take is NO-GO (my reading of Q | MATCH | item at QUESTIONS.md:371; shared words: 2 |
| Q21 item 1 | QUESTIONS.md:110 | 1. Env access in nodes. F-037, F-029 and F-018 (FIX-PLAN item 3) tell the lead to set N8N_BLOCK_ENV_ACCESS_IN_ | MATCH | item at QUESTIONS.md:282; shared words: 2 |
| Q21 item 1 | QUESTIONS.md:111 | 1. Env access in nodes. F-037, F-029 and F-018 (FIX-PLAN item 3) tell the lead to set N8N_BLOCK_ENV_ACCESS_IN_ | MATCH | item at QUESTIONS.md:282; shared words: 1 |
| Q31 item 22 | QUESTIONS.md:121 | 22. [OPEN] T21 METHOD (the audit, 2026-11-16; FINDINGS.md row F-002): T21 is the test that makes the take data | MATCH | item at QUESTIONS.md:425; shared words: 15 |
| Q27 item 9 | QUESTIONS.md:121 | 9. [ANSWERED, lead action pending (F-011 and F-041 must be fixed or downgraded with evidence before Tue 17 Nov | MATCH | item at QUESTIONS.md:355; shared words: 3 |
| Q27 item 10 | QUESTIONS.md:122 | 10. [PARTLY SUPERSEDED (answered; by Q28 items 3 and 4: Step A is removed)] (same check) The decisions file sa | MATCH | item at QUESTIONS.md:356; shared words: 6 |
| Q28 item 1 | QUESTIONS.md:123 | 1. [ANSWERED] RWQ-8 (RUNSHEET-WORDING.md section 4): should the scoped caption (A-016f) say where the one mess | MATCH | item at QUESTIONS.md:361; shared words: 5 |
| Q28 item 2 | QUESTIONS.md:123 | 2. [ANSWERED, lead action pending (the lead puts the post-wait mailbox count and the mf_leads row in frame; a  | MATCH | item at QUESTIONS.md:362; shared words: 3 |
| Q25 item 12 | QUESTIONS.md:126 | 12. [ANSWERED, lead action pending (the lead sets the cut time after the rehearsal measures it)] Stopwatch and | MATCH | item at QUESTIONS.md:333; shared words: 8 |
| Q31 item 13 | QUESTIONS.md:126 | 13. [OPEN] WHO TIMES THE 3-MINUTE TAKEOVER (the audit's own): Q22a said the owner's phone; Q25 item 12 says no | MATCH | item at QUESTIONS.md:416; shared words: 4 |
| Q25 item 4 | QUESTIONS.md:126 | 4. [ANSWERED] Is the closing card used (sweep3 Q-4)? Claims table says answered, run sheet Q-F says open. Reco | MATCH | item at QUESTIONS.md:325; shared words: 1 |
| Q17 item 5 | QUESTIONS.md:127 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 5 |
| Q26 item 5 | QUESTIONS.md:127 | 5. [ANSWERED] Should Row 4 (one made-up lead through the real HubSpot trial) be the first thing done, since it | MATCH | item at QUESTIONS.md:343; shared words: 4 |
| Q25 item 1 | QUESTIONS.md:128 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 5 |
| Q28 item 3 | QUESTIONS.md:128 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 2 |
| Q25 item 6 | QUESTIONS.md:130 | 6. [ANSWERED] Re-pin versus re-check (sweep3 Q-6): is re-pin only the move to the new core commit, or also the | MATCH | item at QUESTIONS.md:327; shared words: 6 |
| Q31 item 8 | QUESTIONS.md:131 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 12 |
| Q30 item 1 | QUESTIONS.md:132 | 1. [ANSWERED] F-002 check is "Wed 07:30Z" but the rehearsal starts about 07:30Z after practice run (1 h) and R | MATCH | item at QUESTIONS.md:376; shared words: 2 |
| Q29 item 3 | QUESTIONS.md:132 | 3. [ANSWERED] Fallback if T19/T20 fail on the patched copy: confirm whether the take is NO-GO (my reading of Q | MATCH | item at QUESTIONS.md:371; shared words: 2 |
| Q31 item 8 | QUESTIONS.md:132 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 13 |
| Q27 item 6 | QUESTIONS.md:132 | 6. [ANSWERED] A real latest re-pin time on the NO-GO path, working back from Mon 23 Nov 18:29Z by practice run | MATCH | item at QUESTIONS.md:352; shared words: 1 |
| Q31 item 8 | QUESTIONS.md:132 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 12 |
| Q30 item 1 | QUESTIONS.md:133 | 1. [ANSWERED] F-002 check is "Wed 07:30Z" but the rehearsal starts about 07:30Z after practice run (1 h) and R | MATCH | item at QUESTIONS.md:376; shared words: 2 |
| Q25 item 10 | QUESTIONS.md:133 | 10. [PARTLY SUPERSEDED (ORDER 037 item 3, ORDERS.md line 177: the sentence "The rehearsal does NOT go into rea | MATCH | item at QUESTIONS.md:331; shared words: 16 |
| Q31 item 5 | QUESTIONS.md:133 | 5. [OPEN] NUMBER OF DELETE MESSAGES (ownersteps7 item 5): the total depends on which runs go through the real  | MATCH | item at QUESTIONS.md:408; shared words: 10 |
| Q26 item 2 | QUESTIONS.md:134 | 2. [ANSWERED] r20, r21, r22 in plain words: see "round" in the glossary. None touches the flow files F-002/F-0 | MATCH | item at QUESTIONS.md:340; shared words: 2 |
| Q27 item 5 | QUESTIONS.md:135 | 5. [ANSWERED] The ledger path the GO/NO-GO test reads, and who decides. Lead: the ledger is egm\BLOCKER-LEDGER | MATCH | item at QUESTIONS.md:351; shared words: 5 |
| Q27 item 7 | QUESTIONS.md:139 | 7. [ANSWERED, lead action pending (the lead decides GO or slip about 09:30Z-10:00Z on Wed 18 Nov, L32)] A go/n | MATCH | item at QUESTIONS.md:353; shared words: 3 |
| Q31 item 6 | QUESTIONS.md:139 | 6. [OPEN] GO/NO-GO MESSAGE (ownersteps7 item 6; ownersteps8 items 2 and 3): does the lead send the owner a mes | MATCH | item at QUESTIONS.md:409; shared words: 12 |
| Q31 item 6 | QUESTIONS.md:139 | 6. [OPEN] GO/NO-GO MESSAGE (ownersteps7 item 6; ownersteps8 items 2 and 3): does the lead send the owner a mes | MATCH | item at QUESTIONS.md:409; shared words: 11 |
| Q31 item 6 | QUESTIONS.md:139 | 6. [OPEN] GO/NO-GO MESSAGE (ownersteps7 item 6; ownersteps8 items 2 and 3): does the lead send the owner a mes | MATCH | item at QUESTIONS.md:409; shared words: 6 |
| Q25 item 3 | QUESTIONS.md:141 | 3. [ANSWERED, lead action pending (the lead sets the wait and the expected attempts value at the rehearsal)] T | MATCH | item at QUESTIONS.md:324; shared words: 6 |
| Q29 item 2 | QUESTIONS.md:141 | 2. [ANSWERED, lead action pending (the lead recounts the mailbox after the stated wait, L31)] Late second mail | MATCH | item at QUESTIONS.md:370; shared words: 6 |
| Q17 item 1 | QUESTIONS.md:146 | 1. [ANSWERED (YES, freeze fill_flows (F3) after round r7; further rounds only for an open Blocker)] Freeze fil | MATCH | item at QUESTIONS.md:249; shared words: 2 |
| Q17 item 2 | QUESTIONS.md:146 | 2. [ANSWERED (YES, park F8 beyond take_check.sh, and F2/F6)] Park F8 beyond take_check.sh (--baseline, --stric | MATCH | item at QUESTIONS.md:250; shared words: 2 |
| Q17 item 2 | QUESTIONS.md:146 | 2. [ANSWERED (YES, park F8 beyond take_check.sh, and F2/F6)] Park F8 beyond take_check.sh (--baseline, --stric | MATCH | item at QUESTIONS.md:250; shared words: 2 |
| Q25 item 9 | QUESTIONS.md:151 | 9. [ANSWERED] "coordinator" or "the lead" (sweep3 Q-9; run sheet Q-W): recommendation: "the lead" everywhere.  | MATCH | item at QUESTIONS.md:330; shared words: 3 |
| Q20 item 3 | QUESTIONS.md:153 | 3. Is the intake address the RECEIVER mailbox? (I inferred it from the flow's toEmail field; the row says unco | MATCH | item at QUESTIONS.md:274; shared words: 5 |
| Q25 item 5 | QUESTIONS.md:153 | 5. [ANSWERED, lead action pending (the lead names the mailboxes at take prep)] Which mailbox is intake, receiv | MATCH | item at QUESTIONS.md:326; shared words: 3 |
| Q22a item 3 | QUESTIONS.md:158 | 3. [ANSWERED, lead action pending (L33: the lead does the check as the last step before the take)] Last check  | MATCH | item at QUESTIONS.md:292; shared words: 1 |
| Q20 item 1 | QUESTIONS.md:161 | 1. Where is the take folder (the folder the take scripts and the v4 mf_leads.sql copy live in)? No input names | MATCH | item at QUESTIONS.md:272; shared words: 1 |
| Q31 item 3 | QUESTIONS.md:161 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 5 |
| Q31 item 8 | QUESTIONS.md:161 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 16 |
| Q24 item 3 | QUESTIONS.md:162 | 3. DESK_ALERT_TO: the files show the unfilled real-v5 has 3 $env reads (DESK_ALERT_TO, DESK_URL, DESK_TIMEOUT_ | MATCH | item at QUESTIONS.md:315; shared words: 6 |
| Q31 item 14 | QUESTIONS.md:162 | 14. [OPEN] WORDS THE ORDERS DO NOT EXPLAIN (the audit's own; glossary entries marked "lead to confirm"): (a) " | MATCH | item at QUESTIONS.md:417; shared words: 5 |
| Q24 item 3 | QUESTIONS.md:163 | 3. DESK_ALERT_TO: the files show the unfilled real-v5 has 3 $env reads (DESK_ALERT_TO, DESK_URL, DESK_TIMEOUT_ | MATCH | item at QUESTIONS.md:315; shared words: 8 |
| Q31 item 14 | QUESTIONS.md:163 | 14. [OPEN] WORDS THE ORDERS DO NOT EXPLAIN (the audit's own; glossary entries marked "lead to confirm"): (a) " | MATCH | item at QUESTIONS.md:417; shared words: 7 |
| Q31 item 7 | QUESTIONS.md:164 | 7. [OPEN] WHAT TYPING y CONFIRMS (ownersteps7 item 7; ownersteps8 item 6): what typing y confirms in the demo  | MATCH | item at QUESTIONS.md:410; shared words: 4 |
| Q26 item 3 | QUESTIONS.md:165 | 3. [ANSWERED, lead action pending (the lead provides the runbook with real commands and places scripts/n8n_api | MATCH | item at QUESTIONS.md:341; shared words: 4 |
| Q31 item 14 | QUESTIONS.md:165 | 14. [OPEN] WORDS THE ORDERS DO NOT EXPLAIN (the audit's own; glossary entries marked "lead to confirm"): (a) " | MATCH | item at QUESTIONS.md:417; shared words: 9 |
| Q31 item 14 | QUESTIONS.md:166 | 14. [OPEN] WORDS THE ORDERS DO NOT EXPLAIN (the audit's own; glossary entries marked "lead to confirm"): (a) " | MATCH | item at QUESTIONS.md:417; shared words: 5 |
| Q31 item 14 | QUESTIONS.md:167 | 14. [OPEN] WORDS THE ORDERS DO NOT EXPLAIN (the audit's own; glossary entries marked "lead to confirm"): (a) " | MATCH | item at QUESTIONS.md:417; shared words: 1 |
| Q30 item 2 | QUESTIONS.md:169 | 2. [ANSWERED, lead action pending (apply the caption and sheet text of F-031 and F-007 and re-read by Wed 18 N | MATCH | item at QUESTIONS.md:377; shared words: 6 |
| Q21 item 3 | QUESTIONS.md:170 | 3. Also open with no number: whether F-011 and F-041 stay Major BEFORE or are Nit AFTER (FINDINGS counts), the | MATCH | item at QUESTIONS.md:284; shared words: 2 |
| Q25 item 1 | QUESTIONS.md:170 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 4 |
| Q31 item 3 | QUESTIONS.md:170 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 10 |
| Q29 item 1 | QUESTIONS.md:170 | 1. [ANSWERED, lead action pending (the lead sends the two made-up mails before the rehearsal, L30)] Positive c | MATCH | item at QUESTIONS.md:369; shared words: 7 |
| Q17 item 5 | QUESTIONS.md:170 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 5 |
| Q31 item 3 | QUESTIONS.md:170 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 11 |
| Q31 item 3 | QUESTIONS.md:170 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 14 |
| Q31 item 3 | QUESTIONS.md:170 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 14 |
| Q31 item 3 | QUESTIONS.md:170 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 11 |
| Q25 item 11 | QUESTIONS.md:171 | 11. [ANSWERED, lead action pending (the lead fills in the facts)] Facts only the lead has, all left as "lead f | MATCH | item at QUESTIONS.md:332; shared words: 1 |
| Q31 item 9 | QUESTIONS.md:171 | 9. [OPEN] CHAT AND DEADLINE (ownersteps7 item 9; ownersteps8 item 1): which chat (app and name) carries the le | MATCH | item at QUESTIONS.md:412; shared words: 2 |
| Q31 item 8 | QUESTIONS.md:173 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 6 |
| Q31 item 3 | QUESTIONS.md:174 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 12 |
| Q25 item 1 | QUESTIONS.md:174 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 3 |
| Q31 item 8 | QUESTIONS.md:175 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 10 |
| Q31 item 5 | QUESTIONS.md:175 | 5. [OPEN] NUMBER OF DELETE MESSAGES (ownersteps7 item 5): the total depends on which runs go through the real  | MATCH | item at QUESTIONS.md:408; shared words: 7 |
| Q24 item 3 | QUESTIONS.md:176 | 3. DESK_ALERT_TO: the files show the unfilled real-v5 has 3 $env reads (DESK_ALERT_TO, DESK_URL, DESK_TIMEOUT_ | MATCH | item at QUESTIONS.md:315; shared words: 1 |
| Q29 item 4 | QUESTIONS.md:177 | 4. [ANSWERED, lead action pending (the lead puts the scripts on a branch; the audit reviews read-only, with a  | MATCH | item at QUESTIONS.md:372; shared words: 1 |
| Q25 item 6 | QUESTIONS.md:179 | 6. [ANSWERED] Re-pin versus re-check (sweep3 Q-6): is re-pin only the move to the new core commit, or also the | MATCH | item at QUESTIONS.md:327; shared words: 4 |
| Q31 item 9 | QUESTIONS.md:179 | 9. [OPEN] CHAT AND DEADLINE (ownersteps7 item 9; ownersteps8 item 1): which chat (app and name) carries the le | MATCH | item at QUESTIONS.md:412; shared words: 5 |
| Q31 item 8 | QUESTIONS.md:180 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 5 |
| Q31 item 3 | QUESTIONS.md:181 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 9 |
| Q31 item 15 | QUESTIONS.md:182 | 15. [OPEN] NAMED WARN READER FOR THE PIN (the audit's own; not from ORDER 037, whose item 2 is the ruff format | MATCH | item at QUESTIONS.md:418; shared words: 15 |
| Q25 item 10 | QUESTIONS.md:186 | 10. [PARTLY SUPERSEDED (ORDER 037 item 3, ORDERS.md line 177: the sentence "The rehearsal does NOT go into rea | MATCH | item at QUESTIONS.md:331; shared words: 9 |
| Q25 item 10 | QUESTIONS.md:187 | 10. [PARTLY SUPERSEDED (ORDER 037 item 3, ORDERS.md line 177: the sentence "The rehearsal does NOT go into rea | MATCH | item at QUESTIONS.md:331; shared words: 4 |
| Q22a item 3 | QUESTIONS.md:187 | 3. [ANSWERED, lead action pending (L33: the lead does the check as the last step before the take)] Last check  | MATCH | item at QUESTIONS.md:292; shared words: 5 |
| Q26 item 1 | QUESTIONS.md:187 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 7 |
| Q31 item 3 | QUESTIONS.md:187 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 7 |
| Q19 item 1 | QUESTIONS.md:195 | Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentenc | MATCH | item at ORDERS.md answer to Q19; shared words: 3 |
| Q21 item 2 | QUESTIONS.md:195 | 2. Saved runs. Q19-1 says the video does not say they are deleted and the take never deletes. Who removes them | MATCH | item at QUESTIONS.md:283; shared words: 9 |
| Q25 item 2 | QUESTIONS.md:213 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 2 |
| Q28 item 1 | QUESTIONS.md:213 | 1. [ANSWERED] RWQ-8 (RUNSHEET-WORDING.md section 4): should the scoped caption (A-016f) say where the one mess | MATCH | item at QUESTIONS.md:361; shared words: 3 |
| Q26 item 5 | QUESTIONS.md:221 | 5. [ANSWERED] Should Row 4 (one made-up lead through the real HubSpot trial) be the first thing done, since it | MATCH | item at QUESTIONS.md:343; shared words: 2 |
| Q25 item 2 | QUESTIONS.md:240 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 6 |
| Q31 item 3 | QUESTIONS.md:246 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 3 |
| Q25 item 1 | QUESTIONS.md:247 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 0; read by hand |
| Q28 item 3 | QUESTIONS.md:247 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 0; read by hand |
| Q25 item 1 | QUESTIONS.md:253 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 5 |
| Q28 item 3 | QUESTIONS.md:253 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 1 |
| Q31 item 3 | QUESTIONS.md:253 | 3. [OPEN] CEILING AND SENDS (ownersteps7 item 3; ownersteps8 item 7): the ceiling for the sends, in US dollars | MATCH | item at QUESTIONS.md:406; shared words: 9 |
| Q25 item 2 | QUESTIONS.md:260 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 1 |
| Q25 item 2 | QUESTIONS.md:262 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 5 |
| Q25 item 2 | QUESTIONS.md:264 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 7 |
| Q27 item 9 | QUESTIONS.md:280 | 9. [ANSWERED, lead action pending (F-011 and F-041 must be fixed or downgraded with evidence before Tue 17 Nov | MATCH | item at QUESTIONS.md:355; shared words: 7 |
| Q25 item 1 | QUESTIONS.md:284 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 1 |
| Q28 item 3 | QUESTIONS.md:284 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 1 |
| Q25 item 12 | QUESTIONS.md:288 | 12. [ANSWERED, lead action pending (the lead sets the cut time after the rehearsal measures it)] Stopwatch and | MATCH | item at QUESTIONS.md:333; shared words: 10 |
| Q31 item 13 | QUESTIONS.md:288 | 13. [OPEN] WHO TIMES THE 3-MINUTE TAKEOVER (the audit's own): Q22a said the owner's phone; Q25 item 12 says no | MATCH | item at QUESTIONS.md:416; shared words: 6 |
| Q25 item 12 | QUESTIONS.md:288 | 12. [ANSWERED, lead action pending (the lead sets the cut time after the rehearsal measures it)] Stopwatch and | MATCH | item at QUESTIONS.md:333; shared words: 11 |
| Q25 item 3 | QUESTIONS.md:288 | 3. [ANSWERED, lead action pending (the lead sets the wait and the expected attempts value at the rehearsal)] T | MATCH | item at QUESTIONS.md:324; shared words: 7 |
| Q26 item 1 | QUESTIONS.md:288 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 1 |
| Q25 item 12 | QUESTIONS.md:290 | 12. [ANSWERED, lead action pending (the lead sets the cut time after the rehearsal measures it)] Stopwatch and | MATCH | item at QUESTIONS.md:333; shared words: 7 |
| Q25 item 3 | QUESTIONS.md:293 | 3. [ANSWERED, lead action pending (the lead sets the wait and the expected attempts value at the rehearsal)] T | MATCH | item at QUESTIONS.md:324; shared words: 10 |
| Q20 item 4 | QUESTIONS.md:302 | Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentenc | MATCH | item at ORDERS.md answer to Q20; shared words: 6 |
| Q27 item 6 | QUESTIONS.md:311 | 6. [ANSWERED] A real latest re-pin time on the NO-GO path, working back from Mon 23 Nov 18:29Z by practice run | MATCH | item at QUESTIONS.md:352; shared words: 4 |
| Q26 item 1 | QUESTIONS.md:311 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 4 |
| Q25 item 3 | QUESTIONS.md:311 | 3. [ANSWERED, lead action pending (the lead sets the wait and the expected attempts value at the rehearsal)] T | MATCH | item at QUESTIONS.md:324; shared words: 2 |
| Q25 item 2 | QUESTIONS.md:311 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 2 |
| Q28 item 1 | QUESTIONS.md:311 | 1. [ANSWERED] RWQ-8 (RUNSHEET-WORDING.md section 4): should the scoped caption (A-016f) say where the one mess | MATCH | item at QUESTIONS.md:361; shared words: 2 |
| Q20 item 4 | QUESTIONS.md:315 | Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentenc | MATCH | item at ORDERS.md answer to Q20; shared words: 6 |
| Q28 item 1 | QUESTIONS.md:323 | 1. [ANSWERED] RWQ-8 (RUNSHEET-WORDING.md section 4): should the scoped caption (A-016f) say where the one mess | MATCH | item at QUESTIONS.md:361; shared words: 4 |
| Q28 item 3 | QUESTIONS.md:328 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 2 |
| Q28 item 4 | QUESTIONS.md:328 | 4. [ANSWERED] Q27 item 10 says the owner types y, the challenge and end on camera (decision 7) and does S9-2 a | MATCH | item at QUESTIONS.md:364; shared words: 3 |
| Q27 item 8 | QUESTIONS.md:329 | 8. [ANSWERED (same answer as Q25 item 8)] Q25 item 8: the decision number for 'recovery is not part of the tak | MATCH | item at QUESTIONS.md:354; shared words: 5 |
| Q17 item 5 | QUESTIONS.md:331 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 5 |
| Q17 item 5 | QUESTIONS.md:331 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 6 |
| Q31 item 5 | QUESTIONS.md:331 | 5. [OPEN] NUMBER OF DELETE MESSAGES (ownersteps7 item 5): the total depends on which runs go through the real  | MATCH | item at QUESTIONS.md:408; shared words: 12 |
| Q24 item 1 | QUESTIONS.md:339 | 1. Date X: no re-pin time written by date X means the take is postponed. Date X: lead to set. I did not invent | MATCH | item at QUESTIONS.md:313; shared words: 1 |
| Q30 item 1 | QUESTIONS.md:339 | 1. [ANSWERED] F-002 check is "Wed 07:30Z" but the rehearsal starts about 07:30Z after practice run (1 h) and R | MATCH | item at QUESTIONS.md:376; shared words: 2 |
| Q25 item 8 | QUESTIONS.md:354 | 8. [ANSWERED (by Q27 item 8, ORDERS.md line 156: decision 1, "and 4" dropped)] Decision number for "recovery i | MATCH | item at QUESTIONS.md:329; shared words: 5 |
| Q25 item 8 | QUESTIONS.md:354 | 8. [ANSWERED (by Q27 item 8, ORDERS.md line 156: decision 1, "and 4" dropped)] Decision number for "recovery i | MATCH | item at QUESTIONS.md:329; shared words: 5 |
| Q31 item 10 | QUESTIONS.md:355 | 10. [OPEN] GATE ACTOR (the audit's own; see the GATE): who must make F-011 and F-041 fixed or downgraded with  | MATCH | item at QUESTIONS.md:413; shared words: 8 |
| Q28 item 3 | QUESTIONS.md:356 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 2 |
| Q28 item 4 | QUESTIONS.md:356 | 4. [ANSWERED] Q27 item 10 says the owner types y, the challenge and end on camera (decision 7) and does S9-2 a | MATCH | item at QUESTIONS.md:364; shared words: 5 |
| Q25 item 7 | QUESTIONS.md:356 | 7. [PARTLY SUPERSEDED (answered; Step A is removed (Q28 item 3) and the current owner list is in Q28 item 4; t | MATCH | item at QUESTIONS.md:328; shared words: 0; read by hand |
| Q28 item 3 | QUESTIONS.md:356 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 1 |
| Q25 item 2 | QUESTIONS.md:360 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 7 |
| Q28 item 1 | QUESTIONS.md:360 | 1. [ANSWERED] RWQ-8 (RUNSHEET-WORDING.md section 4): should the scoped caption (A-016f) say where the one mess | MATCH | item at QUESTIONS.md:361; shared words: 5 |
| Q25 item 7 | QUESTIONS.md:363 | 7. [PARTLY SUPERSEDED (answered; Step A is removed (Q28 item 3) and the current owner list is in Q28 item 4; t | MATCH | item at QUESTIONS.md:328; shared words: 3 |
| Q27 item 10 | QUESTIONS.md:363 | 10. [PARTLY SUPERSEDED (answered; by Q28 items 3 and 4: Step A is removed)] (same check) The decisions file sa | MATCH | item at QUESTIONS.md:356; shared words: 2 |
| Q27 item 10 | QUESTIONS.md:364 | 10. [PARTLY SUPERSEDED (answered; by Q28 items 3 and 4: Step A is removed)] (same check) The decisions file sa | MATCH | item at QUESTIONS.md:356; shared words: 5 |
| Q25 item 7 | QUESTIONS.md:364 | 7. [PARTLY SUPERSEDED (answered; Step A is removed (Q28 item 3) and the current owner list is in Q28 item 4; t | MATCH | item at QUESTIONS.md:328; shared words: 4 |
| Q25 item 1 | QUESTIONS.md:404 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 2 |
| Q25 item 10 | QUESTIONS.md:406 | 10. [PARTLY SUPERSEDED (ORDER 037 item 3, ORDERS.md line 177: the sentence "The rehearsal does NOT go into rea | MATCH | item at QUESTIONS.md:331; shared words: 11 |
| Q25 item 1 | QUESTIONS.md:406 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 2 |
| Q28 item 3 | QUESTIONS.md:406 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 0; read by hand |
| Q17 item 5 | QUESTIONS.md:406 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 6 |
| Q17 item 5 | QUESTIONS.md:406 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 4 |
| Q25 item 1 | QUESTIONS.md:406 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 7 |
| Q28 item 3 | QUESTIONS.md:406 | 3. [ANSWERED] Step A: Q25 item 7 removed it (owner steps = Step D only); Q27 item 10 says "Step A (if kept)".  | MATCH | item at QUESTIONS.md:363; shared words: 2 |
| Q25 item 1 | QUESTIONS.md:406 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 3 |
| Q21 item 3 | QUESTIONS.md:406 | 3. Also open with no number: whether F-011 and F-041 stay Major BEFORE or are Nit AFTER (FINDINGS counts), the | MATCH | item at QUESTIONS.md:284; shared words: 0; read by hand |
| Q25 item 1 | QUESTIONS.md:406 | 1. [ANSWERED, lead action pending (the lead states the ceiling for up to 3 sends from the ledger at take prep) | MATCH | item at QUESTIONS.md:322; shared words: 1 |
| Q21 item 3 | QUESTIONS.md:406 | 3. Also open with no number: whether F-011 and F-041 stay Major BEFORE or are Nit AFTER (FINDINGS counts), the | MATCH | item at QUESTIONS.md:284; shared words: 0; read by hand |
| Q25 item 6 | QUESTIONS.md:409 | 6. [ANSWERED] Re-pin versus re-check (sweep3 Q-6): is re-pin only the move to the new core commit, or also the | MATCH | item at QUESTIONS.md:327; shared words: 4 |
| Q27 item 6 | QUESTIONS.md:409 | 6. [ANSWERED] A real latest re-pin time on the NO-GO path, working back from Mon 23 Nov 18:29Z by practice run | MATCH | item at QUESTIONS.md:352; shared words: 3 |
| Q29 item 3 | QUESTIONS.md:411 | 3. [ANSWERED] Fallback if T19/T20 fail on the patched copy: confirm whether the take is NO-GO (my reading of Q | MATCH | item at QUESTIONS.md:371; shared words: 2 |
| Q25 item 11 | QUESTIONS.md:412 | 11. [ANSWERED, lead action pending (the lead fills in the facts)] Facts only the lead has, all left as "lead f | MATCH | item at QUESTIONS.md:332; shared words: 3 |
| Q30 item 2 | QUESTIONS.md:414 | 2. [ANSWERED, lead action pending (apply the caption and sheet text of F-031 and F-007 and re-read by Wed 18 N | MATCH | item at QUESTIONS.md:377; shared words: 4 |
| Q25 item 12 | QUESTIONS.md:416 | 12. [ANSWERED, lead action pending (the lead sets the cut time after the rehearsal measures it)] Stopwatch and | MATCH | item at QUESTIONS.md:333; shared words: 7 |
| Q25 item 12 | QUESTIONS.md:416 | 12. [ANSWERED, lead action pending (the lead sets the cut time after the rehearsal measures it)] Stopwatch and | MATCH | item at QUESTIONS.md:333; shared words: 6 |
| Q24 item 3 | QUESTIONS.md:417 | 3. DESK_ALERT_TO: the files show the unfilled real-v5 has 3 $env reads (DESK_ALERT_TO, DESK_URL, DESK_TIMEOUT_ | MATCH | item at QUESTIONS.md:315; shared words: 9 |
| Q27 item 9 | QUESTIONS.md:421 | 9. [ANSWERED, lead action pending (F-011 and F-041 must be fixed or downgraded with evidence before Tue 17 Nov | MATCH | item at QUESTIONS.md:355; shared words: 5 |
| Q29 item 3 | QUESTIONS.md:423 | 3. [ANSWERED] Fallback if T19/T20 fail on the patched copy: confirm whether the take is NO-GO (my reading of Q | MATCH | item at QUESTIONS.md:371; shared words: 2 |
| Q31 item 8 | QUESTIONS.md:427 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 10 |
| Q31 item 8 | QUESTIONS.md:427 | 8. [OPEN] TAKE PREP AND AUDIT-PLANNED TIMES (ownersteps7 item 8; ownersteps8 item 8): first, define "take prep | MATCH | item at QUESTIONS.md:411; shared words: 9 |
| Q31 item 6 | QUESTIONS.md:427 | 6. [OPEN] GO/NO-GO MESSAGE (ownersteps7 item 6; ownersteps8 items 2 and 3): does the lead send the owner a mes | MATCH | item at QUESTIONS.md:409; shared words: 4 |
| Q27 item 2 | QUESTIONS.md:434 | 2. [ANSWERED, lead action pending (the lead asks the owner once, at take prep, for the HubSpot token scopes; a | MATCH | item at QUESTIONS.md:348; shared words: 1 |
| Q26 item 4 | QUESTIONS.md:435 | 4. [ANSWERED] Scene 4 (kill and takeover) in or out? Lead: keep scenes 1-4 and film scene 4 only if the rehear | MATCH | item at QUESTIONS.md:342; shared words: 4 |
| Q19 item 1 | QUESTIONS.md:440 | Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentenc | MATCH | item at ORDERS.md answer to Q19; shared words: 3 |
| Q25 item 2 | QUESTIONS.md:444 | 2. [ANSWERED, lead action pending (the lead applies the caption at re-pin; Q28 item 1 adds the words "in the i | MATCH | item at QUESTIONS.md:323; shared words: 4 |
| Q19 item 2 | QUESTIONS.md:447 | Q19: 1 a) do NOT say the saved runs are deleted (the take never deletes; no owner step for it). 2 your sentenc | MATCH | item at ORDERS.md answer to Q19; shared words: 3 |
| Q21 item 3 | QUESTIONS.md:448 | 3. Also open with no number: whether F-011 and F-041 stay Major BEFORE or are Nit AFTER (FINDINGS counts), the | MATCH | item at QUESTIONS.md:284; shared words: 2 |
| Q22a item 1 | QUESTIONS.md:449 | 1. [ANSWERED] Who stops n8n and who starts the stopwatch in scene 4 (Q-A, Q-B), and the fallback if the stop m | MATCH | item at QUESTIONS.md:290; shared words: 2 |
| Q22a item 4 | QUESTIONS.md:450 | 4. [ANSWERED] Proof for "processed once" in the edit: mailbox exactly 1 mail + the mf_leads row + the POST 2 r | MATCH | item at QUESTIONS.md:293; shared words: 6 |
| Q24 item 1 | QUESTIONS.md:451 | 1. Date X: no re-pin time written by date X means the take is postponed. Date X: lead to set. I did not invent | MATCH | item at QUESTIONS.md:313; shared words: 1 |
| Q24 item 2 | QUESTIONS.md:452 | 2. The 45 s lease threshold N (the rehearsal step time above which recovery is off for the take) and the 'unde | MATCH | item at QUESTIONS.md:314; shared words: 3 |
| Q24 item 5 | QUESTIONS.md:453 | 5. The caption owner must change RUNSHEET-WORDING A-016f to 'one mail sent, one row in state done' (this fixer | MATCH | item at QUESTIONS.md:317; shared words: 1 |
| Q25 item 8 | QUESTIONS.md:455 | 8. [ANSWERED (by Q27 item 8, ORDERS.md line 156: decision 1, "and 4" dropped)] Decision number for "recovery i | MATCH | item at QUESTIONS.md:329; shared words: 6 |
| Q26 item 1 | QUESTIONS.md:480 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 11 |
| Q26 item 1 | QUESTIONS.md:481 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 5 |
| Q25 item 10 | QUESTIONS.md:483 | 10. [PARTLY SUPERSEDED (ORDER 037 item 3, ORDERS.md line 177: the sentence "The rehearsal does NOT go into rea | MATCH | item at QUESTIONS.md:331; shared words: 3 |
| Q17 item 5 | QUESTIONS.md:483 | 5. [ANSWERED, lead action pending: YES; the lead asks the owner for a written yes with numbers before Row 4. C | MATCH | item at QUESTIONS.md:253; shared words: 6 |
| Q26 item 1 | RUNBOOK.md:14 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 4 |
| Q27 item 6 | RUNBOOK.md:14 | 6. [ANSWERED] A real latest re-pin time on the NO-GO path, working back from Mon 23 Nov 18:29Z by practice run | MATCH | item at QUESTIONS.md:352; shared words: 1 |
| Q27 item 9 | RUNBOOK.md:14 | 9. [ANSWERED, lead action pending (F-011 and F-041 must be fixed or downgraded with evidence before Tue 17 Nov | MATCH | item at QUESTIONS.md:355; shared words: 5 |
| Q26 item 1 | RUNBOOK.md:60 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 5 |
| Q26 item 1 | RUNBOOK.md:211 | 1. [ANSWERED] DEADLINE VERSUS OUR OWN DATES (failure, stated first): the video is due Wed 18 Nov (owner hard r | MATCH | item at QUESTIONS.md:339; shared words: 3 |

### D file:line: 47

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| FINDINGS.md:114 (F-008) | QUESTIONS.md:114 | / F-008 / Major / ops / take / | MATCH |  |
| FINDINGS.md:115 (F-011) | QUESTIONS.md:115 | / F-011 / Major / security / t | MATCH |  |
| FINDINGS.md:65 | QUESTIONS.md:121 | ## Verdict per part of the build (ORDER 007 item 4; static reading; full text and evidence | MATCH | heading of the verdict section that holds the claim (table rows start at line 70) |
| FINDINGS.md:115 (F-011) | QUESTIONS.md:203 | / F-011 / Major / security / t | MATCH |  |
| FINDINGS.md:115 (F-011) | QUESTIONS.md:279 | / F-011 / Major / security / t | MATCH |  |
| CLAIMS-TABLE.md:112 | QUESTIONS.md:105 | - Test and kill labels (the names used by mf.py, the test runner in the demo folder; mf.py:151-164): | MATCH |  |
| CLAIMS-TABLE.md:73 | QUESTIONS.md:115 | - n8n runs on its own database today (a small SQLite file). This rests on one earlier smoke run (a f | MATCH |  |
| CLAIMS-TABLE.md:45 | QUESTIONS.md:125 | - **P checks** (P1, P2, P4a, P4b, P4c) = five checks run on made-up lead records (listed under "Chec | MATCH |  |
| CLAIMS-TABLE.md:45 | QUESTIONS.md:148 | - **P checks** (P1, P2, P4a, P4b, P4c) = five checks run on made-up lead records (listed under "Chec | MATCH |  |
| CLAIMS-TABLE.md:117 | QUESTIONS.md:145 | - More labels: `id` and `vid` = the two field names in which HubSpot may send back a contact's numbe | MATCH |  |
| CLAIMS-TABLE.md:114 | QUESTIONS.md:154 | - Parts of the system: "desk" = the studio's earlier lead-desk program (its public repository is not | MATCH |  |
| CLAIMS-TABLE.md:114 | QUESTIONS.md:162 | - Parts of the system: "desk" = the studio's earlier lead-desk program (its public repository is not | MATCH |  |
| CLAIMS-TABLE.md:114 | QUESTIONS.md:417 | - Parts of the system: "desk" = the studio's earlier lead-desk program (its public repository is not | MATCH |  |
| CLAIMS-TABLE.md:199 row 6 | QUESTIONS.md:261 | / 6 / VIDEO-RUNSHEET.md / VIDEO-RUNSHEET.md:30 (scene 1, run list) / A-007 (was 6) / "the execution  | MATCH |  |
| CLAIMS-TABLE.md:209 row 16 | QUESTIONS.md:261 | / 16 / VIDEO-RUNSHEET.md / VIDEO-RUNSHEET.md:41 (line 5) / A-053 (was 16) / "retention: the request  | MATCH |  |
| CLAIMS-TABLE.md:217 row 24 | QUESTIONS.md:261 | / 24 / PAGE-STATEMENTS-V4.md / PAGE-STATEMENTS-V4.md:33 (statement 1) / A-057 (was 24) / "A lead who | MATCH |  |
| CLAIMS-TABLE.md:220 row 27 | QUESTIONS.md:261 | / 27 / PAGE-STATEMENTS-V4.md / PAGE-STATEMENTS-V4.md:149 (statement 20) / A-076 (was 26) / "At the f | MATCH |  |
| CLAIMS-TABLE.md:223 row 30 | QUESTIONS.md:261 | / 30 / DOUBTFUL-SCENE.md / DOUBTFUL-SCENE.md:12 / B-077 (was 29) / "The owner gets ONE alert e-mail" | MATCH |  |
| CLAIMS-TABLE.md:267 row 62 | QUESTIONS.md:261 | / 62 / DESIGN-A-README.md / DESIGN-A-README.md:15 and :32 / B-150 (was 51) / "state unknown + one al | MATCH |  |
| CLAIMS-TABLE.md:276 row 71 | QUESTIONS.md:261 | / 71 / V5-README.md / V5-README.md:4 (same line in the real-v5 and film-v5 copies) / B-173 (was 60)  | MATCH |  |
| CLAIMS-TABLE.md:234 row 78 | QUESTIONS.md:261 | / 78 / VIDEO-RUNSHEET.md / VIDEO-RUNSHEET.md: before scene 1 (new sentence) / (no claim id: lead ans | MATCH |  |
| RUNSHEET-WORDING.md:217 (A-007) | QUESTIONS.md:261 | / A-007 / R:30 / "the execution list on screen (status and time columns)" / "n8n lists the runs it s | MATCH |  |
| RUNSHEET-WORDING.md:255 (A-053) | QUESTIONS.md:230 | / A-053 / R:41 line 5 / "Line 5, retention: the request body, with the made-up name and address, sta | MATCH |  |
| RUNSHEET-WORDING.md:255 (A-053) | QUESTIONS.md:261 | / A-053 / R:41 line 5 / "Line 5, retention: the request body, with the made-up name and address, sta | MATCH |  |
| RUNSHEET-WORDING.md:45 (A-057) | QUESTIONS.md:230 | / A-057 / HELD (lead, after the studio owner runs the psql check) / waits for: the check lists the 4 | MATCH |  |
| RUNSHEET-WORDING.md:45 (A-057) | QUESTIONS.md:261 | / A-057 / HELD (lead, after the studio owner runs the psql check) / waits for: the check lists the 4 | MATCH |  |
| RUNSHEET-WORDING.md:258 (N-3) | QUESTIONS.md:230 | / N-3 (new) / R:41 line 6 / (no sentence today) / NO PASTE / CARD line 6, second part / CUT for the  | MATCH |  |
| RUNSHEET-WORDING.md:258 (N-3) | QUESTIONS.md:261 | / N-3 (new) / R:41 line 6 / (no sentence today) / NO PASTE / CARD line 6, second part / CUT for the  | MATCH |  |
| RUNSHEET-WORDING.md:190 (rule 7) | QUESTIONS.md:230 | 7. Numbers rule (W-18): a recovery number is quoted only for one stop point at a time, with its numb | MATCH |  |
| RUNSHEET-WORDING.md:190 (rule 7) | QUESTIONS.md:261 | 7. Numbers rule (W-18): a recovery number is quoted only for one stop point at a time, with its numb | MATCH |  |
| EXCEPTIONS.md:4 (up to 3 live calls) | QUESTIONS.md:284 | / stage call record: (a) the stage journal, one file named stage.journal in the take folder (the tes | MATCH |  |
| fill_flows/README.md line 240 | QUESTIONS.md:334 | 3. In n8n: remove the imported workflows and the saved executions (executions can hold the values). | MATCH |  |
| fill_flows/README.md line 240 | RUNBOOK.md:5 | 3. In n8n: remove the imported workflows and the saved executions (executions can hold the values). | MATCH |  |
| fill_flows/README.md line 240 | RUNBOOK.md:64 | 3. In n8n: remove the imported workflows and the saved executions (executions can hold the values). | MATCH |  |
| fill_flows/README.md line 240 | RUNBOOK.md:93 | 3. In n8n: remove the imported workflows and the saved executions (executions can hold the values). | MATCH |  |
| fill_flows/README.md line 240 | RUNBOOK.md:167 | 3. In n8n: remove the imported workflows and the saved executions (executions can hold the values). | MATCH |  |
| fill_flows/README.md line 240 | RUNBOOK.md:204 | 3. In n8n: remove the imported workflows and the saved executions (executions can hold the values). | MATCH |  |
| QUEUE.md:8 (stale one-database text) | QUESTIONS.md:75 | 6. Inputs copied for you (read-only, made-up data): handover/flows-audit/inputs/. Decisions in force | MATCH |  |
| QUEUE.md:8 (stale one-database text) | QUESTIONS.md:335 | 6. Inputs copied for you (read-only, made-up data): handover/flows-audit/inputs/. Decisions in force | MATCH |  |
| QUEUE.md:8 (stale one-database text) | RUNBOOK.md:210 | 6. Inputs copied for you (read-only, made-up data): handover/flows-audit/inputs/. Decisions in force | MATCH |  |
| PLAN-4-NLITE-FROM-LEAD.md:106 (up to 3 model calls) | QUESTIONS.md:198 | 4. The notice (3 made-up people, up to 3 HubSpot contacts archived at the end, up to 3 mails, up to  | MATCH |  |
| PLAN-4-NLITE-FROM-LEAD.md:106 (up to 3 model calls) | RUNBOOK.md:210 | 4. The notice (3 made-up people, up to 3 HubSpot contacts archived at the end, up to 3 mails, up to  | MATCH |  |
| SCENE-FLOW-MAP:40 | QUESTIONS.md:236 | / 4 Kill n8n, recovery finishes / real-v5 / mf-form.json (the kill lands inside "RunSub"), mf-recove | MATCH |  |
| SCENE-FLOW-MAP:68 | QUESTIONS.md:236 | - C3 (scene 4 figure): scene 4 runs on real-v5, but the only 45 s number (K1) came from older film-v | MATCH | line 68 names the K1 45 s figure and the A-017 caption; the digits 60.8 sit on line 40 only |
| inputs/DECISION-one-store.md lines 7 | QUESTIONS.md:334 | / Postgres table `mf_leads` (written by the n8n Postgres nodes Claim, Stored, SetCrmId, MailClaim, M | MATCH |  |
| n8n-flows-real-v5/mf-recovery.json:178 | QUESTIONS.md:270 | "toEmail": "={{ $env.DESK_ALERT_TO }}", | MATCH | the demo folder copy of the real-v5 flow |
| n8n-flows-real-v5/mf-recovery.json:178 | QUESTIONS.md:275 | "toEmail": "={{ $env.DESK_ALERT_TO }}", | MATCH | the demo folder copy of the real-v5 flow |

### E time: 540

| cite | where found | what the cited line says (first 120 chars) | verdict | note |
|---|---|---|---|---|
| Tue 17 Nov | QUESTIONS.md:42 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:42 | Nov 17 2026 is a Tue | MATCH |  |
| 07:00Z = 12:30 IST | QUESTIONS.md:42 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:42 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:49 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:49 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:50 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:50 | Nov 17 2026 is a Tue | MATCH |  |
| 06:15Z (11:45 IST | QUESTIONS.md:50 | 06:15Z + 5:30 = 11:45 IST | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:50 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:57 | Nov 17 2026 is a Tue | MATCH |  |
| 09:30Z (15:00 IST | QUESTIONS.md:57 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:58 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:58 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:59 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:59 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:60 | Nov 18 2026 is a Wed | MATCH |  |
| 05:30Z = 11:00 IST | QUESTIONS.md:60 | 05:30Z + 5:30 = 11:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:61 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:61 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:61 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:61 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:61 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:61 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:61 | Nov 18 2026 is a Wed | MATCH |  |
| 06:45Z = 12:15 IST | QUESTIONS.md:61 | 06:45Z + 5:30 = 12:15 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:61 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 15:00Z (20:30 IST | QUESTIONS.md:61 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:61 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 16:00Z (21:30 IST | QUESTIONS.md:61 | 16:00Z + 5:30 = 21:30 IST | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:61 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:62 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:62 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:63 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:63 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:63 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:63 | Nov 17 2026 is a Tue | MATCH |  |
| 05:30Z = 11:00 IST | QUESTIONS.md:63 | 05:30Z + 5:30 = 11:00 IST | MATCH |  |
| 08:00Z = 13:30 IST | QUESTIONS.md:63 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:64 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:64 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:65 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:65 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:67 | Nov 18 2026 is a Wed | MATCH |  |
| 07:35Z = 13:05 IST | QUESTIONS.md:67 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 10:00Z = 15:30 IST | QUESTIONS.md:67 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:68 | Nov 18 2026 is a Wed | MATCH |  |
| 07:00Z = 12:30 IST | QUESTIONS.md:68 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:69 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:69 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:70 | Nov 18 2026 is a Wed | MATCH |  |
| 05:30Z = 11:00 IST | QUESTIONS.md:70 | 05:30Z + 5:30 = 11:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:71 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:71 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:74 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:74 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:76 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:76 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:78 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:78 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:78 | Nov 17 2026 is a Tue | MATCH |  |
| 05:54Z = 11:24 IST | QUESTIONS.md:78 | 05:54Z + 5:30 = 11:24 IST | MATCH |  |
| 05:54Z (11:24 IST | QUESTIONS.md:78 | 05:54Z + 5:30 = 11:24 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:79 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:79 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:80 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:80 | Nov 17 2026 is a Tue | MATCH |  |
| 07:00Z = 12:30 IST | QUESTIONS.md:80 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:80 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:81 | Nov 18 2026 is a Wed | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:81 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:82 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:82 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:84 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:84 | Nov 18 2026 is a Wed | MATCH |  |
| 07:00Z = 12:30 IST | QUESTIONS.md:84 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:84 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:85 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:85 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:85 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 07:00Z = 12:30 IST | QUESTIONS.md:85 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:86 | Nov 18 2026 is a Wed | MATCH |  |
| 07:35Z = 13:05 IST | QUESTIONS.md:86 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:87 | Nov 18 2026 is a Wed | MATCH |  |
| 07:35Z = 13:05 IST | QUESTIONS.md:87 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 10:00Z = 15:30 IST | QUESTIONS.md:87 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:88 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:88 | Nov 18 2026 is a Wed | MATCH |  |
| 12:00Z (17:30 IST | QUESTIONS.md:88 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 09:30Z (15:00 IST | QUESTIONS.md:88 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:88 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:89 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:89 | Nov 23 2026 is a Mon | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:89 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| 12:00Z (17:30 IST | QUESTIONS.md:89 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 09:30Z to 10:00Z (15:00 to 15:30 IST) | QUESTIONS.md:89 | 15:00 to 15:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:91 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:91 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:91 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:91 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:112 | Nov 17 2026 is a Tue | MATCH |  |
| 16:00Z (21:30 IST | QUESTIONS.md:112 | 16:00Z + 5:30 = 21:30 IST | MATCH |  |
| 12:30Z (18:00 IST | QUESTIONS.md:112 | 12:30Z + 5:30 = 18:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:130 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:130 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:132 | Nov 18 2026 is a Wed | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:132 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:132 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:132 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 07:35Z (13:05 IST | QUESTIONS.md:132 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 09:30Z (15:00 IST | QUESTIONS.md:132 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:133 | Nov 18 2026 is a Wed | MATCH |  |
| 07:35Z (13:05 IST | QUESTIONS.md:133 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:139 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:139 | Nov 23 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:139 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:139 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:139 | Nov 18 2026 is a Wed | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:139 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 12:00Z (17:30 IST | QUESTIONS.md:139 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 16:00Z (21:30 IST | QUESTIONS.md:139 | 16:00Z + 5:30 = 21:30 IST | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:159 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:159 | Nov 23 2026 is a Mon | MATCH |  |
| 18:29Z (23:59 IST | QUESTIONS.md:159 | 18:29Z + 5:30 = 23:59 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:161 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:161 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:161 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:161 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:161 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:161 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:161 | Nov 17 2026 is a Tue | MATCH |  |
| 06:00Z = 11:30 IST | QUESTIONS.md:161 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 07:00Z = 12:30 IST | QUESTIONS.md:161 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 05:30Z = 11:00 IST | QUESTIONS.md:161 | 05:30Z + 5:30 = 11:00 IST | MATCH |  |
| 07:00Z = 12:30 IST | QUESTIONS.md:161 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:161 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:169 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:169 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:169 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:179 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:179 | Nov 18 2026 is a Wed | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:179 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:179 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:180 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:180 | Nov 18 2026 is a Wed | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:180 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 08:30Z (14:00 IST | QUESTIONS.md:180 | 08:30Z + 5:30 = 14:00 IST | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:184 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:204 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:224 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:288 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z = 13:30 IST | QUESTIONS.md:288 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:292 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:311 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:311 | Nov 23 2026 is a Mon | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:311 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:311 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:339 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:339 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:339 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:339 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:339 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:339 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:339 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:339 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 25 Nov | QUESTIONS.md:339 | Nov 25 2026 is a Wed | MATCH |  |
| 04:00Z Tue (09:30 IST | QUESTIONS.md:339 | 04:00Z + 5:30 = 09:30 IST | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:339 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 09:30Z = 15:00 IST | QUESTIONS.md:339 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:339 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:339 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 07:30Z (13:00 IST | QUESTIONS.md:339 | 07:30Z + 5:30 = 13:00 IST | MATCH |  |
| 07:35Z = 13:05 IST | QUESTIONS.md:339 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:339 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| 15:00Z (20:30 IST | QUESTIONS.md:339 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 18:29Z (23:59 IST | QUESTIONS.md:339 | 18:29Z + 5:30 = 23:59 IST | MATCH |  |
| 15:00Z (20:30 IST | QUESTIONS.md:339 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:349 | Nov 18 2026 is a Wed | MATCH |  |
| 15:00Z (20:30 IST | QUESTIONS.md:349 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:352 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:352 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:352 | Nov 23 2026 is a Mon | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:352 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:353 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:353 | Nov 23 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:355 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:355 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:355 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 07:30Z (13:00 IST | QUESTIONS.md:355 | 07:30Z + 5:30 = 13:00 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:374 | Nov 18 2026 is a Wed | MATCH |  |
| 06:00Z = 11:30 IST | QUESTIONS.md:374 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:376 | Nov 18 2026 is a Wed | MATCH |  |
| 06:00Z Wed 18 Nov (11:30 IST | QUESTIONS.md:376 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:376 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 07:30Z (13:00 IST | QUESTIONS.md:376 | 07:30Z + 5:30 = 13:00 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:377 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:379 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:379 | Nov 23 2026 is a Mon | MATCH |  |
| 13:00Z to 15:00Z, and "13:00Z = 18:30 IST | QUESTIONS.md:379 | 13:00Z + 5:30 = 18:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:382 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:382 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:382 | Nov 18 2026 is a Wed | MATCH |  |
| 08:00Z = 13:30 IST | QUESTIONS.md:382 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 14:00Z = 19:30 IST | QUESTIONS.md:382 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 06:00Z = 11:30 IST | QUESTIONS.md:382 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:386 | Nov 16 2026 is a Mon | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:387 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:387 | Nov 17 2026 is a Tue | MATCH |  |
| 21:00Z (02:30 IST | QUESTIONS.md:387 | 21:00Z + 5:30 = 02:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:388 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:389 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:390 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:391 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:392 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:393 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:394 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:394 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:395 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:396 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:397 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:398 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:398 | Nov 17 2026 is a Tue | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:398 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:404 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:404 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:404 | Nov 18 2026 is a Wed | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:404 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 16:00Z (21:30 IST | QUESTIONS.md:404 | 16:00Z + 5:30 = 21:30 IST | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:404 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:405 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:405 | Nov 16 2026 is a Mon | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:405 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 21:00Z (02:30 IST | QUESTIONS.md:405 | 21:00Z + 5:30 = 02:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:406 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:406 | Nov 17 2026 is a Tue | MATCH |  |
| 15:00Z = 20:30 IST | QUESTIONS.md:406 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 12:00Z (17:30 IST | QUESTIONS.md:406 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 13:00Z (18:30 IST | QUESTIONS.md:406 | 13:00Z + 5:30 = 18:30 IST | MATCH |  |
| 06:45Z (12:15 IST | QUESTIONS.md:406 | 06:45Z + 5:30 = 12:15 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:407 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:407 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:407 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:407 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:408 | Nov 17 2026 is a Tue | MATCH |  |
| 11:00Z (16:30 IST | QUESTIONS.md:408 | 11:00Z + 5:30 = 16:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:408 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:409 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:409 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:409 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:409 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:409 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:409 | Nov 23 2026 is a Mon | MATCH |  |
| Sun 22 Nov | QUESTIONS.md:409 | Nov 22 2026 is a Sun | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:409 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 15:00Z (20:30 IST | QUESTIONS.md:409 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 16:00Z (21:30 IST | QUESTIONS.md:409 | 16:00Z + 5:30 = 21:30 IST | MATCH |  |
| 06:50Z (12:20 IST | QUESTIONS.md:409 | 06:50Z + 5:30 = 12:20 IST | MATCH |  |
| 12:00Z (17:30 IST | QUESTIONS.md:409 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 18:29Z (23:59 IST | QUESTIONS.md:409 | 18:29Z + 5:30 = 23:59 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:409 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 12:55Z (18:25 IST | QUESTIONS.md:409 | 12:55Z + 5:30 = 18:25 IST | MATCH |  |
| 12:00Z (17:30 IST | QUESTIONS.md:409 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 11:55Z (17:25 IST | QUESTIONS.md:409 | 11:55Z + 5:30 = 17:25 IST | MATCH |  |
| 15:00Z (20:30 IST | QUESTIONS.md:409 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:410 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:410 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:410 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:410 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Tuesday 17 Nov | QUESTIONS.md:411 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:411 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:411 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:411 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:411 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:411 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:411 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:411 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:411 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:411 | Nov 17 2026 is a Tue | MATCH |  |
| 05:30Z (11:00 IST | QUESTIONS.md:411 | 05:30Z + 5:30 = 11:00 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:411 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 07:35Z (13:05 IST | QUESTIONS.md:411 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 09:30Z (15:00 IST | QUESTIONS.md:411 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| 11:00Z (16:30 IST | QUESTIONS.md:411 | 11:00Z + 5:30 = 16:30 IST | MATCH |  |
| 07:05Z (12:35 IST | QUESTIONS.md:411 | 07:05Z + 5:30 = 12:35 IST | MATCH |  |
| 07:35Z (13:05 IST | QUESTIONS.md:411 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:411 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:412 | Nov 17 2026 is a Tue | MATCH |  |
| 06:30Z (12:00 IST | QUESTIONS.md:412 | 06:30Z + 5:30 = 12:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:413 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:413 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:413 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 06:15Z (11:45 IST | QUESTIONS.md:413 | 06:15Z + 5:30 = 11:45 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:414 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:414 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:414 | Nov 18 2026 is a Wed | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:414 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:414 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:414 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:415 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:415 | Nov 17 2026 is a Tue | MATCH |  |
| 08:00Z = 13:30 IST | QUESTIONS.md:415 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:415 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:416 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:416 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:416 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:416 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 07:35Z (13:05 IST | QUESTIONS.md:416 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 10:00Z (15:30 IST | QUESTIONS.md:416 | 10:00Z + 5:30 = 15:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:417 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:417 | Nov 17 2026 is a Tue | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:417 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 08:00Z (13:30 IST | QUESTIONS.md:417 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:418 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:418 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:418 | Nov 17 2026 is a Tue | MATCH |  |
| 21:00Z = 02:30 IST | QUESTIONS.md:418 | 21:00Z + 5:30 = 02:30 IST | MATCH |  |
| 04:26Z (09:56 IST | QUESTIONS.md:418 | 04:26Z + 5:30 = 09:56 IST | MATCH |  |
| 07:14Z = 12:44 IST | QUESTIONS.md:418 | 07:14Z + 5:30 = 12:44 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:418 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 03:57Z (09:27 IST | QUESTIONS.md:418 | 03:57Z + 5:30 = 09:27 IST | MATCH |  |
| 06:45Z (12:15 IST | QUESTIONS.md:418 | 06:45Z + 5:30 = 12:15 IST | MATCH |  |
| 03:30Z (09:00 IST | QUESTIONS.md:418 | 03:30Z + 5:30 = 09:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:419 | Nov 17 2026 is a Tue | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:419 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:420 | Nov 17 2026 is a Tue | MATCH |  |
| 06:30Z (12:00 IST | QUESTIONS.md:420 | 06:30Z + 5:30 = 12:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:421 | Nov 17 2026 is a Tue | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:421 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:422 | Nov 17 2026 is a Tue | MATCH |  |
| 07:15Z (12:45 IST | QUESTIONS.md:422 | 07:15Z + 5:30 = 12:45 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:424 | Nov 17 2026 is a Tue | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:424 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:425 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:425 | Nov 17 2026 is a Tue | MATCH |  |
| 06:00Z = 11:30 IST | QUESTIONS.md:425 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 06:15Z (11:45 IST | QUESTIONS.md:425 | 06:15Z + 5:30 = 11:45 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:426 | Nov 18 2026 is a Wed | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:426 | Nov 17 2026 is a Tue | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:426 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:426 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:427 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:427 | Nov 23 2026 is a Mon | MATCH |  |
| 07:15Z (12:45 IST | QUESTIONS.md:427 | 07:15Z + 5:30 = 12:45 IST | MATCH |  |
| 07:35Z = 13:05 IST | QUESTIONS.md:427 | 07:35Z + 5:30 = 13:05 IST | MATCH |  |
| 12:00Z = 17:30 IST | QUESTIONS.md:427 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 14:00Z = 19:30 IST | QUESTIONS.md:428 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 16:00Z = 21:30 IST | QUESTIONS.md:428 | 16:00Z + 5:30 = 21:30 IST | MATCH |  |
| 16:00Z (21:30 IST | QUESTIONS.md:428 | 16:00Z + 5:30 = 21:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:429 | Nov 18 2026 is a Wed | MATCH |  |
| 15:00Z (20:30 IST | QUESTIONS.md:429 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 13:00Z = 18:30 IST | QUESTIONS.md:429 | 13:00Z + 5:30 = 18:30 IST | MATCH |  |
| 12:30Z (18:00 IST | QUESTIONS.md:430 | 12:30Z + 5:30 = 18:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:432 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:432 | Nov 17 2026 is a Tue | MATCH |  |
| 08:29Z (13:59 IST | QUESTIONS.md:432 | 08:29Z + 5:30 = 13:59 IST | MATCH |  |
| 06:00Z (11:30 IST | QUESTIONS.md:432 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:433 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:433 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00Z (19:30 IST | QUESTIONS.md:433 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:433 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:434 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:434 | Nov 16 2026 is a Mon | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:434 | Nov 16 2026 is a Mon | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:434 | Nov 16 2026 is a Mon | MATCH |  |
| 05:54Z (11:24 IST | QUESTIONS.md:434 | 05:54Z + 5:30 = 11:24 IST | MATCH |  |
| 21:00Z (02:30 IST | QUESTIONS.md:434 | 21:00Z + 5:30 = 02:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:435 | Nov 17 2026 is a Tue | MATCH |  |
| 07:00Z (12:30 IST | QUESTIONS.md:435 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:451 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:451 | Nov 23 2026 is a Mon | MATCH |  |
| 08:00Z Tue 17 Nov (13:30 IST | QUESTIONS.md:451 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:454 | Nov 23 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:454 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 16 Nov | QUESTIONS.md:456 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:456 | Nov 17 2026 is a Tue | MATCH |  |
| 13:00Z Mon 16 Nov = 18:30 IST | QUESTIONS.md:456 | 13:00Z + 5:30 = 18:30 IST | MATCH |  |
| 14:00Z = 19:30 IST | QUESTIONS.md:456 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:480 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:480 | Nov 23 2026 is a Mon | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:480 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:480 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | QUESTIONS.md:480 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 23 Nov | QUESTIONS.md:480 | Nov 23 2026 is a Mon | MATCH |  |
| 13:00Z (18:30 IST | QUESTIONS.md:481 | 13:00Z + 5:30 = 18:30 IST | MATCH |  |
| 09:30Z (15:00 IST | QUESTIONS.md:481 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| Tue 17 Nov | QUESTIONS.md:484 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | RUNBOOK.md:1 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | RUNBOOK.md:3 | Nov 17 2026 is a Tue | MATCH |  |
| Tue 17 Nov | RUNBOOK.md:3 | Nov 17 2026 is a Tue | MATCH |  |
| Monday 23 Nov | RUNBOOK.md:3 | Nov 23 2026 is a Mon | MATCH |  |
| 09:30 UTC (15:00 IST | RUNBOOK.md:14 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:15 | Nov 18 2026 is a Wed | MATCH |  |
| 14:00 UTC (19:30 IST | RUNBOOK.md:15 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 07:30 UTC (13:00 IST | RUNBOOK.md:15 | 07:30Z + 5:30 = 13:00 IST | MATCH |  |
| 06:00 UTC (11:30 IST | RUNBOOK.md:15 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| Wed 25 Nov | RUNBOOK.md:22 | Nov 25 2026 is a Wed | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:39 | Nov 18 2026 is a Wed | MATCH |  |
| 15:00 UTC (20:30 IST | RUNBOOK.md:39 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Tue 17 Nov | RUNBOOK.md:46 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:46 | Nov 18 2026 is a Wed | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:46 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 16 Nov | RUNBOOK.md:58 | Nov 16 2026 is a Mon | MATCH |  |
| Tue 17 Nov | RUNBOOK.md:60 | Nov 17 2026 is a Tue | MATCH |  |
| 04:00 UTC Tue 17 Nov (09:30 IST | RUNBOOK.md:60 | 04:00Z + 5:30 = 09:30 IST | MATCH |  |
| 08:00 UTC (13:30 IST | RUNBOOK.md:60 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 06:51 UTC (12:21 IST | RUNBOOK.md:60 | 06:51Z + 5:30 = 12:21 IST | MATCH |  |
| 06:21 UTC (11:51 IST | RUNBOOK.md:60 | 06:21Z + 5:30 = 11:51 IST | MATCH |  |
| 03:31 UTC (09:01 IST | RUNBOOK.md:60 | 03:31Z + 5:30 = 09:01 IST | MATCH |  |
| 04:00 UTC the writing starts at 01:10 UTC (06:40 IST | RUNBOOK.md:60 | 04:00Z + 5:30 = 09:30 IST | MATCH | regex paired the wrong time; by hand 01:10Z+5:30=06:40 IST and 11:05Z+5:30=16:35 IST |
| Tuesday 17 Nov | RUNBOOK.md:79 | Nov 17 2026 is a Tue | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:98 | Nov 18 2026 is a Wed | MATCH |  |
| 06:00 UTC (11:30 IST | RUNBOOK.md:98 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 14:00 UTC (19:30 IST | RUNBOOK.md:98 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Tue 17 Nov | RUNBOOK.md:101 | Nov 17 2026 is a Tue | MATCH |  |
| 14:00 UTC (19:30 IST | RUNBOOK.md:101 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| Wednesday 18 Nov | RUNBOOK.md:103 | Nov 18 2026 is a Wed | MATCH |  |
| 09:26 UTC (14:56 IST | RUNBOOK.md:107 | 09:26Z + 5:30 = 14:56 IST | MATCH |  |
| 07:30 UTC (13:00 IST | RUNBOOK.md:107 | 07:30Z + 5:30 = 13:00 IST | MATCH |  |
| 07:00 UTC (12:30 IST | RUNBOOK.md:108 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| 08:00 UTC (13:30 IST | RUNBOOK.md:108 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 08:30 UTC (14:00 IST | RUNBOOK.md:108 | 08:30Z + 5:30 = 14:00 IST | MATCH |  |
| 07:30 UTC (13:00 IST | RUNBOOK.md:110 | 07:30Z + 5:30 = 13:00 IST | MATCH |  |
| 09:15 UTC (14:45 IST | RUNBOOK.md:114 | 09:15Z + 5:30 = 14:45 IST | MATCH |  |
| 09:45 UTC (15:15 IST | RUNBOOK.md:114 | 09:45Z + 5:30 = 15:15 IST | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:115 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 25 Nov | RUNBOOK.md:115 | Nov 25 2026 is a Wed | MATCH |  |
| 12:00 UTC (17:30 IST | RUNBOOK.md:115 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 15:00 UTC (20:30 IST | RUNBOOK.md:115 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:116 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 25 Nov | RUNBOOK.md:116 | Nov 25 2026 is a Wed | MATCH |  |
| 11:07 UTC (16:37 IST | RUNBOOK.md:116 | 11:07Z + 5:30 = 16:37 IST | MATCH |  |
| 12:02 UTC (17:32 IST | RUNBOOK.md:116 | 12:02Z + 5:30 = 17:32 IST | MATCH |  |
| 11:05 UTC (16:35 IST | RUNBOOK.md:116 | 11:05Z + 5:30 = 16:35 IST | MATCH |  |
| 13:00 UTC (18:30 IST | RUNBOOK.md:117 | 13:00Z + 5:30 = 18:30 IST | MATCH |  |
| 13:30 UTC (19:00 IST | RUNBOOK.md:117 | 13:30Z + 5:30 = 19:00 IST | MATCH |  |
| 17:00 UTC (22:30 IST | RUNBOOK.md:117 | 17:00Z + 5:30 = 22:30 IST | MATCH |  |
| 12:00 UTC (17:30 IST | RUNBOOK.md:119 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 11:27 UTC (16:57 IST | RUNBOOK.md:119 | 11:27Z + 5:30 = 16:57 IST | MATCH |  |
| 12:22 UTC (17:52 IST | RUNBOOK.md:119 | 12:22Z + 5:30 = 17:52 IST | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:120 | Nov 18 2026 is a Wed | MATCH |  |
| 15:00 UTC (20:30 IST | RUNBOOK.md:120 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 08:00 UTC (13:30 IST | RUNBOOK.md:142 | 08:00Z + 5:30 = 13:30 IST | MATCH |  |
| 03:31 UTC (09:01 IST | RUNBOOK.md:142 | 03:31Z + 5:30 = 09:01 IST | MATCH |  |
| 04:00 UTC (09:30 IST | RUNBOOK.md:142 | 04:00Z + 5:30 = 09:30 IST | MATCH |  |
| 08:29 UTC (13:59 IST | RUNBOOK.md:142 | 08:29Z + 5:30 = 13:59 IST | MATCH |  |
| 03:31 UTC (09:01 IST | RUNBOOK.md:142 | 03:31Z + 5:30 = 09:01 IST | MATCH |  |
| 08:29 UTC (13:59 IST | RUNBOOK.md:142 | 08:29Z + 5:30 = 13:59 IST | MATCH |  |
| 09:29 UTC (14:59 IST | RUNBOOK.md:142 | 09:29Z + 5:30 = 14:59 IST | MATCH |  |
| 09:30 UTC (15:00 IST | RUNBOOK.md:142 | 09:30Z + 5:30 = 15:00 IST | MATCH |  |
| 09:00 UTC (14:30 IST | RUNBOOK.md:142 | 09:00Z + 5:30 = 14:30 IST | MATCH |  |
| 14:00 UTC (19:30 IST | RUNBOOK.md:142 | 14:00Z + 5:30 = 19:30 IST | MATCH |  |
| 09:29 UTC (14:59 IST | RUNBOOK.md:142 | 09:29Z + 5:30 = 14:59 IST | MATCH |  |
| 10:26 UTC (15:56 IST | RUNBOOK.md:142 | 10:26Z + 5:30 = 15:56 IST | MATCH |  |
| 11:26 UTC (16:56 IST | RUNBOOK.md:142 | 11:26Z + 5:30 = 16:56 IST | MATCH |  |
| 11:56 UTC (17:26 IST | RUNBOOK.md:142 | 11:56Z + 5:30 = 17:26 IST | MATCH |  |
| 06:51 UTC (12:21 IST | RUNBOOK.md:144 | 06:51Z + 5:30 = 12:21 IST | MATCH |  |
| 06:21 UTC (11:51 IST | RUNBOOK.md:144 | 06:21Z + 5:30 = 11:51 IST | MATCH |  |
| 04:25 UTC (09:55 IST | RUNBOOK.md:144 | 04:25Z + 5:30 = 09:55 IST | MATCH |  |
| 03:55 UTC (09:25 IST | RUNBOOK.md:144 | 03:55Z + 5:30 = 09:25 IST | MATCH |  |
| 03:25 UTC (08:55 IST | RUNBOOK.md:144 | 03:25Z + 5:30 = 08:55 IST | MATCH |  |
| 02:55 UTC (08:25 IST | RUNBOOK.md:144 | 02:55Z + 5:30 = 08:25 IST | MATCH |  |
| 08:31 UTC (14:01 IST | RUNBOOK.md:144 | 08:31Z + 5:30 = 14:01 IST | MATCH |  |
| 08:01 UTC (13:31 IST | RUNBOOK.md:144 | 08:01Z + 5:30 = 13:31 IST | MATCH |  |
| Mon 16 Nov | RUNBOOK.md:146 | Nov 16 2026 is a Mon | MATCH |  |
| 01:10 UTC (06:40 IST | RUNBOOK.md:146 | 01:10Z + 5:30 = 06:40 IST | MATCH |  |
| 01:30 UTC (07:00 IST | RUNBOOK.md:146 | 01:30Z + 5:30 = 07:00 IST | MATCH |  |
| 05:45 UTC (11:15 IST | RUNBOOK.md:147 | 05:45Z + 5:30 = 11:15 IST | MATCH |  |
| 09:29 UTC (14:59 IST | RUNBOOK.md:147 | 09:29Z + 5:30 = 14:59 IST | MATCH |  |
| 09:00 UTC (14:30 IST | RUNBOOK.md:149 | 09:00Z + 5:30 = 14:30 IST | MATCH |  |
| 05:30 UTC (11:00 IST | RUNBOOK.md:149 | 05:30Z + 5:30 = 11:00 IST | MATCH |  |
| 09:29 UTC (14:59 IST | RUNBOOK.md:150 | 09:29Z + 5:30 = 14:59 IST | MATCH |  |
| 05:45 UTC (11:15 IST | RUNBOOK.md:152 | 05:45Z + 5:30 = 11:15 IST | MATCH |  |
| 06:00 UTC (11:30 IST | RUNBOOK.md:152 | 06:00Z + 5:30 = 11:30 IST | MATCH |  |
| 09:37 UTC (15:07 IST | RUNBOOK.md:152 | 09:37Z + 5:30 = 15:07 IST | MATCH |  |
| 15:00 UTC (20:30 IST | RUNBOOK.md:152 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 11:27 UTC (16:57 IST | RUNBOOK.md:152 | 11:27Z + 5:30 = 16:57 IST | MATCH |  |
| 12:22 UTC (17:52 IST | RUNBOOK.md:152 | 12:22Z + 5:30 = 17:52 IST | MATCH |  |
| 11:30 UTC (17:00 IST | RUNBOOK.md:154 | 11:30Z + 5:30 = 17:00 IST | MATCH |  |
| 11:05 UTC (16:35 IST | RUNBOOK.md:155 | 11:05Z + 5:30 = 16:35 IST | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:183 | Nov 18 2026 is a Wed | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:185 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 25 Nov | RUNBOOK.md:185 | Nov 25 2026 is a Wed | MATCH |  |
| 18:29 UTC = 23:59 IST | RUNBOOK.md:185 | 18:29Z + 5:30 = 23:59 IST | MATCH |  |
| 15:00 UTC = 20:30 IST | RUNBOOK.md:185 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| 07:30 UTC (13:00 IST | RUNBOOK.md:187 | 07:30Z + 5:30 = 13:00 IST | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:194 | Nov 23 2026 is a Mon | MATCH |  |
| 07:00 UTC (12:30 IST | RUNBOOK.md:194 | 07:00Z + 5:30 = 12:30 IST | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:195 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 25 Nov | RUNBOOK.md:195 | Nov 25 2026 is a Wed | MATCH |  |
| 12:00 UTC (17:30 IST | RUNBOOK.md:195 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 15:00 UTC (20:30 IST | RUNBOOK.md:195 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:196 | Nov 23 2026 is a Mon | MATCH |  |
| 13:07 UTC (18:37 IST | RUNBOOK.md:198 | 13:07Z + 5:30 = 18:37 IST | MATCH |  |
| 12:22 UTC (17:52 IST | RUNBOOK.md:198 | 12:22Z + 5:30 = 17:52 IST | MATCH |  |
| 15:33 UTC (21:03 IST | RUNBOOK.md:198 | 15:33Z + 5:30 = 21:03 IST | MATCH |  |
| 09:56 UTC (15:26 IST | RUNBOOK.md:198 | 09:56Z + 5:30 = 15:26 IST | MATCH |  |
| 14:02 UTC (19:32 IST | RUNBOOK.md:198 | 14:02Z + 5:30 = 19:32 IST | MATCH |  |
| 11:27 UTC (16:57 IST | RUNBOOK.md:198 | 11:27Z + 5:30 = 16:57 IST | MATCH |  |
| 16:28 UTC (21:58 IST | RUNBOOK.md:198 | 16:28Z + 5:30 = 21:58 IST | MATCH |  |
| 09:01 UTC (14:31 IST | RUNBOOK.md:198 | 09:01Z + 5:30 = 14:31 IST | MATCH |  |
| 11:29 UTC (16:59 IST | RUNBOOK.md:198 | 11:29Z + 5:30 = 16:59 IST | MATCH |  |
| 17:36 UTC (23:06 IST | RUNBOOK.md:198 | 17:36Z + 5:30 = 23:06 IST | MATCH |  |
| 20:02 UTC (01:32 IST | RUNBOOK.md:198 | 20:02Z + 5:30 = 01:32 IST | MATCH |  |
| 05:27 UTC (10:57 IST | RUNBOOK.md:198 | 05:27Z + 5:30 = 10:57 IST | MATCH |  |
| 07:53 UTC (13:23 IST | RUNBOOK.md:198 | 07:53Z + 5:30 = 13:23 IST | MATCH |  |
| 18:31 UTC (00:01 IST | RUNBOOK.md:198 | 18:31Z + 5:30 = 00:01 IST | MATCH |  |
| 06:58 UTC (12:28 IST | RUNBOOK.md:198 | 06:58Z + 5:30 = 12:28 IST | MATCH |  |
| 04:32 UTC (10:02 IST | RUNBOOK.md:198 | 04:32Z + 5:30 = 10:02 IST | MATCH |  |
| 07:00 + 6 h 07 min = 13:07 | RUNBOOK.md:198 | = 13:07 | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:199 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 25 Nov | RUNBOOK.md:199 | Nov 25 2026 is a Wed | MATCH |  |
| 12:00 UTC (17:30 IST | RUNBOOK.md:199 | 12:00Z + 5:30 = 17:30 IST | MATCH |  |
| 15:00 UTC (20:30 IST | RUNBOOK.md:199 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Mon 16 Nov | RUNBOOK.md:200 | Nov 16 2026 is a Mon | MATCH |  |
| 13:00Z = 18:30 IST | RUNBOOK.md:212 | 13:00Z + 5:30 = 18:30 IST | MATCH |  |
| 15:00 UTC post must start by 11:05 UTC (16:35 IST | RUNBOOK.md:217 | 15:00Z + 5:30 = 20:30 IST | MATCH | regex paired the wrong time; by hand 01:10Z+5:30=06:40 IST and 11:05Z+5:30=16:35 IST |
| Tue 17 Nov | RUNBOOK.md:224 | Nov 17 2026 is a Tue | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:233 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 18 Nov | RUNBOOK.md:256 | Nov 18 2026 is a Wed | MATCH |  |
| 15:00 UTC (20:30 IST | RUNBOOK.md:256 | 15:00Z + 5:30 = 20:30 IST | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:259 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:259 | Nov 23 2026 is a Mon | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:259 | Nov 23 2026 is a Mon | MATCH |  |
| Wed 25 Nov | RUNBOOK.md:259 | Nov 25 2026 is a Wed | MATCH |  |
| 10:35 UTC (16:05 IST | RUNBOOK.md:265 | 10:35Z + 5:30 = 16:05 IST | MATCH |  |
| Mon 23 Nov | RUNBOOK.md:266 | Nov 23 2026 is a Mon | MATCH |  |
| 10:07 UTC (15:37 IST | RUNBOOK.md:276 | 10:07Z + 5:30 = 15:37 IST | MATCH |  |
| 11:02 UTC (16:32 IST | RUNBOOK.md:276 | 11:02Z + 5:30 = 16:32 IST | MATCH |  |
| 269 min = 4 h 29 min; 146 min = 2 h 26 min; sums of 17 and 9 step times | RUNBOOK.md:142 | 269 and 146 | MATCH |  |
| 08:00 minus 4 h 29 min = 03:31 UTC (09:01 IST) | RUNBOOK.md:142 | 03:31 / 09:01 | MATCH |  |
| step clock list 04:00 ... 07:14 (15 start times, 7 IST pairs) | RUNBOOK.md:143 | computed from the 17 durations on line 142 | MATCH |  |
| 07:00 to 07:30 ... 11:20 to 13:20 (5 UTC to IST ranges) | RUNBOOK.md:152 | all 5 pairs +5:30 | MATCH |  |
| 10 + 45 + 15 + 45 = 115 min of a 120-min block: spare 5 min | RUNBOOK.md:152 | 115, 5 | MATCH |  |
| 367 min = 6 h 07 min; 07:00 + 6 h 07 min = 13:07 UTC (18:37 IST); margin 5 h 22 min to 18: | RUNBOOK.md:198 | 13:07; 18:37; 5:22 | MATCH |  |
| 13:07 + 2 h 26 min = 15:33 UTC (21:03 IST); margin 2 h 56 min; event must end by 09:56 UTC | RUNBOOK.md:198 | all four | MATCH |  |
| 4 h 29 min + 6 h 07 min + 2 h 26 min = 13 h 02 min; 18:29 minus that = 05:27 | RUNBOOK.md:198 | 782 min; 05:27 | MATCH |  |
| 07:00 starts, 4 h 29 min, ending 11:29 UTC (16:59 IST) | RUNBOOK.md:198 | 11:29; 16:59 | MATCH |  |
| 18:29Z = 23:59 IST (credits stop) | QUESTIONS.md | 18:29+5:30=23:59 | MATCH |  |
| 170 minus 146 = 24 min to spare, fits from 09:30 | RUNBOOK.md:150 | 24 | MATCH |  |
| 45 s lease + 30 s check = about 75 s | QUESTIONS.md / RUNBOOK.md | 75 | MATCH |  |
