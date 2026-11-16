# c6w independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: c6-skip-audit/evidence-c6w-independent/. Recorded, not judged.
## Failures and deviations first
1. The builder's "314 copies, 0 wrong" is NOT reproduced: runner got "316 copies, 5 wrong". Five changed copies exit 0 with 0 failed checks: R1-M-A-gate-removed-row8, U-card-words-90-first, U-card-seconds-36-first, U-budget-40-first, W-C7-row19-G12-hold-removed. In the builder's run the same 5 are "OK" only because D-late failed (live-folder state at 19:45Z while other sessions wrote v35/v19 files). The builder's caught rule counts any new failure. Misses are first-copy-only edits of text that occurs 13, 10, 6 and 1 times.
2. verify-c6w.py on the unchanged report exits 1 (V13: counts differ) when the builder's output files are moved aside; with them back: 272 checks, 0 FAILED. With the runner's own neg/scan outputs V13 would fail (expected: CHANGES numbers are the builder's).
3. REPORT-c6w.md last modified 19:44Z; run-log has 2 lines (19:35:07, 19:41:14); builder's run1-summary shows run 2 ended "verify exit 1 ... 11 FAILED" and "neg exit 1 ... 23 wrong"; the passing verify output was written 19:58 after a later build; not traced what produced the 19:44 version.
4. Runner's 30 hostile copies (29 real changes): 28 caught, 1 missed: 07-card-87-words-first (first "the card then holds 87 words" to 88, L-CARDLEASE row), same class as item 1.
## Passes
verify-c6w.py + parts 2-4 with builder frozen input: 272 checks, 0 FAILED (files in place); D-late passes against the report. scan_c6w.py: 38 files, banned 0 / secret 0 / mail 0 (builder scanned 336-349). verify on REPORT-c6v.md: 272 checks, 48 FAILED, identical failing check names. Forged counts (272->300, runs 2->3, copies 314->267, wrong 0->1, files 349->350, two COUNT lines deleted): each exits 1, only V13 failing; unchanged control exit 0. Two late mutants caught by D-late; V0 exit 0. Hostile edits caught: UTC/IST pairs, IST arithmetic, weekdays (25, 23, 18 Nov), row counts, wave 1, K3B, box word count, lease seconds, recovery interval, G12 OPEN to CLOSED, answer line and "does not do" line deleted, row 50 deleted, row 30 old text, row list swap, title, reviewer order, fake key/token/mail shapes, banned entry.
## Not run
run_all.sh, build_c6w.py, static-checks.sh (report not re-derived); why D-late failed only in the 5 copies; detail-section edits; mutation run, n8n, spend.
## Housekeeping
Hashes of REPORT-c6w.md and REPORT-c6v.md unchanged; no chmod; one heavy slot (7m14s); no processes left; src/ tests/ inputs/ untouched.
