# PR89 (A2, core/mutation-runner-keywords @ 6706e67) round 1, codebase-details review

Reviewer: egm:egm-codebase-details (fresh). Read-only, no execution. Spec used: PARALLEL-PLAN row A2 (no ticket file exists), CHANGELOG, runner docstring, CLAUDE.md.
Status: saved by the cloud session as received; unverified until fixed and re-checked.

## Blockers
None.

## Majors
- M1 (confirmed) tests/test_mutation_runner_keywords.py:457-463 `test_masked_replaces_the_value_and_the_url_password` sets `os.environ[DSN_NAME]` and then deletes it in `finally`. The caller's real value is lost, later Postgres tests skip (evidence: dsn-leak-single-test-313.txt, 4 skipped; TABLE.md 12 skipped in first full runs). CI sets the DSN, so CI would skip them and stay green. Fix: use `monkeypatch.setenv`; add an autouse fixture in the file that sets a sentinel value and asserts it is unchanged after each test (fails on the old test body). Only direct os.environ writes are lines 297, 459, 463. After the fix, rerun the full suite with the DSN set and NO deselect.
- M2 CHANGELOG line 9 and docstring say "with none of them given the runner behaves exactly as before", but two changes are always on: a fixture error at setup or teardown becomes the row FIXTURE ERROR (was KILLED, or CRASH with allow_crash), and `judge()` returns ERROR when no failing test id is known (JUnit with only `<error>` was CRASH, good with allow_crash plus crash_type; now ERROR). The default-call test only checks argument shape. Fix: (a) delete the sentence and state the always-on changes, or (b) make the fixture-error rule opt-in (lead decision, rule 7). Also: the changelog says "first failure is an error inside a fixture" but `broken` (runner line 692) scans every testcase, so a real failure plus a teardown error is ERROR, never KILLED; narrow to the first failing case or document it. Add a runner-level test for the teardown path.
- M3 No per-test fail-before (head tests fail on the old runner only at collection, ImportError of PASS_ENV_ALLOWED) and tests/mutation_runner_mutants.py is still 62 mutants at base and head. Add mutants that must be killed: drop `plugin=conftest` on the mutant `_pytest` call (runner ~675); drop `env_names=env_names` on the mutant call; remove the allowlist check in `_checked_env_names`; remove the `keyword.iskeyword` / `isascii` / `.py` check in `_plugin_module`; drop `_masked` on `first`, on `test_id`, on the baseline skip message; change `forbid_skips and not xml_text` to `or`; swap the FIXTURE ERROR and SKIPPED branches; drop `"failed on teardown"` from the startswith tuple; drop `conftest` from `copied`; drop `not test_id` in judge; move the missing-conftest check after mkdtemp. Evidence-only fail-before: run head tests against the old runner with a shim defining the missing names.

## Minor / nit
- N1 src/hadavin_sdk/testing/mutation.py module docstring lines 8-13 say ERROR is only "any other exit code except 1"; code now also returns ERROR for rc==1 with empty test id. The runner docstring row list lacks FIXTURE ERROR, SKIPPED TESTS, JUNIT MISSING.
- N2 test id `classname.replace('.', '/') + '::' + name` built three times (`first_failure_junit`, `skipped_tests`, `fixture_errors`); same XML parsed three times per mutant (runner 690-692). Add `_case_id(case)` and ideally one pass. `_parse_junit` leaves a useless `root =` local. Byte-copied file: a change needs a new hash in CHANGELOG and manifest.
- N3 test file header "review fixes (order 194 B)" cites an internal order number; use a plain description.
- N4 `test_a_default_call_reaches_pytest_with_the_old_four_arguments_only` asserts `{"plugin": "", "env_names": ()}`; the name says the opposite. Rename.
- N5 `# fmt: skip` at runner lines 304 and 647 is a suppression; reformat with ruff instead. (`# noqa: S314  # nosec B314` in mutation.py is pre-existing and justified.)
- N6 FIXTURE ERROR and SKIPPED TESTS rows set no `first_lines[m.name]`; the reason is lost. Record the masked message.
- N7 (not verified) pytest -q may cut a long value mid-string with "...", so a partial DSN could appear in the first E line. Add a long-value case, or mask any 8+ char substring, or keep the value out of assertions.

## Checked, no finding
Allowlist (PASS_ENV_ALLOWED only HADAVIN_TEST_PG_DSN; bare string raises TypeError; checked before temp folder or pytest start; both `_pytest` and `_run_mutants` call it); `-p` plugin name rules and 13 refusals plus missing-file test; skip/xfail/no-JUnit logic; fake DSNs built from parts; no dev/staging stage names; env read at call time only; SAFETY risk documented; existing tests only mechanically updated for `**kw`.

## Not checked by the reviewer
No test, mutant, lint or hash run; sha256 values unverified (rely on the evidence run); evidence logs beyond TABLE.md; mutants file not in snapshot; Windows; CodeQL/Sonar/CodeRabbit; junit_family other than default; the plan's FIXTURE ERROR decision (M2 needs it).
