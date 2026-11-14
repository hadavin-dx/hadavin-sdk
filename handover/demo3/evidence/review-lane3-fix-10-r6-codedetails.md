# Review lane3 fix-10 round 6, egm-codebase-details (saved inline by lane3, 10:3xZ)
Snapshot /home/user/work/lint-b23, tree 8a5c446e3b59a87b7568497b5ace90631d9b303a. Reviewer read only; ran nothing. Result: 0 Blocker, 0 Major, 2 Minor, 3 Nit.

Checks that hold (reviewer): full-run header (tree, one-commit scratch repo, py3.13, rc 0, 4409 passed, 179 skipped, 950 s; "failed" count not in log, 0 failed follows from rc 0); EXIT_CODE_TABLE built from constants, reset 5 and 8 wording exact; no demo_only in constants.py; no /usr/bin program paths in tests; exceptions.txt and .gitleaks.toml untouched by the patch; start_all.sh ready loop checks process alive AFTER the line, one shared deadline; config_exit.write_line writes UTF-8 bytes; pid-file tests never write own pid. NOT verified by reviewer: contents of tests/test_exit_code_table.py (two-meanings test, TOOL_PROGRAMS match), server.py call sites.

The 179 skips: reasons are in the xml, but the notes describe them wrongly. At least 150 are "could not import playwright.sync_api" (a whole browser-test suite did not run); 6 Windows PowerShell only; 4+ no IPv6; 1 measurement run; 1 root can read a no-permission file; 1 reset-destroys-reply Windows only. Notes said "Windows-only, IPv6-refused and tool-absent".

Mutation claim: log says tree 44219b37, true; the justification "later changes touch none" is false for tests/test_start_all_late_refusal.py (changed after 44219b37, kills r4-10 and r6-1; r5-5 same signature). Rerun r4-10, r6-1, r5-5 on the final tree. r4-10 line still says "declared equivalent": relabel.

Minor 1. scripts/start_all.sh:98 (second demo-server-alive check at the desk-ready step) has no mutant. Fix: mutant removing line 98 plus a test that kills the demo server after the desk line appears.
Minor 2. tests/test_start_all_late_refusal.py:339 and :477: shell stubs run `kill "$pid"` with no pid>1 guard; notes claim every kill refuses pid<=1. Fix: add the guard or correct the notes.
Nit 1. test_start_all_late_refusal.py:552-571 asserts elapsed < 9 on the real clock; can fail on a loaded machine. Widen or label as timing-sensitive in the notes.
Nit 2. scripts/reset.sh:40: stop wait is a count of 0.1 s sleeps, each alive() runs two ps calls: same class as row 12 (start_all). Use a clock deadline.
Nit 3. src/lead_desk/constants.py:122-127 (and 60-61, 38-39): badly wrapped comment lines (notes admit it). Rewrap.

Sibling search: no other "log line then process alive" ready-wait loop found in scripts/ (run_real_check.py:792, :836 and hubspot_probe.py are polling loops, bodies not read). start_all.ps1 and reset.ps1 remain text pins.
