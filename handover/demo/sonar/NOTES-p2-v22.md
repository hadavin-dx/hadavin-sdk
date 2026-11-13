# P2 v2.2 delta (test-only)
Patch: sonar/sonar-p2-regex-http-bug-v2.2-delta.patch. One new file, tests/test_sonar_p2_gaps.py (143 lines, 12 tests). No src change. Closes the reader's rv22 Nit 1 (test gaps) and Nit 2 (clean evidence run); Nit 3 re-measured; Nit 4 untouched (pre-existing, outside the Sonar list).
Touches: only the new file. Applies after db54e13 + P2 v2.1 (needs P1 not at all); verified in all six orders of P1 v3.2 / P2 v2.1 / P3 v3 with the delta last, and with the delta right after P2 (evidence-p2v22-6).

## Failures / not done first
- Not run: full suite (lead's), Sonar, real Windows, Python 3.12 (3.13 used). Tests are not covered by mypy (repo config), so the new file is checked with ruff check/format only.
- The new tests do not prove the reader's M22 or the surviving "unchanged base behaviour" lines are right; they pin the behaviour the reader measured as identical to db54e13.
- Flake test_reserve_covers_its_items: NOT reproduced (0 of 20 under 2 CPU hogs; 0 of 20 plus 0 of 5 neighbour-set runs under 6 hogs on 4 cores). Cause still unproven; patch cannot reach it (no db/portal_api/constants change).

## Tests added (what each kills)
(a) test_a_result_that_is_not_sent_* [unknown, pending, failed] + sent control: stage stays 'new', copy wait kept -> M08.
(b) test_a_database_error_that_is_not_a_lock_answer_propagates (two non-busy OperationalError texts): raises, no "stayed locked" log, wait kept -> M06.
(c) test_c_stale_token_logs_changed_0 (exact text "record_send_result: expected one row, changed 0") -> M01, M09; test_c_one_row_logs_no_warning_* [sent already-further, failed, unknown] -> M01, M04 (count must be the first value, not the moved flag); test_c_nudge_result_with_no_row_logs_changed_0 ("record_nudge_result: ...") -> M01, M10 (the shared _finish_update count).
(d) test_d_the_listening_line_is_exactly_http_host_port: runs server.main with a stub server, asserts the literal line "desk listening on http://127.0.0.1:4321" (not built with desk_origin) -> M26.
Loopback only (HOST from Config, stub server, no socket opened).

## Mutants (evidence-p2v22-1, runner evidence-p2v22-mutant-runner.py, the reader's M01 M04 M06 M08 M09 M10 M26 re-created from its mut.py; only the new file is run)
M01 KILLED (6 tests), M04 KILLED (3), M06 KILLED (2), M08 KILLED (2), M09 KILLED (1), M10 KILLED (1), M26 KILLED (1). New tests on the real code: 12 passed. Source restored after each mutant (finally clause).

## Final stack evidence (P1 v3.2 + P2 v2.1 + delta, fresh clone at db54e13)
- evidence-p2v22-3: the reader's 26 files + test_sonar_p2_gaps = 27 files: 1248 passed, 1 skipped, 0 failed, 499.7 s, one run, rc=0 (Nit 2 closed).
- evidence-p2v22-4: after git add -A (20 files staged): test_hygiene + test_codeant_hygiene + test_sonar_p2_choke_points + test_sonar_p2_gaps, DPLD_REQUIRE_SCAN=1, gitleaks 8.30.1: 52 passed, 0 skipped; gitleaks git --staged: no leaks.
- evidence-p2v22-2: ruff check clean, ruff format --check clean (152 files), mypy linux and win32 clean (27 files), bandit -ll: no medium/high output.
- evidence-p2v22-5: flaky candidate, see above.

## Rung table (R448)
| component | need | rung tried | verdict |
| four pinning tests | kill 7 surviving mutants | existing test helpers (_Crm, _flow, _sql, is_write, rig fixtures), pytest caplog/capsys | KEEP-CODE (tests only, no new helper) |
Sonar: tests only, no issue expected to change (test files are excluded or not part of the gate counts as far as unknown).
