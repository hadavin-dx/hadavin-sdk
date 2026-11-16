# REVIEW of the system-map outputs (ORDER 005), independent cross-review
Reviewer: cloud session flows-audit. Date 2026-11-16 (UTC; IST = UTC+5:30). Target: branch cloud/system-map head 707768f, folder handover/system-map (MASTER-MAP, SWEEP, ONE-PLACE-TABLE, fix plan, cut proposals). Static review only: no runtime, no real data. Raw evidence: evidence-5.md. Lane reports: lane-R5-B/M1/M2/D/Z/C.md. Merged list: resolve-r1.md. Exact fixes: CORRECTIONS.md. Ledger rows: LEDGER-ROWS.md.

## Verdict: PASS WITH CORRECTIONS (not a clean pass)
The facts mostly hold. The severities, five table verdicts and the "nothing with a caller is archived" rule do not. Do not run the archive steps (fix plan rows 8-12, 18-24) until XR-5, XR-6 and XR-7 are fixed. Do not give the studio head the headline as it is (XR-18).

## What failed (failures first)
1. **Blocker count is inflated.** 20 of 20 raw Blocker rows have correct citations (evidence-5: every cited line exact, lane-R5-B), but by the PLAN-005 rubric only 4 distinct issues are Blockers (XR-25): L1c-FD-021 (false claim in live PR text), L2-FD-002 with the leak half of L6-FD-001 (made-up e-mail, name and key canary in n8n's own file), L2-FD-008 = L6-FD-005 (mail lost with no alert), L4c-FD-002 (key forwarded after a redirect and printed in a traceback). 13 rows are Major, 1 is Nit. The lane header said 11; the row list gives 13 (my lane's slip, corrected here).
2. **"Nothing with a caller is archived" is false** for rows J-012, J-019, J-039, J-049 and J-055 (XR-5). The caller grep was never reported (REPORT.md:4). Two of them (J-049, J-055) hold the evidence for open Blockers.
3. **The archive destination breaks a project rule** (archive/ is outside handover/; CLAUDE.md "no private notes outside handover/"; the CI allowlist covers handover/ only) (XR-6).
4. **Wrong owner and wrong duplicate calls:** COUNTER Owner line (XR-1), J-005 (XR-2), J-037 vs J-008 (XR-3), J-042 (XR-4), J-028 with callers (XR-7), J-058 NOT-NEEDED for a live credential (XR-8), J-025 and J-041 "OK" while rated Blocker (XR-10), J-052 intake mail (XR-11).
5. **Fix plan row 1 is not config-only** (XR-12); rows 15 and 16 are banded inconsistently and 15-17 are findings not actions (XR-13); bands are real but labelled wrongly and not in an order of work (XR-19).
6. **Open decisions are not decidable as posed** (XR-14, XR-15, XR-16, XR-17); the headline omits counts and a fifth decision (XR-18); two lists of the decisions differ (XR-17).
7. **The target MISSED** (XR-21 unauthenticated public webhooks with no dollar cap; XR-22 dedupe key is only the caller's submission_id, empty id has no trace; XR-23 n8n env access allowed; XR-24 missing rows: secret/env files, journal writer identity, counters, backup). XR-21 and XR-23 depend on the take (UNVERIFIABLE).
8. **Sweep Majors:** 44 of 105 sampled Majors are Nit by the rubric (XR-29); 12 rows have no claim sentence (XR-27); 6 rows are wrong or partly wrong and 6 overstated (XR-28); 2 possible Blockers hide in Majors (XR-30, UNVERIFIABLE here).

## What holds
Table counts hold (59 rows = 49 + 10 appendix; per-job counts STORE 11, LOG 9, FILTER 9, COUNTER 5, RETRY 8, NOTICE 6, OTHER 1; 183 = 18+66+99; 11 ARCHIVE rows: 5 plain, 6 blocked; verdict totals in evidence-5:578-591; lane-R5-C and lane-R5-Z). 20 of 20 Blocker citations exact. The one-store DECISION is consistent with the table except where noted. FILTER, RETRY (except J-042), LOG and NOTICE owners are right. Bands "before / only if chosen / after" are the right split.

## Citation verdicts (stop rule)
| scope | CONFIRMED | WRONG | UNVERIFIABLE | source |
|---|---|---|---|---|
| 20 raw Blocker rows | 20 facts (some counts slightly off) | 0 | parts: cause of n8n file hit, patch/paste state, take repo | lane-R5-B, evidence-5 |
| Majors sampled by R5-M1 (70 of 140 in lines 61-200) | 62 on cites (categories overlap: 6 overstated) | 4 (L1-FD-025, L3c-FD-007, L3c-FD-018, L4-FD-011) | L2-FD-019, L3c-FD-030, L3c-FD-037, L1-FD-032 (parts) | lane-R5-M1 |
| Majors sampled by R5-M2 (35 of 69 in lines 201-355) | 32 | 2 (L4-FD-021 cite wrong, L5a-FD-008 partly) | 1 (L6-FD-025) | lane-R5-M2 |
| total Majors checked | 105 of 209 (stop rule 105: met, exactly) | | | |
Severity on the 105 (lane counts): agree Major 48 (M1 31, M2 17); Nit by the rubric 44 (M1 27, M2 17); no claim sentence 12 (M1); meta row 1 (L4-FD-021). 48+44+12+1 = 105.

## Table verdicts (59 rows)
AGREE 39 (includes J-034 as the OWNER row, read through XR-1). DISAGREE 8 (J-005, J-037, J-042, J-058, J-049, J-039, J-012, J-055) plus the COUNTER Owner line. CANNOT-JUDGE 12 (J-003, J-011, J-014, J-020, J-027, J-053 and desk rows J-004, J-016, J-029, J-036, J-044, J-054). 39+8+12 = 59. Per-row detail: lane-R5-D "Per row".

## The 4 open decisions
(1) dollar-cap place: right question, not decidable (no figure, options missing) XR-14. (2) second alert channel: need real only for a permanent outage; no candidates XR-15. (3) what the proof counter reads: wrongly posed, DECISION:11 already answers it XR-16. (4) independent count outside n8n; three roles vs a fourth identity: well posed; the fourth identity contradicts DECISION:14 unless the lead amends it XR-8. A key-rotation decision for the studio head and a fifth (one more lane for 183 unread files) are not in the same list XR-17, XR-18.

## The three bands
Real: before the video as decision/config (rows 1,2,3,7,13,14,16,17), only if chosen (4,5,6), after (8-12,15,18-24). Not right: row 1 (XR-12), 15 vs 16 (XR-13), row 11 and row 21 (XR-19, XR-5), row 24 (XR-8). Whether the three Blocker bands "are real": the bands are real; the Blocker grouping is not (XR-25).

## Cut list judgement
Proposed for deletion instead of archive: none outright; but J-028 (remove dead nodes), J-042 (remove node retry), J-018 and J-040 (merge) are removals while the table says "nothing is deleted" (XR-7). NEEDED called DUPLICATE: J-005, J-042 (and J-037 vs J-008 contradictory). DUPLICATE or NOT-NEEDED that is needed now: J-058, J-049, J-055, J-012, J-019, J-039. The reverse (a duplicate called needed) was not found in the checked part.

## Not checked (honest list)
Take repo (film-v5, real-v5, qualify_stage.py), n8n runtime, HubSpot, SMTP, git state of tracked files and whether pending patches were applied; 104 unsampled Majors; 183 files the target did not read; MASTER-MAP.md (797 rows, only through lane citations); SWEEP.md rows 279+ (R5-M2 stopped after line 279 of its range) and rows 88-473 by R5-Z; every one of the 59 rows' evidence citations; the exception list L6-EX-01..11; 12 CANNOT-JUDGE table rows. The reviewers (egm agents) are read-only; I saved their reports myself (condensed, every finding kept). My evidence runner sampled every 3rd Major, existence only (evidence-5); judging of support was done by the reviewers.

## Rounds
Plan review round 1 (fixed in plan v2). Result: lanes round 1 and resolve round 1. Round 2 only after the draft review below.
