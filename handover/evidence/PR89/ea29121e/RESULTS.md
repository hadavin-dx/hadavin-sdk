# PR89 r29 evidence (EVIDENCE RUNNER: records only, judges nothing, fixed nothing)
Head ea29121e9c1fc070acd55cf4bae9b9c613f55535 (fetched from origin/wip/cloud-PR89-r29, sha confirmed equal; detached worktree, tree clean). Raw logs: /home/user/build/evidence-raw/PR89r29-ea29121e/ (outside the repo).

## Failed or not as expected (first)
1. Known flake `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`, alone, holding all three slot locks, ONCE: FAILED (0.60 s), AssertionError at line 836. Not run on origin/main (not asked). Other agents' processes were on the machine.
2. Full pytest: 3 skipped = tests/contracts/test_llm.py:95 (Stubber) and 2 x the mypy test (tests/test_mutation_runner_keywords.py:6018, mypy not in the locked environment). The mypy test was run separately (item 9).
3. NOT run: perf tests (`-m perf`) as a whole; CI jobs other than the ones listed below (Semgrep, zizmor, Trivy, pip-audit, Vault service tests); flake test on origin/main; HADAVIN_TEST_VAULT_ADDR not set. Item 10 was run on the pytest file only (tests/test_mutation_runner_meta.py: 1 failed, 13 passed), not the keywords test file or the mutant runner on the old tree.
4. Set-up notes: Postgres 16.15 refuses to run as root, so it ran as user postgres, in a private mount namespace with its own /tmp (another agent's /tmp/askdata_p2_copy.csv is owned by postgres in the shared /tmp), on 127.0.0.1:56729; PGHOST, PGPORT, PGUSER in the server environment. Install was `uv sync --locked --all-extras --group test` (without --no-build); venv Python 3.13.18. User nobody ran a copy of the tree owned by nobody (PYTHONPATH pointed at that copy's src, HOME and TMPDIR in a nobody-owned mode-700 folder). I ran `chmod o+rx /home/user/build` once (harmless, only to make sure nobody can traverse). My mypy flags for the by-hand count were a subset of the repo's MYPY_FLAGS; the repo test (exact flags) was also run.

## Table
| item | command (short) | exit | last line |
|---|---|---|---|
| 1 | git diff --name-only origin/main...HEAD | 0 | 41 files |
| 1 | git diff --name-only 7e4faf14 ea29121e | 0 | CHANGELOG.md, handover/evidence/PR89/r29/NOTES.md, handover/evidence/PR89/r29/gates.txt, tests/mutation_runner_mutants.py, tests/test_mutation_runner_meta.py (nothing under tools/ or src/) |
| 2a | ruff check src tests demos tools | 0 | All checks passed! |
| 2b | ruff format --check src tests demos tools | 0 | 319 files already formatted |
| 3 | bandit -q -r src demos tools -ll | 0 | only warning: nosec B102 on src/hadavin_sdk/tools.py:389 |
| 4 | python tools/scan_repo.py | 0 | (no output) |
| 5 | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| 6 root | heavy.sh python tests/mutation_runner_mutants.py | 0 | 329 of 329 good; problems: [] |
| 6 nobody | heavy.sh runuser -u nobody ... same | 0 | 329 of 329 good; problems: [] |
| 7 | heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs | 0 | 10833 passed, 3 skipped, 28 deselected in 373.68s |
| 8 | gitleaks git, origin/main..HEAD | 0 | no leaks found |
| 9 | mypy 2.4.1 --platform win32, tools/mutation_runner.py, --python-version 3.12 / 3.13 (3.13 interpreter) | 1,1 (errors found) | 14 errors / 14 errors |
| 9 | repo mypy test, mypy on PYTHONPATH | 0 | 2 passed, 301 deselected |
| 10 | new meta test against the 7e4faf14 tree, head's test file copied in (r28 header) | 1 | 1 failed, 13 passed; the failed one is test_the_folder_link_killer_never_skips_and_the_header_says_so |
| 12 | timing flake test alone, once | 1 | 1 failed in 0.60s |

## Item 11: raw header lines 98-112 of tests/mutation_runner_mutants.py (file header-lines-98-112.txt)
Lines 103-108 (the intro of the second list) read: "- Killers that skip INSIDE their body ... on such a system the mutant SURVIVES, with ONE exception: the folder-link killer is named only because its helper holds a skip that can never fire for it (see the paragraph that begins "Named in the second list below"), so that mutant is killed on every system. The second list between the marker lines below is read by the same test file in both directions: it fails when a named killer has no ``pytest.skip`` call, in its body or in a helper of its file that it calls (the follow is static: it does not look at the system), or when a killer with one is not named. The prose above says why each one skips, or, for that one killer, why it does not."
grep -n -i 'surviv\|skip' over lines 98-112 (numbers relative to line 98, add 97): hits at relative lines 6, 8, 10, 11 = file lines 103, 105, 107, 108. Line 105 holds "SURVIVES, with ONE exception"; the exception is named there.
