# PR89 r28 evidence (EVIDENCE RUNNER: records only, judges nothing, fixed nothing)
Head 7e4faf144ac5c33f4a79911e898bf704041f7076 (tree clean, detached worktree), previous cc1f6228, base main 2a8c2aac. Raw logs: /home/user/build/evidence-raw/PR89r28-7e4faf14/ (outside the repo).

## Failed or not as expected (first)
1. Known flake `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`, alone, 3 times on the head, each run holding all three slot locks: FAILED 3 of 3 (0.65 s, 0.57 s, 0.58 s), `AssertionError: a quadratic function must be flagged` (line 836, `timing.is_superlinear(...)` returned False). Not run on origin/main (the parameters asked for head only). Other agents' processes were running on the 4-core machine outside the slot locks.
2. The full run's pytest summary says "3 skipped": 1 = tests/contracts/test_llm.py:95 (Stubber), 2 = the mypy test in tests/test_mutation_runner_keywords.py:6018 (mypy not in the locked environment). The mypy test was run separately (item d).
3. Not run: items (7) and (9-main) of the common brief that the parameters replaced (fail-before was run against cc1f6228 as asked, not against main); perf step `pytest -m perf` as a whole (the ticket names none; only the one flake test was run); CI's other jobs (Semgrep, zizmor, Trivy, pip-audit, Vault service tests) were not run. HADAVIN_TEST_VAULT_ADDR was not set, so Vault tests are among the deselected or passing-without-Vault ones as pytest decided; the log shows only the 3 skips above.
4. Set-up note: /tmp/askdata_p2_copy.csv was already owned by another agent's database. My Postgres 16.15 ran in a private mount namespace with its own empty /tmp, so the fixed copy-file path was private; tests/demo_askdata/test_validate_harm.py did not fail. Postgres is on 127.0.0.1:56481 (PGHOST and PGPORT set in the server's environment).
5. Install was `uv sync --locked --all-extras --group test` (without --no-build, as told). The venv Python is 3.13.18; HADAVIN_REQUIRE_PINNED_UNIDATA was not set.

## Table
| item | command (short) | exit | last line |
|---|---|---|---|
| 1 | git diff --name-only origin/main...HEAD | 0 | 39 files (raw: diff-names.txt) |
| 2a | ruff check src tests demos tools | 0 | All checks passed! |
| 2b | ruff format --check src tests demos tools | 0 | 319 files already formatted |
| 3 | bandit -q -r src demos tools -ll | 0 | only a warning: nosec B102 on src/hadavin_sdk/tools.py:389 |
| 4a | python tools/scan_repo.py | 0 | (no output) |
| 4b | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| 4c | gitleaks git, log-opts origin/main..HEAD | 0 | no leaks found |
| 5 | heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs | 0 | 10833 passed, 3 skipped, 28 deselected in 357.31s |
| 6 (a) root | heavy.sh python tests/mutation_runner_mutants.py | 0 | 329 of 329 good; problems: [] |
| 6 (a) nobody | heavy.sh runuser -u nobody, HOME and TMPDIR in a nobody-owned mode-700 folder, worktree and venv world-readable | 0 | 329 of 329 good; problems: [] |
| 6 | other CI mutant step: stage_mutants (4b) | 0 | 37 of 37 good |
| b | fail-before, see below | 1 | 1 failed, 314 passed, 2 skipped |
| c | grep, see below | - | - |
| d | mypy 2.4.1, see below | 1 (expected, errors found) | 14 errors in all 4 runs |
| e | see failure 1 | 1,1,1 | 1 failed |

## (b) Fail-before
Worktree of cc1f6228 (src and tools identical to the head: `git diff cc1f6228 HEAD` touches no file under src/ or tools/; PYTHONPATH pointed at the old tree) with the head's tests/test_mutation_runner_meta.py and tests/test_mutation_runner_keywords.py copied in (tests/mutation_runner_mutants.py left as it was at cc1f6228, since its changed header is what the new test reads). Both files run in full: 1 failed, 314 passed, 2 skipped (the 2 skips are the mypy test). 
- FAILS on old code: test_mutation_runner_meta.py::test_the_folder_link_killer_never_skips_and_the_header_says_so (old header paragraph lacks "NEVER skips" and contains "SURVIVES").
- Changed function that PASSES on old code: test_mutation_runner_keywords.py::test_mypy_for_win32_reports_the_errors_the_texts_count[3.12] and [3.13] (docstring-only change, "12" to "13"; run with mypy 2.4.1 on PYTHONPATH: 2 passed on the old tree).
- tests/mutation_runner_mutants.py changed (header prose, round 27 paragraph); it holds no test function.

## (c) Header and CHANGELOG wording (raw: c-grep.txt)
- Header, tests/mutation_runner_mutants.py line 37: `Named in the second list below although it NEVER skips: "a link out of the tree is accepted".` CHANGELOG.md line 55: "The mutant is killed on every system." and line 62: "never skips ... the mutant is killed on every system". Line 74 says "round 28 found that it never skips".
- grep for "survive" in both files: header lines 18, 32, 35, 41, 105, 123 and 330/497 (code text) and CHANGELOG 23 and 510; none of them is in the paragraph that names "a link out of the tree is accepted". A regex for skip or surviv within 300 characters of the phrase matched nothing.
- Observation recorded without judging: the header's intro of the second list (lines 103-106) still says the list names killers that "skip INSIDE their body ... on such a system the mutant SURVIVES" and that the test fails "when a named killer has no pytest.skip call"; the list (line 108) contains "a link out of the tree is accepted". The paragraph at line 37 qualifies it as never skipping.

## (d) mypy 2.4.1 (throwaway venvs, not in the lock), command as in the repo test (`--platform win32 --no-incremental ... --config-file= --python-version V`) on tools/mutation_runner.py
| interpreter | --python-version 3.12 | --python-version 3.13 |
|---|---|---|
| 3.12.3 | 14 errors | 14 errors |
| 3.13.18 | 14 errors | 14 errors |
The repo test itself with mypy on PYTHONPATH (3.13 interpreter): 2 passed (3.12 and 3.13 parameters).
