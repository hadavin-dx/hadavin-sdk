# checkpoint c6x (builder), written 2026-11-16 about 20:20 UTC = 01:50 IST (first checkpoint)
START 20:0x UTC; box 60 min, end about 21:04 UTC.
DONE: inputs read; evidence-c6x/ set up; v35/v19 comparison by script (compare-late-files-output.txt: all three pairs DIFFERENT, c6w-CHANGES 6a was wrong); pinned the steps files (steps-pinned, late-pinned, hash lists) so the checks no longer depend on the live folder (the cause of the 75 D-late first failures, to be confirmed with a command); build_c6x.py builds REPORT-c6x.md + REPORT-c6x-TABLE.md + REPORT-c6x-COVERAGE.md (box 2492 words, limit 2500).
NEXT: make verify-c6x.py pass on the new text (20 checks failed at the first run, mostly c6w counts and names), then rewrite the negative harness (intended check per copy, six new controls from the independent run), run_all.sh twice at most, c6x-CHANGES.md, final report.
BLOCKERS: none yet. NOT RUN: n8n, stopwatch, take script. No commit, no sub-agent.

## Checkpoint 2 (2026-11-16T20:28Z = 2026-11-17 01:58 IST)
DONE: REPORT-c6x.md built (box 2466 words, stated = counted; appendix split into REPORT-c6x-TABLE.md and REPORT-c6x-COVERAGE.md); verify_c6x_part5.py (class 8, C8-1 to C8-15) registered; verifier 287 checks, only the two run-count checks (D-m5, V13) open before the first run; negative harness rewritten (INTENT per copy, state-only failures never count, NOOP detection, changed copies counted without V0, 35 copy-position controls for the six misses, class 8 controls, a planted late file); c6x-CHANGES.md written by gen_changes_c6x.py.
RUNNING: run 1 of run_all.sh; its negative step waits for a free heavy-slot (all three taken by other sessions).
NEXT: read neg-output.txt, fix every WRONG copy, write run1-summary.txt, run 2 only if needed (cap 2), prove the six misses pass on c6w, final report.
