# Resolve, hand-off v17 reviews (security, readiness, independent evidence). Hand-off v18.

Status words: FIXED-IN-TEXT, RUN (a raw file in `evidence-handoff-v18/raw/` shows it on 16.15 with reference code, author-run), OWNER-ONLY, LEAD-ONLY, T (text only). Nothing is "verified" beyond the evidence named. The EGM resolve skill was not invoked (not available to this agent); the lead runs it. Every id with its test: `v18-CHANGES.md`.

| Id | Status | Where |
|---|---|---|
| Sec MA1 and runner spellings | FIXED-IN-TEXT; RUN (96 checks, 0 failed; v17 guard misses 39) | 5.6 1(j) |
| Sec MA2 | FIXED-IN-TEXT; RUN (MA2 31 lines, m7 4 lines); product code T | 5.5b 3b, 5.6 1(o2) |
| Sec MA3 | FIXED-IN-TEXT; RUN (migrate four times, G1, G4, G9, DELETE, TRUNCATE; control); GRANTS and function-grant step T | 5.6 1(o), start gate (vi) |
| Sec MA4 | FIXED-IN-TEXT; RUN (MA4) | 5.6 1(o), L22 |
| Sec m1 to m8 | m1 stated not closed (invoice comparison, L-4); m2 RUN; m3 RUN; m4 RUN (K2); m5 RUN for the prototype, product rule T; m6 FIXED-IN-TEXT, RUN; m7 RUN; m8 each row marked C or T | see `v18-CHANGES.md` |
| Ready V17-Ma1 to Ma3 and minors | FIXED-IN-TEXT (T) | see `v18-CHANGES.md` |
| Evid runner items 1 to 6 | FIXED-IN-TEXT; RUN where a number is given | see `v18-CHANGES.md` |

**Not fixed, reason:** product code and tests (not written; this agent writes hand-off text and reference programs only); Postgres 14 and 17.10 (not installed: L18); `gate4` re-run (not run in v18); independent evidence run of v18 (not done); EGM review of v18 (cannot be invoked here); per-agent logins (L-4, lead decision); the cross-agent settle and the under-reporting by a hostile runtime (database cannot tell callers apart; invoice comparison is the control).
