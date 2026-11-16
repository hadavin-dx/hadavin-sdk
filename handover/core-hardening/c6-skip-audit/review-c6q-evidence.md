# c6q independent evidence (EVIDENCE RUNNER, condensed copy of the report), 2026-11-16
Target: REPORT-c6q.md sha256 e9b5a06b3b83602cc3c7289363f976722e1601f41b50e4c06c4296e3e793f686 (same before and after). Raw: c6-skip-audit/evidence-c6q-independent/ (00-SUMMARY.md). Recorded, not judged.

## Failures and deviations first
1. Source copy not in the repo: the builder checks 89 of 94 rows against a scratchpad copy (nine of ten target files exist only there); against the repo 89 rows are unreadable. The report does not say which copy it used; equality with the studio's real files not verified.
2. Builder's verify-c6q.py now exits 1 (91 pass, 1 fail): OWNER-SHEET-v29-A.md and -B.md were written 16:34:17Z (22:04:17 IST), v29-SOURCE.md 16:34:27Z, after the report's check time 16:32:07Z (22:02:07 IST); the line "only a template of v29 exists" is stale. 54 of 55 builder negative controls right; "V0-control-unchanged" wrong because of this.
3. One fail in the runner's own checker: box line 50 example time 2026-11-16T16:40:00Z has its IST about 90 characters later (pair itself correct).
4. Builder's verify missed 8 of 32 planted mutations: weekdays not checked; lease sentence on caption row 21; capitalised "The lease question"; wrong "42 apply" count; wrong "91 rows" wave-1 figure; stale "58 s" in the box; "(within 45 seconds)" in row 14.
5. Runner's 32/32 is not blind (tuned after missing 6 first); builder's 24/32 is its script as written.

## Passes (runner's own checker, 41 pass, 1 fail)
94 rows, ids 1..94; each old text once on its stated line (scratchpad copy); counts 49/42/3 (rows 23, 58, 59), wave 1 = 91 agree everywhere; card lines 11/35/22/22 = 90 words, 36.0 s, budget 40 s, about 190 s; length table recomputed equals the report (words 90, 74, 115, 87, 130, 114; seconds 36.0, 29.6, 46.0, 34.8, 52.0, 45.6; budgets 40, 30, 50, 35, 55, 50; totals 190, 180, 200, 185, 205, 200); 40 UTC = IST pairs +5:30 and 11 weekday/date pairs right; no report label in any new text; no lease sentence in any row's new text; row 90 ends with database n8n; no "58 s"; 60.1 to 61.9 exact. Mutations: 32 of 32 caught, control clean. Folder scan (546 files): 0 banned, 0 secret-shaped, 0 non-example e-mail shapes.

## Not run
No n8n import, no C-3, C-4, C-5, C-8, C-9, no stopwatch; not verified: scratchpad copy equals real files, meaning of the 94 new texts, section 8 coverage, whole-file uniqueness of old texts.
