# c6f changes: one row per finding id (REPORT-c6e.md to REPORT-c6f.md). Fixed = fixed in REPORT-c6f.md.

| finding id | where fixed (section or row in REPORT-c6f.md) | result |
|---|---|---|
| design B1 (section 4 and gate 6 override decision 10; forward claim; line-14 conditional; F-011 vs N9 disagree) | section 4, rows F-011, N9, H-1 | Fixed. Section 4 states the interim wording is a request to the lead to ratify or veto. It quotes decision 10 as the target. The forward claim is removed. The line-14 edit is unconditional (H-1). N9 is folded into F-006, F-003 and H-1. |
| design B2 (unclassed rows; Q2 as gate conflicts with decision 8) | section 1 List column, section 3, section 5 List column, Q2 | Fixed. Every row has a List value (G, GC, H, A or D). Q2 now has two options (a) drop the kill cases, (b) keep them labelled "stand-in flows, film-v4". N5, N7, review-design-4/3/6, c6b-1/2/4/5/6, N3b, N8 and K3B-mail are classed. |
| design M1 (D2 status and stale text v4 to v8; v9:288 unread) | row D2, Q10 | Fixed. D2 is DECISION ANSWERED / FILES NOT UPDATED. It lists v4 to v8 lines, including v7:137 and v7 row 14. I read v9:288: F.3, "The program does not delete contacts". v9 :166/:169 step 0 delete line is flagged for the lead. |
| design M2 (D10 over-blocks) | rows D10, D10-archive, H-6 | Fixed. The version question is merged into D2 and Q10. The archive note is housekeeping. v3 found at inputs/. |
| design M3 (rows for decisions 5, 6, 8, 9, 11, 12 and the 5 vs 7 tension) | rows D5a, D5b, D6, D8, D9, D11, D12 | Fixed. Read in v9 and the plan where the files allowed; the rest is marked not checked. |
| design M4 (NOTHING LEFT overclaims: c6b-1, review-design-5, Z1) | rows c6b-1, review-design-5, Z1a, Z1b, Z1c | Fixed. c6b-1 is CONDITIONAL. review-design-5 is DUPLICATE of M1. Z1 is split: Z1a NOTHING LEFT, Z1b UNKNOWN (G5 wording), Z1c CONDITIONAL (Route config). "T-ROLES parked" is replaced by ROLE1 and Q4/Q5. |
| design M5 (F-007g conditional) | row F-007g | Fixed. CONDITIONAL. |
| design M6 (Q1 rows; Q2; Q3 yes/no; role question; S1b three roles vs four logins; Q labels) | section 3, ROLE1, section 1 label note | Fixed. Q1 lists N7, c6b-2 (conditional on Q2), review-design-3. Q3 is a yes/no with default. Q4 is the role-test question with default none (decision 3). Q5 reconciles three roles (S1b) with four logins (parked). Labels Q1 to Q10 are consistent. NOT FIXED: Q1 still lists c6b-6 as waiting. It belongs to Q2. Apply the fix named at the top. |
| design nit: line 3 "no further review round" | report head | Fixed. Replaced with "draft for the next independent review; the lead decides". |
| design nit: "about a minute" rounding needs lead acceptance | Q9, section 7 | Fixed. Q9 asks for acceptance and states the rounding is mine. |
| design nit: line 112 "nine lines contain K3" carried over | row F-007f, section 9 item 2 | Fixed. Marked "carried over" per row. |
| design nit: gate item 2 conditional on the 8-flow count | G-3 | Fixed. The count 8 is marked as carried over, with a fallback to "all built flows". |
| design nit: F-020 gate vs housekeeping | rows F-020a, F-020b | Fixed. Split. F-020a is housekeeping with a stated promotion rule. F-020b is LATER VIDEO. |
| design nit: F-022/N6 reliance on F-019 not read | rows F-022, N6 | Fixed. Stated in both rows. |
| design nit: glossary N7-N9 wording | section 10 | Fixed. |
| design "not checked" (scenes 1-4, plan port and decision 8, line 14, v9:288, lane3 numbers) | sections 2, 5, 9 | Partly fixed. The plan port, decision 8, line 14 and v9:288 are now read. NOT FIXED: scenes 1-4 (run sheet absent) and the lane3 numbers (carried over, not re-checked). |
| naive M1 (UTC/IST missing) | section 3 gate intro, section 8 voided runs, section 9 item 8, Z1/D12 rows | Fixed. 17:09:59Z to 17:16:35Z is also given in IST (22:39:59 to 22:46:35). 23 Nov 18:29 UTC = 23:59 IST. 25 Nov 15:00 UTC = 20:30 IST. "Tonight or tomorrow morning IST" is given in UTC. 10:13 UTC = 15:43 IST. |
| naive M2 (compound statuses; STILL OPEN rows not on lists; N3b, N7, N8 absent from section 3; F-006 filed as housekeeping) | sections 1, 3, 5 | Fixed. Compound statuses are split into one status plus a Notes column (N1, N3a, F-007a, F-007g, c6b-1, F-020, N8, N9). F-006 is now a gate row (G-8). N3b, N7 and N8 are in section 3. |
| naive M3 (claims stronger than evidence: M2 zero hits, N7 faster alert, "stopped while the mail was being sent", "table", F-011 DB_* names) | rows M2, N7, F-007a to d, F-011, section 6 | Fixed. M2 "0 hits" is marked carried over. N7 is reconciled with section 7, and lane3 REPORT.md:18 is marked NOT FOUND. The wording is "killed when the mail connection opens". "Before the table was updated" is dropped, because the CRM flag was already set (recompute:32). Claim table and CRM are named separately. F-011 no longer says the DB_* names "exist". It cites DECISION-one-store line 14 and says n8n_start.sh was not checked. |
| naive M4 (labels before definition; no pointer to glossary) | section 1 pointer, section 10 | Fixed. Section 1 points to section 10. Section 10 defines run sheet, page, caption, closing card, kill cases, demo, n8n, T-ROLES, group L, S1b, G5, c6d, zoom-out, flows audit, K1 to K6. T-ROLES and group L are marked "not defined" or UNKNOWN. |
| naive nit: unknown vs UNKNOWN; lane, row, run, table | section 1 table | Fixed. One word, one meaning, with replacement words. |
| naive nit: line 38 vs 118 (is lane3 a person) | section 1 | Fixed. Stated as "not stated in any file I read". |
| naive nit: empty field-name cell in section 8 | section 8 last row | Fixed. Filled with "label, point". |
| naive nit: D2 omits v7:137 | row D2 | Fixed. |
| naive nit: Q2 "(new)" meaningless; Q3 unlabelled | section 3 | Fixed. |
| naive "not checked" (plan lines 38/558, v9 hits, ledgers, c6b, raw-c6e-checks.txt) | sections 2, 9 | Partly fixed. Plan lines 38, 73 and the line count 558 are read. The v9 "twice" hits (lines 18, 408) are used. NOT FIXED: raw-c6e-checks.txt and the ledgers (existence only) were not read. |
| lead Q15.1 (film-v5 out; plan edit as text) | row P1, section 4 | Fixed as text only. The plan edit is given for the lead. Real-v5 against stand-in services on loopback is an open point for the lead. |
| lead Q15.2 (clean start) | row CS1, G-10 | Fixed. One numbered row in steps v4+ is requested. Owner of the step is the lead. |
| lead Q15.3 (claim sentence, lease-expiry sentence) | row CL1, sections 2 and 7 | Fixed. |
| lead Q15.4 (spend limit by owner eye plus stage program) | row D5a | Noted. |
| lead Q14 (A-01 deferred, C-01 cut, G5 kept) | rows Z1a, Z1b | Noted. The G5 text and file are still unknown. |
