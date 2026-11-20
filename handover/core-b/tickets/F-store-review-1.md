# EGM review round 1 of 1: tickets/F-store.md (egm:egm-review-loop through the Skill tool; direct dispatch; model fable)
When: 2026-11-20 05:33 to 05:42 UTC. Target: full file (299 lines before the resolution). Reading list: interfaces/README.md, tickets/F-install.md, src/hadavin_sdk and tests, notes/heads-money.md.
Reviewers: egm:egm-implementation-readiness = completed (standard: implementation-readiness-standard); egm:egm-codebase-details = completed (persona only). Not run: none.
Round result: NOT CLEAN. Blockers 2, Majors 19 (some raised by both), Nits 19. Nothing run by either reviewer (reading only). Both note that step B landed in the tree while they read, so line numbers are from the later state.
Resolution: by core-b in the ticket's section "RESOLUTION of review round 1" (R1 to R14). No finding contested. No round 2 (ORDER 004 item 3); the resolution text itself has NOT been seen by a fresh reviewer: ESCALATIONS.md E2.

| id | severity | where | finding (short) | answered in |
|---|---|---|---|---|
| ir-1-B1 | Blocker | whole ticket | no list of files to create, change, delete; branch files cited that are not in this tree | R1 |
| cb-1-1 | Blocker | per-role tests | "migrate refuses a hand GRANT DELETE" contradicts the code: REVOKE ALL repairs it (migrate.py:188; pinned by test_k2_migrations.py:275-289) | R14 cb-1 |
| ir-1-M1 | Major | limits layer | Limits.reserve and settle claimed by both F-store and F-install | R2 |
| ir-1-M2 / cb-1-2 | Major | decision 2 | per-run cost inside settle has no SQL, invariant, test or mutant; add_cost cannot be reused (same lock, NotFound); README says the opposite; expired then settled lower never reaches the run | R3, R14 cb-2 |
| ir-1-M3 / cb-1-6 | Major | Limits.settle | a repeated settle cannot be told from the first: audit row written again, overshoot of a replay undefined; unknown id differs between the two meters | R4 |
| ir-1-M4 / cb-1-6 | Major | overshoot audit | AuditEvent needs run_id (not None), principal, source | R5 |
| ir-1-M5 | Major | Limits.reserve | try scope, order of agent lookup and stop read, meaning of bad_amount, store amount check undefined | R6 |
| ir-1-M6 / cb-1-4 | Major | contract tests | purge test fails on PostgreSQL: _SplitStore sends it to the runtime login | R1, R7 |
| ir-1-M7 / cb-1-4 | Major | role tests | no fixture creates portal and reset logins; missing_methods pin in test_k5_round6_contracts | R7, R14 cb-4 |
| ir-1-M8 / cb-1-3 | Major | models | SpendReservation(Shape) has ten fields against nine columns | R8 |
| ir-1-M9 | Major | rollback | reverting the migration file breaks migrate; rollout order and CHANGELOG upgrade steps missing | R9 |
| ir-1-M10 / cb-1-5 | Major | expiry age | the ordered test cannot be written: no upper bound on a call's length exists | R10, R14 cb-5 |
| ir-1-M11 | Major | whole ticket | no phases | R11 |
| ir-1-M12 | Major | interface (ii) | ticket and README number the contract points differently | R12 |
| cb-1-7 | Major | reserve SQL | nothing sets or checks READ COMMITTED | R14 cb-7 |
| cb-1-8 / ir-1-N3 | Major / Nit | charge hits | the split of the 11 .charge( hits is wrong (2 Limits, 9 demo meter, 0 Budget) | R13 N3 |
| ir-1-N1 / cb-1-9 | Nit | citations | line numbers moved after steps A and B (table in the second reviewer's report: tick.py STEPS 257-275, migrate.py 55-56, 89-94, 159-175, 358, app.py 203, 207-216, test_p7_store.py 236-255) | R13 N1 |
| ir-1-N2 | Nit | pins | no row needed in tests/test_migration_numbers.py | R13 |
| ir-1-N4 / cb-1-11 | Nit | tick | docstring list; where the purge line sits | R1, R14 cb-11 |
| ir-1-N5 | Nit | memory store | expiry clock unspecified | R13 N5 |
| ir-1-N6 | Nit | SQL | seed statement not written; exception for zero rows at settle; new_id("res") | R13 N6 |
| ir-1-N7 | Nit | tests | month cap not stated in overshoot and midnight tests | R13 N7 |
| ir-1-N8 / cb-1-19 | Nit | mutants, defaults | no mutant file or mapping; RESERVATION_EXPIRE_S against the defaults.py rule; CHANGELOG still names 0006_evidence | R1, R13 N8, R14 cb-19 |
| cb-1-10 | Nit | behaviour list | authorizer and recheck also read blocked | R14 cb-10 |
| cb-1-12 | Nit | role tests | overlap with the generic grant loops | R14 cb-12 |
| cb-1-13 | Nit | reuse | the branch's _close already moves runs.cost_usd | R14 cb-2 |
| cb-1-14 | Nit | invariant 1 | needs amount above zero, counter from 0, no settle in between | R14 cb-14 |
| cb-1-15, cb-1-16 | Nit | unknown agent, unknown id | KeyError against limits_unavailable; NotFound against no-op | R6, R4 |
| cb-1-17 | Nit | CI | 100 connections, T1 fits | R14 cb-17 |
| cb-1-18 | Nit | branch table | tests/test_meter_harness.py (69 lines) missing from the table | noted, no text change (the branch files are not brought in, R1) |

Confirmed by the reviewers (no finding): the conditional UPDATE is exact under READ COMMITTED including first-use counter rows; no deadlock cycle found (reservation row, day, month in reserve and settle); the migration passes the repo's guards (_SAFE_CREATE, check_ledger, check_grants, migration_numbers); NaN and Infinity are refused by the table CHECK; the GRANTS row fits the Grant dataclass after step B; signatures match the interface files.
Not checked by the reviewers: nothing was run; the branches themselves; tests/test_no_hardcoded_values.py; the memory-store design beyond the lock; the size estimates.
