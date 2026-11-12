# Q8c-1 batch 13, gates (round 13)

Tested tree: the code of commit 45173a3c (later commits of this branch change only handover notes and logs; checked with `git diff 45173a3c <pushed head> -- src tests tools .github CHANGELOG.md`, see the report). Raw logs outside the repository: `/home/user/build/b13-ev/`; the cited ones are copied to `logs/`.

## Not run, or not complete (first)

- The 12 tests that need a real Vault server: not run (IMPOSSIBLE-NOW; `ENGINE_RUN` untouched).
- The CI notes step on GitHub: not run (needs a pull request run). Only the tool and its text were tested.
- CI-only jobs (performance step, pip-audit, Semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit): not run here. Tests marked `live` or `perf` were deselected.
- `python tests/stage_mutants.py` ran on the earlier commit 8664dc9b, not again after the last change (the change touched only the notes check and its mutant; the stage mutants do not read those files).
- The mutant `B12 an overdue unchecked claim is reported one day late` is by design not run at the fixed day 2026-12-12.
- The first run of the notes check against origin/main failed (219 rows of earlier batches pointed at a test file name, a quoted word and a log file that was never kept). I fixed the check (a test file name now counts as a name) and corrected two old rows (`b10`: a log that was not kept, `b11`: a quoted word); the mutant for that fix is `B13 the references of a tree leave out the names of the test files`. The whole mutant run, the full suite and the notes checks were run again afterwards.

## Commands and results

| Command | Exit code | Result and log |
|---|---|---|
| `ruff check src tests demos tools` | 0 | `logs/ruff-check.log` |
| `ruff format --check src tests demos tools` | 0 | `logs/ruff-format.log` |
| `uv run --with bandit bandit -ll -q -r src` | 0 | `logs/bandit.log` |
| `python tools/scan_repo.py` | 0 | `logs/scan-repo.log` |
| `python tools/policy_page.py --check` | 0 | `logs/policy-page-check.log` |
| `python tests/stage_mutants.py` (via heavy.sh) | 0 | 37 of 37 good; problems: [], `logs/g-stage.log` |
| `python tests/policy_mutants.py` (real clock, via heavy.sh) | see log | 269 of 269 good; problems: [], `logs/mutants-b13-real.log` |
| `python tests/policy_mutants.py --day 2026-12-11` | see log | 269 of 269 good; problems: [], `logs/g-pm-1211.log` |
| `python tests/policy_mutants.py --day 2026-12-12` | see log | 268 of 268 good; problems: [], `logs/g-pm-1212.log` |
| `python tools/notes_lines_check.py --auto 6d219217` (push base is a new ref, so the batch 12 head) | 0 | `logs/notes-check-push-base.log` |
| `python tools/notes_lines_check.py --auto origin/main` | 0 | `logs/notes-check-origin-main.log` |
| `pytest -m "not live and not perf" -p no:cacheprovider -q` (via heavy.sh, own Postgres 16 as user postgres, `PGHOST` and `PGPORT` in the server environment, checked in `/proc/<pid>/environ`) | see log | 10968 passed, 13 skipped, 28 deselected in 365.86s (0:06:05), `logs/full-pytest.log` |
| gitleaks on `origin/main..HEAD` | see the report | run before the push |

Fail-before: `logs/fail-before-6d219217.log` (four changed test files copied into a clean detached worktree of 6d219217: 19 failed, 417 passed, 0 collection errors; ids in `NOTES.md` section A).
