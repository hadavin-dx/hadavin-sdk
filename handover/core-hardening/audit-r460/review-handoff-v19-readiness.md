# Hand-off v19 readiness review, round 6 (egm-implementation-readiness, condensed copy), 2026-11-16T18:29:25Z
Read-only, no shell. Verdict: S-1, S-2a, DB-1, DB-2 buildable round the majors; S-2b and DB-3 not yet. 0 blockers, 6 majors, 8 minors.
## Failures first
- M1 E0-S1-5 (line 434) still points at CORE-PR-HANDOFF-v16.md and v14 scripts; section 8.1 is the v19 file.
- M2 L19 default contradicts itself: "fails in prod and pilot" (553, OPEN-FOR-LEAD 18) vs ConfigError in prod, warning in pilot (5.5b item 3, 5.6(h)); the check runs only when the decrease record exists, so under defaults it never runs; no L19 test row.
- M3 limits status --check has no spec (exit conditions, output, thresholds); L13 default rests on it.
- M4 start-up query product inputs unspecified: secdef_problems and FUNCTION_POLICY exist only as prototype; where the list lives in src/, operator role name (L23), owner role source, behaviour when no DB-2/DB-3 function applied.
- M5 DB-3 Grant function kind, migrate() keyword, operator read path, L-2 store code undefined.
- M6 L18 run commands wrong or missing (pg_run_v16.sh runs v16 files; run_pg_v19.sh and run_secrets_v19.sh have no example invocation).
- Minors: comparator "four cases" but raw shows two runs; E0-S1-1 row has six cells; OPEN-FOR-LEAD adds three numbers not in section 10; section 5 heading says one held PR (three held); raw-pg-v19-run1 and run2 byte-identical though text says timing line differs; no test rows for L13, L16, L17, L19; DB hash abbreviations ambiguous; 5.1 item 7 leaves discovery to builder.
## Prior
v18 Ma1-Ma4 mostly fixed (one stale v16 path left); L21/L22/L23 rows fixed; five held hashes match sha256-v19.txt by reading.
## Not checked
Sections 5.3, 5.5, 5.7-5.10b, 6, other-tracks; raw outputs; no hash or command run.
