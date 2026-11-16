# S1d report (builder S1d, duplicate-proof-lead-desk, round 3 fixes)

Work tree: /tmp/dpld-s4 (copy of /home/user/build/snap/A4r3). Diff: /home/user/build/S1d.diff (17 files, a/ b/ paths, apply-checked with `patch -p1` on a fresh copy of A4r3: trees identical). Full log: /home/user/build/S1d-full.log. Fail-before: /home/user/build/S1d-failbefore.txt. Checkpoints: /home/user/build/S1d-checkpoint.md.

## What failed, was not done, or is uncertain (first)
1. bandit -ll was NOT run: it is not installed in this container.
2. Fail-before proof is weak for part of the new tests: on the old source, 32 failed, 37 passed, 1 skipped, 70 errors. Most of the 70 errors and many failures are AttributeError on the new constants, not behaviour differences. Behaviour-level failures exist for eviction by stall, the reply write deadline, the non-blocking busy refusal, stop/start/stop/start (two reapers), SIGTERM and fd exhaustion, but a reviewer should not read "102 red on old code" as 102 behaviour proofs.
3. Design deviation from the task text: at start-up the soft RLIMIT_NOFILE is raised to the needed value when the hard limit allows it, and only if the hard limit is too low does main() refuse (exit code 3). A pure "refuse" would reject the default 1024 threads on a usual soft limit of 1024.
4. Known property of the non-blocking `_refuse_busy`: it drains only bytes already arrived. Bytes that arrive after the refusal can still make the operating system reset the connection. contract.md says so. `test_busy_503_is_complete_and_clean` was made tolerant of that; `test_refuse_busy_drains_arrived_bytes` covers the deterministic case.
5. Not done (listed, not hidden): C2 (thin wall-clock bounds), C10, C13 to C17, the "old server failed all of them" and "lead order 219" docstring claims (nothing in the tree to check them), the test that binds a real desk to the wildcard address (E4, second half), and the items F6, F8, F9, N8 from the former CONTRACT-DELTA fix 7, which stay open.
6. C4/C5 (slow tests unmarked): skipped because pyproject.toml defines no slow marker.
7. Full suite result is for this Linux cloud container (Python 3.13.18) only, not Windows. The README states that the earlier Windows runs predate these fixes.
8. R-numbers: the studio bible is not available in this cloud container, so no R-number is cited. EGM review: lead runs it.

## Evidence
* Full suite, run once, detached: `PYTHONPATH=src:tests:. /root/.local/bin/pytest -p no:cacheprovider -q > S1d-full.log` -> `2 failed, 663 passed, 1 skipped in 332.76s`. The 2 failures are the expected ones: `test_hygiene_scan_public` (no gitleaks) and `test_hygiene_wordlist` (no private word list). The skip is the load-measurement test that needs LEAD_DESK_LOAD_N. 666 test cases, 19 test files (README said 17).
* Gates after the last edit: `ruff check .` all passed; `ruff format --check .` 53 files already formatted; `mypy --strict src/lead_desk/server.py constants.py desk.py` no issues in 3 files. (A one-line E501 in a tests/test_flow.py docstring was found and fixed after the full run started; docstring only.)
* Placeholders: no `@@COUNTS@@` left in any .md file.

## Findings handled (security lens 1-7)
1. Eviction by stall: `EVICT_MIN_IDLE_SECONDS` (2.0); per-slot `last_progress` updated by the reader; `_take_slot` evicts only a reading slot idle at least that long; a live dripping crowd is not evicted. 
2. Reply write deadline: `REPLY_WRITE_TIMEOUT_SECONDS` (5.0), one total deadline over head and body in `_send_bytes`.
3. `ensure_descriptor_budget` (3 fds per handler thread plus 64 reserve) before serving; fd exhaustion becomes `SendNoDescriptors` (contract.py, adapters.py) and `Desk._give_back` returns the try (pending, `no_descriptors`); `_abort_unsent` also gives the try back on busy or fd exhaustion.
4. `_refuse_busy` drains non-blocking.
5. Reaper stop/start: `_retiring` is a set added under the lock before the join; a new reaper waits for all older ones; `Desk.reaper_running()`; main() logs when the reaper outlived the stop.
6. SIGTERM handler (main thread only) raises KeyboardInterrupt; shutdown order stop_background, server_close, desk.close, lock.close.
7. Docs: contract.md and README.md updated; CONTRACT-DELTA.md merged into contract.md and deleted; real start-up order in module and main docstrings; 25 s grace (send timeout + 4 busy waits) everywhere; counts keys, resolve/retry rows, two 503 shapes, test counts corrected.
S1c leftovers: `_expire` is NoReturn; SO_LINGER helper.

## Round 3 code/tests/docs items
B1, A1 to A11, C1, C3, C6, C7, C8, C9, C11, C12, C18, C19, E1 (exceptions.txt last line removed, names shortened), E2, E4 (literal), D (support.raw_http and addr added and used in touched files; the wider duplication clean-up was not done everywhere).

## Files changed
README.md, contract.md, CONTRACT-DELTA.md (deleted), exceptions.txt, src/lead_desk/{adapters,constants,contract,desk,server}.py, tests/{support,test_flow,test_hygiene,test_portal_api,test_reaper_start_stop,test_server_hardening,test_slow_sender,test_stall_eviction}.py (test_stall_eviction.py is new, 30 tests).

No commits, no PRs, no sub-agents; nothing started remains running. Scratch dirs removed.
