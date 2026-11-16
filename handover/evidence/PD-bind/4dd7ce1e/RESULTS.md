# Evidence run, PD Part 2 (bind guard), round 13. Raw output only; no judgement.

Sha tested: 4dd7ce1e0bf09085be08da5a9fbece45175e54b2 (scratch worktree /home/user/build/er13-bind, removed at the end).
Old trees: 83cdb7a293b7d5ba7d79bedaf3c8990fe99c4ee4, 82dd69c12f506b9484de7e9ec59593fa943b86e7.
Every run printed hadavin_sdk.__file__: the tested tree's own src (see the logs). Venvs: /home/user/build/er13-venv3.13 (Python 3.13.18), er13-venv3.12 (Python 3.12.3), built with `uv sync --all-extras --group test --group dev`. No network use by any test or probe I ran.

## 2. Lint, format, bandit, suppressions (lint.log)
- ruff check: "All checks passed!" rc=0
- ruff format --check: "330 files already formatted" rc=0
- bandit -ll -q -r src demos tools: rc=0. NOTE: bandit is not in the uv venvs; I used the system /root/.local/bin/bandit. It prints "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389" and many "Test in comment: ... not a test name" warnings (not findings).
- Added lines containing noqa / type: ignore / nosec / NOSONAR / pragma in `git diff origin/main...HEAD` (23 files, +12423/-28): 0 (suppress-lines.txt is empty).

## 3. tests/test_bindguard.py at 4dd7ce1e (pytest-bindguard-*.log)
- 3.13.18: 396 passed, 1 skipped in 47.34s, rc=0. Skip: tests/test_bindguard.py:524 "this machine has no IPv6 loopback".
- 3.12.3: 396 passed, 1 skipped in 51.73s, rc=0. Same skip.

## 4. Mutant table: python tests/bind_mutants.py (mut/chunk00..14.log, 15 chunks of 20 ids, 2 lanes, 3.13 venv)
- Table length printed by import: 300 rows (not 71). All 300 ran; 15 chunks, rc=0 for 14, rc=1 for chunk11.
- Outcomes (per-row lines): KILLED 286, CRASH 11, SURVIVED 3, WRONG_REASON 0, other 0. "good" = 297 of 300.
- Not good (re-run alone in mut/rerun-B240-242.log: same result, "0 of 3 good", rc=1, first line empty):
  - B240 the registry of a runtime is not compared  -> SURVIVED (killer test_a_member_of_the_core_runtime_that_is_not_the_one_build_made_is_counted, expect "a replaced registry was not counted")
  - B241 the audit sink of a runtime is not compared -> SURVIVED
  - B242 the limits of a runtime are not compared -> SURVIVED
  (B240-B242 rows are not in DELTA-vs-54c3d8a2.patch lines; mutation edits src/hadavin_sdk/approvals/requests.py `_RUNTIME_SEALED` entries; `_MEMBERS_WALKED = ("limits","audit","registry","_evidence")` is a separate tuple in that file.)
- CRASH rows (marked ok by the runner), list in mut/crash-rows.txt: B6, B22, B30, B59, B123, B153, B157, B175, B195, B197, B201.
- Builder-named rows B279, B280, B290, B291, B292, B293: all present in the table; all "ok KILLED" (B279 row exists although the module docstring says B279 was dropped; B280 is at table index 272, B279 at 280).
- Builder claim "71 of 71": the table has 300 rows; I did not find a 71-row subset.

## 5. Old trees, new tests/test_bindguard.py copied in, old tree's own src, Python 3.13.18 (pytest-old83.log, pytest-old82.log)
- 83cdb7a2: 300 passed, 96 failed, 1 skipped, rc=1
- 82dd69c1: 330 passed, 66 failed, 1 skipped, rc=1

## 6. Hostile inputs (probes/hostile.py; hostile-3.13.log, hostile-3.12.log; the two logs are identical except timings)
Calls bindguard.held_services_found and require_safe_bind(all-zeros address, config of stand-ins only, held=...) with no socket. 93 rows each: 31 odd values x (held directly / as attribute of FakeChannel / as attribute of MemoryStore) plus 6 held-mapping rows. Time per call: every row under 1 s (slowest 0.25 s). SIGALRM 60 s never fired.
- SCAN_NODES in standins.py is 250000, not 10000. Rows over 10,000 (huge_*_10001) were therefore tested, and rows over 250,000 too.
- BindRefused in 82 of 93 rows.
- NO REFUSAL (bind allowed), 8 rows: held-in-FakeChannel-attr and held-in-MemoryStore-attr with huge_list_10001, huge_dict_10001, huge_nested_10001 (6 rows; all under 250000 nodes; found=()); held-many-stand-ins-300 (300 FakeChannel objects; found=()); held-same-stand-in-shared-hostile (one list of 200000 ints shared by two FakeChannels; found=(), 0.25 s).
- Over budget at 250,001 and 1,000,000 values inside a FakeChannel/MemoryStore: refused with label "over budget (too many values to check)". Deep (9, 50, 1000, 100000 levels), cyclic (list, dict, pair): refused, no RecursionError, ~0.00 s.
- Exception escaped the guard: held-direct/metaclass_name_raises (a class whose metaclass __name__ property raises Boom(Exception)): held_services_found and require_safe_bind both raised Boom: name (rows RAISED). All other raising __eq__/__hash__/__len__/__bool__/__getattribute__/__str__ objects (direct, inside stand-ins) were counted and refused, no exception.
- held-mapping-key-raise-hash and held-mapping-key-raise-eq: my own dict construction raised (Boom) before the guard was called, so the guard was not exercised for those two rows (HARNESS rows).
- Not covered: Python 3.14; real sockets/listen(); the approvals receiver serve() path.

## Files / commands NOT run
Full test suite; tests other than tests/test_bindguard.py (the mutant runner itself ran test_bindguard.py, test_netguard.py, test_loopback_sites.py per mutant on 3.13 only); mutant table on 3.12; gitleaks, scan_repo.py, server_scan.py CLI, check-no-handover-files; DELTA-vs-54c3d8a2 per-line checks.
