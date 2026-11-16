# Evidence for Q8c-1 batch 9, head c6bd7108d3843f9d22f5344966af8e9783969251 (EVIDENCE RUNNER: recorded, nothing judged, nothing fixed)

Date of the run: 2026-11-12 (UTC). Detached worktree of the head, `git rev-parse HEAD` equals the head above, tree clean before and after. origin/main = 2a8c2aac89f83dd0a45af0412563b59ff4fe5632. Raw logs (outside the repo): `/home/user/build/evidence-raw/Q8c1b9-c6bd7108/`.

## What failed or was not run (first)
1. NOT RUN: the "real Vault server refuses the generated policies" tests (ticket item F3, Issue 8, the CI-only gate). No Vault or OpenBao program exists on this machine; 12 tests of `tests/test_policy_engine.py` were skipped in the full run (reason printed: `HADAVIN_TEST_VAULT_ADDR is not set`). In CI `HADAVIN_REQUIRE_VAULT_ENGINE=1` would turn that skip into a failure.
2. DEVIATION in set-up: `uv sync --locked --no-build --all-extras --group test` (the exact command) exits 2 here: "hadavin-sdk==0.1.0 @ editable+. ... marked as --no-build but has no binary distribution". I used `uv sync --locked --no-build-package nothing --all-extras --group test` (exit 0, same lock). Log: `uvsync.log`, `uvsync2.log`.
3. The full suite was run with `HADAVIN_TEST_PG_DSN` and PGHOST/PGPORT set in the server environment (own Postgres 16, TCP 127.0.0.1, own folder): no dblink failure. The known flaky test `test_the_timing_harness_flags_a_quadratic_stand_in` did not appear in the run, so it was not re-run (item f).
4. Not run: perf step (the ticket names no perf item), CI "security" job steps other than bandit (pip-audit, semgrep, zizmor), item 8 beyond the probes listed below (I wrote my own probes only for the day-text and date-limit rules; I did not walk every ticket table).
5. The one test skipped besides Vault: `tests/contracts/test_llm.py:95` (Stubber, skip reason printed by the test).

## Results
| # | Item | Command (via `uv run --no-sync`, cloud variables unset) | Exit | Last line |
|---|---|---|---|---|
| 1 | Changed files vs main | `git diff --name-only origin/main...HEAD` | 0 | 18 files (list in `item1-files.txt`) |
| 2a | Lint | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | Format | `ruff format --check src tests demos tools` | 0 | 324 files already formatted |
| 3 | Bandit | `bandit -q -r src demos tools -ll` | 0 | only two WARNING lines (nosec B102 in src/hadavin_sdk/tools.py:389), no issue |
| 4a | Repo scan | `python tools/scan_repo.py` | 0 | no output besides the uv warning |
| 4b | Stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4c | gitleaks origin/main..HEAD | `gitleaks git --redact --log-opts origin/main..HEAD` | 0 | no leaks found |
| 5 | Full suite | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 0 | 10892 passed, 13 skipped, 28 deselected in 303.48s |
| 6a | Policy mutants, real clock (2026-11-12) | `heavy.sh python tests/policy_mutants.py` | 0 | probe ok (canary day 2026-12-12 reached the child); 122 of 122 good; problems: [] |
| 6b | Policy mutants `--day 2026-12-11` | same with `--day` | 0 | probe ok (fixed day 2026-12-11); 122 of 122 good; problems: [] |
| 6c | Policy mutants `--day 2026-12-12` | same with `--day` | 0 | probe ok (fixed day 2026-12-12); 122 of 122 good; problems: [] |
| 6d | Page check, real clock | `python tools/policy_page.py --check` | 0 | (no output) |

Policy mutant detail: no `WRONG_REASON` line and no `BAD` line in any of the three runs. The weak-first-line line reads "weak ... for 0 of 122 mutants"; the same line lists 22 killer tests shared by more than one mutant (names in `mutants-real.log`). The per-mutant lines (verdict, name, killer test) of the three runs are identical (diff exit 0 for real vs 12-11 and real vs 12-12; 122 lines each). Mutants ran in a second worktree so the suite was not disturbed.

## Fail-before (item 7, c)
- Overlay A: only the changed test files of the batch-9 delta (`tests/test_policy_changelog.py`, `tests/test_policy_docs.py`, `tests/test_policy_guard.py`, `tests/fixtures/policy_sources_2026-11-11.txt`) put on a clean detached worktree of 208a47d5; `pytest tests/test_policy_changelog.py tests/test_policy_docs.py tests/test_policy_guard.py`: exit 1, **3 failed, 357 passed**. Failed: `test_the_changelog_entry_for_the_page_names_no_review_by_day_as_text`, `test_the_page_names_the_review_day_of_the_dated_lists_and_follows_a_renewal` (AttributeError: no `review_date`), `test_the_docs_page_names_the_review_day_of_the_dated_lists_only` (same).
- New or renamed test functions of the delta (from DELTA.patch) run one by one on 208a47d5 (file `failbefore-new-tests-on-208a47d5.txt`): FAIL on old code: 3 (the three above). PASS on old code: 5: `test_plant_a_ci_step_list_without_or_with_a_moved_check_step_is_refused`, `test_plant_a_changelog_entry_that_loses_the_reminder_sentence_or_fixes_a_day_is_refused`, `test_the_kinds_decision_day_is_a_literal_date_call_not_a_name_of_the_tools_date`, `test_the_tools_decision_day_is_the_day_the_names_and_claims_were_decided`, `test_the_day_the_tool_sees_is_the_fixed_day_the_run_was_given`. One test was removed by the delta (`test_the_sixteen_pending_kinds_each_stand_on_the_day_they_were_decided`).
- Overlay B (ticket 6.4): head's `tools/policy_page.py`, the four `tests/test_policy_*.py`, `tests/policy_mutants.py` and the fixture on origin/main 2a8c2aac (main's src, main's ci.yml; PYTHONPATH pointed to main's src): exit 1, **241 failed, 127 passed, 12 skipped**. Failure messages: `no POLICY in` for all three modules (92), for `secrets_vault.py` only (68), for `signer_vault.py` only (10), as `PolicyError` (13), and others; per-test list in `overlay-main-failed-tests.txt`. F1: failing by assertion as the ticket says (the ticket text says ten module names; the head names three, as it did in batch 8). F2 (`docs/least-privilege-policies.md`): that file name is not used by this package (page is `docs/declared-permissions.md`); not run as written. F3: not run (no Vault; 12 skipped as above).

## Issue 1 probes (item d)
Copies of the head in my own folder; `tools/policy_page.py` edited there only.
- Probe A: all three dated entries renewed to 2027-01-10: `review_date()` = 2027-01-10; `--write` exit 0, `--check` exit 0. The page differs from the head page on two lines only (docs lines 21 and 61), both now say 2027-01-10. With the old page restored, `--check` exit 1: "docs/declared-permissions.md differs from the data; run --write and commit".
- Probe B (mixed pair: names 2027-01-10, claims 2026-12-20): `review_date()` = 2026-12-20; the same two lines say 2026-12-20.
- Probe C (hostile): all review_by 2027-03-01 (more than 92 days after the decision): `--check` and `--write` exit 1 with "review_by 2027-03-01 is more than 92 days after the decision of 2026-11-11". Head tool with its clock at 2026-12-12: `--check` and `--write` exit 1 "is overdue (review_by 2026-12-11)" (file `probe-hostile-dates.txt`). Head worktree stayed clean.
- Where the text 2026-12-11 / 2026-12-12 (ISO form) still appears in src, tests, tools, docs, CHANGELOG.md, README.md, .github (25 lines, list in `day-text-grep.txt` in the raw folder): `docs/declared-permissions.md:21` and `:61` (generated by the tool; the day 2026-12-11); `CHANGELOG.md:298` ("from 2026-12-12", day after); tests (changelog 26; docs 134, 148, 153; guard 198, 3957, 3983, 4000, 4221, 4224, 4226, 4264, 4265, 4270 as test data); `tests/policy_mutants.py` 9, 988, 1002, 1018, 1049-1051, 1129. Not in `tools/policy_page.py` as ISO text. The literal `date(2026, 12, 11)` / `date(2026, 12, 12)` appears in `tools/policy_page.py` (3 entries), `tests/test_policy_changelog.py:23` and in `tests/test_policy_guard.py` (51, 183, 196, 1505, 1605, 2807, 3955, 3958, 3970, 4220, 4222).

## Issue 6 by hand (item e)
Plugin outside the repo prints what the tool's clock shows inside the test (`issue6-byhand.txt`): env 2026-12-12 gives 2026-12-12; env 2026-12-11 gives 2026-12-11; env unset gives 2026-11-12 (real clock); the test passes (1 passed) in all three. The mutant runner's own `probe ok` lines (6a to 6c) show the value reaching the child pytest through `CHILD_FIXED_ENV`.

## Clean-up
Own Postgres stopped and its folder removed; worktrees removed; no process of mine left. gitleaks on this folder: see the last line of the final report.
