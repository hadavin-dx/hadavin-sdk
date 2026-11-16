# patch-cloud-1.diff: known-open list (head fix5 535c43e, base 4549a59 = 303127b)

Apply: `git apply handover/demo/patch-cloud-1.diff` (server.py NOT included; hook edits are in CONTRACT-DELTA.md).
Not yet measured on this exact head: ruff/mypy/bandit gate clean (yes, run on fix5), pytest x3 = 6/7/7 failed (known-red list below, one flaky), concurrency x50, load and hostile matrix.

Open findings (round 3 review, handover/demo/reports/cloud-review-3.md), fix6 in progress, will arrive as patch-cloud-2.diff:
- M1 requeue of a `sending` row ignores crm_done<>1 (possible lost email)
- M2 not_sent clears crm_done 2->0 for any unknown row (possible second CRM put)
- M3 backfill of `internal:%` sets crm_done 0 though CRM may have stored it
- M4 poison receipt handling / hint text
- m1-m5 minors (try/finally pop, capability cache on failed refresh, backfill IN-list, review hint, _defer_pending token)
- ORDER 202: 19+ digit item refs rejected in desk core; 503 under bursts (DB lock wait) not yet reduced (keyed 65, blind 124 of 1000 different leads).

Red tests the lead owns/must change: test_flow::test_failed_retry, ::test_retry_twice_concurrent, test_infra::test_demo_adapters, test_mutants::test_mutant_no_claim (intended behaviour changes F4/F6); test_hygiene (2, lead's test file hits); test_server_hardening::test_reply_write_fails_after_commit_followup_still_runs (flaky, also red on unmodified fix3); test_hardening_cloud_b f14 lock-file test (red until the server.py hook edits are applied).
Lead-owned follow-ups: crm_capability in /fake/info; resolve Config.db_path once; contract.md/README rows.
