# fix-questions1 (fixer log, 2026-11-16 11:58Z = 17:28 IST)
Task: apply reviews/style-questions-r1.md (blockers 1-6, majors 7-15) to QUESTIONS.md only. EGM skipped: restructuring of an existing notes file with no new claims (text move and labelling); the lead runs any review. Backup: scratchpad bak-q1/QUESTIONS.md (41243 bytes).

## What failed or is uncertain (first)
- Reviewer words were unverified; I checked each point against the file and ORDERS.md lines 105-171. All 15 points were real (listed below).
- UNVERIFIED and left marked: where the list "S9" lives; what round r24 contains; who must produce F-011/F-041 evidence before Tue 17 Nov 14:00Z (ORDERS.md names no person); whether CUT-LIST.md names the six archive candidates; the label "verdict 4" (defined nowhere I could read; replaced by plain words, original kept in History).
- Q15's answer is not in ORDERS.md (only in ANSWER-Q15-lead.md); stated in the index.
- Line numbers cited for other files (CLAIMS-TABLE.md, RUNSHEET-WORDING.md, FINDINGS.md) were read today and can drift.
- I did not run tools other than check_secrets.py; no other file was edited. Nothing committed.

## Review point -> what was done
1 Q2 stale "deleted at clean-up": current rule written in place; old line moved to History.
2 Q19 header: now says item 2 was reversed by Q25 item 2.
3 Q27-8 repeats Q25-8: both marked; Q25-8 now "answered by Q27 item 8: decision 1, 'and 4' dropped"; first answer kept in History.
4 Q27-10, Q28-3/4 repeat Q25-7: each carries a status and the chain (Step A removed, Q28 item 4 is the current owner list).
5 Undefined codes: GLOSSARY at top (F-002, F-007, F-008, F-011, F-013, F-031, F-041, F-044, T19-T21, S9-2, S9-3, RWQ-*, A-016c/e/f/g, P4a, Q-A/B/H/F, Row 4, Step A/D, take, re-pin, re-smoke, practice run, rehearsal, round with r20-r24, ledger (two kinds), row (three meanings), "lead" (session vs record), Tier B and column words of Q1, UNVERIFIED).
6 Questions needing another file: each of Q4, Q9, Q14, Q19, Q20, Q22b, Q26, Q27 now has key text or "answer by item/row number; texts at file:line".
7 Two Q22: first renamed Q22a; note for old logs in the index and under Q22a.
8 Q8 "verdict 4" replaced by plain words (original in History); Q4 marked "lead action pending" (re-smoke result).
9 Two-meaning words: glossary entries for round, ledger, row, take, re-pin.
10 Q25 header no longer "ALL 14 ANSWERED": per-item status; items 1, 2, 3, 5, 10-14 name the lead action.
11 Q26: answer lines added for items 2-5 (ORDERS.md line 147); wrong time stamp of the lead's block removed from the heading (kept in History); superseded re-smoke length and rehearsal time noted (ORDERS.md line 160, Q30).
12 Q27: per-item status and the lead's answer line for all 10 items (ORDERS.md line 156).
13 Q28/Q29: statuses and answer lines (line 166); Q28 item 1 caption stated in full as the current caption.
14 "Q30" twice: merged into one heading with the answer.
15 Q1 original text: glossary entry for Tier B, machine and judgement columns (from Q1's own words; PLAN-002.md section 1).

## Rules kept
- One status per question (index table, 30 rows incl. Q22a and Q22b; 31 "STATUS:" headings with the Q4-Q9 sub-lines).
- Only ORDERS.md lines 105-171 used for new answers; older answers cite their ORDER blocks. No answer invented; where the lead gave none the text says so.
- Lead time stamps 13:00Z-15:00Z are not used; dated schedule values only (with IST).
- Verbatim check: a script compared each old non-empty line with the new file; 14 old lines changed form on purpose (prefix removed, tags moved, Q27 intro shortened, Q10 line split into current + History); their content is present.
- No secrets, personal data or addresses added.

## check_secrets.py (from handover/flows-audit)
Command: python3 -I tools/check_secrets.py
Output: PASS 0 hits in 1734 files
