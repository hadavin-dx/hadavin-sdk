# Step D (signed trigger endpoint and worker): tested state, 2026-11-20T08:40Z
Code at this commit's parent tree (the board script had already committed it as WIP snapshots; this commit marks the tested state).
- tests/triggers, default order, PostgreSQL 16, own builder run (d-fix4): 1182 passed, 5 skipped, 0 failed (handover/core-a/raw/D-fix4-tests.log)
- ruff check and ruff format clean on the changed files; handover/core-a/inputs ruff clean
- mutant script: run 13 on the previous tree 90 of 90; run 14 on this tree: see raw/endpoint-mutants-run-14.log (running when this was written)
- NOT yet: independent evidence batch on this tree (batch6), the whole suite on this tree, a real Windows run, a real n8n run
- review: step D code three fresh rounds (round 3 left E7 for the lead)
sha256:
8ff23e60491745b59f2840d04d516179300edbc8eecca18d619812ce8a2131cf  triggers/__init__.py
9654c455859897220fa1f31a2c23acfbf3eb6b5fb369aa8a4d25da9086e3356e  triggers/endpoint.py
8cd743ed0552a4d7ef3c058cbd0634f00b5be9edd9160dbfcc368bafea883e84  triggers/server.py
803bf93317dff87e93a1af768e95cfaa82c7253130109af758053bbfb08a7b37  triggers/worker.py
