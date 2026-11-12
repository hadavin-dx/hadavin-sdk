# Q8c-1 batch 11, gates on the code head 351f2b8b (builder run, not independent)

Environment: own venv, own Postgres 16 (UTF8, user postgres, `PGHOST` and `PGPORT` in the server's own environment, a socket folder of its own), no cloud variables. Raw logs: `logs/` next to this file (the last line of each `g-*.log` is `rc=<exit code>`). The commit after 351f2b8b adds only files under `handover/evidence/Q8c-1/b11/`; no code changed after the gates ran (`git status` was clean while they ran).

| Gate | Result |
|---|---|
| `ruff check src tests demos tools` | exit 0, "All checks passed!" |
| `ruff format --check src tests demos tools` | exit 0, "326 files already formatted" |
| `uv run --with bandit bandit -q -r src demos tools -ll` | exit 0 (only the existing "nosec encountered" and "Test in comment" warnings) |
| `python tools/scan_repo.py` | exit 0, no output |
| `python tools/policy_page.py --check` | exit 0 on the real clock (the day of this run is 2026-11-12), no output |
| `python tools/notes_lines_check.py d8441218 handover/evidence/Q8c-1/b11/NOTES.md <the four test files>` | exit 0, no output (every new or changed test has a row; no test is gone) |
| `python tests/stage_mutants.py` | 37 of 37 good, exit 0 |
| `python tests/policy_mutants.py` (real clock) | 180 of 180 good, exit 0; both `probe ok` lines printed; weak 0 of 180 |
| `python tests/policy_mutants.py --day 2026-12-11` | 180 of 180 good, exit 0; "every mutant below runs with the tool's clock fixed to 2026-12-11" |
| `python tests/policy_mutants.py --day 2026-12-12` | 180 of 180 good, exit 0; "RED BASELINE at the fixed day 2026-12-12, as it must be" naming the three date tests; "every mutant below runs with the tool's clock fixed to 2026-12-12" |
| per-mutant result lines, real clock against each faked day | `diff` shows 0 lines for both days |
| `pytest -m "not live and not perf" -p no:cacheprovider -q -rs` (one full run) | **10928 passed, 13 skipped, 28 deselected in 289.65 s, exit 0.** The 13 skips: 12 tests that need a real Vault server (`HADAVIN_TEST_VAULT_ADDR` not set) and one other skip listed in `logs/g-full.log` |
| gitleaks (`origin/main..HEAD`, head 351f2b8b) | exit 0, "no leaks found", 15 commits scanned |

Not run: the 12 Vault engine tests (IMPOSSIBLE-NOW: no Vault server here; `ENGINE_RUN` untouched); the performance step, pip-audit, Semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit and the Python 3.12 job (CI only); the new CI step on GitHub (see `NOTES.md`, section A). The date guard of `--check` at a faked day was not run (the script's day is not settable from outside); the tests that give `main` a day, and the real-clock exit 0, stand in for it. The known timing test was not touched; it did not fail in the full run.
