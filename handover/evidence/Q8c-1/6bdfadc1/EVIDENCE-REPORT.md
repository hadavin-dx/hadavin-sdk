# Q8c PR 1: independent raw evidence, branch head 6bdfadc1 (fix batch 2)

EVIDENCE RUNNER record (Sonnet 5.5). I ran and recorded; I did not judge, fix or edit src/tests; nothing committed or pushed. Run 2026-11-11, about 16:52 to 17:07 UTC (22:22 to 22:37 IST), 15 minutes wall clock. Head `6bdfadc139e23f8d80627c849c4e1c033917622e` (3 commits over origin/main 2a8c2aac). Python 3.13.18, PostgreSQL 16.15 (own cluster, port 56421, started as the postgres user with PGHOST=127.0.0.1 and PGPORT=56421 in the server's own environment). Every test command ran with the nine cloud/token variables removed.

## 0. What failed, what was NOT run (read first)
1. Nothing failed in the commands I ran. Full suite exit 0: 10817 passed, 13 skipped, 28 deselected (275.85 s). The demo_askdata dblink test passed this time (Postgres started with PGHOST/PGPORT).
2. The 12 Vault engine tests were NOT run (they skipped: no HADAVIN_TEST_VAULT_ADDR, no vault/bao/openbao binary; I downloaded nothing). 13th skip: tests/contracts/test_llm.py:95. Nothing here shows a real Vault server refuses or allows anything.
3. NOT run: CodeQL, SonarCloud, CodeRabbit, CI; any Kubernetes cluster; re-fetch of the source rows (V-ACL, V-PARSE, B-ACL, V-KV, B-KV, V-TR, B-TR, V-POL, B-POL) and of the `+` quotations (not in my brief).
4. Section (5) of my brief: the two review files (result-r2-design-full.md, result-r2-codebase-full.md) name NO hostile check commands: both state the reviewer ran nothing. So I re-ran my own earlier probe scripts (renderer probes, 32 plants) from the a77fab7 report unchanged in intent; see rows 7 and 8.
5. Plants: 32 of 32 caught. Process note: my plants harness was killed twice mid-run by the tool session ending (not by the code), once with a plant left applied; I restored the plants worktree with git checkout, and re-ran A11-A21 and A22-A32 from a clean tree. Final `git status` of the plants worktree is clean. A01-A10 ran in the first part, A11-A21 in part 2, A22-A32 in part 3 (files 08-plants.txt, 08-plants-part2.txt, 08-plants-part3.txt; merged one-line-per-plant in 08-plants-all.txt). One A11 result appears in an aborted run too (16 failed) and in the clean re-run (13 failed); the clean re-run is the one counted.
6. Fail-before (row 5): in my copies of the old trees I overlaid head's test files, head's tests/policy_mutants.py, head's tools/policy_page.py and head's sources fixture, but NOT head's docs/declared-permissions.md (old tree keeps its own), so docs-comparison failures on old trees may come from the docs file and not only from src.
7. Secret-shaped test names: 02-full.xml (junit) contains made-up, pre-existing parametrized ids (fake keys, tokens and a private-key header, built to test the secret scanner); the examples are not repeated here so this report passes the secret scan. 02-full.xml is kept out of the push.

## Table
| # | Command / probe | Exit | Result | File |
|---|---|---|---|---|
| 1 | head sha | 0 | 6bdfadc139e23f8d80627c849c4e1c033917622e | 01-head-sha.txt |
| 2 | `pytest -q -m "not live and not perf" -rs --junitxml` via heavy.sh, own Postgres | 0 | 10817 passed, 13 skipped, 0 failed, 28 deselected; junit tests=10830, failures=0, errors=0; 275.85 s (16:55:46 to 17:00:24 UTC) | 02-full.log, 02-full.xml, 02-skips.txt |
| 3a | ruff check | 0 | All checks passed | 03-gates-output.txt |
| 3b | ruff format --check | 0 | 328 files already formatted | same |
| 3c | bandit -ll -r src tools | 0 | No issues identified; Low 12, Medium 0, High 0; (3 nosec skipped as before) | same |
| 3d | tools/scan_repo.py | 0 | no output | same |
| 3e | tools/policy_page.py --check | 0 | no output | same |
| 3f | gitleaks detect, log-opts origin/main..HEAD | 0 | 3 commits scanned, no leaks found | same |
| 4a | tests/policy_mutants.py (heavy.sh, own worktree EV-Q8c1-r3-mut) | 0 | 45 of 45 good; problems []; it also printed "first-line check is weak (killer asserts through same()) for 35 of 45 mutants" and 2 killers shared by more than one mutant (p09a, overdue-entry) | 04-policy-mutants.txt |
| 4b | tests/stage_mutants.py (heavy.sh) | 0 | 37 of 37 good; problems [] | 04-stage-mutants.txt |
| 5 | fail-before: test functions new or changed vs a77fab72 (26 functions, AST differs; 55 cases), head tests over old trees | 1 (expected) | over a77fab72 tree: 8 failed, 285 passed, 12 skipped (all 3 files, 305 cases); among the 55 new/changed cases: 4 failed, 51 passed. Over origin/main tree: 187 failed, 106 passed, 12 skipped; among the 55: 11 failed, 44 passed | 05-fail-before.txt, fb-prev.log, fb-main.log, 05-fail-before-new-tests-that-pass-on-old.txt (lists the functions whose cases ALL pass on each old tree: 20 on a77fab72, 15 on main) |
| 6 | Vault-compatible server | n/a | NOT RUN: no binary | - |
| 7 | renderer probes, 225 values (script probes/probe_render.py) | 0 | 21 accepted, 204 refused; the accepted list is identical to the a77fab7 run (diff of label+verdict empty): mounts `kv/sys`, `system`, `sysx`, `kv/nested/mount`; namespace `kube`, `default` (as namespace and as ServiceAccount namespace); 63-char namespace; 253-char role name; `reader`; `ok-sa`; two namespaces | 07-renderer-probes.txt |
| 8 | plants (32) against tests/test_policy_guard.py (baseline 284 passed each time) | 1 each | 32 of 32 caught (pytest exit 1 each, failing counts 1 to 131); tree clean after every restore; `policy_page.py --check` exit 0 on 23 plants, exit 1 on 9 (data-literal plants A08, A09, A10, A16, A21, A22, A29, A30, A32: "docs/declared-permissions.md differs from the data") | 08-plants-all.txt (+ -part files) |
| 9 | wall-clock | - | whole run about 15 min (16:52 to 17:07 UTC); full suite 4 min 36 s; policy+stage mutants 17:04:40 to 17:05:49 (69 s); heavy.sh slots were held by other agents for about 3 min before my full suite started | EV checkpoint /home/user/build/EV-Q8c1-r3-checkpoint.md |

## Fail-before detail
New or changed test functions (AST differs from a77fab72): 26 (names in the first line of 05-fail-before-new-tests-that-pass-on-old.txt). Of their 55 collected cases, over the a77fab72 tree only 4 fail (the others pass because they are guard-rule tests that live in the test file and pass on old src; the builder named mutants as their proof). The old-tree runs used head's tests with PYTHONPATH to the old tree's src. The builder's own number (8 failed, 279 passed in guard+docs over a77fab72) agrees with mine (8 failed, same 8 fails; mine adds the engine file's 12 skips).

## Not planted by me
Same as before: run-time module load by name from unrecognised text; the `self.mount`-to-setting map through `build`. I did not plant the new batch-2 items (sender pin, query-name regex, `.call` allowlist); policy_mutants covers 4 new mutants (45 vs 41).

## Cleanup
My Postgres (port 56421) stopped and its data folder removed; no process of mine left (checked with ps/pgrep). Worktrees left in place: /home/user/build/EV-Q8c1-r3, -mut, -plants (all clean per git status), and the export dirs EV-Q8c1-r3-fb-main, EV-Q8c1-r3-fb-prev. Raw logs: /home/user/build/evidence-raw/Q8c1-6bdfadc1/. Scripts: probes/ (failbefore.py, plants.py, probe_render.py) and /home/user/build/EV-Q8c1-r3-{env,full,mut,fb}.sh. Evidence files are untracked in the main checkout.
