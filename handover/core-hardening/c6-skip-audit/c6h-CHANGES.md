# c6h changes (REPORT-c6g.md text revised into REPORT-c6h.md; C/REPORT.md updated). One row per item. No n8n, git, database, mail or CRM was run; no flow or program file edited. Files written: REPORT-c6g.md (backup copy of the c6g text, byte-equal to REPORT-c6f.md), REPORT-c6h.md, REPORT.md (edited in place), c6h-CHANGES.md, checkpoint-c6h.md, raw-c6h-checks.txt.

Base folders (H, C, A, FA, L3, S) are defined in REPORT-c6h.md, "Base folders". Every cite below was re-read in the file before the change.

## Failures and things not fixed (first)
- Not fixed, needs the lead: Q1 (closing card), Q2 (kill-case sentence), Q9 (time caption), Q10 (owner sheet; default now v19), Q11 (new: which claim wording), the code-versus-decision 2 conflict (D2, G-7), review-design M1 to M3 (kept as lead questions as ordered).
- Not checkable: whether /home/user/duplicate-proof-lead-desk-n8n/scripts/n8n_api.py equals the take's file (the take's file is not identified). Still not found: qualify_stage.py, the take's n8n_start.sh, the V7 laptop raw files, the bible (R460), review-codebase-1.md (F-01 is known only from AGENT-SCOPE-DO-AND-DONT.md:20 and the v18/v19 open lists: UNVERIFIED).
- Not checked: file times and window overlap of VOID-fl45k3b with 6 other runs (review nit 6); git history; the scratchpad copies were not diffed against the branches.

## Review Majors (review-c6g-codebase.md)
| # | what I did | where (new text) |
|---|---|---|
| 1 | T7b: N8N-START.md:27 relays a lane3 grep, n=1, flows without the four settings (saving ON), not a laptop test with saving off; page statement 18 (PAGE-STATEMENTS-V4.md:125-126) tags it UNBACKED, HB171 raw absent. Removed "key 0 hits can fail"; no measured key result with saving ON exists. | REPORT-c6h.md section 0 first bullet, row M2, row N2; REPORT.md revision 4 item 1 and T7b block |
| 2 | Closing card is :41 (line 3 says "lease plus 25 to 30 s ... n=1 ... the take ran at 45 s, which is NOT measured"); "52.9 to 54.9 s" and "13 min late (n=2)" are in :90; "13 min late" also :82. N7 and c6b-5 now follow Q2 (GC-Q2b), not Q1; Q1 and GC-Q1 list only N5, c6b-4, review-design-4; card line 3 task added. | Q1, GC-Q1, GC-Q2b, rows N5, N7, c6b-5; section 0 second bullet |
| 3 | G-7 and D2 rewritten: v9 states "never deletes" at :18, :40, :169, :285, :288 but the code deletes (AGENT-SCOPE:20); "key needs read, create, change only" (v9 :169) conflicts with a DELETE call and with v19 item 5. Lead decides first. | G-7, row D2, section 0 third bullet |
| 4 | X6 leftovers: F-025 row (DESIGN-A-README.md on disk; demo REPORT.md not C/REPORT.md), F-022 and N6 (F-019 read, FA/FINDINGS.md:113), glossary F-003 etc., "c6f is this one", closing line. | rows F-025, F-022, N6, glossary, last line |
| 5 | "Nothing run" replaced by what was run; raw output saved in raw-c6h-checks.txt (patch dry run, recompute, sha256, grep). | intro, section 9 item 0, rows with "No runtime check" |
| 6 | K1 and K2 are defined: mf.py:151-152, run sheet :33, page :151-152. | section 6 table, glossary, section 0 |
| 7 | v18/v19 open items used: item 8 (claim wording, new Q11 and row CL1), item 18 (step 0 not run, Q7, G-13, D8), item 10 (take-prep contact), item 20 (post-by source exists: ORDERS.md:150, QUESTIONS.md:55, OWNER-STEPS-realrun-v3.md:130; v18 said "no source"), item 1, 4, 5, 7; QUESTIONS.md:56 three wordings and DECISIONS 1 lacks "inside the lease". | Q7, Q11, section 2 narrow claim bullet, gate list intro, rows D2, D6, D8, CL1 |
| 8 | C/REPORT.md: header (no line cite), "Text below is not changed" removed, revision 4 box, gate item 5 (N1) and item 6 (F-006) marked, M3 row "may or may not have gone" marked superseded by revision 3 item 3, N5 line corrected, F-025 line corrected, T7b block corrected. | REPORT.md |

## Review nits
1 section 7 bullet 1 rewritten (no caption until Q9); 2 M1 notes: :85 and :23 allow a measured median and max, decision 1 says "unmeasured" (wrong for film-v4); 3 line cites fixed (scene 7 :36, scene 9 :38, scene 10 :39; F-007f :47 and :54; scene 1 "clicks nothing" limited to the execution list); 4 c6b-5 listed GC-Q2b; 5 F-01 marked UNVERIFIED; 6 listed as not checked; 7 no change.

## Citation check Y1 to Y12
| id | fix |
|---|---|
| Y1 | row c6b-5: card line 3 says n=1; raw RESULTS.md:85 has K1 n=2 (K2 n=1 at :86); the only "(n=2)" in the run sheet is the 13-minute alert in :90 |
| Y2 | HB194 also in H/core-hardening/reviews-of-flows-audit/evidence-A1.md and evidence-A4.md (not under L3) |
| Y3a | A/REPORT.md :33, :526, :528 (not C/REPORT.md, 64 lines) |
| Y3b | DESIGN-A-README.md is on disk (A/n8n-flows/), line 3 read |
| Y4 | first lease-45 start 17:02:01Z (22:32:01 IST); progress lines 101 to 127 run 17:04:03Z to 17:21:28Z (22:51:28 IST); 17:01 was lane0 v4 KS |
| Y5 | v18 finished 12:19:22 UTC (checkpoint-v18.md, file time 12:19:22), started 12:15 UTC |
| Y6 | N7 quote now verbatim from L3/REPORT.md:18 with the omitted words kept |
| Y7 | :47 = old waits at lease 20 s on v3; :54 = note 5 about the drop fault, no lease-20 figures |
| Y8 | desk copy exists (sha256 prefix 0677ec58287c7b84), not byte-equal to the r7u-chain test copies (26cd525a7e0a5ef2); equality with the take's file unchecked; n8n_start.sh files on disk 2, 3, 3, 3, 5, 16 lines, none has line 115; qualify_stage.py and mf_result_* still absent |
| Y9 | OWNER-SHEET-v19.md exists (12:32:43 UTC); Q10 default is now v19; v19-OPEN-FOR-LEAD.md (31 items) used |
| Y10 | rehearsal window "tonight or tomorrow morning IST": conversion shown as mine, 12:30 UTC (18:00 IST) to 04:30 UTC (10:00 IST) |
| Y11 | glossary sentence rewritten: rows F-003, F-007, F-008, F-011, F-019 read; F-006, F-020, F-022, F-023, F-025 only partly known |
| Y12 | C/REPORT.md header cites no line of REPORT-c6f.md any more; the "inside the lease" wording is traced to Q15.3 and REPORT-c6h.md Q11 |
