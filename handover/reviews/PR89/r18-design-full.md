<!-- full hand-back report of sub-agent af950fd4, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

REVIEW of PR 89 (core/mutation-runner-keywords @ db0d9eb), design-critic pass. Verdict: NOT READY. There are no code Blockers that I could prove by reading, but there are 4 Majors. The evidence available is also not READY-grade.

What I read: all of DIFF.patch, except that I only sampled tests/test_mutation_runner_keywords.py (about 2,800 lines, 134 tests; I read lines 1-330, 430-550, 2176-2260 and 2785-2855). I also read tools/mutation_runner.py (the diff hunks), src/hadavin_sdk/testing/mutation.py, CLAUDE.md, STUDIO-RULES.md and the tool-ladder rule.

Evidence: /home/user/hadavin-sdk/handover/evidence/PR89/db0d9eb/RESULTS.md exists. It was run by the planning session, not by an independent EVIDENCE RUNNER. It covers only:
- 134 keyword tests passed.
- ruff passed.
- bandit NOT RUN.
- The full suite, Postgres tests, mutation checks, hostile inputs and gitleaks were NOT RUN.

FAILURES, most serious first

1. Major (process and test quality): the new mutant list has never been executed.
- Where: tests/mutation_runner_mutants.py (EXPECTED_MUTANTS rises from 62 to 217, including 4 mutants of tests/conftest.py), and the evidence file.
- Scenario: the 155 new mutants and the keyword-test killers are only meta-checked (the killer exists, the search string occurs once). Nobody has run them to see them KILLED, or noticed that the new always-on rule makes a kill an ERROR row. The 4 conftest mutants are the real risk. They need the conftest plugin to load inside a mutant tree that contains only the runner test, the keyword test and the conftest. Any fixture failure there now becomes FIXTURE ERROR and never a kill.
- "Prove new tests fail on the old code" is claimed once in the CHANGELOG (for the head/tail cost test) and is not shown by any command output for the rest.
- Fix: a separate EVIDENCE RUNNER runs `python tests/mutation_runner_mutants.py` (all 217 must be good). It also runs the full suite, bandit, the Postgres-backed tests and the keyword tests against `main`'s runner and judge, and saves the raw output.

2. Major (redaction and security path): the masker is a denylist with documented gaps.
- Where: tools/mutation_runner.py `_masked`, `_fragment_spans`, `_secret_values`, and the "Not covered" paragraph of the module docstring.
- Scenario: a test in the mutated tree fails on `assert dsn[5:30] == ...`, `assert urlsplit(dsn).netloc == ...`, or a base64 or hex form of the value. The first `E` line then goes unmasked into `first_lines` or a row's test id. The docstring and CHANGELOG list these as "Not hidden", which the rule "no hiding behind known limitation" forbids for a security path.
- The masker only catches the whole value, its password forms, and head/tail pieces right next to `...`.
- The code is about 600 lines of special cases (KMP tables, percent-decoding chains, work caps) and the tests are about 2,800 lines. That points to the wrong class fix.
- Fix at the choke point: do not mask by guessing forms. Mask every substring of length >= N (for example 6) of any secret, as a k-gram set or rolling check. The tests already have a `_windows(secret, 6)` helper. Also add an output allowlist. When `pass_env` is set, `first_lines` and test ids keep only `ExceptionClass:` plus the caller's `expect` fragment, or a character-class allowlist with a length cap. This removes the need for the odd-character refusals (quote, backslash and non-ASCII values), the `...` logic and the MAX_* caps.
- Add property or fuzz tests with random slices of the secret.

3. Major (least privilege): nothing in code checks that the passed address is a throwaway database.
- Where: `pass_env` / `PASS_ENV_ALLOWED` and `_run_mutants`. The only protection is the SAFETY text in the docstring. grep of the keyword tests finds no test that refuses a remote or production-looking address. The only localhost hits are lock-name spellings.
- Scenario: a demo passes a shared or production DSN. Every mutant run, plus the extra canary run after each mutant, executes tests that can write or drop tables. The CI address is `postgres@localhost:5432/postgres`, a superuser on the maintenance database.
- The CLAUDE.md rule "every new role or kind ships a negative test and an over-breadth review" is not met.
- Fix: refuse by default a host that is not loopback or a unix socket, and a database name without a marker the caller states. Allow an override only through an explicit keyword. Add a negative test for each refusal. Write the over-breadth review down.

4. Major (unverified regressions): changes that reach every caller were never run against the rest of the suite.
- Where: `judge()` in testing/mutation.py now returns ERROR for exit 1 with no test id (it was CRASH or KILLED). Every fixture error or collection error is now an ERROR row, never a kill. Also the new autouse fixture `_test_database_address_is_left_as_found` in tests/conftest.py calls `pytest.fail` at teardown.
- Scenario: any existing unit test of `judge`, any demo mutant list, and any test (Postgres-backed ones in CI) that writes `HADAVIN_TEST_PG_DSN` directly now fails, or turns into an ERROR row. The snapshot holds only the changed files, and RESULTS.md says the full suite was not run, so I could not check.
- The CHANGELOG admits that existing fixture-based kills turn into error rows.
- Fix: run the full suite and CI with Postgres, search for siblings (all `os.environ[...HADAVIN_TEST_PG_DSN` writes, all `judge(` callers) and record the search. Also search demos that pin the old copy.

5. Minor (rung table and reuse): the diff contains no ladder line.
- Where: the PR and CHANGELOG (grep for "rung" and "ladder" in the snapshot finds nothing). The ticket or plan was not supplied to me.
- The runner already imports from `hadavin_sdk`, yet it writes its own masker and does not show why `guard.runmap.redact_text` (the core redactor) could not be reused. "Reuse before writing" requires that evidence in writing.
- Fix: add the ladder line (rung 1 or rung 7, with the reason lower rungs were rejected) and a paragraph on the reuse check. The redaction part must stay in tested code, which is allowed.

6. Minor (wording):
- tools/mutation_runner.py module docstring: the masking paragraph is dense, with sentences of 100 or more words, and uses labels such as "hidden text", "plain texts" and "pairs" before explaining them. The CHANGELOG bullet is a single wall of text.
- tests/test_mutation_runner_keywords.py:2846: `assert "every" in (mr._masked.__doc__ or "")` asserts a docstring word. It is a weak test of documentation, not of behaviour.
- Fix: split into short steps, one table of "what is hidden / refused / not hidden", and drop the docstring assertion.

7. Minor (lock file, tools/mutation_runner.py `_lock_dir`, `_one_run_per_database`):
- The lock lives in the shared temp folder under a predictable name, `hadavin_mutation_<16 hex of sha256>`. Another local user can pre-create the file. The uid check then refuses the run, which is a denial of service. The hash input is low entropy (host, port, database name), so it can be dictionary-checked.
- Fix: use a per-user subfolder created with mode 0700 and a keyed hash (HMAC). Alternatively use an advisory lock inside the database itself.

8. Minor (tests):
- Several tests use wall-clock bounds (`< 60`, `< 30` s). They are loose and backed by exact counts, so I rate them low risk.
- tests at 2176-2200 get the fixture function through `getattr(fixture, "__wrapped__", fixture)`. That depends on pytest internals, and the evidence only shows pytest 9.2.0.
- Fix: test the guard through a real inner pytest run, as the other tests do.

9. Minor (design cost):
- The canary run after every mutant roughly doubles the time with no opt-out. Without `forbid_skips`, a canary with a missing database (skipped tests) still passes. The docs say so.
- Fix: a documented keyword, or make `forbid_skips` implied when `pass_env` is set.

What is good (checked):
- The `pass_env` allowlist is a single exact name, checked before anything runs.
- One environment snapshot per call.
- The lock is released through an ExitStack inside the `try`.
- The JUnit file is read only as a regular file, with a size check.
- The skipped-test and no-test-id false kills are closed at the single `_row` choke point.
- The leak tests have positive controls (masking switched off, the secret must show).
- Odd characters are refused by name only, never echoing the value.

NOT checked:
- I did not run anything, so no test pass or fail is verified.
- I read only parts of the 2,800-line keyword test file, so I cannot say whether each test fails on the old code.
- I did not read the mutants file in full.
- I did not read the lines between DIFF.patch 3864 and the start of `_address_parts` (the grammar before that point).
- I did not check demos or any other callers of `judge`, or the CI workflow, because the snapshot lacks them.
- I did not check pytest-version behaviour of the `...` truncation beyond what the docstring claims (9.2.0).
- I did not check the ticket, plan or ledger, so the rung table could not be compared to a plan.
- I did not check SonarCloud, CodeQL or CodeRabbit.
- I did not review Windows paths.
