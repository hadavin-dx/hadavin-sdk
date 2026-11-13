# E3b evidence: lane3-fix-1-r2 (raw run, no judgement)
Patch sha256 b53334fa... verified. Trees: e3b-fix1 (f3c39cf8 + patch), e3b-stack (f3c39cf8 + claims stack + patch); `git add -A` done before tests.

FAILURES AND GAPS FIRST: the e3b-fix1 full suite never ran to the end in one go. Three runs ended with KeyboardInterrupt (exit 2) or SIGTERM (exit 143) from outside the tests (cause unknown: probably a signal from another process on the shared machine; the stack run was not hit). No test failed in any run. Pytest has 3892 tests on the stack tree; 3196+ passed before the stop at 86% of run 1.

| tree | scope | passed | failed | skipped | errors | wall | exit |
|---|---|---|---|---|---|---|---|
| fix1 | tests/test_docs_claims_lane3.py | 9 | 0 | 0 | 0 | 2s | 0 |
| fix1 | tests/test_hygiene.py | 20 | 0 | 4 | 0 | 41s | 0 |
| fix1 | FULL run1 (interrupted at 86%, test_server_hardening) | 3196 | 0 | 184 | 0 | 1115s | 2 |
| fix1 | FULL run2 (SIGTERM at 5%) | few | 0 | - | 0 | 107s | 143 |
| fix1 | FULL run3 (interrupted at 67%) | 2584 | 0 | 56 | 0 | 743s | 2 |
| fix1 | tail run: the 18 test files from test_server_hardening.py to the end | 512 | 0 | 16 | 0 | 95s | 0 |
| stack | tests/test_docs_claims_lane3.py | 9 | 0 | 0 | 0 | 2s | 0 |
| stack | tests/test_hygiene.py | 20 | 0 | 4 | 0 | 41s | 0 |
| stack | FULL | 3692 | 0 | 200 | 0 | 1142s | 0 |

Stack difference to baseline 3683: +9 (the new file's 9 tests). Skips 200 = baseline 200.
Hygiene skips (both trees, gitleaks missing): test_hygiene_scan_public, test_gitleaks_reports_a_carriage_return..., test_lock_file_hashes_are_allowed_only_at_the_root, test_a_relative_gitleaks_path_still_works.... The 20 hygiene tests that ran passed with the new files staged.
fix1 full total NOT proven as one run: run1 + tail cover everything (overlap only in test_server_hardening), with 0 failures, but that is a union of partial runs. Next step: rerun fix1 full alone on a quiet machine.
Logs: evidence/raw/ (fix1-*, stack-*). Time at finish about 14:13Z.
