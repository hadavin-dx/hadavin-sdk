# Q8c-1 light evidence run, head ad588599fe75af1702ed91f05c80c0007a284bb0 (delta d598d967..ad588599)

EVIDENCE RUNNER: results recorded, nothing judged, nothing fixed. Raw logs (outside the repo): `/home/user/build/evidence-raw/Q8c1-ad588599/`; small copies are in this folder.

## What was NOT run or deviated (first)
- `uv sync --locked --no-build` failed (exit 2: the project itself has no binary build); I ran `uv sync --locked --all-extras --group test` instead (exit 0).
- Vault engine tests did NOT run: `HADAVIN_REQUIRE_VAULT_ENGINE` and `HADAVIN_TEST_VAULT_ADDR` not set, no binary downloaded: 12 skipped in `tests/test_policy_engine.py` (alone and inside the full run). CI sets both; CI behaviour not reproduced. `HADAVIN_REQUIRE_PINNED_UNIDATA` also not set (Python here is 3.13.18; not checked against the pin).
- Timing test not run on its own: it was not needed (full suite exit 0; `-m "not perf"` deselected 28 tests; the timing test name does not appear in the log).
- No perf run, no CI steps other than those you listed (also ran the two CI mutant steps `stage_mutants.py`, `policy_mutants.py`).
- Old-tree comparison runs (`wtold`, d598d967) import `hadavin_sdk` from the HEAD worktree's `src` (editable install in the shared venv); the delta has no `src` change, so this only matters if you read it otherwise. `tools/` and `tests/` came from the old tree (pytest `pythonpath=["."]`).
- Real clock on this machine: 2026-11-12 UTC (the real-clock runs are therefore before the 2026-12-11 review date).

## Table
| Item | Command (short) | Exit | Last line / result |
|---|---|---|---|
| Fail-before (tests only) | head's `tests/test_policy_guard.py` copied onto d598d967 (old `tools/policy_page.py`), pytest on that file | 2 | collection error: `AttributeError: module 'tools.policy_page' has no attribute 'DECIDED'`; 1 error, 0 tests ran (`failbefore-testsonly.log`) |
| Fail-before (tests + head's policy_page.py copied) | same plus head `tools/policy_page.py`, 3 policy files | 0 | 346 passed (shows the tool change is what the new tests need) |
| Old tree, clock faked to 2026-12-12 | pytest 3 policy files on d598d967 with fake clock | 1 | 13 failed, 331 passed (names in `pol3-fake-old-failed.txt`) |
| Head, clock faked to 2026-12-12 | same on ad588599 | 0 | 346 passed |
| Head, real clock | `tests/test_policy_guard.py tests/test_policy_changelog.py tests/test_policy_docs.py` | 0 | 346 passed in 6.61s |
| Old, real clock | same on d598d967 | 0 | 344 passed |
| Full suite | heavy.sh pytest `-p no:cacheprovider -q -m "not live and not perf" -rs`, own Postgres 16.15 port 56877, PGHOST/PGPORT in server env | 0 (pytest's own) | 10878 passed, 13 skipped, 28 deselected in 263.81s (12 Vault engine skips + 1 `tests/contracts/test_llm.py:95`); wall 326s incl. queue |
| ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| ruff format | `ruff format --check src tests demos tools` | 0 | 324 files already formatted |
| bandit | `bandit -q -r src demos tools -ll` | 0 | only 2 warnings "nosec encountered (B102) ... src/hadavin_sdk/tools.py:389"; no issues |
| scan_repo | `python tools/scan_repo.py` | 0 | no output |
| policy page check | `python tools/policy_page.py --check` | 0 | no output |
| policy mutants | `python tests/policy_mutants.py` (script's own exit) | 0 | `first-line check is weak (killer asserts through same()) for 40 of 108 mutants; killer shared by more than one mutant: [17 test names]`; the line before: `108 of 108 good; problems: []` |
| stage mutants | `python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| gitleaks origin/main..HEAD | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| Engine tests alone | `pytest tests/test_policy_engine.py -rs` | 0 | 8 passed, 12 skipped |

## Fake clock method
pytest plugin `fakeclock.py` (this folder), loaded with `PYTHONPATH=<dir> pytest -p fakeclock`: an autouse fixture replaces the module attribute `tools.policy_page.datetime` with a subclass whose `now()` returns 2026-12-12 12:00 UTC. Source has `datetime.now(UTC).date()` in `data_problems`; no other clock use in the tool.

## Probe: `tools.policy_page.main([mode], today=...)` (script `probe.py`, run on a `git archive` copy of the head so the real tree is untouched; `probe.log`)
| today | mode | exit |
|---|---|---|
| 2026-12-11 | --write | 0 |
| 2026-12-11 | --check | 0 |
| 2026-12-12 | --write | 1 (each overdue `PENDING_NAMES` entry such as ('secrets/vault', 'never:{mount}/undelete/*') reported: "is overdue (review_by 2026-12-11)" with the "What to do" text) |
| 2026-12-12 | --check | 1 (same lines) |

## Not-run list for the timing test
Not run (see above). Worktrees: `/home/user/build/EV-Q8c1-ad588599/{wt,wtold,wtmain}`; head `git status` clean at the end; no commit, no push.
