# EVIDENCE RUNNER results Q8c1r7, package Q8c-1, head d598d96703b2fab4e5fb754e7e4953b8024a7bd3
Recorded, not judged. Nothing was fixed. Head confirmed with `git rev-parse HEAD`; tree clean. Raw logs: /home/user/build/evidence-raw/Q8c1r7-d598d967/.

## What failed or was not run (first)
- `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` FAILED 6 of 6 runs alone with all 3 slots held (3 on head, 3 on origin/main), each "a quadratic function must be flagged". Not intermittent here. The test is marked perf, so the full run deselected it (28 deselected).
- The 12 Vault engine tests were NOT run against a server (no Vault server; no binary downloaded, as told). With HADAVIN_REQUIRE_VAULT_ENGINE=1: 8 passed, 12 errors (all "HADAVIN_TEST_VAULT_ADDR is not set"). Without it: 8 passed, 12 skipped.
- Fail-before on the strict rule (only new or changed test files copied, src and tools from the base): collection errors, 3 errors on 5015c990, 4 errors on origin/main (the tools module `policy_page` has no `PENDING_NAMES` / does not exist on the bases). A second run that also copied head's `tools/policy_page.py` and `docs/declared-permissions.md` is below.
- policy_mutants exit code was not captured (run started in the background through heavy.sh); the log shows the final lines below.
- Not run: perf runs (ticket names no perf item), live model calls, CI services (CodeQL, SonarCloud, CodeRabbit).

## Table
| Item | Command (short) | Result |
|---|---|---|
| 1 changed files | `git diff --name-only origin/main...HEAD` | 14 files: ci.yml, CHANGELOG.md, README.md, docs/declared-permissions.md, secrets_vault.py, signer_vault.py, sources/kubernetes.py, tests/fixtures/policy_sources_2026-11-11.txt, tests/policy_mutants.py, tests/test_policy_{changelog,docs,engine,guard}.py, tools/policy_page.py |
| 2 ruff | `ruff check` / `ruff format --check` src tests demos tools | exit 0 "All checks passed!" / exit 0 "324 files already formatted" |
| 3 bandit | `bandit -q -r src demos tools -ll` | exit 0 (only a nosec B102 warning on src/hadavin_sdk/tools.py:389) |
| 4 scan_repo | `python tools/scan_repo.py` | exit 0 |
| 4 stage mutants | `python tests/stage_mutants.py` | exit 0 "37 of 37 good; problems: []" |
| 4 gitleaks | `gitleaks git ... origin/main..HEAD` | exit 0 "no leaks found" |
| 5 full pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own Postgres port 56150) | exit 0 (no failures in log) "10876 passed, 13 skipped, 28 deselected in 271.86s". 13 skips: 12 Vault engine (no server) + 1 contracts/test_llm.py. Queue wait before start: about 1 h of wall clock |
| 6 policy_page | `python tools/policy_page.py --check` | exit 0 |
| 6 policy mutants | `python tests/policy_mutants.py` | "103 of 103 good; problems: []"; also prints "first-line check is weak (killer asserts through same()) for 41 of 103 mutants; killer shared by more than one mutant: [...]" |
| 6 vault engine | `HADAVIN_REQUIRE_VAULT_ENGINE=1 pytest tests/test_policy_engine.py` | exit 1: 8 passed, 12 errors (no server) |
| 9 timing test | alone under 3 slot locks, 3x head, 3x main | 6 failed of 6 (see top) |

## Item 7: fail-before (4 test files of the diff: changelog, docs, engine, guard; plus fixture)
| Base | Test files only | Test files + head's tools/policy_page.py + docs page |
|---|---|---|
| head | 352 passed, 12 skipped | same |
| 5015c990 | 3 collection errors (AttributeError PENDING_NAMES), test_policy_engine.py collected | 18 failed, 334 passed, 12 skipped |
| origin/main | 4 collection errors (cannot import policy_page) | 233 failed, 119 passed, 12 skipped (no POLICY in the three kind modules) |
Lists: `fails-on-old-5015c990.txt`, `fails-on-main.txt`, `passes-on-old.txt` (334 tests that pass on 5015c990), `passes-on-main.txt` (119).

## Item 8: own probes of the claim-mark rules (`python tools/policy_page.py --check`, run on a scratch copy; edits typed by me)
Full output: `probes-head.txt`, `probes-old.txt`. Exit codes (head | 5015c990):
| Probe | head | 5015c990 |
|---|---|---|
| baseline | 0 | 0 |
| a1 clause appended to R17 claim in the module | 1 (0 marks, R17 unmarked, stale head text) | 1 only "page differs from the data" |
| a2 clause appended to R17 claim in the head line | 1 (0 marks, stale text) | 1 (0 marks, stale start) |
| b swap R17 and R18 marks | 1 (both entries named) | 1 (R18 has 2 marks) |
| c1 start of R17 claim also under nobody-read | 1 ("matches no claim: delete it") | 1 (2 marks) |
| c2 start of R18 claim also under builder-read | 1 (matches no claim) | 1 (2 marks) |
| c3 full R17 text under both marks | 1 ("is under both marks") | 1 (2 marks) |
| d0 BOM at file start | 0 (accepted) | 1 traceback |
| d1 BOM before the first data row | 1 (id '﻿V-POL' not a source id) | 1 traceback |
| d2-d5 BOM before BUILDER-ONLY / PARTLY / CLAIM-BUILDER / CLAIM-NOBODY line | 1 each, "a row has five columns" at that line | 1 traceback each |
| e1 / e2 trailing " ;;" on builder / nobody line | 1 each ("holds ;; inside a claim text") | 1 each ("claim start ... matches no claim") |
| e3 trailing " ;; " (with space) | 1 ("empty claim text") | 1 traceback |
| e4 trailing ";;" no space | 1 ("holds ;;") | 1 |
| f1 NOTE_CLASSES entry () | 1 (class not a non-empty tuple) | 1 ("matches no note") only |
| f2 ("claim", 5) / f3 ("claim", "") | 1 each (needs exactly one non-empty text) | 1 ("matches no note") only |
| f4 key not a pair | 1 (key not a tuple of two texts) | 1 traceback |
| g1 R17 grant verified None, no pending row | 1 (no PENDING_NAMES entry) | 1 only "page differs" |
| g2 R18 grant verified None, no pending row | 1 (no PENDING_NAMES entry) | 1 only "page differs" |
"traceback" = the 5015c990 tool ended with a Python traceback instead of one problem line. Probes d1-d5 on the head give exit 1 with a message about a row, not about a byte-order mark.
