# Linux final-gate evidence, trees A and B (order 212, record only)
Raw files: `linux-final-treeA-5d352f7302dd/`, `linux-final-treeB-a5cf0b3d0eec/` (gate.txt, conc.txt, arrival.txt, final-gate report and raw stage files). Clock: chain ended 17:55Z (23:25 IST).
Pytest, three runs per tree, read from the raw stage files:
- Tree A (5d352f7302dd): run 1 and 2: 7 failed, 595 passed; run 3: 6 failed, 596 passed.
- Tree B (a5cf0b3d0eec): run 1 and 2: 7 failed, 644 passed; run 3: 8 failed, 643 passed.
- Failures common to all runs (known-red list): test_flow::test_failed_retry, test_flow::test_retry_twice_concurrent, test_hygiene (2: no gitleaks, no word list), test_infra::test_demo_adapters, test_mutants::test_mutant_no_claim.
- Differences between runs: test_server_hardening::test_reply_write_fails_after_commit_followup_still_runs failed in 5 of 6 runs (passed in tree A run 3); tree B run 3 also failed test_portal_api::test_lead_id_grammar_checked_before_db (once in 6 runs; not looked into). The known-red list also has test_hardening_cloud_b::test_f14_lock_file_unopenable; it did not fail here (these runs may be as root).
Concurrency (20 runs each): same_source_ref, ten_parallel, reconcile_counts 20/20 pass; test_retry_twice_concurrent 0/20 pass in both trees (known red).
Arrival (blind mode, tree A and B alike): mixed50 100 requests all 201, 50 leads, 50 CRM rows, 50 emails, lost_receipt 0; rate 5/s for 60 s: 300 requests all 201, 300 CRM rows, 300 emails, lost_receipt 0.
Not judged here. Open: the one-off test_lead_id_grammar failure needs a look.
