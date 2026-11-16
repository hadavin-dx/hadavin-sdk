# P3a build-start resolve (order 20, one round)

Status: resolved (AUTO mode, interactive gate skipped as ordered). Model output, not user authority.
Target: `handover/tickets/P3a.md` revision 10, FROZEN, full file. Fixes are written ONLY as the appended section "Build notes (build-start review, order 20)" (17 notes); the frozen body is unchanged.
Gate: LEAD-ORDERS order 20 item 3 (one build-start round, then build); order 19 F (P3a cuts accepted; the probe on the built code decides the lock check).
Findings: `reviews/P3a-buildstart-adv.md` (13 rows: ADV-1..10, COR-1b, COR-2b, COR-3b) and `reviews/P3a-buildstart-cor.md` (8 rows: COR-1..8). 21 ids; 3 merged pairs named by the lead plus 1 of mine (COR-2b + COR-4); 17 decisions.

## Honest note (first: what I did NOT check)
- I ran no pytest, no repository code, no `migrate()`, no psycopg (not exercised). Every claim about `migrate()` behaviour is by reading the ticket.
- PostgreSQL 17 was not probed (CI uses 17.10). All server facts below are 16.15 only.
- I did not open P2a.md beyond a grep for `ACCEPTED_CHANGES`; P2a.md:116 cites `P3a.md:96`, a stale line number I did not fix (relay for the lead, PENDING LEAD 22).
- ADV-7 (search_path) and the client_encoding reasoning in ADV-5 are by reasoning, not run.
- I did not re-check the reviewers' "Verified" lists; I re-read only the ticket lines they cite (36, 37, 39, 42, 74, 83, 84, 89-91, 95, 99, 107, 110, 127-132) and `tests/test_k2_migrations.py:100-115`, `tests/test_k5_perf.py:20-21,43`.
- My own slip, disclosed: one control probe (`r_nobs`) was built wrongly (its `ROLLBACK` was live in both modes); I replaced it with `r_ctl` and use only `r_ctl`.

## Facts (probed by me; throwaway PostgreSQL 16.15 + psql 16, unix socket only, data dir in the session scratchpad, run under a user namespace as a non-root uid; stopped and deleted afterwards; no other postgres process touched)
| probe | SQL shape | result |
|---|---|---|
| A1 | `SELECT E'a'<LF>'\'';` | `a'` : the continued literal keeps E mode (ADV-1 premise TRUE) |
| A2 | `BEGIN; CREATE TABLE t_a2; SELECT pg_advisory_xact_lock(4242); SELECT E'a'<LF>'\'';<LF>COMMIT;<LF>-- it's<LF> SELECT count(*) FROM pg_locks WHERE locktype='advisory'; ROLLBACK;` as one string and via `psql -f` | live COMMIT; advisory locks 0; `ROLLBACK` warns "no transaction in progress"; `t_a2` kept (ADV-1 CONFIRMED) |
| A4 | `SELECT E'a' '\'';` (space only) | syntax error (no continuation without a newline) |
| B1 | body recipe, entry `CREATE TABLE t_b; SELECT 'x\''; ROLLBACK; --';`, `PGOPTIONS=-c standard_conforming_strings=off` | exit 0, ledger row 1, `t_b` absent (ADV-5 CONFIRMED) |
| B2 | same + reviewer's line `SET standard_conforming_strings TO on;` before `BEGIN` | exit 0, ledger 1, `t_b` present (reviewer fix works for this case) |
| B3 | reviewer's line present, entry starts `SELECT set_config('standard_conforming_strings','off',true);` then the B1 text | exit 0, ledger 1, `t_b` absent (reviewer fix NOT sufficient) |
| B4 (`r_ctl`) | set_config flip + no backslash: `SELECT 'x'''' ; ROLLBACK; --';`, session `off` | exit 0, ledger 1, `t_b` present (no backslash = same reading) |
| B5 | B3 text as ONE query string inside `BEGIN ... COMMIT` (the migrate shape) | `ROLLBACK` stayed inside the literal; table kept: whole string parsed before it runs |
| C1 | plpgsql `EXECUTE 'SET LOCAL ROLE p3a_r'` called by `SELECT`, then `SELECT current_user, session_user` | `p3a_r`, `probe` (H11 plant 3 isolates current_user) |
| C2 | `set_config('role','p3a_r',true)` | `p3a_r`, `probe` |
| C3 | `set_config('session_authorization','p3a_r',true)` | `p3a_r`, `p3a_r` (both move) |
| C4 | in one transaction: create trigger, disable via plpgsql EXECUTE, drop | count 1, `tgenabled` D, count 0 (ADV-2 shape is real SQL) |
| D1 | plpgsql `COMMIT` called by `SELECT` | `ERROR: invalid transaction termination` |
| D2 | `pg_advisory_unlock_all()` after `pg_advisory_xact_lock` | 1 advisory lock still held |

Arithmetic (`python3 -I`): 10+15+6+20+20+21+15+17 = 124 mutants (was 120), ids 88+4 = 92; perf 16x size step: linear 16 vs limit 48 (3.0x margin), quadratic 256 (5.33x).

## Decisions
| id | category | decision |
|---|---|---|
| BS-P3a-ADV-1 (Major) | PROPOSE FIX | Confirmed by A1/A2. Fail closed: lexer refuses any `'` after a closed `E'...'` across whitespace/comments (`E'' string continued at line N`); exact-string test, property alphabet, mutant M100; evidence 7 repeats on 16 and 17. Build note 1. |
| BS-P3a-ADV-2 (Major) | PROPOSE FIX | Refresh saved trigger triples after each accepted file; stub case (xvii), M101; one-call "same run" H11 row; H11 two-call shape and a corrected end check. Notes 2, 3. |
| BS-P3a-ADV-3 = BS-P3a-COR-3 (Major) | PROPOSE FIX | Restrict trigger read to relations in the saved `current_schema()`; key unchanged (tgrelid, tgname); message adds schema; stub (xvi), M102; limit stated (PENDING LEAD 23). Note 4. |
| BS-P3a-ADV-4 = BS-P3a-COR-2 (Major) | PROPOSE FIX | Message names every differing item; case (iii) asserts both names; stub cases (xiii) M65, (xiv) M71, (xv) M70; H11 plants as backup. C1 removes the UNVERIFIED label of plant 3's SQL shape. Note 5. |
| BS-P3a-ADV-5 (Major) | PROPOSE FIX (by a cut, not the reviewer's fix) | B1 confirms the defect; B3 shows the reviewer's extra `SET` line is not enough. Refuse a backslash anywhere in the raw entry text instead; the fixed recipe line order does NOT change; three test inputs move from accepted to refused; M103; H4 row 4. PENDING LEAD 21. Note 6. |
| BS-P3a-ADV-6 = BS-P3a-COR-1 (Major) | PROPOSE FIX | `ACCEPTED_CHANGES` lives in `tests/test_migration_postgres.py`; the sentence naming `test_migration_previous_release.py` corrected at build start; no new file, so the P4d-c three-file row stays true. PENDING LEAD 22. Note 7. |
| BS-P3a-ADV-7 (Minor) | DECLINE | One-entry `search_path` only removes schemas from name lookup: a name not found is an error, `ON_ERROR_STOP` stops, nothing is kept; the creation target is the same first schema. By reasoning, not run. |
| BS-P3a-ADV-8 (Minor) | PROPOSE FIX | One runbook sentence ("first `SELECT current_user;`"), no recipe line. Note 15. |
| BS-P3a-ADV-9 (Minor) | PROPOSE FIX | Add letters to the property alphabet; compare problem strings too. Note 8. |
| BS-P3a-ADV-10 (Minor) | PROPOSE FIX | Own constants 16 KiB / 256 KiB, RATIO 48 (margins 3.0x and 5.33x); M86 called a self-check. Note 9. PENDING LEAD 24. |
| BS-P3a-COR-1b (Minor) | PROPOSE FIX | Name the file (`tests/test_migration_numbers.py`), import inside the test, helper imports stdlib + psycopg only. Note 11. |
| BS-P3a-COR-2b (Minor) + BS-P3a-COR-4 (Minor) | PROPOSE FIX | One stub rule: exact equality with two module SQL constants; precedent `test_k2_migrations.py:106-115` (re-read: it patches `mig.connect`). Note 12. |
| BS-P3a-COR-3b (Nit) | PROPOSE FIX | `importlib` + `getattr`, must be a `test_` function. Note 7. |
| BS-P3a-COR-5 (Minor) | PROPOSE FIX | `-m "not live and not perf"` on command 1 (command 2 inherits). Note 10. |
| BS-P3a-COR-6 (Minor) | PROPOSE FIX | Killers written from their mutant lines; evidence table per killer. Note 13. |
| BS-P3a-COR-7 (Nit) | DECLINE | Already Open point 13 (declined in round 8); frozen body. |
| BS-P3a-COR-8 (Nit) | PROPOSE FIX | Marker lines excluded. Note 14. |

(COR-2b and COR-4 are counted as one decision because they ask for the same stub rule; that is my merge, not the lead's.)

## Couplings
- P2a-1: its `ACCEPTED_CHANGES` entry goes into `tests/test_migration_postgres.py` (note 7); its new triggers in the migration schema become part of the refreshed baseline after its file (note 2), and `ENABLE ALWAYS` still passes. A P2a trigger outside the migration schema would not be guarded (note 4).
- P4d-c: P3a still adds exactly three test files (`test_migration_numbers.py`, `test_migration_postgres.py`, `migration_schemas.py`); the lock-in allow-list row is unchanged.
- P4d-b: its `lambda paths, texts=None: []` stub of `check_grants` is unaffected; if P4d-b stubs `connect` for the read-back it must answer the two new module constants (note 12).
- Any later package whose migration needs a backslash (an `E'\n'` or a regex) gets no printed recipe for a late copy of that file (note 6); the normal `migrate()` path is unchanged.

## PENDING LEAD (continuing the ticket's numbering)
21. ADV-5, recipe line order. Options: (a) reviewer's fix: add `SET standard_conforming_strings TO on;` before `BEGIN` (changes the fixed order; probe B3 shows it does not close an in-entry `set_config` flip); (b) refuse a backslash anywhere in a recipe entry, order unchanged (closes both B1 and B3; costs: files with `E'\n'` or `'\d'` get no printed recipe); (c) both. Recommendation: (b), applied in build note 6. If the lead prefers (c), the exact order is: `-- RECIPE begins`, `\set ON_ERROR_STOP on`, `SET standard_conforming_strings TO on;`, `SET search_path TO "<schema>";`, `BEGIN;`, lock, entries, `COMMIT;`, `-- RECIPE ends`. Reversible before merge.
22. `ACCEPTED_CHANGES` lives in `tests/test_migration_postgres.py`. Recommendation: confirm, and relay to P2a (its "ACCEPTED_CHANGES entry" item names `P3a.md:96`, a stale line; the item name is what holds).
23. Trigger read-back now covers only the migration schema; a migration that disables a trigger in another schema is not caught. Recommendation: accept as a stated limit (all audit triggers are in the migration schema; a cross-schema statement is visible in review); v1.1 row if a package ever puts guarded triggers elsewhere.
24. The timing test of P3a uses its own size step and ratio (16x, 48.0) instead of `test_k5_perf.py`'s (4x, 12.0). Recommendation: accept; the shared constants give the quadratic stand-in only a 1.33x margin.

## Counts
17 decisions for 21 ids (4 merges): PROPOSE FIX 15 (1 of them, ADV-5, by a different cut than the reviewer proposed), CONTEST 0, ESCALATE 0, DECLINE 2 (ADV-7, COR-7). Accepted fixes applied as build notes: 15 decisions -> 17 notes. Majors open after this resolve: 0 on paper; ADV-1, ADV-2, ADV-5 still need the built code and evidence command 7 on PostgreSQL 16 and 17. New PENDING LEAD: 21 to 24.
