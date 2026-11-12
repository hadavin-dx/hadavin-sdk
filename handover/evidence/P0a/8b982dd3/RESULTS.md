# Evidence for PR 71 (core/P0a), head 8b982dd3a06fa4c2ae9b728e0f38db2b5b2d8a69
EVIDENCE RUNNER: records only, no judgement. Run 2026-11-12 on a clean detached worktree (`git rev-parse HEAD` = the sha above, `git status -s` empty). 7 commits on top of origin/main; the diff is one new file, tests/test_no_pglast_in_runtime.py (419 lines).

## Not run, or run differently (read first)
1. Full pytest was NOT re-run by me. handover/core/run-ledger.tsv already holds an identical head + command row: `8b982dd3... pytest full -m "not live and not perf"  exit 0, 10233 passed 457 skipped, 312 s` (2026-11-12). I did not verify that run myself, so its result is the earlier runner's, not mine. No Postgres was started, so the dblink-connect question did not arise.
2. The unreadable-folder probe cannot raise as root (root ignores mode 000): exit shows no violation and no error. It was repeated as the `nobody` user with the system python and a 4-line stand-in for the `pytest` import: there it raised PermissionError. So the nobody run did not use the repo venv or real pytest.
3. Gates were run as separate commands (not through heavy.sh): each took 0-2 s, so no heavy slot was needed.
4. The planted-failure runs used `uv run`, which also rewrote uv.lock in the throwaway worktree when pyproject.toml changed; the failure text for the "runtime dependency" and "include-group" plants therefore also names a uv.lock hit. The test did fail for the plant in both cases, but I did not separate the two causes.
5. Not run: a plant of the guard against old code (the file is new, so there is no old version to run it on).

## Gate table
| command | exit | last line | seconds |
|---|---|---|---|
| pytest full (ledger row, not mine) | 0 | 10233 passed 457 skipped | 312 |
| ruff check src tests demos tools | 0 | All checks passed! | 0 |
| ruff format --check src tests demos tools | 0 | 321 files already formatted | 0 |
| uv run --with bandit bandit -ll -r src demos tools | 0 | (summary) No issues identified; High 0, Medium 0 at -ll | 2 |
| python tools/scan_repo.py | 0 | empty (only a UV_NATIVE_TLS deprecation warning) | 1 |
| gitleaks detect --log-opts origin/main..HEAD | 0 | no leaks found (7 commits scanned) | 1 |
| pytest -v tests/test_no_pglast_in_runtime.py | 0 | 62 passed in 0.42s | 1 |
New test file count: 62 tests = 59 parametrised `test_guard_catches` cases (the "mutant" list, including 4 clean/fine cases) + test_repository_ships_no_pglast + 3 more (unreadable dir raises, missing tree raises, symlink not entered). Raw logs: raw/*.log.

## Fail-before
The file is new (not on main), so there is no old guard to fail. Instead, each plant was made in a throwaway worktree of the same sha and `test_repository_ships_no_pglast` run (clean throwaway worktree reset between plants):
| plant | exit | result |
|---|---|---|
| none (baseline) | 0 | 1 passed |
| "pglast==8.7" added to [project] dependencies | 1 | 1 failed (also a uv.lock hit, see item 4) |
| `import pglast` appended to src/hadavin_sdk/__init__.py | 1 | 1 failed: "src: hadavin_sdk/__init__.py imports pglast" |
| src/hadavin_sdk/_pglast.cpython-313-x86_64-linux-gnu.so | 1 | 1 failed: "src: compiled _pglast.cpython-313-x86_64-linux-gnu.so" |
| include-group entry in a non-test dependency group | 1 | 1 failed (also a uv.lock hit, see item 4) |
Note: the .so plant used the name `_pglast...so`, not `pglast...so`; the name `pglast.cpython-313-...so` appears in the probes below.

## Hostile probes (calls `violations(root)` from the test file on a minimal tree; "exit" is the probe script's exit, always 0 unless noted; the finding is the returned list)
| probe | returned violations |
|---|---|
| baseline | [] |
| src/pglast-extras/ folder | [] (not flagged) |
| src/pglastic/ | [] (not flagged) |
| src/Pglast/ | ['src: vendored dir Pglast'] |
| src/PGLAST/ | ['src: vendored dir PGLAST'] |
| src/pglast_ext/ | [] (not flagged) |
| src/pglast.so.1 | ['src: compiled pglast.so.1'] |
| src/pglast.cpython-313-x86_64-linux-gnu.so | ['src: compiled pglast.cpython-313-x86_64-linux-gnu.so'] |
| demos/x/pglast/ | ['demos: vendored dir pglast'] |
| src/link -> folder holding `import pglast` (symlink named link) | [] (not entered; the test file documents this) |
| unreadable folder, run as root | [] (root ignores mode 000) |
| unreadable folder, run as nobody | PermissionError raised |
| tools/run, python shebang, pglast named only in a comment | [] (no import there) |
| `from pglast import x` | ['src: m2.py imports pglast'] |
| tab-split requirement `pglast<TAB>>=1` in group ci | ['group ci'] |
| uv.lock package depending on pglast | ['uv.lock other-pkg: dependencies'] |
Items a reader may want to look at, stated without judgement: `pglast-extras` and `pglast_ext` folders are returned clean; the shebang probe contained no actual import, so a shebang script WITH an import is covered only by the test's own mutant "python script with a shebang" (passes).

## Cleanup
Both worktrees, /tmp/nbprobe and the venv listed below were created by me and removed after this commit.
