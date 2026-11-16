# Resolve, hand-off v16 reviews (security, readiness, evidence). Hand-off v17.

Status words: FIXED-IN-TEXT, RUN (a raw file in `evidence-handoff-v17/raw/` shows it on 16.15 with reference code), OWNER-ONLY, LEAD-ONLY. Nothing is "verified" beyond the evidence named. The EGM resolve skill was not invoked (not available to this agent); the lead runs it. Every id with its test: `v17-CHANGES.md`.

| Id | Status | Where |
|---|---|---|
| Sec M1 | FIXED-IN-TEXT as DB-3; RUN (G0 to G11, 49 of 49 twice); OWNER-ONLY to apply (L22), LEAD-ONLY role (L23); store code not written | 5.6 1(o), 5.10b |
| Sec M2 | FIXED-IN-TEXT; RUN (20 mutants, 12 missed by v16 guard, 30 real-file checks clean) | 5.6 1(j) |
| Sec M3 | FIXED-IN-TEXT; RUN (7 secrets checks, OS user `nobody`); product code and the independent re-run open | 5.6 1(g2) |
| Sec m4, m5 | FIXED-IN-TEXT; RUN (H1, K) | 5.4 4b, 5.6 1(m) |
| Sec m6, m7, m8 | FIXED-IN-TEXT; not run | 5.3, 5.5, 5.6 item 4, 5.10b |
| Ma1 to Ma8, Mi1 to Mi9 | FIXED-IN-TEXT; Ma8 RUN (raw numbers); the rest are text, no product code | see `v17-CHANGES.md` |
| Evid 1 | FIXED-IN-TEXT; RUN (lock test of all five files fails 55P03 at 5 s; v16 DB-2 file hits 57014) | 5.6 1(n) |
| Evid 2, 3 | FIXED-IN-TEXT; sha256 list in `sha256-v17.txt`; cite read by hand | section 8, 7.1 |

**Not fixed, reason:** product code and tests (not written; this agent writes hand-off text and reference programs only); Postgres 14 and 17.10 (not installed: L18); `gate4` re-run (not run in v17); EGM review of v17 (lead).
