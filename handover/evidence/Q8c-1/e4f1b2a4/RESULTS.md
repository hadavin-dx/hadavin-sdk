# Q8c-1 batch 11 evidence (EVIDENCE RUNNER: records, does not judge)

Head `e4f1b2a4a6a0ef5389a364ff9c9d9af5199574ad` (origin/wip/cloud-q8c1-b11; code head 351f2b8b, last commit adds only evidence files). Previous reviewed head d8441218. origin/main = 2a8c2aac. Tree clean at start and at end (`git status` empty). Real clock: 2026-11-12 UTC. Raw logs: `/home/user/build/evidence-raw/Q8c1b11-e4f1b2a4/`.

## What failed, deviated or was not run (first)
1. Nothing failed. Every command below exited as shown.
2. Set-up deviation: `uv sync --locked --all-extras --group test` WITHOUT `--no-build` (b10 found `--no-build` fails for the editable install; I did not retry it). Own Postgres 16 had to be started as user `postgres` (root refused); port 56711.
3. Not run: the 12 tests that need a real Vault server (HADAVIN_TEST_VAULT_ADDR not set) and 1 other skip (`tests/contracts/test_llm.py:95`); perf step, pip-audit, Semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit, the Python 3.12 job. The new CI notes step was NOT run on GitHub: only parsed as YAML (it exists, `if: github.event_name == 'pull_request'`). Timing flake test (item 9): not run (the ticket names no perf item).
4. Observation: a first full-suite start of mine was killed by me within seconds (Postgres could not start as root); the run in the table is the second, complete one.
5. Observation (not judged): `--auto origin/main` exits 1 with 113 "no row" lines (the builder's notes cite 136 before its notes existed); `--auto d8441218` (the push base) exits 0.
6. Observation (not judged): with both dated lists emptied on a copy of the real head, `policy_page.py --check` and `--write` exit 1 (one line per unchecked name or claim in the kind modules), as in b10. The "no review date applies now" wording appears only when `data_problems` is stubbed to no problems (labelled STUBBED; the brief asked for no stubs, so the unstubbed result is the primary one).
7. `src/` against origin/main: 3 files added (`actions/secrets_vault.py`, `audit/signer_vault.py`, `sources/kubernetes.py`, 536 insertions; this package's own work). `git diff d8441218 HEAD -- src` is EMPTY (0 lines). I did not judge whether a grant widened.

## Results table
| Item | Command | Exit | Last line / result |
|---|---|---|---|
| 1 changed files | `git diff --name-only origin/main...HEAD` | 0 | 62 files (`diff-names.txt`) |
| 2 lint | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 format | `ruff format --check src tests demos tools` | 0 | 326 files already formatted |
| 3 bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only the nosec warning at src/hadavin_sdk/tools.py:389 |
| 4 repo scan | `python tools/scan_repo.py` | 0 | no findings |
| 4 stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4 gitleaks | `gitleaks git --redact --config .gitleaks.toml --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 5 full pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own Postgres 16, PG DSN set) | 0 | 10928 passed, 13 skipped, 28 deselected in 265.88s |
| 6 policy mutants, real clock | `python tests/policy_mutants.py` | 0 | 180 of 180 good; problems: []; weak 0 of 180 |
| 6 `--day 2026-12-11` | same with `--day 2026-12-11` | 0 | 180 of 180 good; weak 0 |
| 6 `--day 2026-12-12` | same | 0 | 180 of 180 good; weak 0; "RED BASELINE at the fixed day 2026-12-12, as it must be" line printed |
| 6 `--day=2026-12-11` (equals form) | same | 0 | 180 of 180 good |
| 6 identical across days | per-mutant lines (timings stripped), `diff` real/1211, real/1212, 1211/1212 | - | 0, 0, 0 differing lines of 180 |
| 6 clock-only killers | runner line | - | 5 of 180 mutants killed ONLY by a test that reads the clock function (all three runs) |
| 6 policy page, head | `python tools/policy_page.py --check` | 0 | no output |
| 6 policy page, COPY, real lists | `--write` then `--check` | 0, 0 | page file byte-identical to the head's |
| 6 notes check, b11 files | `notes_lines_check.py d8441218 handover/evidence/Q8c-1/b11/NOTES.md <5 test files>` | 0 | no problem lines (also 0 with the four files without the runner) |
| 6 notes check, `--auto d8441218` (push base) | `--auto d8441218` | 0 | no lines |
| 6 notes check, `--auto origin/main` | `--auto origin/main` | 1 | 113 "has no row" lines |
| 6 ci.yml | `yaml.safe_load` | 0 | parses; jobs check, tests-py312, security; the notes step is in `check`, pull requests only |
| 7 fail-before, five test files copied into detached d8441218 (old `tools/`, old src) | pytest the 4 test files + `tests/policy_mutants.py` copied | 1 | 20 failed, 376 passed, 0 collection errors |
| 7 four files, old `tests/policy_mutants.py` kept | pytest | 1 | 23 failed, 373 passed, 0 collection errors (the 3 extra failures are the runner tests) |
| 7 of the 45 note rows | tests failing on old code / passing on old code | - | 23 fail, 22 pass (list of the 22 with their row kind: `new-tests-passing-on-old-code.txt`) |
| src change | `git diff --stat origin/main...HEAD -- src` / `git diff d8441218 HEAD -- src` | 0 | 3 files, 536 insertions / empty |

## Probes (item 8)
**Empty and partial lists** (copies of the head; `probe-policy-page-states.txt`): both lists emptied: `--check` 1, `--write` 1, `--check` 1 (13 lines: 6 names, 7 claims); only names emptied: 1/1/1 (6 lines); only claims emptied: 1/1/1 (7 lines). Partial renewal (copy edits of `review_by` to 2027-01-11): names renewed only, claims renewed only, one name group renewed only: each `--check` 0, `--write` 0, `--check` 0; the page still names 2026-12-11 (the entries not renewed). STUBBED (`data_problems` set aside): both lists emptied: `review_date()` None, `--write` 0, `--check` 0, page head: "a deployment chooses OpenBao; no review date applies now, because no dated entry is waiting for a check"; the only day in the page is 2026-11-11.
**Notes check plants** (copy `cpN`, base d8441218, five test files; control exit 0, no lines): row removed: exit 1, one line "...has no row of its own in the notes"; row's file cell changed to another test file: exit 1, same line; id moved to another cell of the row (`something_else` in the id cell): exit 1, same line. Weakened helper (`_changelog_entry` in tests/test_policy_docs.py made to return `changelog_entry()[:10]`, base HEAD, empty notes; control with no plant: exit 0, 0 lines): exit 1, listing 4 tests of that file that use it. Bad base commit: plain form exit 1 and `--auto` exit 1, "the base commit 'deadbeef00' does not resolve: every test would look new"; no arguments: exit 2.
**Day arguments** (`probe-day-arguments.txt`): `policy_mutants.py --day`, `--day=`, `--day 20261212`, `--day abc`: exit 2 "--day needs one day written YYYY-MM-DD"; `--day 2020-01-01`, `--day=2020-01-01`, `--day 2026-11-10`: exit 2 "is before 2026-11-11, the day the dated lists were decided"; `--day 2026-13-45`: exit 2 "is not a real day"; `--day` twice (both forms): exit 2 "--day may be given once only". So the runner never runs a red baseline at 2020-01-01. Guard file alone with `HADAVIN_POLICY_FIXED_DAY=2020-01-01` and the mutant marker set (`-k "date or review or overdue or pending" -x`): exit 1, first failure lists 16 "decided 2026-11-11 is in the future" lines; at 2026-12-12 with marker: exit 1, 7 overdue lines; without the marker either day: exit 2 "is set but this is not a mutant run".

## Cleanup
Own Postgres stopped and folder deleted; worktrees (head, d8441218, copies) removed; no push; nothing committed on the branch; no processes of mine left.
