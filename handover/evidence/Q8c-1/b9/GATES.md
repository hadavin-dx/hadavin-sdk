# Q8c-1 batch 9, gates on the final head (builder run, not independent)

Environment: own venv, own Postgres 16 (UTF8, user postgres, `PGHOST`/`PGPORT` in the server's environment), no cloud variables. Raw logs outside the repository: `/home/user/build/b9-ev/`.

| Gate | Result |
|---|---|
| `ruff check src tests demos tools` | exit 0, "All checks passed!" |
| `ruff format --check src tests demos tools` | exit 0, "324 files already formatted" |
| `bandit -q -r src demos tools -ll` | exit 0 (only the existing "nosec encountered" warnings) |
| `python tools/scan_repo.py` | exit 0, no output |
| `python tools/policy_page.py --check` | exit 0 on the real clock (the day of this run is 2026-11-12) |
| `python tests/stage_mutants.py` | 37 of 37 good, exit 0 |
| `python tests/policy_mutants.py` (real clock) | 122 of 122 good, exit 0; `probe ok` line printed; weak 0 of 122 |
| `python tests/policy_mutants.py --day 2026-12-11` | 122 of 122 good, exit 0; "every mutant below runs with the tool's clock fixed to 2026-12-11"; `probe ok` printed |
| `python tests/policy_mutants.py --day 2026-12-12` | 122 of 122 good, exit 0; "every mutant below runs with the tool's clock fixed to 2026-12-12"; `probe ok` printed |
| `diff` of the per-mutant result lines, real clock against each faked day | 0 lines for both days |
| `pytest -m "not live and not perf" -p no:cacheprovider -q` (one full run, `HADAVIN_TEST_PG_DSN` set) | **1 failed, 10891 passed, 13 skipped, 28 deselected, exit 1.** The failure is `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`: the server I started first had no `PGHOST`/`PGPORT` in its own environment (my setup slip), so dblink looked for the default socket. After restarting the server with them set, that file alone: 253 passed, exit 0 (`dblink-rerun.log`). The full run was not repeated. |
| Date guard at a faked day for `--check` itself | NOT RUN in this batch (the day shim for the script is outside the repository); the real-clock exit 0 and the test `test_the_check_command_uses_the_tools_own_clock_when_no_day_is_given` (own clock at 2026-12-11 and 2026-12-12) stand in for it |
| gitleaks | see the report (run before the push) |
