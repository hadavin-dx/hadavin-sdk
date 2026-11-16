# EV-PRHr4 results: PR H (strip hidden controls) head d08ec151af49e2429430f7c1cff60cf3e379b05f

EVIDENCE RUNNER: results are recorded, not judged, nothing was fixed. Run 2026-11-12 00:20 to 00:52 UTC (05:50 to 06:22 IST). Raw logs: /home/user/build/evidence-raw/PRHr4-d08ec151/ (outside the repository).
Head sha confirmed: `git rev-parse HEAD` = d08ec151af49e2429430f7c1cff60cf3e379b05f, `git status --short` empty. Previous reviewed head e852b577, main 2a8c2aac (origin/main).
Builder evidence folder handover/evidence/PRH/b4/ and builder notes were NOT read.

## Failed or not run, or different from the ticket (first)

| # | What | Result |
|---|---|---|
| F1 | Ticket 6.1 item 1: files outside the allowed list | `! grep -v -x -E '<allowed>' files.txt` exits 1. Four changed files are not in the ticket's allowed list: src/hadavin_sdk/defaults.py, tests/fixtures/prh_accidental_pairs.json, tests/fixtures/prh_main_passes.json, tests/test_k5_fixes3.py |
| F2 | Ticket 6.1 item 2: no added `noqa` / `type: ignore` / `nosec` | the grep finds 2 added lines, both in tests/test_prh_perf.py: `pytest = None  # type: ignore[assignment]` and `subprocess.run(  # noqa: S603 (fixed argv, no shell)` (grep exit 0, so the ticket's `! ... grep -q` check would exit 1) |
| F3 | `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` | FAILED 3 of 3 runs on the head and 3 of 3 runs on origin/main on this machine (assertion: "a quadratic function must be flagged"), each 0.6 s, run after the perf job while holding all three slots. It is not intermittent here. In the full suite at the head it was not failing (see item 5) |
| F4 | Cost table (ticket 6.1 item 9) | printed rows only for 262,144 characters and only S1-S5 and H1-H4 (no 65,536 rows, no W row, no passes column). H rows ratio to main 2.70, 3.22, 4.65, 3.22 (S1-S5 0.96 to 1.01). Raw: cost.log |
| F5 | Install | `uv sync --locked --no-build ...` fails here: "hadavin-sdk==0.1.0 @ editable+. ... marked as --no-build but has no binary distribution". Ran `uv sync --locked --all-extras --group test` (without --no-build) instead, exit 0, for every venv |
| F6 | Not run | Python 3.12 full suite (ticket 6.1 item 3); full suite on origin/main and the skip-list diff (item 3); the CI job steps outside the redaction package (Semgrep, zizmor, Trivy, pip-audit, workflow audit); ticket 6.1 item 11 as the ticket's own row table (my probe covers L1-L12, M2a, M2b, G1-G3 only, no F/B/M5 rows); `tests/test_prh_perf.py` run on its own file (it was included in the perf marker run) |
| F7 | Mutant count | 55 of 55 (the brief expected 55; the ticket text said 43; the runner's own last line is 55) |

Earlier failures the lead named: at this head `tests/test_k5_fixes3.py::test_the_decoded_view_is_computed_once_not_once_per_secret_form` PASSED and `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]` PASSED, in the full run and in two targeted runs (PGHOST = my server's socket directory: 262 passed with test_k5_fixes3.py; PGHOST = 127.0.0.1 with PGPORT: 253 passed for test_validate_harm.py alone). I did not run it with PGHOST unset.

## Results table

| Item | Command (all from the head worktree, cloud variables unset) | Exit | Last line |
|---|---|---|---|
| (1) changed files | `git diff --name-only origin/main...HEAD` | 0 | 29 files, `files.txt` |
| (2) ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| (2) ruff format | `ruff format --check src tests demos tools` | 0 | 333 files already formatted |
| (3) bandit | `bandit -q -r src demos tools -ll` | 0 | only the line "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389" (twice) |
| (4) scan | `python tools/scan_repo.py` | 0 | (no output) |
| (4) stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| (4) gitleaks | `gitleaks git --config .gitleaks.toml --redact --exit-code 1 --log-opts origin/main..HEAD` | 0 | no leaks found |
| (5) full suite | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs`, own Postgres 16 (127.0.0.1:56731, PGHOST = socket dir, HADAVIN_TEST_PG_DSN set) | 0 | 12897 passed, 1 skipped, 62 deselected in 330.36s; skipped: tests/contracts/test_llm.py:95 |
| (6) PR H mutants | `heavy.sh python tests/prh_mutants.py` (own separate worktree, so no file rewrite under the full run) | 0 | 55 of 55 good; problems: [] |
| (c) perf alone | three slot locks nested, `pytest -m perf -rs` (62 perf tests in the repository, includes tests/test_prh_perf.py) | 0 | 62 passed, 12898 deselected in 121.37s |
| (d) fail-before on e852b577 src | changed test files of the delta (7 test files, listed in changed-tests) on a worktree of e852b577, `-m "not live and not perf" --continue-on-collection-errors -rA` | 1 | 54 failed, 2132 passed, 34 deselected |
| (d) fail-before on origin/main src | the same files on a worktree of origin/main | 1 | 1821 failed, 236 passed, 34 deselected, 2 errors |
| (e) spelling probes | own script probe_spellings.py, head vs origin/main | 0 | table below |
| timing test x3 head, x3 main | see F3 | 1 each | 1 failed in 0.6s |
| cost table | `python tests/test_prh_perf.py --compare-main <main worktree>` alone | 0 | see F4 |

Changed test files of the delta (git diff --name-only e852b577 d08ec151 -- tests): tests/fixtures/prh_regressions.json, tests/hidden_oracle.py, tests/prh_mutants.py, tests/test_k5_fixes3.py, tests/test_prh_contract.py, tests/test_prh_hidden_unit.py, tests/test_prh_perf.py, tests/test_prh_regressions.py, tests/test_prh_steps.py, tests/test_prh_tools.py. (prh_mutants.py is a runner and was not run as a test file; the fixture and oracle files were copied.)

## (d) Fail-before detail (lists only)

- On e852b577 src: 54 FAILED (`failbefore-e852b577-failed.txt`). 52 test ids exist in the delta that did not exist at e852b577; of these 49 FAILED and 3 PASSED: tests/test_prh_regressions.py::test_named_ids_exist_and_the_converse_holds, tests/test_prh_regressions.py::test_pinned_secret_rows_count, tests/test_prh_regressions.py::test_regression_row[b4_ctl_colour]. 5 FAILED ids existed before: test_k5_fixes3.py::test_the_decoded_view_is_computed_once_not_once_per_secret_form, test_prh_contract.py::test_mf_masked_pairs, ::test_mf_masked_singles, test_prh_hidden_unit.py::test_hidden_module_imports_nothing_from_the_package, test_prh_regressions.py::test_every_prh_mutant_still_applies.
- On origin/main src: 1821 FAILED, 236 PASSED, 2 collection ERRORS (tests/test_prh_contract.py and tests/test_prh_hidden_unit.py: `AttributeError: module 'hadavin_sdk.guard.runmap' has no attribute 'decodes'` / `_no_created_shapes`, and `ImportError: cannot import name 'record_prh_main'` because I copied only the changed files, as the brief says). The same 3 new ids as above PASSED on main src. Failure list: `failbefore-main-failed.txt`.
- Every FAILED line, including the assertion text where one exists, is in the raw logs failbefore-*.log.

## (e) Readable-secret probe: does a piece of the secret stand in the output? (yes = readable)

Inputs typed from the ticket's section 2.4 table with the constants of section 2 (made-up values built from parts). Paths: untrusted = `runmap.redact_untrusted(t, {})`; tool = `tools.prepare_output(t, {}, 4000, handed_out)`; error = `tools.error_reason(ValueError(t), handed_out)`; head = `runmap.safe_head(t, 4000)`. "readable" = the full value or its tail piece (the part after the hidden item) occurs in the output. Handed-out list given only for L6 and L12 and only on the tool and error paths (as in the ticket: the other two paths have no list, so L6/L12 untrusted and head say yes on the head too).

Full per-path table: `probe-main.txt` and `probe-head.txt`. Summary, per row: main untrusted/tool/error/head -> head untrusted/tool/error/head:

| Row | main | head |
|---|---|---|
| L1 L2 L3 L4 L5 L7 L9 L10 L11 M2a M2b | yes/yes/yes/yes | no/no/no/no |
| L6, L12 (handed out) | yes/yes/yes/yes | yes/no/no/yes (no list on untrusted and head) |
| L8 (NUL) | no/yes/no/no | no/no/no/no |
| G1 G2 | no/no/no/no | no/no/no/no |
| G3 | yes/yes/yes/yes | no/no/no/no |
| control: plain key | no/no/no/no | no/no/no/no |
| control: key cut by a tab (not hidden) | yes/yes/yes/yes | yes/yes/yes/yes |

No call raised or was refused in my probe (no R values).

## Environment
Python 3.13 venvs per worktree. Machine load was shared with other agents' heavy jobs; waiting for slots: the full run queued about 5 minutes, the perf lock job about 4 minutes, the timing/cost job about 8 minutes. Own server: Postgres 16.15 started as the postgres user, stopped and removed at the end; worktrees (wt, wt2, main, prev, prev0) removed at the end.
