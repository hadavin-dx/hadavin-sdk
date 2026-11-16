# PR73 (P3a-2) round 6 result review, codebase and test details, head 0c52491

Reviewer: egm codebase-details agent (fresh, read-only, snapshot /tmp/snap/core_P3a-2-0c52491). Saved by the cloud lead, condensed from the hand-back.
Verdict: 0 Blocker, 1 Major (new), 5 Minor. Round-5 findings have real fixes, except the live-process lock item (only partly fixed, see N1).
Not checked by the reviewer: no code or tests run; no independent evidence read (none existed yet); no raw per-mutant output; PostgreSQL 17 not run (owner-only); non-UTF-8 single-byte databases not checked (the ASCII fold is right only for UTF-8 databases; failure mode is a missed foreign-owned function).

## Round-5 items confirmed fixed (by reading code only)
Blocker 1 ruff format (gates.txt shows exit 0; not re-run by reviewer); Major 1 mutant-runner allow-list; Major 2 portal role through effective_problems; Minors 1-6 and design minors A, C, D, F, G1, H fixed. E (NOREPLICATION in printed SQL) added; whether a test asserts it was not checked. G2 only partly fixed (see N1).

## New findings
**Major N1. The "this test process is alive" lock is per database, not per server** (tests/fixtures/migration_role.py:68-81, :103). Advisory locks are scoped to one database. Process A holds its lock in database X; process B sweeps from database Y on the same cluster, sees A's role (roles are cluster-wide), its try-lock on Y succeeds, and it runs DROP OWNED BY ... CASCADE and DROP ROLE on A's live role mid-run. Same scenario as round-5 Major 3, with databases instead of servers. The docstring "One lock per server" is false. The studio rule faster-builds item 5 tells builders to share one Postgres with a database each. Wiring tests use a fake psycopg.connect and cannot see this.
Fix: open the hold connection with application_name set to the role name; in sweep_stale_roles add `AND NOT EXISTS (SELECT 1 FROM pg_stat_activity a WHERE a.application_name = r.rolname)`; (alternative: always take the lock in one fixed maintenance database). Add a real-server test (hold from database X, sweep from database Y, role survives), a mutant SW7 removing the guard, and fix the docstring.

**Minor N1.** Test logins without a password remain (tests/contracts/kinds/store_postgres.py:43, tests/test_k5_round10_postgres.py:100), so CHANGELOG.md:19 ("the other login roles the tests make get a hash the same way") is wrong. Use create_login_role and pass the password to make_conninfo, or narrow the sentence. Also in _hold_the_role: if hold.execute raises, the new connection is neither closed nor stored; the _HOLDS key holds the password in clear (internal only).
**Minor N2.** The `NOT rolsuper` term in the settings query (migrate.py:404) has no mutant (NS1 plants only the members CTE). Add NS2 killed by the `[settings]` case.
**Minor N3.** CHANGELOG.md:15 names only part of the portal tightening. Also refused now: other applications' objects in the schema, PUBLIC grants, the four role flags, owning a relation, sequences. Add one sentence. Lead decision (cost only): this goes beyond the ticket text and may refuse a setup that works today. Not covered by the check: rights in other schemas, EXECUTE on functions, column-level REFERENCES.
**Minor N4.** Mutant runner: (a) a test asserting on a helper thread's errors list fails with an assert head even if the thread died of a psycopg error, and counts as KILLED; fix by reading per-mutant raw output; (b) a ConfigError head counts as a kill; (c) NOTES.txt:2 says the full 164-mutant run was not repeated after the SU2/PA2/PA3 test fix (only those 3, 3 of 3 killed); O1 and T1 rest on a second killer. The raw per-mutant output is not in the evidence folder: run the full 164 once on the final head with MIGRATE_MUTANTS_RAW_DIR and grep for psycopg.errors.
**Minor N5.** Wording: CHANGELOG items 6 and 7 are one very long bullet each with unexplained terms (advisory lock, pg_auth_members, grant option); split them. The comment at migrate.py:658 says a plain name "does not start with a digit" but `_PLAIN_NAME = \w[\w$]*` allows one. "grant map" appears in refusal messages (:1043, :1054, :1064) without explanation.

## SQL injection and quoting
None found (bound parameters, sql.Identifier, role-name fullmatch, ascii-escape check on printed names, linear regexes). A CREATE FUNCTION after a `;` inside a string or $$ body is still read as a managed name; pinned in a test; fails safe (false refusal only).

## Open lead decisions (cost only)
Fixed per-file timeouts; pg_database_owner exemption (migrate.py:571); scope beyond the ticket (portal tightening, NOT rolsuper filter, ASCII fold, `$` handling); rolreplication check.
