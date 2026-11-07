# PR 73 (P3a-2) @ea40242: round 2, codebase-details review (condensed by the coordinator, ids kept)
No Blocker. `\b` sweep correct (over-match only); runbook tests really run the CHANGELOG SQL; mutants 66/66. Ran nothing.
C1 Major | tests/test_migration_postgres.py, CHANGELOG case (a) | No test runs the recipe `order_problems` prints for a late file. Ticket H1 test_hand_recipe_works and H4 test_recipe_failure_leaves_nothing_psql do not exist. Add them, or state in case (a) the recipe is never run; confirm scope with lead (build note 5 / order 74(b) not read by reviewer).
C2 Nit (Major if order binding) | test_migration_postgres.py:33 | PREVIOUS_RELEASE_LAST is 0004_audit_checkpoint_meta, order 89 says 0005_evidence; at 0005 the test is empty. Follow order 89 and fail/skip loudly when nothing follows.
C3 Nit | helpers scratch/require_module duplicate pg_schema and importorskip logic.
C4 Nit | _NAME_CHAR written twice (_ident_char); agreement test covers 17 chars. Loop over range(0x3000).
C5 Nit | mutant P9 killed only by AST test; add behavioural case `SET LOCAL lock_timeout$x = 1`.
C6 Nit | runbook.py stale comment; header text hard-coded in the test, not cut from CHANGELOG.
C7 Nit | migrate.py _scan lexes each file twice; de-dup relies on identical strings.
C8 Nit | test_migration_rules.py:465-472 pins docstring wording; compare to len(_READBACK_VALUES).
