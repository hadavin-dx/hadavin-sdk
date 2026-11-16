# PR73 (P3a-2) fresh review at 2e35f76 (egm-codebase-details, read-only, no shell; saved condensed by the cloud worker)
Scope limits: no shell; evidence dir had only scripts, no results; pins vs real file bytes UNVERIFIED; Postgres behaviour UNVERIFIED by run.
Verdict: no Blocker; M-4, M-6, F2 as specified: 0 Major. Two Majors on the behaviour change.
- M-4 pins sound by reading (MM4 killed by pin test only; MM5 by :361 and :387-390; MM6 by :364-365). Hex/length check complete (fullmatch [0-9a-f]{64}; non-string value/key ConfigError). Nit: duplicate JSON key silently takes the last (object_pairs_hook would close it). Nit: ticket BN-P3a-2-c (P3a.md:280) names tests/fixtures/migrations_released.json; real file is src/hadavin_sdk/store/migrations_released.json (lead's note must say so).
- RECIPE_TIMEOUTS single source confirmed (migration_numbers.py:67; used at migration_numbers.py:256, migrate.py:43/:497, tests/fixtures/runbook.py). Nit: scan covers store/*.py and test_migration*.py only, not unquoted forms.
- SET LOCAL placement correct (inside db.transaction() after pg_advisory_xact_lock; autocommit connection gets explicit BEGIN); all raise paths roll back; timeout leaves ledger unchanged (tests :948-987, UNVERIFIED by run).
- MAJOR A: limits also apply to the grant phase and to runs with nothing pending (every normal deploy): a GRANT/REVOKE waiting >5 s fails an otherwise empty run; docs say only "a file"; no test for the grant phase; error surfaces as raw LockNotAvailable/QueryCanceled, not plain words (cli.py display unchecked).
- MAJOR B: CHANGELOG.md:6 under-documents (no numbers/scope; statement_timeout per statement vs whole string UNVERIFIED).
- Nit A: a migration file may SET LOCAL lock_timeout/statement_timeout itself (allowed) and the setting carries over to later files; docs should say the guarantee holds only for files that do not set it.
- Nit B: SET LOCAL runs after the advisory lock, so a second migrate waits without limit (hand recipe sets the timeouts before the lock); docs say "same lines as the hand recipe" without the order difference.
- Deleted test replaced by behavioural tests (wiring :484-538); call order vs check_ledger/check_grants UNVERIFIED.
- M-6 fine (PREVIOUS_RELEASE_LAST = 0005_evidence); P3a.md:264/:278 still say "provisionally 0004", superseded by BN-PREV-RELEASE.
- Hygiene: no real-looking secret.
