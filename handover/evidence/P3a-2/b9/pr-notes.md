# P3a-2 batch 9: builder notes (head = see "Head" at the end)

## What failed or was NOT done (first, on purpose)
- The four mutant runs of the final head did NOT finish: this builder's jobs have the lowest queue priority in /home/user/build/heavy.sh and were starved for the whole time box by higher-priority builders. A first run of all 30 new or repaired mutants (V122, V149-V177) was stopped by the 30-minute background limit with an empty log; a second run (3 jobs) never got a slot. So: NO mutant result of this batch exists. V149-V177 are written and their snippets were checked to exist exactly once (the run stops with "out of date" otherwise: it did so for V122 and V176, both repaired), but they are NOT shown killed.
- NOT run on the final head: the four migrate_mutants batches, migration_numbers_mutants, stage_mutants, the full pytest, ruff/bandit/scan_repo/gitleaks on the final head (see the report for what was run).
- Group 6 (dblink-connect on the fixed socket, head vs main 2a8c2aac, copy-program x10) : prepared (mount-namespace script /home/user/build/b9-g6.sh, main worktree B-P3a2-b9-main), queued behind the same slots, NO result.
- Group 9 (the 39th old-source failure) and group 5 (cite RESULTS.md): not done.
- tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in: not touched, not run.
- IMPOSSIBLE-NOW: PostgreSQL 17 tests, Python 3.12, semgrep, zizmor, trivy, pip-audit, Vault engine tests.
- Group 10 (O8, schema owner): OWNER-ONLY, off, nothing built.
- EGM evidence runner and egm:* result reviewers were not run by this builder (the lead runs them).

## Fail-before on 6a25ae5d (measured)
Clean detached worktree of 6a25ae5d with only the new or changed tests copied in, PYTHONPATH on the old src (checked). New ids: 108. Result: 94 failed, 14 passed (twice, same). Raw: B-P3a2-b9-failbefore-1.txt and -2.txt.

## The 14 that pass on old code, one reason each
- 6x `..._stays_the_refusal_of_exit_2[...]`: control. The refusal that is not transient must keep exit 2 before and after; they pin that the new transient path did not widen.
- 2x kill-switch exit-2 controls: control, same reason (an unrelated refusal keeps its exit code).
- 4x driver-quote controls: control. The driver's quoted words were already not shown by old code; the tests keep it so.
- `test_every_raise_from_of_migrate_is_on_the_written_list_...`: written list is a count of existing sites; old code already has the same sites, the test fails only when a new site appears (the planted-site test below proves the scan sees one).
- `test_the_scan_of_raise_from_finds_a_planted_site_and_skips_from_none`: tests the scanner itself on planted text, independent of src.

## Fixes (class, standard)
1. Group 1/2: error chaining leak. Python data model: `raise X from e` sets __cause__; a `raise` inside `except` sets __context__ (`from None` only sets __suppress_context__). Fix at the one exit of `migrate`: decorator `_keeps_no_driver_error` cuts any chain holding a driver error, except the two limit errors; step 8 raises outside its `except`.
2. Group 3: a sign-in failure that a second try can cure is `StoreUnavailable` (exit 4), others stay refusals (exit 2). `SignInError.kind/.transient`; `is_transient` in auth_aws.py (botocore import stays in that kind module).
3. Group 8: a DSN the driver cannot read: the driver's error words can quote a word of the address; `dsn_parts` raises a class-name-only ConfigError outside the except; `connect`, `tls_mode`, `build` all read through it.
4. Group 7: docstring renames (V131-V133 wording). The claim in a docstring that the choke-point AST test also fails for V131-V133 is UNVERIFIED (not run).
Honest design notes: the guard is stricter than the review (it also cuts the chain of the commit-unknown case; the code stays in the message); `migrate` still exits 2 for a transient sign-in failure; the cloud-client step is never transient. Mutants are in tests/migrate_mutants.py (as batch 8), not stage_mutants.py.
