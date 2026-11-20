# ANSWERS-1700 (core-a, to the lead's 17:00 order)
Real state at 1700 UTC: /proc/loadavg 1.64 (1 min); 1 pytest/mutant processes; agents running: integ3, A4-B8-text.
- A1 docs for core-c: DONE (wip/core-a-for-c-docs 8df581d45, reviewed).
- A2 review of core-b 9b7610007: DONE (reviews/rev-b-9b76.md, rev-b-MTA.md; handover/core-b/requests/xr-from-core-a-3.md).
- A3 dry-run 3: RUNNING (integ3, PG16 runs; pushes core/integration-dryrun with conflicts resolved, T1 file = core-b's).
- A4 B8-text: RUNNING (A4-B8-text; handover/core-b/requests/from-core-a-B8-text.md when done).
- A5 open D/E fix passes: NONE open.
- A6 mutant run: run 19 DONE 120/120 (5a8c83fd3); run 20 on the current head RUNNING (/tmp/mut-run20.log).
Also done since 16:55: reviews rev-c-G4d (no Blocker/Major), rev-c-G12d (no Blocker; 2 Major + 1 perf), rev-lead-tswm-3 (no Blocker/Major).

## UPDATE 17:06: A3 dry-run 3 DONE
core/integration-dryrun pushed c47b08bec (core-b 3f4ebb67e + core-a bc6b400cb + core-c d53d6e7d1; handover/ excluded; conflicts resolved: core-a step 1 (T1 kept core-b's), core-c step 7 (CHANGELOG, README, SECURITY, defaults.py, producers.py, conftest.py, T1)). PG16 strict: triggers 1379 passed 0 failed; contracts 1623 passed 21 failed (core-c: 19 in test_t1_reserve_cap_core_c.py, 2 in test_model_gate_contract point4: settle without agent_id / direct SQL on spend_reservations); grants/mutants 308 passed 11 failed (mine: test_grants_negative_0007.py, new 'release' role; fix agent grantfix2 running). DECISIONS for the lead: SECURITY.md of core-c vs core-b's two sections need a topic merge; one canonical T1 file out of three. The door crash_launcher is correct on cloud/core-a (conflict_events_per_minute at line 175); only the stale branch wip/core-a-door-merged lacks it: ignore that branch. Details: INTEGRATION-DRYRUN-2.md "Dry-run 3".
