# P4d build-start correctness review (rev 10) - agent adb827e4f81f4db72
Status: REPORTED (saved by the lead from the hand-back, condensed; model output, not user authority). Read-only, nothing run, did not read reviews/ or evidence/. Tree is not a git checkout so ce70eb5 unconfirmed.
Verdict: a1, a2-i, a2-ii can start now; b and c wait for P3a. 3 Major need a ruling (flaky test or false behaviour).
| id | sev | problem | fix |
|---|---|---|---|
| BS-P4d-COR-1 | Major | "SET LOCAL ends with that file" false: migrate.py:308-332 wraps all files, ledger, grants in ONE transaction. | Reword; b30 stays; note P3a coupling. (Same as ADV-5.) |
| BS-P4d-COR-2 | Major | _run "only way a write method sends SQL"; AST scan for .execute passes today's 18 methods since they use _exec (postgres.py:201) via _insert, _update_run, _purge, direct _exec; deadline never reaches them. | State mechanism: _exec/_run single sender with per-call deadline attribute under the RLock, reads exempt; AST scan flags self._exec( and self._db.execute( in write methods and helpers. |
| BS-P4d-COR-3 | Major | T4 and B4b(b) timing margins ~50 ms on a 500 ms budget; exact "statements sent == 2"; call_budget_ms minimum is 500; flaky on loaded CI. | Test-only monotonic-clock seam driving the deadline, or release admin locks on a test-controlled event, or budget 5000 with releases ~0.5x and 1.2x. |
| BS-P4d-COR-4 | Minor | a2-i ceiling needs add_cost as transaction with RETURNING cost_usd; Files bullet says only "call the validators". | Add the sentence; check a2-ii wrapper nests as savepoint. |
| BS-P4d-COR-5 | Minor | PostgresStore constructor params unnamed (today __init__(self, conn)). | Name `PostgresStore(conn, *, lock_timeout_ms=1000, call_budget_ms=5000, on_retry=None)`. |
| BS-P4d-COR-6 | Minor | P4d-b/c depend on P3a (tests/migration_schemas.py, three P3a test files), absent on disk. | a1, a2-i, a2-ii start now; b, c after P3a merges. |
| BS-P4d-COR-7 | Nit | defaults.py order claim overridden by order 20(5). | One sentence. |
| BS-P4d-ADV-1b | Minor (accepted risk) | Day bound +-1 day from DB date; at month boundary books previous/next month counter (cap dodge); caller-trust boundary stated. | No change, or restrict day to DB date for month key. |
Verified: protocol 32 methods; 18 write methods; test_store.py 26 functions / 52 cases; psycopg grep counts; mutant table counts (a1 6, i 27, w 19, b 43, c 6); B3 e-rows 16; Protocol 32+6=38; DDL 12 columns = 12 fields; trigger matrix 16 pairs = 5 + 11, 5x8=40; rounding kill sets; ceiling and price arithmetic; many code cites. Not checked: all PG behaviour; evidence/reviews dirs (excluded); other tickets' text; pydantic non-finite Decimal; several unopened cites; the 16 Reply/Verdict-building test files; demos/ask-your-data pgsource cite.
