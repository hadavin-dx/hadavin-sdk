# Hand-off v15: what changed from v14 (v14 files are unchanged)

Failures and gaps first. Not run in this pass: unit tests, ruff, bandit, gate4.sh (still UNTESTED, disclosed). EGM skills could not be invoked from this agent. Postgres runs are 16.15 only (CI uses 17.10). The decrease-log reader role is specified and tested at privilege level in a throwaway cluster only; no product code exists.

| Finding | Old (v14) | New (v15) | Test that fails on the old design |
|---|---|---|---|
| Sec M1 held file | default file carried the Infinity clause | default `spend_nonneg.sql` = Q34 exact; clause in variant `spend_nonneg_finite.sql`; each has its own sha256; pre-flight lists +Infinity; DB-2 states Postgres 14+; code-level finite check stated independent of L7 | pg_v15 checks on both files (93 of 93) |
| Sec M2 | L7, L9 "Decides: lead"; reader = portal role | L7, L9 OWNER-OPEN; reader = audit reader role with policy and negative tests | pg_v15 audit-reader denials |
| Sec M3 | author-run only | independent re-run of B1 closure, migration step as non-superuser, two runs kept, 16.15 caveat | raw-pg-v15-run1/2 |
| Sec m1 | `window_only=True` flag | `WindowOnlyGate` class; S-1 alone stated as a date stop | C7 test renamed, C8 added |
| Sec m2 | qualify mode switch | allowlist stated | section 5 (qualify) |
| Sec m3 to m5 | numbers, wedge, +Infinity | wedge stated; v15 numbers (+0.04 to +0.075 ms, 110.6 B); planning bound +0.33 ms, 167 B | pg_v15 |
| Sec m6, m8 | mixed numbers, `test_gate` | one set of numbers (earlier-run difference unexplained); helper renamed | grep |
| Sec m7, m9 | not asked | partly: injection-screen question in 5.5; retention = L16; G-4(v) NOT separately asked (gap) | none |
| Ready M1 | 5.11 layered | folded into 5.1 to 5.9, one PR owner each | grep for 5.11 |
| Ready M2 | `spend_refused` in S-1 test | `guard_unavailable` | E0-S1-3(b) |
| Ready M3 | no source for numbers | `SpendSettings`, `Limits(..., window=None, spend=None)` | signature in 5.5 |
| Ready M4 | no owner PR | owners and signatures; S-2b detects log with `to_regclass`; `store/postgres.py` in DB-2 hot files | 5.5b, 5.6 |
| Ready M5 | tests assumed L7 | conditional table (7.2) | 7.2 |
| Ready M6 | S-2a test needs DB-1 | DB-1 test: no held name without an OWNER_YES entry | 7.2 |
| Ready M7 | two release rules | one rule (`NO_BILL_STATUSES`), events named, `KeptTotal` class | 5.3 |
| Citations | 28 near-miss | ranges widened; 402 cites: 321 exact, 5 within 2 lines, 55 MOVED (15 read, 40 unread), 7+12 unanchored, 2 ambiguous | cite_check_v15.py |
| Planned names | unlabelled | 142 labelled by rule (not read one by one) | planned-names-v15.txt |
