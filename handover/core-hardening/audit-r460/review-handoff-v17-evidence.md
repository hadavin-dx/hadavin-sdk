# Hand-off v17 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: audit-r460/evidence-handoff-v17-independent/ (00-TABLE.md, raw-01..13). Recorded, not judged. Postgres 16.15 only.
## Failures and deviations first
1. SECURITY DEFINER guard misses 8 of 25 spellings (all accepted by Postgres 16.15, each leaves a SECURITY DEFINER routine): dynamic SQL in a DO block built with ||, format('%s'), E' ', chr(32) (cases 12-15); double-quoted names containing -- or /* (19-21; strip_comments not quote-aware); a second overload of a declared name with no REVOKE (25; REVOKE check accepts any argument list). The builder's "20 of 20" holds only for its own 20 spellings.
2. sha256-v17.txt incomplete: secdef_guard_v16.py has no hash line (25 hashed, 26 files).
3. secdef_mutants_v17.py needs its second argument (product migrations folder) to reach 30 of 30; without it 25 of 25 (runner's first-run slip).
4. Observations: runtime login can settle any agent_id's open reservation; kill_switch_engage() succeeds silently if the row is missing; spend_reserve accepts any month date, empty or 100 KB agent_id, 'infinity'::date, values up to 2^63 or 1e30 (1e131072 gives 22003).
5. Runner's own test error: 74 of 75 hostile checks (CREATE TRIGGER does not conflict with ACCESS SHARE). DB-2 under ROW EXCLUSIVE gives 55P03 after 5.01 s.
6. Measured trigger is the DB-2 decrease trigger, not "DB-1 timing".
## Results
sha256sum -c 25 of 25; pg_v17 49 of 49; pg_v16_regress 175 of 175; secrets 7 of 7; mutants 20 of 20 + 5 real files clean (30 of 30 with argument). Hostile DB-3 tests 74 of 75: direct writes refused 42501, SET ROLE/SESSION AUTHORIZATION refused, bad values refused or inert, settled money never fell; races (20x5 reserves = 100; racing settles one wins) hold; lock_timeout 55P03 at 5.01-5.02 s on all 5 held files, nothing recorded. Trigger cost +0.051 to +0.079 ms/lowering (builder said +0.071, +0.099); 110.6 bytes/row. Section 8 hash table 5 of 5 match. Citations: 30 of 315 sampled resolve; 3 not fully traced.
## Not run
Postgres 14 and 17.10, gate4_v17.sh, product tests, ruff, bandit.
