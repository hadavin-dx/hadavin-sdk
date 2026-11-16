# fix-findings7 (fixer, round 16Z section C, 2026-11-16)

Files edited: FINDINGS.md, LEDGER-ROWS.md. Backups: scratchpad bak-fl7-FINDINGS.md and bak-fl7-LEDGER-ROWS.md. Nothing was run in n8n; static edits only.

Rating changes (counts recounted by `python3 -I tools/count_findings.py`: Blocker 5, Major 5, Nit 35 = 45; BEFORE 11, AFTER 34; before: 5/7/33, BEFORE 13, AFTER 32):
- F-004 Major to Nit (file not shown, not reachable in the take; patch still applied at re-pin).
- F-042 Major to Nit, F-043 Major to Nit (not reachable; Blocker-if-said grep line; alert text stays as is).
- F-018 Nit to Major (reachable: CrmUpsert error, false CrmIdOk and Qualify error go to OutStage before MailClaim; pass line = FIX-PLAN step 10b).
- Kept: F-002, F-031, F-007 Blocker (lead ruling); F-011, F-041 Major (Q21, deadline Tue 17 Nov 14:00Z).

Other edits: F-002 WHY restated, T19/T20/T21 pass lines, fallback decision proposed; F-003 and F-008 titles narrowed; F-007 pass line, owner and date; F-031 second pass line; F-011/F-041 deadline, automatic NO-GO, downgrade evidence, wording conditional on fix A, take cell; LEDGER-ROWS: 11 rows re-copied, take-path flag added to all 45 area cells.

Edits needed in files this fixer may not edit: see the report to the lead.
