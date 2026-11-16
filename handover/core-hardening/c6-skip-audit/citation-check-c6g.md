# Citation check C6g (EVIDENCE RUNNER: runs and records, does not judge)

File checked: handover/core-hardening/c6-skip-audit/REPORT-c6f.md (now C6g, 376 lines). Date 2026-11-16. No git, no spend, no secret printed, no repo-guard word printed. Only this file was written.

Paths: H = /home/user/hadavin-sdk/handover. C = H/core-hardening/c6-skip-audit. S = /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad. A = S/c6/tree/handover/demo (audited demo folder copy). FA = S/c6/tree/handover/flows-audit. L3 = S/l3/handover/demo3 (lane3 branch copy). Raw lane3 = C/raw-lane3/.

Method: every distinct file:line, quoted text or number in the report was opened or recomputed once; a list such as "lines :4 :11 :12" is one unit per line. The unit total is my count by group (section 3); it is approximate by a few units because some cites are inside prose that restates an earlier row (counted once, at the first row). Nothing was run except python3 -I on results.jsonl, grep, sed, wc, ls, and `patch --dry-run` on the scratchpad copy.

## Counts

- Units checked: about 308.
- MATCH: about 297.
- MISMATCH: 10 (Y1, Y3a, Y3b, Y4, Y5, Y6, Y7, Y8, Y11, Y12).
- NOT FOUND at the cited path: 1 (Y2).
- Observations that are not mismatches (stale since the report was saved, or the report's own arithmetic): Y9, Y10 (section 2).
- Previous check X1 to X11: all 11 are now correct in the report. Two of them (X6, X8) still leave a residue (Y3b, Y2, Y8). See section 4.

## 1. Mismatches and not-found, failures first

| id | report place | what the report says | what the file says | size |
|---|---|---|---|---|
| Y1 | row c6b-5 (line 220) | "closing card line 3 n = 2, from n8n up" (as the difference found) | A/VIDEO-RUNSHEET.md:41 line 3 says "lane3 v4 K1 144.3 s at lease 120 s, n=1, relayed independent". "n=2" is not on the card. It is the raw count in C/raw-lane3/RESULTS.md:85 (K1 n 2), reported in REPORT-c6b.md item 5 ("closing card ... n=1: raw n=2"). The only "(n=2)" in the run sheet is in :90, about the 13-minute-late alert. The row's wording reads as if the card says n = 2. | wording |
| Y2 | section 0, bullet X8 (line 20) | HB194 is also written "in L3/reviews-of-flows-audit/evidence files" | NOT FOUND at that path: L3 (S/l3/handover/demo3) has no folder reviews-of-flows-audit, and grep for HB194 under S/l3 finds 0 files. The files exist elsewhere: H/core-hardening/reviews-of-flows-audit/evidence-A1.md and evidence-A4.md contain HB194 (grep). The other two places (A/VIDEO-RUNSHEET.md:90; A/n8n-flows/PAGE-STATEMENTS-V4.md:20 and :148) are correct. | path |
| Y3a | row F-025 (line 244) | "updates C/REPORT.md:33, :526-528" | C/REPORT.md has 64 lines. Lines :33 and :526-528 with the text about v1-superseded are in A/REPORT.md (the demo folder's own REPORT.md, 6012 lines): :33 "design A flows and table (v1-superseded kept)", :526 and :528 about v1 runs. Wrong file named. | file name |
| Y3b | row F-025 (line 244) | "DESIGN-A-README.md:3 (NOT FOUND)" | The file is on disk: A/n8n-flows/DESIGN-A-README.md, line 3 reads "... The earlier version (updated_at rule) is kept in v1-superseded/ for the compare only." The report's own section 9 item 4 lists it as on disk. The row contradicts section 9. | status word |
| Y4 | row review-design-3 (line 226) | run_all.progress lines 101 to 127: queues overlapped "17:01 to 17:21 UTC, 22:31 to 22:51 IST" | L3/kill/data/run_all.progress lines 101 to 127 run from 17:04:03Z (line 101, lane3 fl45k2a) to 17:21:28Z (line 127). 17:01:46Z is line 99 to 100 (lane0 v4 KS, not a lease-45 case). The first lease-45 t_start in results.jsonl is 17:02:01Z (fl45k2a, fl45k1a). REPORT-c6b.md review point 3 says 17:02:01 to 17:21:28. So the start should be 17:02 (results.jsonl) or 17:04 (those lines), not 17:01. The end and the IST sums (+5:30) are right. | 1 to 3 min |
| Y5 | section 0 X4 (line 18) and Q10 (line 118) | OWNER-SHEET-v18.md "written 12:16 UTC" | steps-edits/checkpoint-v18.md: "started 2026-11-16T12:15Z; finished 2026-11-16T12:19:22Z"; file mtime 12:19:22 UTC. 12:16 is neither. | minor |
| Y6 | row N7 (line 256) | quotes L3/REPORT.md lines 9 to 20: "OLD v4 flows: alert at 750 s, 1 alert, 1 intake mail (the earlier n=2 runs were 780 s). FIXED flows (kill/flows-go1): alert at 60 s in 3 of 3 runs" | L3/REPORT.md:18 reads "OLD v4 flows: alert at 750 s, 1 alert, 1 intake mail (go1-old-ks; the earlier n=2 runs were 780 s). FIXED flows (kill/flows-go1: n8n "started" trigger + one SQL clearing unsent alert claims): alert at 60 s in 3 of 3 runs (go1-fix-ks, go1-fix-ks2, and the agent's ev-go1-ks), 1 alert and 1 intake mail each." The report shortens the text inside quotation marks without an ellipsis. Meaning is unchanged; numbers 750, 780, 60, 3 of 3 are right. | quote not verbatim |
| Y7 | row F-007f (line 200) | ":47 and :54 are notes about old lease-20 numbers" | :47 is (old waits at lease 20 s on v3). :54 is note 5: "Scene 7 to 9 numbers: the drop fault has no measured row (T12 not run on v3) ... K3 and K3B do not back them." It is about the drop fault, with no lease-20 figures. The nine-line K3 list (:24 :32 :36 :38 :39 :41 :47 :54 :90) is right (grep). | minor description |
| Y8 | section 9 item 4 (line 338), row N1 (line 182) | the take's scripts\n8n_api.py NOT FOUND, "only test copies under H/core/evidence/r7u-chain/"; the take's n8n_start.sh: only "2-line and 16-line stubs" (line 31) | A copy of scripts/n8n_api.py exists in the desk repo checkout /home/user/duplicate-proof-lead-desk-n8n/scripts/n8n_api.py (branches main and claude/vibrant-hamilton-ucz1qk; written 06:43 UTC; no take/nlite branch there). Whether it equals the take's file: not checked. So "only test copies" is false. n8n_start.sh files on disk: 2, 3, 3, 3, 5 and 16 lines (not only 2 and 16); none has a line 115 (largest is 16 lines), so "line 115 not checkable" holds. qualify_stage.py: still absent everywhere (find over / returned 0), so that NOT FOUND is correct. mf_result_* files: 0 found, correct. | partial |
| Y11 | glossary line 357 | F-003, F-006, F-007, F-008, F-011, F-019, F-020, F-022, F-023, F-025: "full text NOT FOUND; only parts quoted in C/REPORT.md are known to me" | FA/FINDINGS.md exists and the report itself read its rows F-003 (:89), F-007, F-008 (:96), F-011 (:97), F-019 (:113) (sections 0, 5, 9). The glossary sentence is the c6f text and contradicts those rows. | stale sentence |
| Y12 | C/REPORT.md line 1 (not the file under test; it cites it) | "the narrow claim in force is 'inside the lease' (REPORT-c6f.md:64)" | REPORT-c6f.md:64 is now a row of the status-word table ("DECISION ANSWERED / NOTHING LEFT"). "inside the lease" is at REPORT-c6f.md lines 93, 280, 308 and 309. | cite moved |

## 2. Observations (not counted as mismatches)

- Y9. Stale since saving: steps-edits/OWNER-SHEET-v19.md now exists (mtime 12:28 UTC, after REPORT-c6f.md was saved at 12:24 UTC). Its second line says "Do not use any older sheet (v4 to v18)". The report says v18 is the newest sheet (section 0 X4, Q10, row D10-archive "v4 to v15 and OWNER-SHEET-v16 to v18"). Not an error when written; the default "v18" in Q10 is now out of date.
- Y10. Section 3, gate list (line 120): the report converts decision 12's "tonight or tomorrow morning IST" to "about 12:30 UTC on 16 Nov to 06:30 UTC on 17 Nov". 12:30 UTC = 18:00 IST (right). 06:30 UTC = 12:00 IST (midday), which is the edge of "morning". The decisions file (DECISIONS-2026-11-16.md item 12) gives no hours; the conversion is the report's own.
- The scene 4 caption quote, scene 3 and closing-card quotes, the K3B quote at :90 and all numbers in section 8 match (section 3).
- Dates and weekdays recomputed: Mon 16 Nov, Wed 18 Nov, Mon 23 Nov, Wed 25 Nov 2026 correct; 18:29 UTC = 23:59 IST and 15:00 UTC = 20:30 IST and 10:13 UTC = 15:43 IST correct; 17:09:59Z to 17:16:35Z = 22:39:59 to 22:46:35 IST correct.

## 3. Lane3 recompute (done by me from C/raw-lane3/results.jsonl with python3 -I; not copied from earlier reports)

Raw file: 128 result lines; source-sha.txt = 23f3101a868c2f0538ec4880668e22e989c30c8e (matches the report's "23f3101a").

- Lines with flows = 873a908a-film-v4-lease45: 23. Of these: 2 labelled VOID (VOID-fl45k6c, VOID-fl45k3b), 3 error-case lines (fl45err1 to 3, point "error"), 18 kept (reached_terminal true, a kill_to_final_s value).
- Kept per case (lane3 file names): K1 5, K2 5, K3 5, K6 3.
- kill_to_final_s over the 18: min 60.1, max 61.9, median 60.85 (computed 60.849999..., i.e. 60.85). This matches "60.1 to 61.9 s, median 60.85".
- Per case min / median / max: K1 60.1 / 60.8 / 61.9; K2 60.4 / 60.9 / 61.2; K3 60.1 / 60.4 / 61.6; K6 60.1 / 60.1 / 61.5. All match row M1.
- Largest |kill_to_final_s - (restart_s + recovery_s)|: 0.1. restart_s 6.6 to 8.8; recovery_s 52.8 to 54.9. Match.
- RESULTS.md Part 3 lease-45 rows (lines 83 to 92 region): recovery median/max K1 52.9/54.9, K2 52.9/52.9, K3 52.9/54.9, K6 52.8/54.8; kill-to-final K1 60.8/61.9, K2 60.9/61.2, K3 60.4/61.6, K6 60.1/61.5. Match the recompute.
- crm_upsert_events: 2 in 13 of 18 (K2 5, K3 5, K6 3); 1 in the 5 K1 runs. crm_rows 1 in all 18. stage_calls 1 in all 18. total_stage_requests 2 in all 18. mail_to_intake: K1 1, K2 1, K3 0 (5 of 5), K6 1 (3 of 3). alert: K1 0, K2 0, K3 1, K6 1. total_mails: 1 for K1, K2, K3; 2 for K6. End states: done 10 (K1 5, K2 5), unknown 8 (K3 5, K6 3). Final attempts field: 2 in all. All match section 8.
- rows_at_kill (fields lead_key, state, attempts, mail_sent, crm_id; order from L3/kill/harness.py:192): all 18 are state processing, attempts 1; K1 and K2 mail_sent f, crm_id empty; K3 and K6 mail_sent t, crm_id crm-1 (8 of 8). Match section 6 and rows F-007a, F-007d, K3B-mail.
- Attempted runs at lease 45: kept 18 + voided 2 = 20 (K1 5, K2 5, K3 5+1 void = 6, K6 3+1 void = 4); the 3 error lines are not in the 20. Match.
- VOID-fl45k3b: t_start 17:09:59Z, t_end 17:16:35Z, reached_terminal false, kill_to_final_s 338.7, no error field. VOID-fl45k6c: error "RuntimeError: fakes_not_up". Match. harness.py:337 wait limit 330 for non-error points: match.
- Not in results.jsonl and not claimed: there is no "K3B" label (report says so, correct).

## 4. Status of X1 to X11 of citation-check-c6.md

| id | now | evidence |
|---|---|---|
| X1 ("5678" 0 hits) | CORRECT | Section 0 and row D6 now say v9 has 2 hits (:9, :227) and the plan 5 (:121, :230, :421, :486, :489); "own free port" 0 in both. I counted: v9 5678 at lines 9 and 227; plan at 121 230 421 486 489; "own free port" 0 and 0. |
| X2 ("twice" 0 hits) | CORRECT | Report says "twice" finds only plan :377 ("in-flight crash MISSED twice") and names plan :341 cases A and B and QUESTIONS.md:22. Checked: :377 has the phrase; :341 has A (2 replies, repeat true) and B (10 replies, at most 1 repeat false); QUESTIONS.md:22 has "the same-id-twice cases A and B (plan :341)". "same id", "same lead", "made-up lead", "one lead", "T-ROLES": 0 hits each (checked). |
| X3 (v9:408) | CORRECT | v9:18 has A twice, B ten times, C once, 13 sends; v9:408 only says the notice text "B ten times at once" is a fixed string. Report says exactly that. |
| X4 (no v10 sheet) | CORRECT (with Y5, Y9) | steps-edits holds OWNER-STEPS-realrun-v10 to v15 (v10 mtime 10:17), OWNER-STEPS-v10 to v15-APPENDIX, OWNER-DAY-CARD-v12 to v15, OWNER-SHEET-v16, v17, v18 (and now v19). Report text matches except the v18 time (Y5) and v19 (Y9). |
| X5 (T7b not found) | CORRECT | mf.py:274 `def t7b()`, docstring :275-276, saving forced off at :278, result lines :296 and :318-320. Report cites these. |
| X6 (files absent) | CORRECT, residue Y3b, Y8, Y11 | The report now separates "not under H" from "on disk in the scratchpad copies" and lists qualify_stage.py, the take's n8n_start.sh, scripts/n8n_api.py, mf_result_* and the bible as not found. All listed files exist at the paths in the base-folders line. Residue: DESIGN-A-README "(NOT FOUND)" in row 35 (Y3b); n8n_api.py exists in the desk checkout (Y8); glossary "full text NOT FOUND" (Y11). |
| X7 (lane3 REPORT.md) | CORRECT | L3/REPORT.md exists; :11 "not imported into the demo flows", :18 "alert at 60 s in 3 of 3 runs", "750 s", "780 s". Report quote is shortened (Y6). |
| X8 (HB194 only in commit) | CORRECT, residue Y2 | Report now says HB194 is in A/VIDEO-RUNSHEET.md:90 and A/n8n-flows/PAGE-STATEMENTS-V4.md :20 and :148 (verified), and says no commit message was read. The extra path "L3/reviews-of-flows-audit/evidence files" is wrong (Y2). REPORT-c6b.md line 2 still holds the old commit-message claim; that is another file. |
| X9 (G5 text) | CORRECT | H/core-hardening/patches-ready/v5/G5-wording.patch exists, 3 files (src/hadavin_sdk/approvals/gate.py, src/hadavin_sdk/guard/redact.py, tests/warden_port/test_gate.py); README.md:9 says APPLY NOW with the quoted command; ORDERS.md:48 "G5: DROP it", :59 "the G5 wording drop", :122 "G5 wording kept"; plan :533 and :540 hold a different G5 (row for wp6-smoke/fill_flows.py). Report says all of this. |
| X10 (C/REPORT.md superseded) | CORRECT | C/REPORT.md line 1 carries the superseded note; a "Revision 3 (c6g)" block exists and item 8 says the lane3 raw is on disk. Its cite "REPORT-c6f.md:64" is wrong now (Y12). |
| X11 (mf.py:158) | CORRECT | mf.py:158 K3B text "n8n killed after mail_sent was set, while the SMTP node was connecting (stand-in holds the greeting 6 s), mail NOT yet delivered"; :164 K3 text "killed after the mail was delivered (stored by the stand-in), before the table update (acknowledgement held 6 s)". Report quotes both as read; no "NOT FOUND, carried over" is left on them. |

## 5. MATCH groups (units opened and compared; n = units)

| group | what | n | result |
|---|---|---|---|
| G1 | A/VIDEO-RUNSHEET.md (90 lines): :4 :11 :12 :22 :24 :30 :31 :32 :33 :34 :36 :38 :39 :41 :56 :78 :82 :85 :86 :90 (20 lines); nine K3 lines (count and list); caption quotes at :32 (scene 3), :33 (scene 4 table caption "lease plus 25 to 30 s"), :90 (scene 4 FINAL caption, "Raw not seen by me", "From n8n up: 52.9 to 54.9 s", "up to 13 min late (n=2)"), :41 line 2 ("80 kills, 0 lost, 0 doubled; 40 of the 80"); scene 5 stand-in :12 :34; scene 11 optional :40; scene 12 closing card :41 | 27 | 26 match, 1 mismatch (Y7 for :54) |
| G2 | A/n8n-flows/PAGE-STATEMENTS-V4.md (161 lines): :20 :49 :148 :149 :150 :153 and quoted text | 8 | match |
| G3 | A/n8n-mainframe/mf.py (365 lines): :12 :83 :153-158 :159-164 :274 :275 :276 :277 :278 :281 :296 :318-320 | 10 | match |
| G4 | stage_server.py :3-5 :16 :48-52 :54 (3 units); N8N-START.md :4, :15-27 values, :27 text (3); PLAN-4 :64 :78 :80 (3); DOUBTFUL-SCENE.md:13, n8n-table-screen README:3, v2 README :3 :5 :48 :51 (6); v1-superseded mf-recovery.json (every 30 s, secondsInterval 30, Every30s) and README.txt "kept for the compare only" (4); DESIGN-A-README.md:3 content (1) | 20 | match (label issue Y3b counted separately) |
| G5 | L3/kill/harness.py :22-25 :192 :261 :275 :337 :339 :341 (8); L3/REPORT.md :11 :18 (3 numbers) :20; PLAN-V3-ALERT.md:24 "0 lost"; COMPARE-demo.md:5; RESULTS.md :2 :83-92 :97 :100 Part 4; grep-claims.txt ("80 kills" 0, "0 doubled" 2, "0 lost" 3); source-sha | 25 | 23 match, 2 mismatch (Y6 quote, Y4 time span) |
| G6 | FA/FINDINGS.md :89 :96 :97 :113; EXCEPTIONS.md:5; CUT-LIST.md v1-superseded row (3 / 53, "kept for the compare only"); F-003 patch (72 lines, 5 hunks at 1-7, 19-26, 30-54, 59-65, 76-82; dry run prints only "checking file ..."; hunk 1 sets line 4 to "scenes 1 to 4"; scene 4 hunk K1 5 runs median 60.8 max 61.9; does not touch :85 or :90) | 11 | match |
| G7 | plan-wp6-resmoke-v5.md (558 lines): :38 :73 :99 :103 :120 :121 :125 :126 :148 :230 :236 :272 :273 :277 :284 :298 :321 :341 :377 :421 :486 :489 :533 :540 :543 :550; film-v5 at exactly 120 236 284 298 543; saving all :125; ports 5690 to 5693 and Postgres 55433; roles smk_n8n, smk_app, smk_count; N1-N10; 0 hits for "T-ROLES", "made-up lead", "one lead", "same id", "same lead" | 36 | match |
| G8 | DECISIONS-2026-11-16.md items 1 to 12 as used | 12 | match |
| G9 | DECISION-one-store.md:14 wording and "n8n_start.sh (line 115)" quote (2); AGENT-SCOPE-DO-AND-DONT.md:20 (DELETE call, run_real_check_n8n.py:1051, crm_hubspot.py:504-509, F-01, CODE-CHANGE-NEEDED, read-only token fails at archive) (1); ORDERS.md :48 :59 :121 :122 :123 and "10:13Z" (5); QUESTIONS.md :1 :22 (2); FAIL-CAUSE.md:41 (1); v18-OPEN-FOR-LEAD.md items 1, 4 (5701 and 5702 "unsourced"), 7, 9 (4); OWNER-SHEET-v18.md R7 (1); ZOOM-OUT-not-checked.md gap list (1); H/ledger.md and H/reviews/ledger.md exist (2); checkpoint-v18.md (1) | 20 | match (the time in Y5) |
| G10 | OWNER-STEPS v9 (411 lines): :9 :18 :22 :35 :137 :147 :166 :169 :227 :285 :288 :341 :396 :399 :400 :402 :408; "own free port" 0; "mf_leads"/"fresh lead" 0; "S9-" only at :399 :400; stop time Mon 23 Nov 18:29 UTC = 23:59 IST | 22 | match |
| G11 | v4 :96 :98 :179; v5 :127 (quote "The program then deletes this run's contacts" verified) :130; v6 :135-136 :206; v7 :57 :136 :137 :223 :226; v8 :64 :155 :157 :247 :250 | 18 | match |
| G12 | v10:24, v10:80, v15:59 (clean start); v10 mtime 10:17 against c6f-CHANGES 10:22 | 4 | match |
| G13 | Dates, weekdays, IST arithmetic (16, 18, 23, 25 Nov; 18:29, 15:00, 10:13 UTC; 17:09:59 and 17:16:35 UTC) | 8 | match (Y10 note) |
| G14 | results.jsonl recompute: every number in section 3 above against report rows M1, section 6, section 8, K3B-mail, F-007a, F-007d, c6b-1 | 45 | match |
| G15 | review-design.md (M1, M2, M3, m1 to m4), review-codebase.md, REPORT-c6b.md (six numbered findings, items 4 and 5, review round points 1 to 3), review-c6e-design-r2 "2 Blockers, 6 Majors", review-c6e-naive-r2 "4 Major, 8 Nit" | 13 | 12 match, 1 mismatch (Y1) |
| G16 | A12-style flow facts: 11 flow folders each with mf-form.json (n8n-flows, -v3, -v4, -real, -real-v3, -real-v4, -real-v5, -film, -film-v3, -film-v4, -film-v5); real-v5 and film-v5 both path mf-form; mf-hook path in real-v5; real-v5 mf-form.json :238 :254 :293 only n8n_error false; CrmUpsert real-v5 = hubspot node, film-v5 = MF_CRM_URL; 0 errorWorkflow in the 8 files; desk doors "Reply 2xx" and "Reply error" nodes; 0 hits of DB_TYPE and DB_POSTGRESDB under A | 12 | match |
| G17 | Existence claims: about 45 files named as read or as existing (list in section 6) | 45 | match |
| G18 | NOT FOUND claims: qualify_stage.py absent (find /): correct; mf_result_* absent: correct; bible R460 absent: not checkable by me; n8n_start.sh line 115 absent: correct; n8n_api.py: see Y8; FINDINGS full text: see Y11 | 6 | 4 correct, 2 mismatch (Y8, Y11) |
| totals (units) | | about 345 before de-duplicating restated cites; about 308 distinct | about 297 match |

Note on the totals: the group n values add up to more than 308 because some units (for example the scene 4 caption lines and the results.jsonl numbers) are cited from several rows; I counted each distinct file:line or number once in the headline count and per group in the table. The mismatch list in section 1 is exact; the match count is approximate.

## 6. Not checked, or not checkable (by me)

- Git history: commit 2595b8c3, commit 873a908a, the branch origin/demo/lane3 itself (no git). The lane3 numbers and text I used come from C/raw-lane3/ and from the scratchpad copies (S/l3, S/c6/tree). I did not diff the scratchpad copies against the branches.
- Bible and rule R460 (not on disk).
- Runtime claims (n8n 2.46.6 behaviour, saved runs, two flow sets, error workflow, T7b results): nothing was run; those cells in the report are labelled UNVERIFIED and I did not test them.
- Judgement text: status words, priorities, gate lists, defaults and questions Q1 to Q10 are not citations and were not checked. The report's reading of decision 2 versus the code (AGENT-SCOPE:20) was checked only as a quote; the code lines (run_real_check_n8n.py:1051, crm_hubspot.py:504-509) are on a branch not on disk (the desk checkout has crm_hubspot.py with `def archive` at :492 on main, a different version).
- OWNER-STEPS v10 to v15 beyond :24 and :80 (v10) and :59 (v15); OWNER-SHEET v16 and v17; PAGE-STATEMENTS beyond the cited lines; FA/FINDINGS.md rows not cited.
- The k-numbered lines of the plan (S9-5, S9-12, S9-3 text in v10 to v18): the report says it did not check them either.
- Row N8's earlier sentence about commit 2595b8c3 is only in REPORT-c6b.md line 2 now (report says it read no commit message): not a defect in the file under test.

Files opened for this check (all found): the 18 cited tree files under A, FA and L3 (VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md, N8N-START.md, DESIGN-A-README.md, PLAN-4-NLITE-FROM-LEAD.md, DOUBTFUL-SCENE.md, V7-NUMBERS-lead-read.md, stage_server.py, mf.py, FINDINGS.md, EXCEPTIONS.md, CUT-LIST.md, F-003-runsheet-claims.patch, REPORT.md, harness.py, PLAN-V3-ALERT.md, COMPARE-demo.md, run_all.progress); H/core-hardening/inputs (DECISIONS-2026-11-16.md, DECISION-one-store.md, plan-wp6-resmoke-v5.md, AGENT-SCOPE-DO-AND-DONT.md, OWNER-STEPS-realrun-v3.md); steps-edits (v4 to v10, v15, v18 sheet, v18-OPEN-FOR-LEAD.md, checkpoint-v18.md, v19 sheet for Y9); QUESTIONS.md, ORDERS.md, patch-test-runs/FAIL-CAUSE.md, patches-ready/v5 (README.md, G5-wording.patch), cross-read/ZOOM-OUT-not-checked.md, reviews-of-flows-audit/evidence-A1.md and evidence-A4.md (grep only), ledgers (existence), C/raw-lane3 (RESULTS.md, results.jsonl, grep-claims.txt, source-sha.txt), C/REPORT.md, REPORT-c6b.md, review-design.md, review-codebase.md, review-c6e-*-r2.md.
