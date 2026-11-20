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
