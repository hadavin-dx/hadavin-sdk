# Report: FIX-PLAN follow-up fixes (fixer 64b; static; nothing run in n8n; nothing marked passed)
## Unverified / not done first
- All new wording is untested static text. Owner/time values were copied from TAKE-CHECKLIST.md Inputs-list items, QUESTIONS.md and FIX-PLAN's own table; I did not re-verify them against RUNBOOK.md section 10.
- Where no source time exists (six-statements rows 1 and 3) I wrote the line-35 rule (owner the lead, Tue 17 Nov 04:00Z (09:30 IST), AUDIT PROPOSAL); this is a fallback, not a lead decision.
- Step-result words in the last table that name no committed command (items 25, 38 (b), 71, 80, 81, 79, 35) say "none printed" or "recorded judgement"; the judgement wording for 25, 80, 81 is my reading, the lead should confirm.
- Cross-references kept on purpose: `RUNBOOK section 10, M7 (b)/(h)/(i)`; `round 23` / `round 24` as the lead's code rounds (old lines 195, 275, 281).
## Per item
- M16 fixed: own owner and time added on old lines 14, 89, 91, 155, 195 (Machine, shell, REPO), 196 (port and a per-value owner/time list for values 1 to 10), 221, 230, 253, 255, 256 (x3), 257 (item 8, 8b), table rows. Steps 5, 6, 8 already had times in their own text (checked).
- M17 fixed: pairs added at old lines 12, 198 (slot list), 200, 229, 231, 232, 235, 241, 233, 249, 296, 302, 307, 313, 325, 327; Gated Wednesday schedule (lines 98-106) now `HH:MMZ (HH:MM IST)` in every cell. Lines 94, 105, 217, 221, 224 re-read: no bare time left. Lines 34 and 75 untouched. Script check: 417 pairs, 0 with offset other than 5:30. Line 28 `08:00Z = 13:30 IST` kept (a pair).
- M10 fixed: last-section table has seven columns with a Supplied word column and a Step result word column plus Responsible; rows 10 (a) and 38 (d) added; intro and BLOCKED-items paragraph reworded to match. 
- Labels moved: fixed. Round, finding, reader, gate 2 r2 labels removed from FIX-PLAN.md and listed by old line number in reviews/fix-plan-changelog.md (which I appended to, as the target of the move). Remaining `round` hits: lines about the lead's code rounds 23/24.
## Files changed
FIX-PLAN.md (now 329 lines because two table rows were added; lines 1-36 still 36 lines, lines 37-84 unchanged), reviews/fix-plan-changelog.md (appended), this file.
