# BATCH6 summary
head d42737de30cb8b75d6ab43efde00e5c7774f0cf7 ; 2026-11-20 ~08:48Z ; Python 3.13.18 (sha256 in BATCH6-env.log)
1 lint: ruff check All checks passed; ruff format --check: 2 files would be reformatted (handover/core-a/tickets/E-test-helpers.md:81 [md code block], handover/core-a/tools/board.py:23), 432 ok
2 bandit -ll -r src: prints summary "No issues identified" (Low 7 / Med 0 / High 0 with nosec noted), rc=0
3 suite: 14 failed, 12221 passed, 458 skipped, 75 xfailed, 8 warnings in 320.37s
4 combined (core-b 70c61a4b6, scratch ev6-b): STILL RUNNING at hand-off, ~72% in crash-matrix tests, see BATCH6-combined.log; n8n does not exist in core-b (archive without it)
5 mutants: SKIPPED ON PURPOSE (coordinator order)
