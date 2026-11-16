# Q8c-1 evidence, head 208a47d5694179a1d2deddbe211cfa3af001ec4d (delta from ad588599)

EVIDENCE RUNNER: recorded, nothing judged, nothing fixed. No commit, no push. Raw logs outside the repo: `/home/user/build/evidence-raw/Q8c1b8-208a47d5/`. Worktrees `/home/user/build/EV-Q8c1b8-208a47d5/{wt,wtold,wtmain}` (wt clean, HEAD = 208a47d5 verified; origin/main = 2a8c2aac).

## Failed or not run (first)
- **No failures** in the head runs below. Full suite: 0 failed, 0 errors.
- **Vault engine tests NOT run**: 12 skips in `tests/test_policy_engine.py` (no Vault server here; `HADAVIN_TEST_VAULT_ADDR` and `HADAVIN_REQUIRE_VAULT_ENGINE` not set). CI behaviour not reproduced. `HADAVIN_REQUIRE_PINNED_UNIDATA` not set (Python here 3.13.18; not checked against the Unicode pin). 13th skip: `tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock]` (Stubber).
- **Deviation, run 1 of the full suite**: I forgot `HADAVIN_TEST_PG_DSN`; that run gave 10429 passed, 469 skipped (103 were "PG DSN not set"), exit 0. I reran with the DSN set: that is the run reported below (`full-run1-nodsn.*` kept).
- `uv sync --locked --all-extras --group test` used (not `--no-build`), as the brief said.
- No perf run, no timing-test runs (not asked in this brief). The CI "tests-py312" job not run.
- The ticket 6.4 text (ten kinds, `docs/least-privilege-policies.md`, moto) is older than this PR (three kinds, `docs/declared-permissions.md`); I ran the overlay as the brief said (head's policy files onto main), not the ticket's F1-F3 messages literally.
- Date-guard mutant runs at faked days: I could not see the shim's confirmation line inside the mutant runner's child pytest (its stderr is captured), so that the fake day reached the children is shown only for direct pytest and `--check` runs, not for the runner.
- `policy_page --check` at the faked day was run with a global `datetime.datetime` replacement (the script runs as `__main__`, so patching the module attribute does not reach it); pytest and the mutant runner used the module-attribute patch.
- Clock on this machine: 2026-11-12 UTC.

## Table
| # | Item | Command (short) | Exit | Result |
|---|---|---|---|---|
| 1 | Files vs main / vs ad588599 | `git diff --name-only origin/main...HEAD` (15 files), `ad588599..HEAD` (7 files) | 0 | lists in `diff-main.txt`, `diff-prev.txt` |
| 2 | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 | ruff format | `ruff format --check src tests demos tools` | 0 | 324 files already formatted |
| 2 | bandit | `bandit -q -r src demos tools -ll` | 0 | only warning: nosec (B102) src/hadavin_sdk/tools.py:389; no issues |
| 2 | scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 2 | stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 2 | policy_page --check, real clock | `python tools/policy_page.py --check` | 0 | no output |
| 2 | same, clock 2026-12-11 | FAKE_TODAY shim | 0 | no output |
| 2 | same, clock 2026-12-12 | FAKE_TODAY shim | 1 | 13 "PENDING_NAMES/PENDING_CLAIMS ... is overdue (review_by 2026-12-11)" lines (first lines in `pp-check-fake-2026-12-12.head.txt`; the "What to do" text follows each) |
| 3 | Policy mutants, real clock | `heavy.sh python tests/policy_mutants.py` | 0 | `111 of 111 good; problems: []`; then `first-line check is weak (killer asserts through same()) for 40 of 111 mutants; killer shared by more than one mutant: [...]` (list in raw `policy-mut-real.log`); run 423 s |
| 4 | Full pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rfEs --junitxml`, own Postgres 16.15 port 56931, PG DSN set | 0 (pytest's own) | XML: 10898 tests, 0 failed, 0 errors, 13 skipped; log: 10885 passed, 13 skipped, 28 deselected in 261.22 s; queue wait about 1013 s |
| 4 | Reruns of failing files on main | none needed (no failures); `tests/demo_askdata/test_validate_harm.py` did not fail (no /tmp path clash) | - | - |
| 5 | Policy test files (changelog, docs, guard), real clock | `pytest tests/test_policy_changelog.py tests/test_policy_docs.py tests/test_policy_guard.py` | 0 | 353 passed in 6.67 s |
| 5 | same, clock 2026-12-12 | `-p fakeclock` (pytest plugin from the ad588599 evidence) | 0 | 353 passed in 6.23 s |
| 5 | `tests/test_policy_engine.py` alone | pytest -rs | 0 | 8 passed, 12 skipped (Vault server) |
| 6 | Fail-before on ad588599: head's 3 test files + `policy_mutants.py` overlaid (old `tools/policy_page.py`, old ci.yml, old CHANGELOG), PYTHONPATH = that tree's src and tools (imports `wtold/tools/policy_page.py`, confirmed) | pytest 3 files | 1 | **3 failed, 350 passed**: `test_policy_docs::test_ci_runs_the_policy_page_check_right_after_the_policy_mutants` ("ci.yml has no step `python tools/policy_page.py --check`"), `test_policy_docs::test_the_changelog_names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder`, `test_policy_guard::test_the_tool_docstring_holds_no_date_that_is_not_in_the_dated_lists` ("holds a date that is in no dated list: ['2026-12-12']") |
| 6 | same, clock 2026-12-12 | `-p fakeclock` | 1 | same 3 failed, 350 passed |
| 6 | same plus head's ci.yml and CHANGELOG.md | pytest 3 files | 1 | 1 failed, 352 passed: only `test_the_tool_docstring_holds_no_date_that_is_not_in_the_dated_lists` |
| 6 | head's `tests/policy_mutants.py` on the old tree | `python tests/policy_mutants.py` | 1 | `RuntimeError: the unmutated copy does not pass its tests` (traceback in `fb-prev-mutants.log`) |
| 7 | Overlay on origin/main (2a8c2aac): head's `tools/policy_page.py`, `tests/test_policy_{changelog,docs,engine,guard}.py`, `tests/policy_mutants.py`, `tests/fixtures/policy_sources_2026-11-11.txt`; main's src and CI | pytest 4 files | 1 | **239 failed, 122 passed, 12 skipped**. By file: changelog 1 failed; docs 6 failed; engine 2 failed (+12 skipped); guard 230 failed. Most guard failures: `no POLICY in src/hadavin_sdk/actions/secrets_vault.py, .../audit/signer_vault.py, .../sources/kubernetes.py` (92 list all three, 68 vault only, 10 signer only, 2 kubernetes only, 13 as PolicyError). Non-guard failures: docs/changelog texts missing, ci.yml has no `policy_page.py --check` / `policy_mutants.py` steps, engine: `HADAVIN_REQUIRE_VAULT_ENGINE is not set beside HADAVIN_TEST_VAULT_ADDR` and `AttributeError: 'NoneType' object has no attribute 'platform'` (test_the_refused_requests_are_the_ones_the_page_names). Per-test list: `fb-main-pertest.tsv` |
| 8 | Date guard: policy mutants at 2026-12-11 and 2026-12-12 | FAKE_TODAY shim, heavy.sh | 0 and 0 | both `111 of 111 good; problems: []` and the same weak line; `diff` of the per-mutant output against the real-clock run: 0 lines for both days (no mutant result changes with the date) |
| 8 | `--check` at 12-11 / 12-12 | see row 2 | 0 / 1 | as row 2 |
| 9 | ci.yml new step (lines 94-99; added by this delta, 2 lines) | | | `- name: Declared-permission mutants (...) (blocks)` / `run: python tests/policy_mutants.py` / **`- name: Declared-permission page and dated lists (fails from the day after the earliest review date, until renewed) (blocks)` / `run: python tools/policy_page.py --check`** / then the comment `# Timing tests have their own step and it blocks ...` and `- name: Performance of the redaction patterns (blocks)` (`pytest -q -m perf -rs`). The Tests step before sets `HADAVIN_TEST_VAULT_ADDR`, `HADAVIN_REQUIRE_VAULT_ENGINE: "1"`, `HADAVIN_REQUIRE_PINNED_UNIDATA: "1"`. Neighbour lines in `ci-lines.txt` |
| 10 | gitleaks git | `gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..208a47d5"` | 0 | 11 commits scanned, no leaks found |
| 10 | gitleaks dir on this folder | 0 | no leaks found |

## Fake clock method
- pytest: plugin `fakeclock_pytest_plugin.py` (copy of the ad588599 one): autouse fixture replaces `tools.policy_page.datetime` with a subclass whose `now()` returns the faked day 12:00 UTC. Run as `PYTHONPATH=<shim dir> pytest -p fakeclock`.
- `--check` and mutant runner: `fakeclock_sitecustomize.py` (env `FAKE_TODAY=YYYY-MM-DD`): for the script, `FAKE_GLOBAL=1` replaces `datetime.datetime` in the process; otherwise an import hook patches `tools.policy_page.datetime` after import (also in child processes via PYTHONPATH).

gitleaks dir on this folder (config .gitleaks.toml, --redact): exit 0, no leaks found (95 KB scanned).
