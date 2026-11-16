# fix-cite9 (2026-11-16): FINDINGS.md cites from reviews/citation-r8.md

Result: FINDINGS.md was NOT changed (diff against backup bak-cite9.md is empty). Reason below.

## What I found
All 28 FINDINGS.md MISMATCH rows (citation-r8.md lines 43-70) are cites written in QUESTIONS.md (found at QUESTIONS.md lines 108, 113, 116-120, 140, 203, 209, 235, 279, 297 in the checker's copy) that point INTO FINDINGS.md. FINDINGS.md itself holds none of these cites (grep "FINDINGS.md" in it hits only prose lines 23, 31, 58, 103, none a line cite). The wrong text is in a file I was told not to edit. I did not touch QUESTIONS.md.

## Checked by me (current FINDINGS.md, 153 lines): the checker is right on every row
F-id: real line (cited line): F-002 109 (108); F-007 111 (110); F-013 130 (128); F-031 112 (111); F-041 118 (117); F-044 151 (150); F-023 126 (124); F-012 127 (125); F-014 131 (129); F-019 135 (134); F-022 138 (137); F-025 140 (139); F-035 147 (146); F-036 148 (147); F-039 150 (149); F-045 152 (151); F-005 124 (122); F-006 125 (123). Range "122-125, 129-151": 122-125 hold F-043, F-001, F-005, F-006; F-023 is 126, F-012 127. Line 89 is blank; the counts/BEFORE-AFTER text sits on line 88 (heading line "Counts after ORDER 007 ..."). No row rejected.

## Recommended fix for the lead (QUESTIONS.md owner)
Replace every "FINDINGS.md:<n> (F-xxx)" with "FINDINGS.md row F-xxx" (stable name; row order in FINDINGS.md changes whenever severity changes, so line numbers drift). Replace "FINDINGS.md lines 122-125, 129-151" with "FINDINGS.md rows F-043 to F-046 (Nit block)" or list ids. Replace "FINDINGS.md:89" with "FINDINGS.md, the 'Counts after ORDER 007 ...' paragraph". Note QUESTIONS.md was being edited (line numbers of the citing rows moved since the checker's copy); locate by text, not line.

## Not mine (5 further D rows on OWNER-STEPS-q16-rows.md) left alone.

## LEDGER-ROWS.md
No cell text changed, nothing to list.

## Gates (run from handover/flows-audit)
count_findings.py FINDINGS.md: rc 0, 45 rows = 5 Blocker, 5 Major, 35 Nit. check_secrets.py rc 0. check_refs.py rc 0 (PASS 5168 references). ruff check . rc 0. ruff format --check . rc 0. No citation checker script exists in tools/ (the round-8 check was an ad-hoc python run), so I did not rerun it. Not committed.
