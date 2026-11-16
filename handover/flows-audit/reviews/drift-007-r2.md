# Drift check r2 of the audit documents against reviews/drift-007.md (read-only; nothing run in n8n, HubSpot, SMTP or Postgres)
Read between 15:58Z and 16:00Z on Mon 16 Nov 2026 (`date -u`: 15:58:17, 15:58:24, 15:59:23). This file replaces an older 12:02Z file of the same name (a different review of the patches, 2042 bytes); that older text is gone from this path. FIX-PLAN.md, RUNBOOK.md and TAKE-CHECKLIST.md were still being written (mtime 15:58:11) when I read them, and QUESTIONS.md at 15:56:09, so line numbers below may move. Fixed nothing. Raw output of my scripts was not saved as a file.

## Counts (commands run)
- `python3 -I tools/count_findings.py`: rows 45 unique 45; Blocker 5 (BEFORE 5, AFTER 0), Major 5 (5, 0), Nit 35 (1, 34), all 11 + 34 = 45. SAME as drift-007.
- FINDINGS.md and LEDGER-ROWS.md: 45 ids each, identical id sets, severity first word 5/5/35 in both, no severity difference per id. STILL TRUE.
- F-numbers in FINDINGS, FIX-PLAN, CUT-LIST, EXCEPTIONS, QUESTIONS, LEDGER-ROWS, TAKE-CHECKLIST, RUNBOOK, RUNSHEET-WORDING, CLAIMS-TABLE, REPORT: none outside F-001..F-046 (script scan). STILL TRUE.
- patches/ holds 4 .patch files (F-002, F-003, F-004, F-008); F-001 only in patches/archive/. STILL TRUE.

## NEW since drift-007
1. QUESTIONS.md Q31 totals are stale in two places and right in two others.
   - Grep `awk 'NR>=420' QUESTIONS.md | grep -E "^[0-9]+[A-Z]?\. \["` gives 104 lines: 96 OPEN, 2 ANSWERED (items 20, 43), 6 NOTE (41, 42, 44, 45, 46, 66). Item 15A is at QUESTIONS.md:688 (written "- 15A. [OPEN]", not matched by that grep, so +1 labelled, +1 OPEN): 105 labelled, 97 OPEN. Main list = items 1-39 and 47-104 = 97 numbered.
   - Correct (match grep): QUESTIONS.md:452 and :629 ("97 numbered items ... 95 OPEN ... 105 labelled, 97 OPEN").
   - STALE: QUESTIONS.md:40 (index row Q31) says "86 numbered items ... numbers 1 to 39 and 47 to 93 ... 84 [OPEN] ... in all 94 labelled items, 86 of them [OPEN]". QUESTIONS.md:42 (LEAD-ACTION COUNT paragraph) repeats the same 86/93/94/86. Both lack items 94-104 added by fix-q31-11.
2. Table-format break in F-041. The row FINDINGS.md:128 splits into 12 cells (11 expected) and the same row in LEDGER-ROWS.md into 11 cells (10 expected): a literal pipe character sits inside the fix cell (text `... single database'` ...). Effect: the status cell reads "lanes7 N7-7" (sources column) in a naive split, and the status "OPEN (new, ORDER 007)" lands one column late. count_findings.py still counts the row, so counts are unaffected; a tool that reads columns by position gets F-041's status wrong. Not in drift-007.
3. Item numbers cited from other files: every "Q31 item N" in FINDINGS, FIX-PLAN, CUT-LIST, EXCEPTIONS, QUESTIONS, LEDGER-ROWS, TAKE-CHECKLIST, RUNBOOK, RUNSHEET-WORDING, CLAIMS-TABLE, REPORT, STATUS-BOARD is within 1-104; none above 104; items 40-46 cited only as item 45 (RUNSHEET-WORDING.md:31, 268, 269, 345, 412), which exists ([NOTE]). No dangling item.
4. Times. All 619 "HHZ = HH IST" pairs in QUESTIONS, FIX-PLAN, TAKE-CHECKLIST, RUNBOOK, FINDINGS, RUNSHEET-WORDING, CUT-LIST, EXCEPTIONS, LEDGER-ROWS convert correctly (IST = UTC + 5:30); no wrong pair.
5. Same input, different time or rule between files (both halves are marked open by the audit, so this is difference, not hidden error):
   - HubSpot token-scopes ask (Q27 item 2): QUESTIONS.md:78 (L22) says ask before Tue 17 Nov 05:54Z (11:24 IST), not Wednesday 07:00Z. FIX-PLAN.md:53 and TAKE-CHECKLIST.md:47 say "asked Wed about 07:00Z, reply wanted 08:00Z, no reply by 08:30Z means no recording that day; stays Wednesday unless the lead decides by Mon 21:00Z" (Q31 items 27, 30). TAKE-CHECKLIST.md:78 itself notes the clash. Also QUESTIONS Q31 item 30 reading 1 says silence blocks nothing, while FIX-PLAN.md:53 says no reply blocks the recording. Not settled by the lead.
   - Rehearsal 1 start: QUESTIONS.md:67 and :87 say 07:40Z (13:10 IST); QUESTIONS.md:86/:132 and FIX-PLAN.md:71 put a positive-control mail run at 07:30 to 07:40Z and passes from 07:40Z inside a block that starts 07:30Z; TAKE-CHECKLIST.md:115 calls the rehearsal window "about 07:30Z to 09:30Z". Q31 item 101 asks which is right (OPEN); RUNSHEET-WORDING.md:167 quotes both. Consistent with item 101 being open.

## STILL TRUE from drift-007
- FINDINGS.md:95 says "items 2 to 9 are left, 8 items"; FIX-PLAN.md:64 heading says "9 numbered items plus 8b". Wording difference only (FINDINGS.md:95 explains items against rows).
- STATUS-BOARD.md: ITEMS_TOTAL is now 10 (was 12) but ITEMS_OPEN is still 30, larger than the total. STATUS-BOARD.md:54 still says "Answer Q4-Q9 in QUESTIONS.md ... " although REPORT.md:31 says Q4 to Q9 are ANSWERED.
- REPORT.md:83 ("34 findings = 2 Blocker, 23 Major, 9 Nit") and :102 (older dated sections; no SUPERSEDED mark in place) unchanged.
- FINDINGS.md:55 (item 15, "Load, burst-size and isolation numbers (rule R370) were out of scope; only the 10-at-once test M1 exists") still a plain statement with no next step: OPEN under fix-dont-defer (no exception 2(a)/(b)/(c) named).
- bash tools/check_patches.sh printed "SKIP no patches" again (not a PASS). Whether the 4 patches apply is NOT verified by me; lanes7/evidence-patches-r5.txt exists but I did not read it.

## FIXED since drift-007
- FIX-PLAN.md F-018/F-019: the heading at FIX-PLAN.md:64 now says F-018 is rated Major and F-019 is a Nit rated AFTER the video with no BEFORE item. The old "Nit-rated lines (F-018, F-019, F-028)" sentence is gone (grep "Nit-rated" in FIX-PLAN.md: no hit).
- Old brief numbers 8/8/29 and 17/28 appear only as marked history (not re-checked line by line).

## Trigger words (file:line, classification)
- limitation, TODO, deferred, skipped, not verified: 0 hits in FINDINGS, FIX-PLAN, CUT-LIST, EXCEPTIONS, QUESTIONS, LEDGER-ROWS.
- out of scope: FINDINGS.md:55 only = OPEN (see above).
- could not: FINDINGS.md:124 and LEDGER-ROWS.md:11 (F-008, "could not tell an applied patch from an unapplied one" describing the old guard) = history, fixed by the new guard text; QUESTIONS.md:385 (a reader's finding, quoted) and QUESTIONS.md:460 ("a fill after 08:00Z could not be checked by step 13": a stated rule, tied to Q31 item 8) = stated.
- not done: FIX-PLAN.md:104 ("row not done" = a pass/fail word) and :122 (NO-GO rule) = stated rule; FIX-PLAN.md:128 (F-005, F-006, F-023 "not done before the video", Nit for a later video, Q14) = stated exception; QUESTIONS.md:91 (IF NOT DONE rule), :251 (FIX-PLAN item 8 waits, Q21 gate), :455, :531, :554, :587, :603, :604 (steps that stay "not done" if the lead gives no answer; each carries IF UNANSWERED and a lead-to-confirm default) = stated, waiting on the lead (exception 2(b)).
- EXCEPTIONS.md and CUT-LIST.md: no trigger words.

## Not checked
Anything needing n8n, Postgres, HubSpot or SMTP; whether the 4 patches apply; lanes7/ and patches/ content (only listed); ledger_check (not in this repository); per-node tables in FLOWS-AUDIT.md; every other same-input time (only the HubSpot ask, rehearsal start and the Z/IST arithmetic); the revert cases of Q19 and Q21; RUNBOOK.md and TAKE-CHECKLIST.md beyond F-ids, Q31 item numbers and times; CUT-LIST.md and EXCEPTIONS.md line by line; first-word status agreement beyond the F-041 cell shift (the other 44 rows agree in a column-by-position compare).
