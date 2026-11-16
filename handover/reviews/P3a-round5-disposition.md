# P3a round 5 disposition (author, revision 7, 2026-11-05 17:58 UTC = 23:28 IST)

Target: `handover/tickets/P3a.md` revision 7. Input: `P3a-round5-resolve.md` (16 PROPOSE FIX rows). Nothing was run by the author in this revision (text only); every code cite was re-read, not executed. Where a ticket location says "Interface", "Tests", "Mutation plan", "Rollback", "Open points" or "UNVERIFIED", it means that part of the single ticket file.

| id | decision | where in the ticket | note |
|---|---|---|---|
| ADV-R5-1 (blocker) + COR-R5-C2 | applied | Interface `hand_recipe`, `order_problems`; Tests H4 (real psql, two parameter rows), FAIL-BEFORE text; Rollback rule for every hand step; Problem item 6 | Recipe is a file run with `psql -v ON_ERROR_STOP=1 -f`, SQL inlined, DO check before the INSERT, no include command. Exit code 3 labelled drafter's 16.15 run for `-f` only; the test asserts non-zero. Mutants M39-M42. |
| ADV-R5-2 | applied (narrowed as resolved) | Interface `statement_text` (tag rule, fail closed); Lexer tests `test_non_ascii_dollar_tag`, `test_unrecognised_dollar_refuses`; M50; evidence 7a | The class is any non-ASCII character (a superset of "Unicode letter"; the safe direction). Server rule UNVERIFIED until 7a runs. |
| ADV-R5-3 | applied (narrowed) | Interface `refused_statements` group (e); M44-M49; planted-file tests | DO, EXECUTE (at statement start), ALTER ROLE/USER/DATABASE wholesale, DROP OWNED, REASSIGN OWNED. No DO allow-list. The 34-statement count is asserted again. |
| ADV-R5-4 | applied (relay) | Field "Depends on" overlap (3); Coupling table | P3a lists its three test files for P4d-c; its own diff leaves the lock-in guard alone. |
| ADV-R5-5 (scope) | applied (cut), four parts | (1) group list and v1.1 row; (2) layer 1 at the first tag only, v1.1 row; (3) runbook (e) gated on Open point 12; (4) file-state tests cut, directory row kept (FAIL-BEFORE 4) | See "Reading" below for two interpretations. |
| ADV-R5-6 | applied | Mutation plan, count table | CREATE SUBSCRIPTION mutant removed with its refusal. |
| ADV-R5-7 | applied | Tests H7a-H7c | H7c re-labelled as the recovery case; rule stated in one line. |
| ADV-R5-8 | applied | Interface `read_files`, `migrate()`; Tests `test_migrate_executes_the_text_it_scanned`; M38 | One read per file. There is no hash in P3a (no manifest); noted in Open point 9. |
| ADV-R5-9 | applied | Interface `order_problems` text; Security notes; `test_recipe_has_no_include_command` (no `://`) | Message prints no connection string; schema comes from `SELECT current_schema()`. M43. |
| ADV-R5-10 | applied | Rollback runbook (b) and (e) | Stem rule stated once; only E1 touches `0006_evidence`. |
| COR-R5-C1 | applied | Interface (`MigrationNumberError`) | All refusals are `ConfigError`; subclass for number, order, gone, folder; exact-type check only for those tests. |
| COR-R5-C3 | applied | Refusal list "NOT in the list" paragraph | Variants not recorded are said so; `DROP SUBSCRIPTION` marked "refused to stay safe"; moot after the cut. |
| COR-R5-C4 | applied | Header; UNVERIFIED | All 16.15 results are unverified on 17.10. |
| COR-R5-C5 | applied | Layer 1 paragraph on P2a-1; Depends-on line | Cites P2a.md 10, 41, 75, 118 (read this round). Stale "does not rely" removed. |
| COR-R5-C6 | applied | Rollback (e) | Same as ADV-R5-10. |
| COR-R5-C7 | applied | Layer 1 seeds | "15 tables" plus two sequences; counted from `CREATE TABLE` occurrences 8+3+2+0+2. |
| COR-R5-C8 | applied | Tests (killer names in brackets and in the mutation plan) | Killer names added. |

Counts: 16 rows in the resolve map to 17 finding ids; applied 17 (3 narrowed as the resolve directed), contested 0, declined 0.

Mutants: 90 in revision 6, 13 removed (1 old M9b, 12 refusal-list items), 13 added (M38-M50) = 90. Group arithmetic is in the ticket's count table (10+14+5+23+11+21+6 = 90). The equal total is a coincidence, not a target.

## Readings and deviations the lead should check
1. "Trim to (c),(d)" is read as cutting all of groups (a) and (b), and adding (e) because ADV-R5-3 demands it. If the lead meant keep (a)/(b) partly, say so.
2. "Layer 1 at the first tag only" is read as: the comparer, seeds and planted cases ship now (they are the only proof the comparer can fail); only the baseline moves at the first tag. If the lead meant drop the comparer until then, delete the layer 1 block and M27-M29.
3. "ONE psql test" is one function with two parameter rows (second row kills M39).
4. The dollar-tag class is wider than the resolve's "Unicode letter".
5. Runbook (e) is built and its text depends on Open point 12.
6. Possible conflict: ruff S603 suppression precedent (`tests/demo_askdata/conftest.py`) against "no suppressions"; ticket says try without first.
7. The ticket is longer than hoped; no sections were cut beyond those the resolve named.

## Unverified
Every SQL result "run on 16.15"; the server's dollar-tag rule; the builder's seeds; whether P4b1 edits `migrate.py`; the Postgres 17 source for the evidence runner.
