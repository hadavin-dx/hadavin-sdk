# c6r independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: c6-skip-audit/evidence-c6r-independent/. REPORT-c6r.md sha256 c5326b55a9295c09d5dbc8386897bb080d20eebbb8db77a6025389e4d3161950 before and after. Recorded, not judged.

## Failures and deviations first
1. New owner sheets after the check time: report check time 16:52:47Z (22:22:47 IST) names v29 newest; at about 16:56 UTC the folder steps-edits also holds OWNER-SHEET-v30-A/B (16:54:56Z = 22:24:56 IST), v30-SOURCE (16:54:50Z = 22:24:50 IST), appendix, card, film person page and v30-OPEN-FOR-LEAD. L-SHEET line and section 0 are stale.
2. Builder's verify-c6r.py rerun as is: 123 checks, 2 FAILED, exit 1 (check time names newest sheet v30; no owner sheet changed after the check time).
3. Builder's neg_controls_c6r.py rerun: 78 copies, 1 wrong (V0, the unchanged control, exits 1 because of 2); the other 77 exit non-zero as expected.
4. static-checks.sh glob (OWNER-SHEET-v19 to v2x) does not include v30; C-10c phrase counts on v30 counted by hand: A 0/0/0/1, B 0/0/0/1, SOURCE 0/0/0/2 (same pattern as v29).
5. Source copy: only 5 of 94 rows (DECISION-one-store.md) can be read in the repo; the other 89 name files not in the repo; the scratchpad copy cannot be shown equal to the real files (matches the report's own statement).
6. The runner ran a copy of neg_controls_c6r.py in the scratchpad (one line changed) to avoid writing into evidence-c6r/; builder files unchanged (sha256 listing identical).

## Own checker (39 checks, 0 failed)
94 rows, ids 1..94; old text once on its stated line for all 94 (89 vs scratchpad copy, 5 vs repo); rows apply in order; 94 = 49 + 36 + 3 (23, 58, 59) + 6 (53, 55, 62, 64, 66, 68); wave 1 = 85; printed lists match; 62 UTC times each with IST (61 explicit pairs exactly +5:30); weekdays and dates correct; card arithmetic for all 6 length-table rows; 17 "N words, about X s" statements; 11+35+22+22 = 90; no row-number references in new text; lease sentence on no row; no stale 58 s; no key shape or e-mail; 60.1 to 61.9 intact.

## Mutations
40 changed copies; run 1: 38 caught, 2 missed (one checker gap, widened; one not a real fault); run 2: 40 caught, 0 missed (not an unseen test). Banned scan 0 of 10 over report and runner files.

## Not run
n8n, flows, loopback re-smoke, import check, stopwatch (none exist); source-copy equality with the real files; v30 files against the report content beyond phrase counts; checks C-3 to C-9.
