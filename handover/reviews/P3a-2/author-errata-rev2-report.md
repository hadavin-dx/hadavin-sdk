<!-- full hand-back report of sub-agent ab2d8714, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

ERRATA rev 2 of the P3a-2 round 13 ticket is written into handover/tickets/P3a-2-r13-verify-final-state.md. It is NOT claimed READY: it needs plan review round 2 by fresh reviewers. I made no commits and no push. The lead's own "sync handover working files" commits (latest d6ca6df7, 16:48 UTC) already picked up most of my edits. Still uncommitted on core/cloud-handover: the ticket (small final edits), handover/questions-for-lead.md, and plan-r2/README.md and run_queries_r2.out.

**What failed, or what I could not check**
- Nothing in the repository was run: no tests, no ruff, no mutants. I ran only PostgreSQL 16.15 and psycopg 3.3.6 probes.
- Nothing ran on PostgreSQL 17 or 18.
- Not measured: the mutant run time (the "30+ min for 288" figure is the reviewer's), the matrix run time, and the cost of the final Q2/Q3 on a large catalog. My setups were small: Q2 took 16.8 ms, and 25.6 ms after it was widened.
- Not run: `file_fdw` and `allow_in_place_tablespaces` in the CI image (taken from the PostgreSQL docs); how psycopg reports a `pg_terminate_backend` during COMMIT.
- The rung-table rows for the outside tools (pg_permissions, pgTAP, ldap2pg) are still from memory, not researched live.
- I cited no bible R-numbers: the bible is not in this repository.
- The CI route for `max_prepared_transactions` is still untried.
- My first COMMIT-cut probe was invalid: the relay forwarded the reply too early. I fixed it and re-ran; f2.out is the valid run.

**Probes run** (raw SQL, scripts and output in handover/evidence/P3a-2/plan-r2/; README.md there lists each file)
Throwaway cluster: initdb as the OS user postgres in /home/user/build/pg-p3a2r13b, port 56231. It was stopped and deleted, then started once more for one re-run, then stopped and deleted again. The postgres process still running (/tmp/pg-q8c1b2) belongs to another agent and was not touched.
- (a) REVOKE and grantors:
  - Superuser and owner REVOKE leave entries granted by a grant-option holder.
  - `GRANTED BY` on an object right is refused ("grantor must be current user").
  - `SET ROLE <grantor>; REVOKE …; RESET ROLE` works.
  - A membership granted by a CREATEROLE role needs `REVOKE … GRANTED BY` (without it: only a WARNING, nothing removed).
  - Step 4's `REVOKE ALL` leaves another grantor's table and column entries.
  - A table-level `REVOKE GRANT OPTION … CASCADE` left the grant-option holder's column grant in place.
- (b) Sequences have no row type on 16. Row types exist for relkinds r/p/v/m/f. The exact key is `typtype='c' AND typrelid<>0 AND relkind<>'c'`.
- (c) The `public` schema on 16 is `{pg_database_owner=UC/…,=U/…}` (everyone may use it, nobody else may create in it).
- (d) A psycopg `options=` keyword replaces the DSN's `options`, so a role switch is lost. Also, `store/postgres.connect` does not accept `options` at all.
- (e) The re-defer attack is confirmed as a plain role: promise-table row 3 holds.
- (f) A COMMIT the server refuses gives an SQLSTATE with the connection still open. A connection cut after COMMIT is sent gives `OperationalError`, SQLSTATE None, status UNKNOWN, and the commit DID happen.
- (g) With `ALTER ROLE … SET statement_timeout=1`: 100/100 fresh connections cancelled; with `SET LOCAL` limits first: 100/100 passed.
- (h) A `pg_monitor` member made rev 1 print 12 lines and 12 REVOKEs on pg_catalog objects. The right fix is one membership statement.
- Extra runs:
  - Rev 1's extension-owner conflict is settled: the installing plain role owns `citext`.
  - Mutant count settled: 288 = 279 written entries + 9 from `cmp_mutant`.
  - Create plus drop of one database per test case: about 24 ms.
  - The final queries ran as a plain role; the new closure took 1.9 ms on a 25-level diamond of roles, while the old shape was cancelled at 10 s.

**Decisions now in the ticket** (change list at the top; every finding answered in the new section 11)
- **R-B1:** a rebuilt commit order of 6 commits. A per-commit green command includes the mutant-list test, and mutants change in the same commit as their code. Work packages A1, B1, A2, C1, B2, C2, each run in 60-minute builder sessions.
- **R-B2:** everyone may hold USAGE on the schema of the run. O7 now covers everyone. A `public`-schema test and its sensitivity control are added.
- **Step 8:** no `options` argument. All of step 8 sits in one `try`, so any exception gives exit 5. The limits come from the existing `RECIPE_TIMEOUTS` constant. It reads with REPEATABLE READ, read only.
- **COMMIT (design M3):** a server refusal gives exit 2; an unknown outcome gives exit 5 with "may or may not have happened".
- **Oracle:** a superuser login is required (a failure, not a skip). One database per case, fixture variants P/O/C/T, and a table of the attempt that shows each of the 37+2 effects. Unknown error codes count as INCONCLUSIVE, never as allowed. The banned-word check uses whole words.
- **Tests and mutants:** every affected test and mutant is named (wiring, k2, CHANGELOG pins, MT1/MT2, R23, SH1, 16 re-checked). Every acceptance item has a test id. Mutants run in four batches. Final count 288 − 29 + 55 = 314.
- **Module layout:** no import from `migrate` into the new module; `_label` moves to `migration_numbers`; the reviewed list is passed at call time. The full query texts are pasted verbatim (checked against the probed file), together with `PROBLEM_KINDS` and the table of rights per role kind.
- **Design M4–M7:** object side = option (b), written as an AUTHOR ADDITION. O5 is struck. A right through a `pg_*` role is one membership line, and no statement is ever printed against a system object. `Problem` carries the grantor, with the probed statement forms.

**Gaps I found myself and fixed in the ticket**
- Rev 1 had silently dropped the refusal of a package table handed to a third role in the schema of the run. New rule O8 refuses it; Q2's third condition was widened and re-run. Two tests that hand objects to a group the migration role belongs to are retired with that change.
- With the search path pinned, `current_schema()` answers `pg_catalog`, which would break the kept reads that use it. Those reads now take the schema from step 1 (new acceptance item 2b).

**Needs the owner** (appended to handover/questions-for-lead.md)
1. Is sharing the migration role or the schema of the run with another application supported? This decides option (a) or (b) for the object side and a pre-flight refusal.
2. Confirm striking O5.
3. The CI route for `max_prepared_transactions`.

**Files changed:** handover/tickets/P3a-2-r13-verify-final-state.md (1,115 lines), handover/questions-for-lead.md, and the new folder handover/evidence/P3a-2/plan-r2/ (probe .sql/.py/.out files and a README). Checkpoint: /home/user/build/checkpoints/P3a2-errata.md. Scratch work: /home/user/build/p3a2r13-author2/. Head d6ca6df7. Real clock 16:22–16:53 UTC (21:52–22:23 IST). I did not measure my own token use.
