# PR73 core/P3a-2 head c727453, design review, wave 2 round 1 (security path, uncapped)
Reviewer read snapshot /tmp/snap/core_P3a-2-c727453, ticket P3a.md and evidence c727453-cloud3. Ran nothing. Verdict: 0 Blocker, 6 Major, 5 Nit.
- F1 Major: scope beyond the frozen ticket (release manifest, trigger allow list, refusal of superuser/CREATEROLE/CREATEDB/BYPASSRLS roles, fixed 5s lock and 60s statement limits, pg_auth_members and pg_db_role_setting read-back, hidden COMMIT detection, new refused statements, pglast differential test, global autouse fixture). Code cites orders 89, 112, 186; lead must confirm each or the ticket gets an errata.
- F2 Major: upgrade path. A deployment whose tables are owned by the old superuser login is refused, and the printed SQL grants only USAGE, CREATE on the schema; later ALTER TABLE fails with "must be owner", and grants may silently no-op. No test or runbook step covers ownership transfer.
- F3 Major: survivor R4 is a real gap. Grant option of an existing membership is not proven on a real server; only a stub test kills it.
- F4 Major: survivor M88 is a mis-pointed killer. test_a_disabled_trigger_is_refused hits the other branch; the right test is test_a_trigger_created_disabled_is_refused_and_one_created_enabled_is_not (test_migration_wiring.py:426). Docstring at line 408 wrong. Not claimed killed until re-run.
- F5 Major: CHANGELOG item 11 holds placeholder text "LEAD TO FILL IN"; all server evidence is Postgres 16.15, CI uses 17.10; CHANGELOG and docstrings cite internal order/ticket/R448 ids.
- F6 Major: all SET/RESET refused, so SET LOCAL lock_timeout in P4d 0006 cannot pass; 5s/60s are hard-coded constants, not validated config. Lead must tell P4d and P2a-1.
- F7 Nit-to-Major: trigger allow list keyed by (file, trigger) only, no table; a listed trigger can be silently disabled (D or R). Key by (file, schema.table, trigger) and keep refusing D/R.
- F8 Nit: role membership by inheritance (member of a superuser role) not checked.
- F9 Nit: cluster-wide read-back can cause false refusals on shared clusters.
- F10 Nit: global autouse fixture wraps every migrate test in SET ROLE; scope it.
- F11 Nit: lexer note claims an unkept sqlglot comparison; pglast is GPL-3.0 (test group only), state in PR text.
Unplantable 11 mutants of handover/tools/p3a2_mutants.py: stale text (written for 2b0941b), 8 re-covered by tests/migrate_mutants.py (87/89), P9 equivalent in migration_numbers_mutants.py (unconfirmed), M88b dropped unexplained. Retire that script as a count source; one table runner/ids/killed/not killed. Checked-in runner began as a "reconstruction of the lost runner", so earlier counts are unauditable.
Not checked: no code run; most of the ~5000 test lines; PG17 behaviour; wheel packaging of the two JSON files; LEAD-ORDERS, P2a/P4d/P4b2 tickets.
