# A21a round 2, egm-codebase-details, snapshot head 98a3ed9. Saved by the cloud session from the reviewer's inline report (read-only, ran nothing).
Verdict: no Blocker; one Major; round-1 fixed except small remainders. Mutants L1-L10, S1-S8, P1-P11 killed for the right reason (expect texts match real assert messages); weak but acceptable: L10 expect "calls for cap", P3/P4 share "read at", P5/P6 share one message. DSN guard sound (pg_schema pytest.fail when CI == "true").
MAJOR M1 (tests/contracts/test_t1_meter_cap.py near line 95): no test or in-repo note for NaN/negative/Infinity charges (only ledger row + untracked seed). Fix: parametrized contract test over Decimal("NaN"), Decimal("-1"), Decimal("Infinity") pinning today's behaviour on both stores, marked as a pin A21b flips (baseline pin asked by LEAD-ORDERS.md:748); at least a docstring pointer to BL-core-a21b-seed-01.
m1 wording/private refs: meter_support.py:8, test_t1_meter_cap.py:8-9, meter_mutants.py:11; bare labels T1/T2 at test_store_time_rules.py:1, meter_mutants.py:1.
m2 meter_support.py:149-174 Schedule.decided_and_wait ignores cond.wait_for result: assert it ("not every caller reached the decision point"); check the 3 stub controls still pass.
m3 meter_support.py:81-85 docstring names registry.load; real function is load_registry(config).
m4 postgres_mutants.py:238 IndexError on empty output; return early with exit 1 when the baseline fails; catch TimeoutError from _run_pytest in main and print the mutant.
m5 missing case: daily or monthly budget "0" must block the first call; add one parametrized case.
m6 meter_mutants.py lists L10 before L9 (cosmetic).
Evidence: folder name ba89ea7-builder-r2 vs head 98a3ed9 in TABLE.md disagree; rename or say so. Flaky 3.13 failure tracked as w2-18; should not block once the independent check shows it fails on main too.
Not checked: any run; tools/mutation_runner.py; store/postgres.py and SQL anchors; schema checks; other pg_schema users; full DIFF.patch beyond file list.
