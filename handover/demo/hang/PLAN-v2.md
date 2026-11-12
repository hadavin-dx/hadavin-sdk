# H2 (order D14, round 2): test-suite stop guard, fix plan v2

Base: public pr-3-tests f5fe824. Patch: `hang-fix-v2.patch` (REPLACES `hang-fix.patch` entirely; 15 files; git diff with `git add -N`).
Fixes the round-1 findings in `REVIEW-1.md`. Rules used: R5, R6, R7, R19.

## 1. What failed or is NOT proven (read first)

1. THE CAUSE OF THE SUSPECTED STALL IS UNPROVEN. A stop with no time limit (the standard library's `BaseServer.shutdown()`)
   can stall a run; the helpers in `tests/support.py` bound it and print the stacks of all threads. The earlier full run that
   looked stalled was most probably only slow, or its buffered progress file looked stale (868 old tests took 210 s and
   passed, `evidence-h-9`). This is a DIAGNOSTIC GUARD, not the fix of a known cause. Correction of PLAN.md section 1:
   - item 1: "the thread started late is ruled out as the cause" stays true as a fact about the standard library (a late
     start does not hang it), but it does not show that any stop was the cause of the run seen slow.
   - item 2: the sentence "the server whose loop is gone is the one being shut down. Why its loop is gone: UNKNOWN" over-reads
     one dump. Two dumps a minute apart showed different tests, so the run was moving; one frame in `shutdown` is not a stall.
   What IS proven: a stop whose loop is not running never returns (`evidence-h-1`, exit 124 under `timeout 60`), and the new
   helper turns that into a failed test in about 0.5 s with all stacks printed. That proves the guard, not the cause.
2. NOT run by me: the full suite (an INT-2b runner uses the machine), the browser tests, Windows. Only the 12 touched test files ran.
3. The bound for a product server stop was a guess in v1; it is measured now (section 3).

## 2. What changed from hang-fix.patch (each review finding)

- M1 (honesty): the docstring of `start_serving`, the module docstring of `tests/test_server_stop_guard.py`, and the line
  "the hang seen in the full run" now say plainly that the cause is unproven and this is a diagnostic guard. grep of the patch for
  "hang seen", "made that wait endless", "stalled the whole": none left (the word "stall" appears only as "can stall").
- N1 (bound): see section 3. `Env.serve` and `Env.fakes` now use `DESK_STOP_SECONDS = 2 * REQUEST_TIMEOUT_SECONDS` (60 s); plain stub servers keep 20 s.
- N2: `faulthandler.dump_traceback` goes through `_dump_all_stacks()`: sys.stderr first, then `sys.__stderr__`, each in try/except
  Exception, so `--capture=sys`/capsys can never replace `ServerDidNotStop` with `io.UnsupportedOperation`. New test runs under
  capsys; the whole guard file also ran with `--capture=sys` (`evidence-h2-3-capture-sys.txt`, with the old behaviour shown failing).
- N3a: `start_serving` closes the listening socket before it raises (one place, so every construction site is covered:
  `_server`, `_run_against`, the other helpers). Not covered: a test that builds two servers and the second construction raises
  (the first stays open until the test ends).
- N3b: `Env.close` already recorded every stuck server in `env.stuck` (the list); the test failure now names ALL of them
  (`Env.stuck_report`). The raise moved from the end of `env` fixture into a new autouse fixture `_stuck_servers_fail_the_test`
  (torn down last), because the end of `env` fixture is the anchor of two other patches (xdist, codeant2-tests-hardening).
  Test: two stuck stand-ins, both named; scratch proof that a real `env` test fails at teardown naming both (`evidence-h2-2-env-two-stuck.txt`).
- N3c: new `support.stop_all(servers)`; the two-server loops in `test_n8n_api_url.py` use it: both are stopped even if the first fails;
  test with a stuck first server and a good second.
- N3d: the docstrings of the stuck-stop test (1) and the never-starting-loop test (4) say that one daemon helper thread stays
  blocked until the test process ends. Not changed.
- N4: the redundant `thread.join(timeout=5)` after `stop_serving` in `test_stamp_locks_and_budget.py` is gone. N5: left (a
  `ServerDidNotStop` raised in a `finally` can mask the first assertion; better than a hang).

## 3. N1 measured: can a legitimate stop last longer than 20 s?

- `REQUEST_TIMEOUT_SECONDS` is 30.0 (src/lead_desk/constants.py:192). `serve_in_thread.stop()` (server.py 1018-1022) is
  `shutdown()`, `server_close()`, `thread.join(timeout=REQUEST_TIMEOUT_SECONDS)`. `_Server` is a `ThreadingHTTPServer`; measured:
  `daemon_threads = True`, `block_on_close = True` (only non-daemon threads are joined, so `server_close()` does NOT wait for handler threads).
- Scratch test (not committed; `evidence-h2-2-stalled-stop.txt`): a real desk server, 3 clients that stall in the body and 1 that stalls in the header, then `stop()`:
  0.00 s in 4 runs. So a stalled client does not slow the stop today.
- Still: the product stop has its own join limit of 30 s, so a legitimate worst case is 30 s plus the shutdown poll. A 20 s bound could
  turn that red. Product stops now get 60 s; a plain stub (a stop is milliseconds) keeps 20 s. The guard's job is to catch an endless wait, not a 30 s one.
- Not measured: a handler thread inside the desk's own long work at stop time (not joined either, because daemon).

## 4. Tool versions, the xdist CI patch

- Pinned pytest: `pytest==9.2.0` (requirements-dev.in and .txt). `faulthandler_timeout` is a built-in ini option since pytest 5.0; it only prints
  stacks (`dump_traceback_later(exit=False)`), it never fails or kills a test. No new dependency, no lock change.
- `speed/ci-xdist-demo-b29bb1f.patch` touches: `.github/workflows/lint.yml`, `requirements-dev.in`, `requirements-dev.txt`,
  `requirements-dev-win.txt` (adds pytest-xdist) and `tests/conftest.py` (appended after `env` fixture: the browser grouping hook and
  `pytest_configure`). It does NOT touch `pyproject.toml` or `addopts`, so `faulthandler_timeout` does not collide. The only shared
  file is `tests/conftest.py`: v2 keeps the end of the file and the `env` fixture unchanged, so `git apply --check` passes both orders
  (`evidence-h2-5-apply.txt`). With xdist, `faulthandler_timeout` runs inside each worker. (v1, which edited the end of `env` fixture, would have conflicted: I did not check it.)

## 5. Gates (on the final tree, new file `git add -N`)

See `evidence-h2-1-lint.txt` (ruff check, ruff format, mypy linux+win32), `evidence-h2-4-touched.txt` (12 touched files, one pytest process: 879 passed, 1 skipped, 301 s; ran while the INT-2b runner was also running),
`evidence-h2-6-hygiene-gitleaks.txt` (15 passed) and `evidence-h2-6-gitleaks.txt` (dir and git: no leaks), `evidence-h2-7-failfast.txt` (old unbounded helper: exit 124 after 60 s; new: passes the stuck-stop test in 0.8 s wall), `evidence-h2-5-apply.txt`.
The two `mypy` errors at `tests/conftest.py:51,70` and others in conftest are old (present before my change); the project's mypy gate covers src/ and tools/ and is clean.

Patch sha256: 1afc6709bab01f3b26fd0999fe28cc4c2078af7907c0a6bcaf2be77d3485e397. Tree: /tmp/work/h2-base (f5fe824 + v2, uncommitted).
