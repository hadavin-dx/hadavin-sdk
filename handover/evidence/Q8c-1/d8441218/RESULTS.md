# Q8c-1 batch 10 evidence (EVIDENCE RUNNER: records, does not judge)

Head `d84412189fd92962b0769302007714c301f8823d` (branch wip/cloud-q8c1-b10; previous head c6bd7108). origin/main = 2a8c2aac. Tree clean at start. Raw logs: `/home/user/build/evidence-raw/Q8c1b10-d8441218/`. Dates: real clock was 2026-11-12 (UTC).

## What failed, deviated or was not run (first)
1. Set-up deviation: `uv sync --locked --no-build ...` failed (rc 2: "hadavin-sdk editable can't be installed because it is marked --no-build but has no binary distribution"). I ran `uv sync --locked --all-extras --group test` (without `--no-build`, rc 0). All results below are from that venv. Python/dependency versions follow uv.lock.
2. Not run: the 12 tests that need a real Vault server skipped (HADAVIN_TEST_VAULT_ADDR not set; no Vault here). Also not run: the perf step, pip-audit, Semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit, Python 3.12 job (CI only). Timing flake test: not run (it did not show in the full run, per brief item e).
3. Fail-before (item c) on the old tree gives a different count depending on what is copied (see table): the four test files alone give 7 failed + 1 collection error; with the new `tests/policy_mutants.py` also copied: 3 failed + 1 collection error. The collection error is `tests/test_notes_lines_check.py` (needs `tools/notes_lines_check.py`, absent in c6bd7108). The builder's NOTES say "3 failed, 368 passed"; I get 3 failed, 369 passed, 1 error (runner copied) -- I did not copy `tools/notes_lines_check.py`.
4. Probe observation (not judged): `HADAVIN_POLICY_FIXED_DAY=2026-12-12` without the marker, run on the four changed files together, ends with rc 2 and the Exit line only AFTER 16 tests (the notes-check, changelog and docs tests, collected before the guard file) already passed ("16 passed"). On the guard file alone it prints the Exit line and "no tests ran" (rc 2).
5. Probe observation: with both lists emptied in a copy of the head, `policy_page.py --check` and `--write` exit 1 (not 0) because the kind modules still hold `claims_unverified` and unread names (one line per entry, "has no PENDING_NAMES / PENDING_CLAIMS entry"); the page file stays as it was. Exit 0 and the "no review date is set" page text appear only when `data_problems` is also set aside (as the builder's test does).

## Results table
| Item | Command | Exit | Last line / result |
|---|---|---|---|
| 1 changed files vs origin/main | `git diff --name-only origin/main...HEAD` | 0 | 23 files (list: raw `diff-names.txt`) |
| 2 lint | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 format | `ruff format --check src tests demos tools` | 0 | 326 files already formatted |
| 3 bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only a nosec warning (src/hadavin_sdk/tools.py:389) |
| 4 repo scan | `python tools/scan_repo.py` | 0 | no output lines |
| 4 stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4 gitleaks | `gitleaks git --redact --config .gitleaks.toml --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 5 full pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own Postgres 16, PGHOST/PGPORT in server env) | 0 | 10908 passed, 13 skipped, 28 deselected in 276.61s (the 13 skips: 12 Vault-server tests + 1 `tests/contracts/test_llm.py:95`) |
| 6 CI: policy page | `python tools/policy_page.py --check` | 0 | no output |
| 6 CI: policy mutants (real clock, 2026-11-12) | `python tests/policy_mutants.py` | 0 | 141 of 141 good; problems: [] |
| a: `--day 2026-12-11` | `python tests/policy_mutants.py --day 2026-12-11` | 0 | 141 of 141 good; problems: [] |
| a: `--day 2026-12-12` | `python tests/policy_mutants.py --day 2026-12-12` | 0 | 141 of 141 good; problems: []; RED BASELINE line (below) |
| a: `--day <real today 2026-11-12>` | same | 0 | 141 of 141 good; problems: [] |
| b: notes line check | `python tools/notes_lines_check.py c6bd7108 handover/evidence/Q8c-1/b10/NOTES.md <the four test files>` | 0 | no problem lines. It prints one line per test that is new/changed against c6bd7108 (AST differs) with no table row in NOTES, or a deleted test; reason cell must be 12+ characters |
| b: new tests | `pytest tests/test_notes_lines_check.py` (inside the 376-test run on the head, real day) | 0 | 376 passed (four files together) |
| c: old tree, 4 test files copied | pytest in detached c6bd7108 | 1 | 7 failed, 365 passed, 1 error (collection) |
| c: old tree, 4 test files + tests/policy_mutants.py copied | same | 1 | 3 failed, 369 passed, 1 error (collection) |
| c: head, FIXED_DAY=2026-12-12, no marker | pytest four files | 2 | "16 passed" then `Exit: HADAVIN_POLICY_FIXED_DAY is set but this is not a mutant run (...)`; guard file alone: "no tests ran" |
| c: head, FIXED_DAY=2026-12-12 + MUTANT_RUN=1 | pytest four files | 1 | 3 failed, 373 passed (the three date tests) |
| d4: `--day`, `--day 2026-13-45`, `--day 20261212`, `--day 2026-W50-5`, `--day abc` | `policy_mutants.py ...` | 2 each | one line each: "--day needs one day written YYYY-MM-DD..." or "--day 2026-13-45 is not a real day; write YYYY-MM-DD" |

## Details
**Policy mutants, three runs:** exit codes 0 / 0 / 0 (real, 12-11, 12-12), each "141 of 141 good", weak line "for 0 of 141 mutants". Per-mutant lines (141 each, timings stripped) are identical across the three runs: `diff` of real vs 12-11, real vs 12-12, 12-11 vs 12-12 each gave 0 differing lines. Mutants killed ONLY by a clock-reading test: 1 of 141 in every run: `B10 the clock function of the date tests reads the real day`. Probes printed in every run: "probe ok: at the fixed day 2027-02-01 exactly the three date tests are red" and "probe ok: the fixed day 2026-12-10 reached the tool's clock in the child pytest". Shared-killer list printed (see raw log). Per-mutant lines: `policy-mutants-lines-real.txt`.

**Red baseline at 2026-12-12 (runner line):** exactly these three tests red: `test_every_grant_name_is_verified_or_pending_and_every_source_id_resolves`, `test_every_kind_is_declared_pending_or_holds_no_identity`, `test_every_unchecked_claim_has_a_dated_entry_and_the_suite_goes_red_when_it_is_overdue`; the mutants then ran with those three deselected in the child only.

**Fail-before, failing tests on the old tree (four files copied):** test_policy_changelog::test_the_changelog_entry_for_the_page_writes_no_day_but_the_kinds_days_read_from_the_list; test_policy_docs::test_the_changelog_names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder; test_policy_guard::test_the_runner_refuses_a_day_argument_that_is_missing_or_not_a_day; ::test_the_probe_day_is_never_the_real_day_and_is_never_after_the_review_day; ::test_the_clock_readers_of_the_guard_file_include_the_three_date_tests; ::test_the_message_scan_counts_only_assert_messages_match_and_what_texts; ::test_with_both_dated_lists_empty_the_page_names_no_day_and_the_commands_still_report. With the new runner copied too, the failing three are the changelog test, the docs test and the empty-lists test. (The old venv's editable install points at the head's src; src is identical, `git diff c6bd7108 HEAD -- src` is empty.) New tests that pass on the old code are every other new/changed test (not listed one by one; counts above).

**Old tree at faked day (item d3):** c6bd7108 with `HADAVIN_POLICY_FIXED_DAY=2026-12-12`: guard, docs, changelog files: 360 passed, 0 red (the three date tests read an import-time day). Head with day + marker: 3 failed, 369 passed (the three date tests named above). Head at 2026-12-11 + marker: 372 passed.

**Probe 1, empty lists (copy of head, `probe1/` in raw dir):**
- both lists emptied: `--check` rc 1, `--write` rc 1, `--check` after write rc 1; messages: six "never:... has no PENDING_NAMES entry" lines and seven "... unchecked claim ... no PENDING_CLAIMS entry" lines. Only names emptied: rc 1/1/1 (six names lines). Only claims emptied: rc 1/1/1 (seven claims lines).
- with `data_problems` stubbed to no problems: both emptied: review_date None, `--write` 0, `--check` 0, page head "...a deployment chooses OpenBao (no review date is set: no permission name or claim is waiting for a check) (ledger row BL-core-q8c1-openbao)." and "No permission name or claim is waiting for a check now: the tests hold no dated entry for one." Names only emptied or claims only emptied: review_date 2026-12-11, rc 0/0, page names 2026-12-11 twice.

**Probe 2, weak scan:** for mutant "A1 a second request or send..." with expect text only in (a) a comment, (b) a loop literal, (c) a predicate `any(text in p ...)`, (d) a docstring: each is listed weak (True); text in an assert message or a `pytest.raises(match=)`: not weak. End to end: I edited the real killer so the text was only in a trailing comment: `weak_mutants` printed "weak count: 1" naming that mutant (files `probe-weak-scan-*.txt`). Copy reverted.

**Probe 5, review-day text (grep for 2026-12-10/11/12 and 2027-01-2x over src tests tools docs CHANGELOG.md; 33 lines):** src: none; tools: none; CHANGELOG.md:298 ("7 of them from 2026-12-12 and the other 9 from 2027-02-01"); docs/declared-permissions.md lines 21 and 61 (generated page: "2026-12-11"); tests/test_policy_changelog.py 26, 71, 72, 73; tests/test_policy_docs.py 154; tests/policy_mutants.py 9, 997, 1011, 1027, 1035, 1210, 1211, 1292; tests/test_policy_guard.py 222, 4035, 4061, 4078, 4320, 4323, 4325, 4363, 4364, 4369, 4372, 4451, 4455, 4458, 4519, 4609, 4614. Full list with text: raw `probe5/review-day-grep.txt`.

## Cleanup
Own Postgres stopped and its folder deleted; own worktrees removed; no push; nothing committed on the branch. No processes left running that I started.
