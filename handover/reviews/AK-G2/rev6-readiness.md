# AK-G2 rev 6 plan review, round 6, egm-implementation-readiness (agent af3568bb)
Verdict: NOT READY for a zero-decision builder. 1 Blocker (Done-gate), 7 Majors, 9 Nits. Counts agree (79 rows, 143 mutants, 4 fail-before).
B1 Mutation evidence cannot be produced until runner keywords exist (conftest, pass_env, forbid_skips). Lead ORDER 181 now says R1 YES: runner PR must be listed in "Depends on" of both sub-PRs (-a and -b), needs own ticket/owner; no R2 command needed.
M1 SQL not exact: no CREATE TABLE for inbound_receipts/bodies/key_checks (types, NOT NULL, defaults, state/reason CHECKs); 3 trigger bodies prose only; SQLSTATE/message only for 3 refusals, store mapping of the others unstated; REOPEN_SQL, claim UPDATE (SKIP LOCKED, attempts+1), purge join not literal; Grant new fields by name only; UNVERIFIED points without fallback (check_grants empty list, column SELECT via _apply_grants, has_column_privilege PG16/17, current_user in NOLOGIN trigger); migrate() takes only 3 roles today, re-run owner NOLOGIN/distinct checks new code.
M2 Row L20 (i)-(iv) in BN-3 contradicts BN-38/BN-30 (does receive update the stored check? no, only dispatch). Rewrite in one place.
M3 BN-47 gate fact stale: peel worktree already has _same_message_run, run_id, InvalidRunId (PR87). Restate with head sha (now 5520a67).
M4 ORDER 57 A.1 accepted cuts (door_app/wsgiref, B2 to k6) never applied or overruled in the ticket.
M5 Evidence commands not exact (a-postgres, a-failbefore, B1-B3, a-suite, bursts; DSN missing in pytest line so Postgres rows SKIP; who creates the 3 roles + NOLOGIN owner in -b).
M6 Mutants lack old/new patch text; multi-file mutants; schema-per-mutant mechanism; home for guard test.
M7 BN-15 rollback query "as the runtime role" but runtime has no rights on inbound tables; name dispatch role or migrator.
Nits: N1 57 vs 67 notes; N2 BN-35 six vs four fail-before rows, D2b/D2c file; N3 "10 methods" leftovers (11), two overlapping CHANGELOG texts, L14 two vs four GRANTS rows; N4 key_check as rec field and keyword; N5 set_inbound_key_check readers unused; N6 L19 golden vectors independent of implementation; N7 weak rows D13, D4b, L1, D5, L13, L21, C6; N8 no row-to-file map; N9 L23(ii) custom store reach, C4 skip rule.
Not checked by reviewer: all PostgreSQL behaviour; git state; per-row kill logic.
