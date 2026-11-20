# Step D (signed trigger endpoint and worker): tested state after d-fix4, 2026-11-20T08:48Z
- tests/triggers, default order, PostgreSQL 16, builder run: 1182 passed, 5 skipped, 0 failed (raw/D-fix4-tests.log; HADAVIN_REQUIRE_PG was NOT set in that run)
- mutant script run 14 on this tree: 89 killed, 1 crash-accepted (G20j), 0 known survivors, 90 of 90 as expected (raw/endpoint-mutants-run-14.log)
- ruff check and format clean on the changed files and on handover/core-a/inputs
- review: step D code 3 fresh rounds (round 3 left E7: lead decided keep stdlib server); extra fresh pass D-rev4 running
- strict mode: HADAVIN_REQUIRE_PG=1 now fails the core-b-config tests at test time (tests/triggers/test_t5_strict_mode.py), no collection error
- NOT yet: independent batch6 (whole suite, combined tree with n8n/), real Windows run, real n8n run (lead runs it)
sha256:
8ff23e60491745b59f2840d04d516179300edbc8eecca18d619812ce8a2131cf  triggers/__init__.py
9654c455859897220fa1f31a2c23acfbf3eb6b5fb369aa8a4d25da9086e3356e  triggers/endpoint.py
8cd743ed0552a4d7ef3c058cbd0634f00b5be9edd9160dbfcc368bafea883e84  triggers/server.py
803bf93317dff87e93a1af768e95cfaa82c7253130109af758053bbfb08a7b37  triggers/worker.py

## Update 09:50Z: D with E1 (conflict audit, /health, recovery) and E with 7 review rounds
- tests/triggers + tests/test_testing_crash.py, -n 3, PG16, builder run: 1352 passed, 5 skipped (raw/D-fix8-tests.log). Step E: 7 fresh rounds, round 7 found no Blocker/Major (reviews/E-result-review-7 = round 7 text in board; E-result-review-5/6.md).
- NOT yet: mutants for E1 (script run 17), fresh review of the E1 code, independent batch (BATCH8). Last independent whole-suite batch (BATCH7) was before E1.
sha256:
8ff23e60491745b59f2840d04d516179300edbc8eecca18d619812ce8a2131cf  triggers/__init__.py
fdd9ae116d6add8229daefdae674975d80582fa9528bf693c3d65b86a804651f  triggers/endpoint.py
8cd743ed0552a4d7ef3c058cbd0634f00b5be9edd9160dbfcc368bafea883e84  triggers/server.py
ad69f85b402fcd5217e89f5e1c36c6e9ce6360978f6a9be954e2427e1b15eb95  triggers/worker.py
ebf79b05cc0bd9131b7121c494155e6934cdd812c5fbdc8a5322861b982551df  testing/crash.py
