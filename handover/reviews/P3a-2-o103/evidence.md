# P3a-2 evidence, ORDER 103 (builder, Sonnet 5.5). Head SHA: 63658aaceadc2f3e8e5429c5d01681c3b8b42f67 on core/P3a-2 (pushed, fast-forward from 967d5a1; base main 0dabf1f)

Every log in this folder names this head on its first line (mutants-p3a2.log: first line replaced by hand with the head; the runner's own line follows). The builder only builds and records; the lead runs the EGM review steps.
Environment: Linux; PostgreSQL 16.15 (own server, port 55434, data dir `pgdata/` here, UTF8 cluster, stopped at the end; CI uses Postgres 17: NOT run). Python 3.13 and 3.12, own venvs `venv-P3a-2-o103-313/312`, `PYTHONPATH=<build-dir>/src` (import path printed in fail-before.txt and mutants-p3a2.log). No spend, no model call.

## What failed first / not checked
- My first cluster was initialised without a locale (SQL_ASCII): psycopg returned bytes and `migrate()` crashed with TypeError in `gone_message` (BN item 8). Re-made as UTF8.
- First merged build failed P3a-1's guard test `test_the_lock_key_and_the_folder_are_the_ones_migrate_uses` (raw record in fail-before.txt): fixed (`migrate.py` no longer assigns `_LOCK`).
- First full suites ran at the same time against one cluster: both failed one test (`test_validate_harm[create-role]`, a cluster-global role name collides); logs kept in `concurrent-run/`. Re-run one after the other: green.
- First mutants run: 55 of 56; N6 (require_module skips even with the DSN set) SURVIVED because `pytest.raises(fail)` lets a Skipped through and the test was only skipped. Test fixed (`_outcome`), head moved. Then 34 of 36 for the P3a-1 mutants: two expected text fragments went stale because migrate.py now imports the key and folder; updated (head moved again). Older logs: `old1/`, `old2/`.
- NOT checked: PostgreSQL 17; runbook case (e) steps E1-E3 (no test); the real `psql` test (not in P3a-2); the CI run itself; CodeQL/Sonar/CodeRabbit.

## Results at the final head (log names in this folder)
| gate | result |
|---|---|
| ruff check / ruff format --check (src tests demos) | clean, 317 files (lint.txt) |
| bandit -q -r src demos -ll | rc 0, 0 Issue lines (bandit.txt) |
| tools/scan_repo.py | rc 0 (scan_repo.txt) |
| pytest 3.13, DSN set, `-m "not live and not perf"` | 10506 passed, 1 skipped, 0 failed (pytest313.log) |
| pytest 3.12, same | 10506 passed, 1 skipped, 0 failed (pytest312.log) |
| skipped with the DSN set | 1 per version: `tests/contracts/test_llm.py:95` (stubber, not P3a-2; also skipped on the base). None in a P3a-2 test. |
| P3a-2 mutants (mutants.py) | 56 of 56 killed (mutants-p3a2.log): the first 36 + 20 new (N1-N19, N3b) |
| P3a-1 mutants (`uv run python tests/migration_numbers_mutants.py`) | 36 of 36 good (mutants-p3a1.log) |
| `python tests/stage_mutants.py` (new CI step) | 37 of 37 good (stage-mutants.log) |
| perf-marked tests of test_migration_numbers.py, alone | 2 passed (perf.log): includes the real-clock self-check |
git status after all mutation runs: clean. Mutants ran on a git-archive copy, never on the worktree.

## FAIL-BEFORE (fail-before.txt): new tests on 967d5a1
FAIL on the base: `test_every_caller_in_the_package_uses_the_right_form`, `test_the_scan_calls_the_pair_function_and_hand_recipe_the_raising_one`, `test_the_migrate_docstring_says_where_role_membership_is_changed`, `test_the_changelog_never_gives_the_false_evidence_name`, `test_the_changelog_no_longer_advises_dropping_the_evidence_tables`, `test_the_runbook_carries_the_real_lock_the_command_and_every_case`, and `test_no_p3a2_test_skips_silently` for the base's own wiring and postgres files (importorskip). Also P3a-1's guard test on the merge commit 2cde7e2 (before the lock fix).
PIN tests (pass on the base by design; the killing mutant in brackets, order 89): require_module outcome tests [N6, N7, N10]; skip-rule files check [N5, N8, N9]; pair/str form real-file check [N1, N2, N3, N4; N3b shows the old wiring tests also kill N3]; role-membership tripwire `..._whatever_the_comments_and_names_hold` [N11 substring on, N12 kept view, N13 rule removed]; `test_privileges_on_objects_are_not_refused...` [N14]; `test_no_role_membership_form_holds_a_standalone_on` [no source mutant: it fails only when pglast's grammar gains an ON in a role grant]; `test_migrate_takes_the_one_advisory_lock_key_first` [MW8]; docstring [N15]; CHANGELOG [N16-N19]. The self-tests of the two AST checkers (made-up snippets) have no mutant of their own.

## Per item
- A merge: plain `git merge origin/main`; conflicts in 5 files taken as main's; P3a-2's 50 test lines re-added to test_migration_numbers.py; stale `tests/test_migration_numbers_fix1.py` removed. `git diff origin/main --stat`: 9 files, only P3a-2 work.
- B: `hand_recipe` already uses `checked_statement_text` on main; P3a-2's only pair caller is `_scan` (correct). Test `test_every_caller_in_the_package_uses_the_right_form` (AST over all of `src`) fails on a wrong unpack; mutants N1 (dead helper, only that test kills it among the new tests), N2, N3, N4.
- C1: P3a-2 adds no clock test. The real-clock self-check lives in P3a-1's merged `test_the_timing_harness_flags_a_quadratic_stand_in` (16 KiB vs 256 KiB, ratio rule, median of 3, no fixed seconds); it passed alone (perf.log). QUESTION for the lead: the ledger row text is not in the repo; if it asks for a change to the P3a-1 fixture (e.g. best-of-N in `timing.py` or a retry), that file is P3a-1 as merged and I did not touch it.
- C2: `tests/fixtures/dsn_skip.py::require_module` replaces `importorskip` in the wiring and postgres test files (DSN set: fail; no DSN: skip with a reason naming the variable); AST test over the three P3a-2 test files forbids importorskip, bare skip marks and any skip not under `not DSN`. The sys.platform skips in test_migration_numbers.py are P3a-1's.
- C3: erratum in the `migrate()` docstring (checked by a test), proposed ticket text BN-P3a-2-f in BN.md; tripwire = pglast comparison over 810 statements (135 role-grant forms x 6 comment wrappers) plus 9 object-grant forms. Limit: it cannot see grammar PostgreSQL has not got yet; it fails when a pglast upgrade puts ON in a role grant. If "a later standalone on token" meant something else, say so.
- D: `grep -n 0006_evidence CHANGELOG.md` prints nothing (rc 1). Repair step reworded (drop advice removed), a late-file sentence that became false after P3a-1 corrected, "Migration runbook (P3a)" appended (cases a-f, from the ticket's Rollback text and build note 15; the DO check text is mine, run on 16.15: runbook-do-check.txt), condensed copy in the migrate.py module docstring. Ungrounded: case (e) steps E1-E3 are not tested here (stated in the CHANGELOG).
- Extra: `migrate.py` uses the imported `MIGRATE_LOCK` (P3a-1's guard test); wiring test reads the lock parameter; two P3a-1 mutant fragments updated in tests/migration_numbers_mutants.py (4 lines).
