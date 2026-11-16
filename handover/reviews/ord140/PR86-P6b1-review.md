# Fresh review: PR86 (P6b1 39b136a)
Reviewer: egm-codebase-details (fresh, read-only, ran nothing). No correctness bug found in the code.
1. MAJOR (open decision): `self_hosted` basis is accepted on any openai_compat host (table.py ~624-632); only the loopback case is tested; comment reads as if the code limits it; README admits it. Options: (a) accept, pin with a test, reword the comment; (b) allow only loopback/private/operator-listed hosts; (c) leave to the client-profile check (P6a).
2. Reviewer said M23b and M31 survived and step logs were missing at 39b136a. REFUTED by the worker: the reviewer read the 9b153d4 evidence; the 39b136a evidence is in the o133 run (mutants 3.12 and 3.13 both "not-killed count: 0"; M31 KILLED by test_t7_non_ascii...; M23b SURVIVED as stated equivalent BN-11; step0-probe, step3-guards, lint, failbefore2 all at 39b136a).
3. MINOR: tests hard-code 90 and 91 (intentional pinning); test_t7 monkeypatches a private name; prod rows of t2 weak positive proof; t6b covers only openai_compat in dev.
4. NIT: README line about the loopback refusal is UNVERIFIED (BN-13).
