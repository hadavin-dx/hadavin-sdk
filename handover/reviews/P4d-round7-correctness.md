# P4d round 7 correctness review (egm:egm-codebase-details), ticket rev 8 (head 8680691). Condensed by the lead; read-only.
Verdict: no blocker, no major. 7 findings (5 minor, 2 nit).
| id | sev | where | problem | fix |
|---|---|---|---|---|
| C7-1 | Minor | Tell the authors P4a bullet, PL17 | Cites P4a.md:60 and MAX_PRICE_USD_PER_MTOK; P4a defines MAX_ROUTE_PRICE_USD_PER_MTOK at :66 and :346 | Fix cite and name everywhere |
| C7-2 | Minor | mutant i5 (L77-78) | Killed only by >28 significant digits; rows a1-a8 do not reach | Add a 29-digit row or mark equivalent |
| C7-3 | Nit | rounding table L80 | ROUND_05UP unnamed; CEILING=UP and FLOOR=DOWN only after sign guard; i10g killers partial | Name them |
| C7-4 | Minor | L71-72 | Same as ADV R7-6: price with >=28 significant digits rounds down before round_cost_up | Cap price decimals, local context, or narrow claim |
| C7-5 | Nit | migration 0006 Files | test_p2_postgres._sql_columns is a regex: one column per line, `\n);` last | Add sentence |
| C7-6 | Minor | memory reserve_spend L162,170 | Same as ADV R7-7: memory Lock self-deadlock class | State helpers do not take the lock or use RLock; A10 covers memory |
| C7-7 | Minor | check_text/check_id | NUL/surrogate strings in test_k5_postgres/round5/round6/p4_secrets/fixes7/8 judged unaffected; k1b_bundle/diagnosis/replay, demo_askdata tests not run | Builder runs these 5 files before/after, adds to re-run list |
Existing tests broken: test_p2_postgres.py:290 (+:31,:61), test_k5_fixes2.py:260-309 (both listed). Verified: 17 fields, cites, lock-to-RLock compatible with tests, migrations 0001-0005 have no FKs, FK lock-mode claim backed by evidence/P4d-fk-lock-probe.md (PG16.15 only).
