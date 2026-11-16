# Q8c PR 1: independent raw evidence, branch head a77fab7 (fix batch 1)

EVIDENCE RUNNER record (Sonnet 5.5). I ran and recorded; I did not judge, fix or edit src/tests. Run 2026-11-11, about 16:21 to 16:45 UTC (21:51 to 22:15 IST).
Head `a77fab727f8435177a9c4789ba63c9c4218c5c57` (2 commits over origin/main). Python 3.13.18, PostgreSQL 16.15 (own cluster, port 56291, socket dir /tmp). Every test command ran with the nine cloud/token variables removed. I read the builder's PR notes for commands only.

## 0. What failed, what was NOT run (read first)
1. **Full suite: exit 1, 1 failed, 10777 passed, 13 skipped, 28 deselected.** The failure is `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`: `dblink_connect('dbname=postgres')` inside my server tried the DEFAULT socket `/var/run/postgresql/.s.PGSQL.5432`, which my cluster (port 56291, socket in /tmp) does not provide. Same single test alone: head exit 1, clean origin/main exit 1 (`rerun-dblink-*.log`). Machine setup, not this branch's files; I state no further cause.
2. **Vault server tests (12) NOT RUN.** `which vault bao openbao` and a search of the file system for executables named vault/bao/openbao found none; I downloaded nothing. All 12 engine test cases that need a server were skipped (see section 2). Nothing here shows a real Vault refuses or allows anything.
3. CodeQL, SonarCloud, CodeRabbit, CI not run (pull-request side). No Kubernetes cluster used.
4. Plants: all 32 of mine were caught by `tests/test_policy_guard.py` (none un-caught). Not planted by me: dynamic module load by name from unrecognised text; the `self.mount` attribute-to-setting map through `build` (builder's own stated limits).
5. Renderer: accepted-and-printed cases that a reader may care about are listed in section 7 (e.g. mount `kv/sys`, `system`, `sysx`; namespace `kube`, `default`; two namespaces).
6. gitleaks printed nothing (exit 0). Source hashes of the new rows (V-ACL, V-PARSE, B-ACL) and the `+` quotations were NOT re-fetched by me (no fetch task in the brief).

## Table
| # | Command / probe | Exit | Result | File |
|---|---|---|---|---|
| 1 | head sha | 0 | a77fab727f8435177a9c4789ba63c9c4218c5c57 | 01-head-sha.txt |
| 2 | `pytest -q -m "not live and not perf" -rs` via heavy.sh, with Postgres | 1 | 1 failed, 10777 passed, 13 skipped, 28 deselected, 354.5 s | 02-full-suite-failures-and-skips.txt, 02-full.xml |
| 3a | ruff check | 0 | All checks passed | 03-gates-output.txt |
| 3b | ruff format --check | 0 | 328 files already formatted | same |
| 3c | bandit -ll -r src tools | 0 | No issues identified; Low 12, Medium 0, High 0; 17480 lines | same |
| 3d | tools/scan_repo.py | 0 | no output | same |
| 3e | tools/policy_page.py --check | 0 | no output | same |
| 3f | gitleaks origin/main..HEAD | 0 | no output | same |
| 4a | tests/policy_mutants.py (heavy.sh, own worktree) | 0 | 41 of 41 good; problems: [] | 04-policy-mutants.txt |
| 4b | tests/stage_mutants.py (heavy.sh) | 0 | 37 of 37 good; problems: [] | 04-stage-mutants.txt |
| 5 | fail-before (3 files: guard, docs, engine; 54 test functions new vs 7af13809, 171 cases) | n/a | see section 5 | 05-*.txt, fb-*.log |
| 6 | Vault-compatible server | n/a | NOT RUN: no binary | - |
| 7 | renderer probes, 225 hostile/baseline values | n/a | 21 accepted, 204 refused | 07-renderer-probes.txt |
| 8 | plants (32) | n/a | 32 of 32 caught (pytest exit 1 each), tree restored each time | 08-plants.txt |

## 2. Skips (13)
12 engine test cases (tests/test_policy_engine.py lines 244, 252, 260, 274, 286, 299, 358, 371 (x2), 386, 398, 410 = 12 cases): "needs a real Vault server (HADAVIN_TEST_VAULT_ADDR is not set): the local fake enforces no policy, so a refusal there would show nothing. CI runs these against its Vault service and requires them." Plus `tests/contracts/test_llm.py:95` "Stubber refuses a malformed Converse shape before the kind sees it". (12 + 1 = 13.)
The earlier timing failure (`test_the_timing_harness_flags_a_quadratic_stand_in`) did not occur this time.

## 5. Fail-before (raw counts; files test_policy_guard/docs/engine at head, over each old tree)
| Tree under test | exit | result (all 266 cases) | among the 171 cases of the 54 new test functions |
|---|---|---|---|
| 7af13809 complete tree + head tests | 1 | 133 failed, 121 passed, 12 skipped | 116 failed, 54 passed, 1 skipped |
| origin/main + head tests + head tools/policy_page.py | 1 | 185 failed, 69 passed, 12 skipped | 119 failed, 51 passed, 1 skipped |
| head with only the 3 src files put back to 7af13809 | 1 | 31 failed, 223 passed, 12 skipped | 18 failed, 152 passed, 1 skipped |
New test functions that still PASS on the old trees are listed in `05-fail-before-new-tests-that-pass-on-old.txt` (e.g. on 7af13809: the import-list, other-module-uses-client, indirect-way, p09a and "old everything-below-prefix" plants). "New" is by test function name vs 7af13809; I did not judge whether a passing one is meaningful.
Method: git archive of each tree; head's test files copied over; PYTHONPATH to that tree's src.

## 8. Plants (against tests/test_policy_guard.py, 245 tests baseline all passed; `tools/policy_page.py --check` exit 0 on every plant)
All 32 plants: pytest exit 1, tree clean after restore. Failing-test counts per plant are in 08-plants.txt (smallest: A32 never-list `sys/*`->`sys/+` 1 failed; A24 follow=true 5; A18-A20 6). Includes: extra path, query string, deeper path under declared id, import httpx, methodcaller, attrgetter, getattr literal, computed getattr, vars(), `+*`, `*` capability, old star form, DELETE verb, urlopen, opener, transit rotate/decrypt/suffix/wide, k8s watch/follow/secrets path/DELETE/import requests/unquoted/verb `*`/resource `*`/getattr.
Note: plants ran with PYTHONPATH to the plants worktree src; `page --check` could not catch any (exit 0 each) because it checks the data literal, not code.

## Files
Everything in this folder; raw logs in /home/user/build/evidence-raw/Q8c1-a77fab7/; probe scripts in probes/. Worktrees /home/user/build/EV-Q8c1-a77fab7{,-plants,-mut}, fb-* dirs left in place.
