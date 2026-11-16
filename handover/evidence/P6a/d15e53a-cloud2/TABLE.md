# PR 72 core/P6a head d15e53a8352079c8a7915f6a520198e9099db933 (cloud2 evidence run, worktree HEAD verified)

FAILED / NOT RUN first:
- full suite 3.12 and 3.13: 1 failed each, tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]. The server-side dblink connects to the default socket /var/run/postgresql/.s.PGSQL.5432, which does not exist on this machine (cluster is on port 55420). Environment only (same row recorded as environment-only earlier, q255); not re-proved on base here.
- perf 3.13: 1 failed in the first run (tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in, timing under load); rerun once alone: 28 passed (perf-313-rerun.txt). Both logs kept.
- NOT RUN: P6a-1 mutants (62 mutants). The by-hand runner (p6a1_mutants_by_hand.py) is not in any repo or on this machine; I did not write a replacement. Needs the builder script.
- NOT RUN: gen_evidence hygiene cell script (not on this machine); hygiene cell here = tools/scan_repo.py only (rc 0, empty output).
- NOT RUN: Vault tests (HADAVIN_TEST_VAULT_ADDR unset; 1 skipped as before). Lint/bandit on 3.13 only. CI/CodeQL/Sonar not run.
- Deviations: bandit via uvx (not in the test group), scope `src demos tools -ll` as ci.yml:178. HADAVIN_REQUIRE_PINNED_UNIDATA=1 only on 3.13 (as CI). First attempt lacked the PG DSN / port and was aborted; its logs are in aborted-first-attempts/ (not evidence).

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos | 3.13 | 0 | all checks passed | ruff-check.txt |
| ruff format --check src tests demos | 3.13 | 0 | already formatted | ruff-format.txt |
| bandit -q -r src demos tools -ll | 3.13 | 0 | no findings | bandit.txt |
| tools/scan_repo.py (hygiene cell) | 3.13 | 0 | no hits | scan_repo.txt |
| pytest tests/test_client_profile.py -q -rA (P6a-1) | 3.12 | 0 | 65 passed | p6a1-client-profile-312.txt |
| same | 3.13 | 0 | 65 passed | p6a1-client-profile-313.txt |
| pytest test_k3_pilot_env + test_k5_round8_postgres (PG) | 3.12 | 0 | 11 passed, 0 skipped | p6a1-pg-312.txt |
| same | 3.13 | 0 | 11 passed, 0 skipped | p6a1-pg-313.txt |
| pytest -m "not live and not perf" (PG DSN set) | 3.12 | 1 | 1 failed, 10510 passed, 1 skipped, 28 deselected | full-312.txt |
| same | 3.13 | 1 | 1 failed, 10510 passed, 1 skipped, 28 deselected | full-313.txt |
| pytest -m perf | 3.12 | 0 | 28 passed | perf-312.txt |
| pytest -m perf | 3.13 | 1 | 1 failed, 27 passed | perf-313.txt |
| pytest -m perf (rerun, alone) | 3.13 | 0 | 28 passed | perf-313-rerun.txt |
| python tests/stage_mutants.py | 3.13 | 0 | 37 of 37 good | stage-mutants-313.txt |
| P6a-1 mutants (62) | - | NOT RUN | - | - |
