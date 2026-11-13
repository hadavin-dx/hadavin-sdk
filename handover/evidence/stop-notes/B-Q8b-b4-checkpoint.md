checkpoint 2 (builder Q8b batch 4, ~01:00 into the box)
done: all fixes, tests, mutants (stage 37/37, q8b 75/75 after M72 fix, runner 64/64), lint/bandit/scan green, fail-before run, probe tables; whole suite running (PG 56094)
next: read suite result, gitleaks, commit, push ff, stop PG, report
blockers: tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in is flaky under load on 4091f8b1 too (3 of 6 runs fail) -> migration_numbers_mutants baseline fails under load; not Postgres; not my diff
sha: 4091f8b1 + uncommitted
