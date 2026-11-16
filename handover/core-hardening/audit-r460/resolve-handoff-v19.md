# Resolve, hand-off v18 reviews (security, readiness, independent evidence run). Hand-off v19.

Status words: FIXED-IN-TEXT, RUN (a raw file in `evidence-handoff-v19/raw/` shows it on 16.15 with reference code, author-run), STATED (not closed, reason given in `CORE-PR-HANDOFF-v19.md` section 0 item 0 (5)), OWNER-ONLY, LEAD-ONLY, T (text only). Nothing is "verified" beyond the evidence named. The EGM resolve skill was not invoked (not available to this agent); the lead runs it. Every id with its test: `v19-CHANGES.md`.

| Id | Status | Where |
|---|---|---|
| Sec MA1 (guard not deny by default) and the runner's `CREATE VIEW` | FIXED-IN-TEXT; RUN (152 mutant checks, 0 failed; v18 misses 49 of 51 new; 30 of 30 runner spellings; the three exploits shown on a real server) | 5.6 1(j) |
| Sec MA2 (schema and case aliasing; atomic bodies unscanned) | FIXED-IN-TEXT; RUN (N1, N3 mutants; start-up query by `proname`); product code T | 5.6 1(j), 1(o2) |
| Sec MA3 (secret-check claims) | FIXED-IN-TEXT (claims corrected, plan withdrawn); detectors T; real protection is the operator's | 5.6 1(g2) |
| Sec m1, m2, m3, m7 | RUN (DB-2 INSERT record; settle needs the day row; day window; `statement_timeout`); m3 row spam inside the window STATED | 5.6 1(m), 1(o), 1(e2) |
| Sec m4 | FIXED-IN-TEXT; RUN (N35, N42 to N45) | 5.6 1(j) |
| Sec m5 | `proname` and grantable column RUN; body hash and wider membership check NOT done (STATED; reason: cannot test stability on 14 and 17) | 5.6 1(o2) |
| Sec m6, m8, m9 | RUN (three counts); FIXED-IN-TEXT; FIXED-IN-TEXT | 5.6, 8 |
| Ready Ma1 | FIXED-IN-TEXT; RUN for the comparator (4 cases); `gate4_v19.sh` NOT run | 7.2 |
| Ready Ma2, Ma3, Ma4 and minors 1 to 8 | FIXED-IN-TEXT | 7.2, 5.6, 8, 10; `v19-CHANGES.md` |
| Evid runner (1) to (4) | (1) RUN; (2) RUN; (3) days, amount 0, agent-name spellings RUN, settle worst 0 and cross-agent settle STATED; (4) no action | see `v19-CHANGES.md` |

**Not fixed, reason:** product code and tests (not written; this agent writes hand-off text and reference programs only); Postgres 14 and 17.10 (not installed: L18); `gate4_v19.sh` run (not run); independent evidence run of v19 (not done); EGM review of v19 (cannot be invoked here); per-agent logins (L-4, lead decision); the cross-agent settle, the under-reporting by a hostile runtime, row spam inside the window and case-different agent names (the database cannot tell callers apart; invoice comparison is the control); body hash pinning (see above).
