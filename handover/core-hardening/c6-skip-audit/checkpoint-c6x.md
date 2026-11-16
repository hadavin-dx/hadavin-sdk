# checkpoint c6x (builder), written 2026-11-16 about 20:20 UTC = 01:50 IST (first checkpoint)
START 20:0x UTC; box 60 min, end about 21:04 UTC.
DONE: inputs read; evidence-c6x/ set up; v35/v19 comparison by script (compare-late-files-output.txt: all three pairs DIFFERENT, c6w-CHANGES 6a was wrong); pinned the steps files (steps-pinned, late-pinned, hash lists) so the checks no longer depend on the live folder (the cause of the 75 D-late first failures, to be confirmed with a command); build_c6x.py builds REPORT-c6x.md + REPORT-c6x-TABLE.md + REPORT-c6x-COVERAGE.md (box 2492 words, limit 2500).
NEXT: make verify-c6x.py pass on the new text (20 checks failed at the first run, mostly c6w counts and names), then rewrite the negative harness (intended check per copy, six new controls from the independent run), run_all.sh twice at most, c6x-CHANGES.md, final report.
BLOCKERS: none yet. NOT RUN: n8n, stopwatch, take script. No commit, no sub-agent.
