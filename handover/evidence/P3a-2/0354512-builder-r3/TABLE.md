# Mutant table, PR branch core/P3a-2, fix round 2 (builder)

Mutant runs were made at commit 0354512. The only later change (ffe896e) is in `tests/fixtures/migration_role.py`
(a plain test role per test process, dropped at exit); no mutant text or killer id was touched by it.

| Runner | Ids | Killed | Not killed |
|---|---|---|---|
| tests/migrate_mutants.py (raw: migrate_mutants.log) | 115: behaviour 97, prose 11, test-helper 7 | 115 of 115 (behaviour 97/97, prose 11/11, test-helper 7/7) | none |
| tests/migration_numbers_mutants.py (raw: migration_numbers_mutants.log) | 40 | 40 of 40 | none |

New in this round (15): SU1, SU2 (session user), PD1 (built-in roles), PA1 (parameter grants), GO1, GO2 (grant option, schema usage),
FO1 to FO4 (ownership refusal: words, partitions, names with control characters, every statement printed), OW1, OW2
(inheritance, function half), EX1, EX2 (extension objects, function half and table half), TN1 (trigger name). Nine old mutant
texts (T3, T14, T17, S2 to S5, B2, B3) were brought up to the new source. Re-run in full: R4, B1, B2, O1.
The first run of the new list had two survivors, FO2 and EX1: FO2 planted a change in a line that the test could not
reach (it changed the list of object kinds, not the dependency exemption) and EX1 targeted the table half although the
test only had functions. Both mutants were corrected and EX2 added, the extension test now also installs an extension
that makes a view; the corrected runs killed them (see migrate_mutants.log, last full run).

Runner change (f): each killer id runs on its own, without `-x`, with `-rf`; only the killer ids that really fail are printed.
Command: `HADAVIN_TEST_PG_DSN=<scratch PostgreSQL 16.15> uv run python tests/migrate_mutants.py` (through /home/user/build/heavy.sh).
Not run on PostgreSQL 17.
