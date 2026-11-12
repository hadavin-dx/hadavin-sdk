# Q8c-1 batch 14, gates (round 14)

Tested tree: the code of the commit named in the push report (the commits after the last code change of this branch add only notes and logs under `handover/evidence/Q8c-1/b14/`; check with `git diff <code commit> <pushed head> -- src tests tools .github CHANGELOG.md`). Raw logs outside the repository: `/home/user/build/b14-ev/`; the cited ones are copied to `logs/`.

## Not run, or not complete (first)

- The 12 tests that need a real Vault server: not run (IMPOSSIBLE-NOW; `ENGINE_RUN` untouched).
- The CI notes step on GitHub: not run (it needs a pull request run). Only the tool and its text were tested.
- CI-only jobs (performance step, Python 3.12, pip-audit, Semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit, the CI Vault service, the timing test run alone): not run here. Tests marked `live` or `perf` were deselected.
- `uv sync --locked --no-build` fails in this evidence box; `bandit` is not in the project venv and ran as `uv run --with bandit`. CI must still run both.
- The mutant `B12 an overdue unchecked claim is reported one day late` is by design not run at the fixed day 2026-12-12 (the runs at 12-12 and 12-13 show 323 mutants, not 324).
- The first full suite run failed 4 tests (a Postgres environment slip of mine and three renewal plants that were red for a stale mutant file); both causes are in `NOTES.md` section A; the log is `logs/full-pytest-run1-bad-env.log`. The table below is the second run, on the final code.
- The first real-clock run of the mutant list found 3 problems of the day-scan mutants (see `NOTES.md` section A); fixed, and the whole list re-run on the final code: the table below.

## Commands and results

| Command | Exit code | Result and log |
|---|---|---|
| `ruff check src tests demos tools` | 0 | `logs/ruff-check.log` |
| `ruff format --check src tests demos tools` | 0 | `logs/ruff-format.log` |
| `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | `logs/bandit.log` |
| `python tools/scan_repo.py` | 0 | `logs/scan-repo.log` |
| `python tools/policy_page.py --check` | 0 | `logs/policy-page-check.log` |
| `python tests/stage_mutants.py` (via heavy.sh) | 0 | 37 of 37 good; problems: [], `logs/g-stage.log` |
| `python tests/policy_mutants.py` (real clock 2026-11-12, via heavy.sh) | 0 | 324 of 324 good; problems: [], weak first-line check 0 of 324, `logs/mutants-b14-real.log` |
| `python tests/policy_mutants.py --day 2026-12-11` | 0 | 324 of 324 good; problems: [], `logs/mutants-b14-2026-12-11.log` |
| `python tests/policy_mutants.py --day 2026-12-12` | 0 | 323 of 323 good; problems: [], `logs/mutants-b14-2026-12-12.log` |
| `python tests/policy_mutants.py --day 2026-12-13` | 0 | 323 of 323 good; problems: [], `logs/mutants-b14-2026-12-13.log` |
| Renewal rehearsal: `HADAVIN_POLICY_FULL_RENEWAL_RUN=1 HADAVIN_POLICY_FIXED_DAY=2026-12-12 pytest tests/test_policy_changelog.py -k "plant_a_full or plant_a_renewal_of"` (via heavy.sh) | 0 | 3 passed, 6 deselected in 1536.55s (0:25:36): the full renewal, the renewal of the kinds alone and of the names and claims alone, each run on a renewed copy with the whole mutant list on the new decision day and the day after, `logs/rehearsal-1212.log` |
| `python tools/notes_lines_check.py --auto c65d9c27` (the base of this branch) | 0 | `logs/notes-check-c65d9c27.log` (empty: no problem line) |
| `python tools/notes_lines_check.py --auto origin/main` | 0 | `logs/notes-check-origin-main.log` (empty: no problem line) |
| `pytest -m "not live and not perf" -p no:cacheprovider -q` (via heavy.sh, own Postgres 16.15 on port 56214 started as user postgres with `PGHOST` and `PGPORT` in the server environment, checked in `/proc/<pid>/environ`; `HADAVIN_TEST_PG_DSN` set) | 0 | 10983 passed, 13 skipped, 28 deselected in 647.31s (0:10:47), `logs/full-pytest.log` |
| gitleaks on `origin/main..HEAD` | 0 | `logs/gitleaks.log` |

Fail-before: `logs/fail-before-final-c65d9c27.log` (the four changed test files copied into a clean detached worktree of c65d9c27, without the three slow renewal plants and one fast older test of the same words: 13 failed, 434 passed, 4 deselected, 0 collection errors; the first failing line of each of the 13 is in `NOTES.md` section C). The plants on the old code: `logs/fail-before-plants-only-c65d9c27.log` and `logs/fail-before-plants-oldguard-c65d9c27.log` (what they show and do not show is in `NOTES.md` section A).

`src` against main and against c65d9c27: `logs/src-vs-main.log`.
