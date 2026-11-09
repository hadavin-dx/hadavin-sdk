# PR 73 (P3a-2) round 1, egm-codebase-details, head 2b0941b (condensed). Nothing run by reviewer.
BLOCKER
- B1 migration_numbers.py:5-7 and :14-15 say "NOTHING calls them / read-back is a later change"; false after this PR. Reword to present tense, cite migrate.py.
MAJOR
- M1 Manifest moved to src/hadavin_sdk/store/migrations_released.json (migrate.py:320) while q202/BN-P3a-2-c say tests/fixtures copy is the single source; other PR trees (P1a, P1b, P6a, PR66) still read the tests/fixtures copy. State whether the fixtures copy was deleted; tie or delete; fix BN-P3a-2-c and merge notes.
- M2 "read once, scanned text is run text" not true for released-file hash (migration_numbers.py:324-331 read_bytes before read_files at migrate.py:518/522); test patches only Path.read_text. Hash texts[p].encode("utf-8"); lone-CR inconsistency.
- M3 PostgreSQL 17 evidence missing (ORDER 132); CHANGELOG wording must say "not tested on 17".
- M4 P3a-2 66 mutants are a reconstruction; original runner not in repo; fail-before is at ea40242 not 2b0941b. Commit the runner / list mutant texts.
NITS: N1 released_problems checks package constant not patched files; N2 PREVIOUS_RELEASE_LAST note says 0004, code 0005 (order 89), no history evidence; N3 ticket says CREATE ROLE/EXTENSION/LOAD/COPY PROGRAM not refused, code refuses them (+DISCARD, ALTER SYSTEM); N4 ticket says 7 values/2 queries, code 9/3, triggers only current_schema; N5 dead tgrelid; N6 pg_auth_members cluster-wide false refusals; N7 double lexing; N8 CHANGELOG line 6 garbled.
Correct: wiring order, k2 stub edit, keep_quoted view, error types, runbook cases a-g, sqlglot/pglast pins.
