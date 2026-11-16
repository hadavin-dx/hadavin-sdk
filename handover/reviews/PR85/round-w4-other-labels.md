# PR85 / A17 second review: label check, all rows except src/hadavin_sdk/k1b/*

Head 4b1b3f9. Reviewer read only (no tests, no mutant runner, no 3.12 vs 3.13 cmp). Could not recompute row hashes; rows mapped to source by file, symbol, count and reason pattern (by reading).

VERDICT: no Blocker or Major. No OPERATOR or LITERAL row formats outside text. Every FOREIGN row confirmed. 3 Minors, 1 Nit.

Rows covered: CSV lines 2-89 and 160-204 (k1b lines 90-159 are in round-w4-k1b-labels.md).
Counts match the CSV: tools.py 17/17, config.py 16/16, app.py 14/14, store/migrate.py 8/8, secrets_vault 7/7, registry.py 7/7, secrets_file 6/6, postgres.py 5/5; the other files also match.

## Findings
- Minor 1, CSV 173 (migrate.py:306): reason says file names are "(escaped)". The `check_ledger` that `migrate()` calls is the one in migrate.py, which formats `p.name` raw at migrate.py:100 (no `_esc`). Names come from the shipped migrations folder, so the label holds; the reason text is false. Escape at :100 or drop "(escaped)".
- Minor 2, CSV 181 (migration_numbers.py:95-97): OPERATOR holds only while every caller passes `_esc`-escaped or fixed text. The file docstring says P3a-2 will add `migrate` as a caller. Reason should say so.
- Minor 3, CSV 163/164/188/189: OPERATOR depends on a relay (registry.py:330 `str(exc)`) the scan cannot see. Design limit, reason states it.
- Nit 1, CSV 198-201 (tools.py:434,437,439): `op!r` / `method!r` of dict keys from the tool module's READ_OPERATIONS may run a `__repr__`; module is pinned operator code. Reason could say "operator's tool module code".

## Not covered
src/hadavin_sdk/k1b/*; the pytest file, mutant runner and 3.12 vs 3.13 cmp were not run; generator and test sources not re-read (first reviewer covered them).
