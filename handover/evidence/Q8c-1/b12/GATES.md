# Q8c-1 batch 12, gates (round 12)

Tested tree: commit cf5702ad (local) of branch `core/q8c1-b12`; the pushed commit holds the same `src/`, `tests/`, `tools/`, `.github/` and `CHANGELOG.md` (checked: `git diff cf5702ad <pushed head> -- src tests tools .github CHANGELOG.md` is empty) and adds only files under `handover/`. Base e4f1b2a4. Logs are in `logs/` next to this file (raw logs also in `/home/user/build/b12-ev/g2/`).

## Not run, or not complete (first)

- The 12 tests that need a real Vault server: not run (IMPOSSIBLE-NOW; `ENGINE_RUN` untouched).
- The new CI notes step on GitHub: not run (needs a pull request run). Only its text and the tool were tested.
- CI-only jobs (performance step, pip-audit, Semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit): not run here. Tests marked `live` or `perf` were deselected (28 deselected).
- The first full mutation runs (earlier in this batch) were NOT good: 14 of 234 mutants (12 stale snippets, 2 survivors) and one more survivor later; they were fixed and every gate below was run again on the final tree (see section A of `NOTES.md`). The earlier pytest run had one failure (`tests/demo_askdata/test_validate_harm.py ... [dblink-connect]`) because my Postgres server was started without `PGHOST` and `PGPORT` in its own environment; I restarted it with both and the full run below passed.
- The mutant `B12 an overdue unchecked claim is reported one day late` is by design not run at the fixed day 2026-12-12 (its killer is a date test that is red on that day); it ran in the other two runs.

## Commands and results (all on the tested tree)

| Command | Exit code | Result and log |
|---|---|---|
| `ruff check src tests demos tools` | 0 | all checks passed, `logs/ruff-check.log` |
| `ruff format --check src tests demos tools` | 0 | 326 files already formatted, `logs/ruff-format.log` |
| `uv run --with bandit bandit -ll -q -r src` | 0 | no medium or high finding, `logs/bandit.log` |
| `python tools/scan_repo.py` | 0 | `logs/scan-repo.log` |
| `python tools/policy_page.py --check` | 0 | `logs/policy-page-check.log` |
| `python tests/stage_mutants.py` (via heavy.sh) | 0 | 37 of 37 good, `logs/g-stage.log` |
| `python tests/policy_mutants.py` (real clock, via heavy.sh) | 0 | 235 of 235 good, 0 weak, `logs/g-pm-real.log` |
| `python tests/policy_mutants.py --day 2026-12-11` | 0 | 235 of 235 good, 0 weak, `logs/g-pm-1211.log` |
| `python tests/policy_mutants.py --day 2026-12-12` | 0 | 234 of 234 good (one mutant not run that day, see above), 0 weak, `logs/g-pm-1212.log` |
| `python tools/notes_lines_check.py --auto e4f1b2a4` (push base) | 0 | `logs/notes-check-push-base.log` |
| `python tools/notes_lines_check.py --auto origin/main` | 0 | `logs/notes-check-origin-main.log` |
| `pytest -m "not live and not perf" -p no:cacheprovider -q` (via heavy.sh, own Postgres 16, `PGHOST` and `PGPORT` in the server environment) | 0 | 10951 passed, 13 skipped, 28 deselected in 281 s, `logs/g-pytest.log` |
| gitleaks on `origin/main..HEAD` | see the report | run again on the pushed head before the push |

Fail-before runs: `logs/fail-before-e4f1b2a4.log` (five test files copied into a clean detached worktree of e4f1b2a4: 17 failed, 401 passed, 0 collection errors), `logs/fail-before-origin-main.log` (clean origin/main worktree: 5 collection errors), `logs/fail-before-two-names.log` (the one test added late: 1 failed).
