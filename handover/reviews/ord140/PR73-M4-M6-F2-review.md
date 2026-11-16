# Fresh review: PR73 (P3a-2 d01c84b) decisions M-4, M-6, F2
Reviewer: egm-codebase-details (fresh, read-only; read no evidence logs, ran nothing).
1. MAJOR M-4: a released migration can be edited with no test failing if the same commit also edits migrations_released.json; no test pins the five hashes independently (tests read the same json). Side effect: the test asserting exactly 5 rows fails when a row is added at release, contradicting the docstrings. Fix: pin the first five hashes as literals, allow more rows; validate 64 hex chars.
2. MAJOR F2 (no hardcoding): timeouts 5s and 60s are literals in RECIPE_TIMEOUTS plus tests/fixtures/runbook.py, test_migration_numbers.py, migrate.py docstring, CHANGELOG. Derive or import from the one constant.
3. MAJOR F2 (drift): migrate() sets no lock_timeout or statement_timeout; only the hand recipe does; CHANGELOG still says migrate has no timeout. Make it true or state the difference deliberately.
4. MINOR: a source-text test (inspect.getsource) adds nothing over the behavioural test; a loose either/or assertion in test_migration_rules; garbage hash in the json gives "changed" not a config error; the real-database proof for F2 is skipped without Postgres.
5. NIT: stale wording about the lock name; BN-P3a-2-c in tickets/P3a.md names the old fixture path.
M-6: the reviewer found no definition; builder to state what it is.
