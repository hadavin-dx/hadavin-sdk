# EVIDENCE RUNNER results, PR89 round 27, head cc1f62287e1c73ebfbd07f28423f37d71bf8775d

Recorded only. Nothing was judged or fixed. Raw logs: /home/user/build/evidence-raw/PR89r27-cc1f6228/ (outside the repo). Worktree /home/user/build/EV-PR89r27, tree clean, `git rev-parse HEAD` equals cc1f6228.

## Failed or not run (first)

1. Full pytest, first run: 1 failed, 10831 passed, 3 skipped, 28 deselected (exit 1). The failure is `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`: the test database server was started by me WITHOUT PGHOST/PGPORT in the server environment, so `dblink_connect('dbname=postgres')` looked for the default socket. My setup slip, not a head result. The server was restarted with PGHOST and PGPORT in its environment and the full run was repeated: 10832 passed, 3 skipped, 28 deselected, exit 0 (second run). Both logs kept.
2. The 2 skips named `tests/test_mutation_runner_keywords.py:6018` (mypy test) skip in the locked venv, as designed (mypy not locked). I ran mypy separately (item 6).
3. Item 9 (the known flaky timing test, 3 runs on head and 3 on main) was not in this brief's run list: NOT RUN.
4. Perf run (`-m perf`) not run: no perf item in the brief.
5. Fail-before: two tests that already existed on r26 and that changed in r27 fail on the old code (listed in item 5 below); of the 6 test names that are new in r27, 3 pass on old code (listed).
6. The PR's own handover evidence (`handover/evidence/PR89/r27/`), builder notes and FAILBEFORE-TABLE were not read, as instructed.

## Command table

| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 changed files vs origin/main | `git diff --name-only origin/main...HEAD` | 0 | 31 files (list in raw dir `changed.txt`) |
| 2a | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | `ruff format --check src tests demos tools` | 0 | 319 files already formatted |
| 2c | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only the two existing "nosec encountered (B102)" warnings for src/hadavin_sdk/tools.py:389; no finding |
| 2d | `python tools/scan_repo.py` | 0 | (no output) |
| 2e | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 2f | `gitleaks git --config .gitleaks.toml --redact --exit-code 1 --log-opts origin/main..HEAD` | 0 | no leaks found |
| 3 full pytest run 1 (no PG env in server) | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 1 | 1 failed, 10831 passed, 3 skipped, 28 deselected in 340.55s |
| 3 full pytest run 2 (PGHOST, PGPORT in server env) | same command | 0 | 10832 passed, 3 skipped, 28 deselected in 351.97s |
| 4a mutants as root | `heavy.sh uv run --no-sync python tests/mutation_runner_mutants.py` (TMPDIR in own folder) | 0 | 329 of 329 good; problems: [] |
| 4b mutants as non-root | `heavy.sh runuser -u nobody -- env -i ... python tests/mutation_runner_mutants.py` (HOME and TMPDIR in a folder owned by nobody, mode 700; worktree and venv world-readable) | 0 | 329 of 329 good; problems: [] |
| 5 fail-before | 4 changed test files + mutants file + manifest copied onto detached worktree of 916c71ea (src and tools of r26); `pytest -rA tests/test_mutation_runner_keywords.py tests/test_mutation_runner_meta.py` | 1 | 5 failed, 309 passed, 2 skipped |
| 6 mypy 3.12.3 | `mypy --platform win32 --no-incremental --no-error-summary --no-color-output --no-pretty --hide-error-context --show-error-codes --config-file= --python-version 3.12 tools/mutation_runner.py` (mypy 2.4.1 in a throwaway venv, not added to the lock) | 1 | 14 errors |
| 6 mypy 3.13.18 | same, `--python-version 3.13` | 1 | 14 errors |
| 7 hostile probes | own script, see below | n/a | see below |

Mutants: in both runs no mutant was not good (first-failing-line list empty). Heavy-slot wait: no measurable wait (slots were free).

## Item 5, fail-before detail (list only)

New test names in r27 (head collection minus r26 collection): 6.
- Fail on old code (3): `test_a_file_with_a_second_name_keeps_its_mode_when_it_is_refused`, `test_a_named_pipe_under_the_name_of_a_made_file_does_not_block_the_open`, `test_the_docstring_says_that_ci_does_not_run_the_mypy_count`.
- Pass on old code (3): `test_that_ci_does_not_run_the_mypy_count_is_true_of_the_workflow_and_the_lock_file`, `test_every_decorator_is_read_even_after_a_true_mark_and_an_unreadable_one_raises`, `test_the_header_names_the_killers_that_drop_a_case_by_the_system_name_and_both_lists_are_checked`.
Also failing on old code (test existed before, changed in r27): `test_a_new_os_or_signal_name_is_noticed_so_the_win32_error_count_in_the_texts_stays_true`, `test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets`.
The other mutant list killers were not run on old code beyond what is above (the mutants file itself is not a pytest file).

## Item 6, mypy detail

Both versions: 14 error lines each. 13 are `Module has no attribute` for POSIX-only names (WNOWAIT, killpg, SIGKILL, getuid, O_DIRECTORY, O_NOFOLLOW, P_PID, WNOHANG and similar); 1 is `Cannot find implementation or library stub for module named "hadavin_sdk.testing.mutation"` at tools/mutation_runner.py:359 (the package was not installed in the throwaway venv). Count matches the CHANGELOG text of 14. Raw: mypy3.12.log, mypy3.13.log.

## Item 7, hostile probes (own script, run as root, on `tools.mutation_runner` functions `_make_private_file`, `_refuse_unless_private`, `_make_private_dir`, with a 5-second alarm)

| Probe | Result |
|---|---|
| FIFO under a made-file name, no reader | REFUSED, OSError ENXIO (no hang) |
| FIFO under a made-file name, with a reader | REFUSED, RuntimeError "is not a regular file" |
| Second hard link to a made file, mode 0644 | REFUSED ("open to group or others"); mode stayed 0644, content kept |
| Second hard link, mode 0600 | REFUSED ("has more than one name"); content kept |
| Symlink (to an existing file) as result path | REFUSED, OSError ELOOP; target content unchanged |
| Dangling symlink as result path | REFUSED, OSError ELOOP; target file not created |
| Existing folder with mode 0777 (`_refuse_unless_private`) | REFUSED, RuntimeError "open to group or others (it must have mode 0700)" |
| `_make_private_dir` onto an existing 0777 folder | REFUSED, FileExistsError; mode left 0777 (not narrowed) |
| Control: fresh file | ACCEPTED |

Not probed: the same inputs through the full `run_mutants` call path (only the helper functions were called directly); probes ran as root only.

## Cleanup

My Postgres 16 (port 56731) stopped and its folder deleted; throwaway mypy folders and probe folders removed; the old-sha worktree removed. The head worktree /home/user/build/EV-PR89r27 and venvs are left in place for the lead. No other agent's process or folder was touched. No git push, no commit.
