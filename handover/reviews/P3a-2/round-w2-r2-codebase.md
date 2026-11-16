# PR73 (A5, core/P3a-2 @ ef2adc7) round 2, codebase-details review (security path, uncapped)

Reviewer: egm:egm-codebase-details (fresh, read-only, ran nothing; cloud evidence folder did not exist yet). Saved as received; unverified until fixed and re-checked.
Verdict: 1 Blocker, 4 Major, 7 Minor. Round-1: 9 of 13 fixed, 3 partly, 1 open.

## Blocker
B1 CHANGELOG.md:17 (item 11) repeats "Tested on PostgreSQL 16.15" twice, ends without a full stop, and says "the CI run on 17.10 is recorded in the pull request"; builder evidence says PostgreSQL 17 was NOT run (order 186 G73-7 asked for it). Fix: run the real-server tests and the 100 mutants on 17 and log them, or delete the 17.10 clause; one sentence ("Tested on PostgreSQL 16.15 (and 17.x, only if the log exists).").

## Majors
M1 Migration role checked less strictly than the "no switch" text (migrate.py:390, 538-541): only `current_user` flags read, only four flags dangerous. (a) `session_user` flags never read: a superuser login that SET ROLEs to a plain role (DSN option `-c role=`; the fixture does this) passes; a DO body can RESET ROLE then COPY ... PROGRAM via EXECUTE; the read-back sees the change only after. (b) Membership of pg_execute_server_program, pg_write_server_files, pg_read_server_files, pg_write_all_data not refused. Fix: test session_user too in `_ROLE_FLAGS_SQL` and `_BORROWED_ROLES_SQL`; add `OR r.rolname IN (...)` to `_BORROWED_ROLES_SQL`; real-server test and mutant for each. Ticket G73-5 names current_user only: say the extension in the ticket.
M2 `_FOREIGN_OWNED_SQL` and refusal message (migrate.py:571-611): (a) pg_proc includes procedures ('p') and aggregates ('a') but the printed line is always ALTER FUNCTION (errors; the one-transaction hand file fails): select prokind and print FUNCTION/PROCEDURE/AGGREGATE, add test. (b) `d.deptype IN ('e','a','i')` on pg_class hides a foreign-owned partition (auto dependency on parent): apply 'a' and 'i' only when relkind = 'S', keep 'e' for all. (c) names go raw into printed ALTER lines (606, 609) while the object list uses `_label`; the owner is another role and controls the name: if `escape_name(x) != x` omit the statement and say a person must write it by hand; test with a newline in a table name. Comment at 605 is wrong: regprocedure::text omits the schema when on the search path.
M3 Round-1 private-id finding only partly fixed: migration_numbers.py:11 ("R448 rung decision"), :26, :484/:492, :37; tests/test_migration_numbers_guards.py:1, :149; tests/migration_numbers_mutants.py:5, 7, 311, 317; tests/test_migration_numbers.py:806; names `test_no_p3a2_test_skips_silently` (test_migration_rules.py:157), `0006_p3a_*.sql`, `p3a_*` objects (66 hits in test_migration_postgres.py). Order 133 item 1 wants these gone. Fix: plain descriptions; neutral names (`test_no_migration_test_skips_silently`, `0006_alter`); update killer ids in migrate_mutants.py (SKIPS constant line 66 and others).
M4 Ownership refusal tested only for the refusing case (O1, O2). No test of the safe case (owner is a role the migration role belongs to, with and without inherit: the `pg_has_role(...,'USAGE')` choice), none for the extension skip ('e'), none mutating the pg_proc arm; a mutant USAGE to MEMBER would survive. tests/test_migration_postgres.py:1429 hard-codes "owner postgres". Fix: real-server test where the old owner is a member of the migration role and migrate proceeds; extension object test; mutants USAGE->MEMBER and drop pg_proc arm; take the owner name from `SELECT current_user`.

## Minor
m1 test_migration_wiring.py:459 "T1..T5" but runner has T1, T2, T5 (no T3, T4, T6); write "T1, T2, T5 and T7" (order 186 G73-8).
m2 `_trigger_changes` (migrate.py:467-481) accepts any non-empty string as `trigger`; match `_TRIGGER_NAME` or the printable-name rule.
m3 Trigger allow-list semantics inconsistent: line 691 refuses a created trigger that is D or R even if the entry names `enabled_state`, but the TriggerChange docstring (434) and CHANGELOG say the entry allows it; `after[0] != entry.state` (686) refuses a trigger already D before the file whose definition changed. Honour it for new triggers or say "for an existing trigger" in both places.
m4 `md5(p.prosrc)` (migrate.py:409) fails on FIPS servers: select prosrc or hash in Python.
m5 `WITH INHERIT FALSE` (test_migration_postgres.py:1356) needs PostgreSQL 16+; lexer docs say 15+. Skip below 16 with a named reason or state the floor.
m6 test_migration_rules.py:644 runs `uv build` (build backend, maybe network): confirm it passes in CI with no network.
m7 CHANGELOG.md:15 "the next change in this series merges": plain name. migrate.py module docstring is one very long sentence: split.

## Round-1 status
Fixed: R4 killer, M88 re-pointed, M65 re-added, N2, N4, N5, N6, N7, N3/F7. Partly: M2 private ids (see M3), N1 stage words (CHANGELOG clean), M3 placeholder (see B1). Not re-checked: N8, N9.

## Costs of the open lead decisions (reviewer does not rule)
1. Per-file lock/statement-timeout override: today 5s/60s cannot be raised (a long ALTER uses the documented hand recipe); an override adds a reviewed-list entry type, a read-back exemption, tests, mutants and a new way for a file to weaken the guard.
2. Scope beyond the ticket (foreign-owned refusal, inheritance check, fixture changes): ownership check adds one catalog query and a refusal to every run (also with no pending file), a runbook case, tests, mutants; covers tables, views, sequences and functions only, not types or domains; inheritance check over-refuses members with SET FALSE; fixture changes are test-only. Needs a ticket amendment or "V" row, or removal.
3. Shared helper for the released-files stub: small cost in tests/fixtures; duplicates risk drift; mutants do not depend on it.

## Not checked
Whether 10712 / 100 / 40 are true; released-file SHA-256s; shipped wheel; the whole ~5000 test lines and lexer; shared stub helper; ticket lines 52-202; PostgreSQL 15 and 17 behaviour; cloud evidence.
