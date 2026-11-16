# Hand-off v15 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16T16:59:44Z
Raw: audit-r460/evidence-handoff-v15-independent/00-SUMMARY.md. Recorded, not judged. PostgreSQL 16.15 only (17.10 and below 16 not run).
Deviations: reader SELECT grant and REVOKE TEMPORARY applied by harness (held files contain neither; audit_read code does not exist in src/); ~55 min vs 45 box.
Passes: held-sql sha256 3 of 3 match; own suite 122 PASS 0 FAIL; builder pg_run_v15 93 of 93 rc 0; default CHECK refuses negative INSERT..ON CONFLICT (23514); variant refuses -0.01/NaN/+-Infinity; SECURITY DEFINER with search_path pg_catalog, pg_temp; PUBLIC no EXECUTE; temp-table attack fails; REVOKE TEMPORARY gives 42501; lock timeout 55P03 after 5.0 s; 35 of 35 planted mutations caught (3 search_path mutants only by static check; TG_TABLE_SCHEMA non-public not tested).
Cites: 402 found; sample 60: 49 HIT, 1 NEAR, 8 MOVED, 2 NOANCHOR, 0 MISSING; of 55 MOVED, 3 weak: config.py:400-415 (date/null rule not in range), chain.py:171 (no claim), config.py:346 (word-list only).
Banned scan 0 of 26 files. Not checked: migrate()/GRANTS product code, set_config timeouts, real parallel load.
