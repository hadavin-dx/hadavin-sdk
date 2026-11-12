# EVIDENCE RUNNER results, PR 89 round 26, head 916c71ea4e5c458dce9329f42a02a853a67804f8 (previous reviewed head 580b4adf, main 2a8c2aac)

Recorded, not judged. Head sha confirmed (`git rev-parse HEAD` equals it); tree clean before and after every run (`git status --short` empty). The builder's folder `handover/evidence/PR89/r26/` and its notes were NOT read. Raw logs: `/home/user/build/evidence-raw/PR89r26-916c71ea/`.

## What failed or was not run (first)
- Fail-before (item e/7): 9 failed, 299 passed, 2 skipped on `tools/mutation_runner.py` + `mutation.py` at 580b4adf with the four changed test/fixture files of the delta copied in (list in `fail-before-failed-tests.txt`).
  New tests of the delta that PASS on the old code (5): `test_a_module_level_pytestmark_and_a_named_mark_are_read_and_an_unknown_decorator_is_an_error`, `test_a_skipif_condition_the_reader_cannot_evaluate_is_an_error_not_no_skip`, `test_the_creation_site_walk_sees_aliases_module_level_code_and_the_other_creating_spellings`, `test_the_header_names_every_mutant_whose_killer_skips_inside_its_body_and_each_skip_is_there`, `test_the_mypy_error_pattern_reads_the_lines_mypy_writes_and_not_the_notes` (they test test-side readers, not the runner). New tests that FAIL on old code (7) and 2 changed tests that fail (`test_every_folder_and_file_the_runner_creates_is_made_by_one_of_the_helpers`, `test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets`).
- Timing test `test_the_timing_harness_flags_a_quadratic_stand_in`, run alone (all three heavy slots held), 3 times each: head fail, pass, fail; origin/main fail, pass, pass. So it flaked on both. The ticket names no perf item; `-m perf` was not run.
- mypy: NOT run as the test does. mypy 2.4.1 was run through `uv run --with mypy` (scratch overlay), with `--platform win32 --python-version 3.12|3.13` and the test's flags approximated (`--no-error-summary --no-color-output --config-file=`; not the test's full `MYPY_FLAGS`), but both runs used the venv interpreter, which is Python 3.13.18; a real 3.12 interpreter exists (/usr/bin/python3.12) but was not used. The test that runs mypy itself is SKIPPED in the full suite (mypy not in the locked environment).
- `uv sync --locked --no-build` as in the common brief FAILED (`hadavin-sdk==0.1.0 @ editable+.` has no binary distribution); I used `uv sync --locked --all-extras --group test` (builds the editable project only).
- Windows/macOS: not run. Semgrep, zizmor, Trivy, pip-audit and Python 3.12 pytest: not run (not named by the ticket; ci.yml scan job).
- No heavy-slot wait problem except queueing: full run queued 00:22:53 UTC, started 00:25:53 (3 min); mutants queued 00:24:27 started 00:27:57 (3.5 min); timing runs waited about 10 min.

## Table
| # | item | command (all through `env -u` cleaning, own venv) | exit | last line |
|---|---|---|---|---|
| 1 | changed files | `git diff --name-only origin/main...HEAD` | 0 | 16 files: CHANGELOG.md, 7 under handover/evidence/PR89/r26/, src/hadavin_sdk/testing/mutation.py, tests/conftest.py, tests/fixtures/mutation_manifest.json, tests/mutation_runner_mutants.py, tests/test_mutation_runner.py, tests/test_mutation_runner_keywords.py, tests/test_mutation_runner_meta.py, tools/mutation_runner.py |
| 2 | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 | ruff format | `ruff format --check src tests demos tools` | 0 | 319 files already formatted |
| 3 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only the existing nosec warning (tools.py:389) |
| 4 | scan_repo | `python tools/scan_repo.py` | 0 | (no output) |
| 4 | stage mutants (c) | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4 | gitleaks | `gitleaks git --redact --config .gitleaks.toml --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 5 (a) | full pytest, once | `pytest -q -p no:cacheprovider -m "not live and not perf" -rs` via heavy.sh, own Postgres 16 | 0 | 10826 passed, 3 skipped, 28 deselected in 351.75s |
| 5 (a) | dblink-connect | `pytest tests/demo_askdata/test_validate_harm.py -k dblink` (also inside the full run) | 0 | 1 passed (own Postgres on 127.0.0.1, port 56926, PGHOST and PGPORT set in the server's environment; it passed, not skipped) |
| 6 (b) | full mutant runner alone | `python tests/mutation_runner_mutants.py` via heavy.sh (own second Postgres, port 56927, not shared with the full run) | 0 | 327 of 327 good; problems: []; 327 ok lines; started 00:27:57, ended 00:36:07 UTC; `git status` clean afterwards |
| 6 | other ci.yml steps | ci.yml has no step that runs `tests/mutation_runner_mutants.py`; steps run: lint, format, scan_repo, pytest, stage_mutants, perf | - | see rows above |
| 7 (e) | fail-before | the four changed delta files onto 580b4adf (runner and mutation.py at 580b4adf), `pytest -rf tests/test_mutation_runner_keywords.py tests/test_mutation_runner_meta.py` | 1 | 9 failed, 299 passed, 2 skipped in 93.76s |
| 8 | hostile inputs | own script (`probe-refusals.txt`): 24 calls of `run_mutants` with bad paths, names, hosts, addresses (long, quote, non-ASCII, 400-layer percent encoding, upper-case scheme, query tail, password and sslcert keys, empty, ports 0 and 65536, no host, unlisted host, socket dir, password equal to an exception name), bare strings, foreign test_file | - | 24 of 24 refused (ValueError or TypeError) before any run; the made-up password does not appear in any message (`secret-in-message=no` in all 24) |
| (d) | mypy count | `mypy --platform win32 --python-version 3.12` and `3.13` on tools/mutation_runner.py (venv interpreter 3.13.18, see above) | 1 | 13 errors each (12 POSIX names + 1 untyped import of hadavin_sdk.testing.mutation); files `mypy-3.12.txt`, `mypy-3.13.txt` |
| 9 | flaky timing test alone x3 | see above | - | head: fail, pass, fail; main: fail, pass, pass |
