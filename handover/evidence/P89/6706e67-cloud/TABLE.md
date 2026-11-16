# PR 89 core/mutation-runner-keywords head 6706e6728483b67e549101b1680111a4c2b89471 (cloud evidence, EVIDENCE RUNNER: raw output only, no verdict)

Worktree: detached snapshot of origin/core/mutation-runner-keywords, `git rev-parse HEAD` = 6706e67... (first line of every log). Origin head checked 18:4x UTC: still 6706e67. Base for "old": 2742c1b (merge-base with main).
Machine: cloud session, 3 heavy slots (heavy.sh), own venvs (python 3.12 and 3.13), own throwaway Postgres 16 on a local port (initdb UTF8), run 19:01-19:34 UTC.

FAILED / PROBLEM rows first (mechanical list, not a verdict):
1. FOUND, not fixed (evidence runner does not edit the branch): in the first full runs (full-3.12.txt, full-3.13.txt) HADAVIN_TEST_PG_DSN was set in the environment, yet 12 Postgres tests SKIPPED with "HADAVIN_TEST_PG_DSN not set". Cause shown by dsn-leak-single-test-313.txt: running tests/test_mutation_runner_keywords.py::test_masked_replaces_the_value_and_the_url_password before tests/test_p7_store.py gives "4 skipped" (lines 457-463 of the test file: `os.environ[DSN_NAME] = dsn` then `del os.environ[DSN_NAME]` in finally, which deletes the caller's real value instead of restoring it). The three runner files each run before test_p7_store.py (dsn-leak-probe-313.txt): test_mutation_runner.py 80 passed, test_mutation_runner_keywords.py 62 passed 4 skipped, test_mutation_runner_meta.py 27 passed. Effect: every later test in the same pytest process that needs the Postgres address silently skips (CI has the DSN set, so CI would also skip them).
   Workaround rows (full-withdsn-*.txt): the same full suite with that one test deselected, DSN set, so the Postgres tests really ran.
2. fail-before: head's tests against the OLD runner and judge (base files swapped into a copy): collection error in tests/test_mutation_runner_keywords.py (ImportError PASS_ENV_ALLOWED); with --continue-on-collection-errors: 1 failed (test_the_manifest_pins_the_files_a_demo_copies), 75 passed, 1 error. The new keyword tests therefore are not run individually against old code (they cannot import); no per-test fail-before count for them.
3. NOT RUN: the 13 skips in the first full runs are listed in full-3.13.txt (12 Postgres, 1 Stubber shape); Vault tests (HADAVIN_TEST_VAULT_ADDR unset, 1 skipped as always); Windows runs (runner Windows paths); CodeQL, SonarCloud, CodeRabbit, GitHub checks; no new "mutants of the keywords" script exists in the repo besides tests/mutation_runner_mutants.py (62 mutants at base and at head: same count, so the new keywords have no mutants of their own there); no hostile-input run beyond the repo's own tests; no EGM review (not my role).
4. Deviation: full-withdsn-312 ran with HADAVIN_REQUIRE_PINNED_UNIDATA=0 (3.13 had =1 as ci.yml; the first 3.12 run had it unset). A grep of tests/ and src/ for that name found nothing in this tree, so the value is probably unused here; not checked further. bandit via `uvx` (not in the test group), scope as ci.yml. Lint scope `src tests demos tools` as ci.yml.

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos tools | 3.13 | 0 | All checks passed | ruff-check.txt |
| ruff format --check src tests demos tools | 3.13 | 0 | 318 files already formatted | ruff-format.txt |
| bandit -q -r src demos tools -ll | 3.13 | 0 | no issue lines | bandit.txt |
| python tools/scan_repo.py | 3.13 | 0 | no hits | hygiene.txt |
| scan of these logs with the repo's scan patterns | - | 0 | no hits | hygiene-logs.txt |
| pytest -q -m "not live and not perf" -rs (DSN set but lost mid-run, see 1) | 3.13 | 0 | 10518 passed, 13 skipped, 28 deselected | full-3.13.txt |
| same | 3.12 | 0 | 10518 passed, 13 skipped, 28 deselected | full-3.12.txt |
| same, `--deselect` of the leaking test, Postgres really used | 3.13 | 0 | 10529 passed, 1 skipped, 29 deselected | full-withdsn-313.txt |
| same | 3.12 | 0 | 10529 passed, 1 skipped, 29 deselected | full-withdsn-312.txt |
| pytest -m perf -rs (run alone) | 3.13 | 0 | 28 passed | perf-3.13.txt |
| same | 3.12 | 0 | 28 passed | perf-3.12.txt |
| python tests/stage_mutants.py | 3.13 | 0 | 37 of 37 good | stage-mutants.txt |
| python tests/mutation_runner_mutants.py, NEW head | 3.13 | 0 | 62 of 62 good | mutation_runner_mutants-newhead-313.txt |
| same, NEW head | 3.12 | 0 | 62 of 62 good | mutation_runner_mutants-newhead-312.txt |
| python tests/mutation_runner_mutants.py, OLD base 2742c1b (its own file and runner) | 3.13 | 0 | 62 of 62 good | old-base-mutants-313.txt |
| pytest the 3 runner test files, OLD base | 3.13 | 0 | 76 passed | old-base-runner-tests-313.txt |
| pytest 4 runner test files, head tests vs OLD runner+judge, plain | 3.13 | 2 | collection error (ImportError) | failbefore-head-tests-old-runner-313.txt |
| same with --continue-on-collection-errors | 3.13 | 1 | 1 failed, 75 passed, 1 error | failbefore-head-tests-old-runner-313-continue.txt |
| pytest Postgres files alone (p2, p7, audit chain, contract kinds, k2) | 3.13 | 0 | 127 passed, 0 skipped | pg-files-313.txt |
| probe: runner test file then test_p7_store (3 orders) | 3.13 | 0 | 80 passed / 62 passed 4 skipped / 27 passed | dsn-leak-probe-313.txt |
| probe: the one leaking test then test_p7_store | 3.13 | 0 | 18 passed, 4 skipped | dsn-leak-single-test-313.txt |
| (gen_evidence's own table, same run) | - | - | - | TABLE-gen_evidence.md |
