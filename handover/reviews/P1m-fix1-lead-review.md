# PR 62 (core/P1m-fix1, head e55333e) review, egm-codebase-details, 2026-11-06 (saved by lead)
0 Blocker, 0 Major, 4 Minor: reviewer calls it CLEAN. Reviewer ran nothing. All four review-4 items fixed at the root, tests fail on old code.
M1 _refuse_junctions walks only children of its base: if src or the fixture folder itself is a junction, or an intermediate path part (tests in tests/fixtures), it is not refused. Check isjunction(base) and each part.
M2 test docstring (test_mutation_runner.py:111-115) says a real Windows junction is "checked by hand there, see the CHANGELOG" but no record exists. LEAD ran the probe: egm/hadavin-sdk/p1m/evidence-lead-19-junction-probe.txt (Windows Python 3.13.3, mklink /J: islink False, isjunction True). Cite that file or add a Windows-only test.
M3 _ReapedElsewhere only in the os.waitid branch (macOS/no-waitid still returns 0 with SIGCHLD ignored); the reaped-leader path returns without _kill_tree. State both limits in the Limits docstring.
M4 no mutant for the baseline branch `if base_rc == REAPED_ELSEWHERE`.
