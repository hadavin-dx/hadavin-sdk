# fix-rswording7 (RUNSHEET-WORDING.md), 2026-11-16, static, made-up data only, nothing committed

Before: check_runsheet_paste.py = FAIL, missing claim ids A-015, A-024, A-039, A-049, B-102.
After: RESULT: PASS; 176 rows (48 / 19 / 66 / 43); 87 flagged ids, none without a row; UNTRACED 47, 41 without a row (by design).
ruff check: All checks passed; ruff format --check: 579 files already formatted (no python file touched).

Changes (only RUNSHEET-WORDING.md):
- New rows A-015 and A-049 (DELETE, same old sentences as A-016c and A-016e); A-024 (DELETE of the last sentence only, later video); A-039 (string "No second lead mail in this run." from the table row); B-102 (NO PASTE: remove only the words "exactly 1 alert per lead"; the table gives no replacement and the quoted line is cut short with "...").
- N-4a and N-4b were old pastes that still said one alert ("An alert e-mail message arrives.", "an alert, no second lead e-mail message"); set to NO PASTE, superseded by A-024 and A-039 (Q19-3: no sentence about how many alerts come).
- Status table: A-015 and A-049 added to the CUT group; new status row for B-102.
- Verdict counts (line 19) now 119 / 70 / 61 / 29 / 48 = 327; row-count paragraph in section 6 updated.
- "2 runs" removed from A-023b, A-075, A-088 (and the A-023a note, line 174 glossary): now "the number of runs is not confirmed", "not lost in that test".
