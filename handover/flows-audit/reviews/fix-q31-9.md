# fix-q31-9 (fixer log, Mon 16 Nov 2026)

Scope: QUESTIONS.md (Q31 only), patches/F-003-runsheet-claims.patch, this log. Nothing committed. FINDINGS.md and LEDGER-ROWS.md NOT edited (another reader is reading them).

## What I did NOT verify (first)
- What TAKE-CHECKLIST.md GO row 6 holds was NOT re-read; item 89 takes it from the ledger text (fix-findings-ledger5.md A) and says UNVERIFIED.
- The five defaults in items 89 to 93 are audit proposals, marked "lead to confirm"; none is a decision of the lead.
- The F-003 patch was only checked with `git apply --check` on a scratch copy of handover/demo/VIDEO-RUNSHEET.md; the patch was not applied for real and the changed run-sheet sentences were not read against rebuilt flows.
- Other copies of the F-003 patch (patches/archive, patches/archive-pre-decision1, patch-apply/) were not touched or searched for the old retention sentence.
- No ORDERS.md line was re-read; "ORDERS.md line 156" in item 93 is copied from FINDINGS.md.

## Q31 changes (QUESTIONS.md)
New items after item 88 (next free number was 89; re-grepped, items ran to 88): 
- 89 = A (F-003 vs GO row 6; take at Wed 18 Nov 06:00Z = 11:30 IST); answer by Tue 17 Nov 06:45Z = 12:15 IST.
- 90 = B (F-007 still open at Wed 06:00Z); Tue 07:00Z = 12:30 IST.
- 91 = C (F-031 same); Tue 06:30Z = 12:00 IST.
- 92 = D (T19 fails about 07:00Z Wed = 12:30 IST; does the 07:30Z = 13:00 IST check move); Tue 07:00Z = 12:30 IST.
- 93 = E (may the owner overrule a Blocker rating or a NO-GO); Tue 06:50Z = 12:20 IST, with item 6 (order: 83, 93, 6).
Each has one question, WHO ANSWERS: the lead, ANSWER BY in UTC and IST, and IF UNANSWERED: AUDIT PROPOSAL, lead to confirm, with the schedule effect (the take does not run / slip rule of items 84 and 85; item 93: the owner step does not run, schedule unchanged). Item 66 (the index) got the new items in the 06:30Z, 06:45Z, 06:50Z and 07:00Z rows (tags and IF NOT) and three group D lines.
Counts updated in all five places (line 40 table, line 42, the Q31 count paragraph, the Note after item 88, the "32 to 88" and "67 to 87" ranges): 86 numbered items in the main list (1 to 39 and 47 to 93), 84 [OPEN], 94 labelled in all, 86 [OPEN].

## F-003 patch
The three sentences "the 4 real-v5 flows save no runs, so the list is empty until the patch ... is applied" (patch lines 17, 84, 106) now say: apply F-008 first; before F-008 the four real-v5 flows save no runs; after F-008 "saved runs are on for mf-form, mf-hook and mf-sub-crm-mail (F-008)" (the true sentence of the F-003 cell in FINDINGS.md). One-line replacements, hunk counts unchanged.
`git apply --check` on a scratch copy of VIDEO-RUNSHEET.md: rc=0 before and rc=0 after.

## Lines the LEAD must change (FINDINGS.md and LEDGER-ROWS.md; same text in both; I did not edit them)
FINDINGS.md line / LEDGER-ROWS.md line:
- FINDINGS 16 (words list, WHO DECIDES WHAT): "(question text in reviews/fix-findings-ledger5.md); no Q31 item asks it" -> "(Q31 item 93 asks it)".
- FINDINGS 110 = LEDGER-ROWS 3 (F-002): "(question text in reviews/fix-findings-ledger5.md; no Q31 item asks it) whether the 07:30Z check moves when T19 fails" -> "(Q31 item 92) whether ..."; also drop "the nearest Q31 items are" for 8 (e) and 49 if desired.
- FINDINGS 111 = LEDGER-ROWS 4 (F-003): "(question text in the audit log, reviews/fix-findings-ledger5.md, because no Q31 item exists for F-003)" -> "(Q31 item 89)"; the later sentence "the nearest Q31 item is 31" can say "item 89 asks it; item 31 asks the same for F-018". The same cell's patch-sentence text ("patches/F-003-runsheet-claims.patch still carries the old sentence and is not edited by this fixer") is now false: the patch carries the F-008 sentence.
- FINDINGS 112 = LEDGER-ROWS 7 (F-007): "(question text in reviews/fix-findings-ledger5.md; Q31 item 11 asks only who applies ..., and no Q31 item asks that)" -> "(Q31 item 90)".
- FINDINGS 113 = LEDGER-ROWS 8 (F-031): "(question text in reviews/fix-findings-ledger5.md); the Q31 items that exist for F-031 are 17, 23, ..." -> add Q31 item 91 (due Tue 06:30Z = 12:00 IST).
Also reviews/fix-findings-ledger5.md says "no Q31 item asks it" (a log, history; leave).

## Checks (output)
- check_refs: PASS 5176 references (rc=0)
- check_names: PASS 655 rows (rc=0)
- check_secrets: PASS 0 hits in 2013 files (rc=0)
- ruff format --check (run from the repo root on handover/flows-audit): 726 files already formatted
- Own grep count (labelled items from line 420): main list 86 numbered = 84 [OPEN] + 1 [NOTE] (66) + item 20 [ANSWERED]; second list 40 to 46 = 1 [OPEN] (40), 5 [NOTE], 1 [ANSWERED] (43); plus 15A [OPEN]: total 94 labelled, 86 [OPEN]. (The plain regex `^[0-9]*\. \[OPEN\]` finds 85 because 15A has a letter; with 15A, 86.)
