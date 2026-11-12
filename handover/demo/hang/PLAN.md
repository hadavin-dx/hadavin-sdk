# H1 (order D14): test-suite hang, fix plan and evidence

Base: public pr-3-tests head f5fe824 (unchanged since the order). Patch: `hang-fix.patch` (git diff of the working tree with `git add -N`; 16 files).
Rules used: R5 (fix, do not defer), R6 (honest), R7 (class-level fix, fails-before proof), R19 (processes stopped).

## 1. What failed or is NOT proven (read first)

1. THE ROOT CAUSE OF THE REAL HANG IS NOT PROVEN. I could not make the full-suite hang happen again. What is proven:
   - The standard library's `BaseServer.shutdown()` waits on an event with no time limit. It only returns when the
     `serve_forever` loop of THAT server finishes. If that loop is not running (never started, gone, or stuck), the
     call never returns. Reproduced: `evidence-h-1-old-hangs.txt` (exit 124 after `timeout 60`, py-spy shows
     MainThread in `Event.wait` <- `BaseServer.shutdown` socketserver.py:255, the same frames as the INT-2 dump).
   - Delaying the start of `serve_forever` by 0.5 s does NOT hang (stdlib handles it), and 40 start/request/stop
     cycles of a plain stdlib server do not hang. So "the thread started late" is ruled out as the cause; that guess in the
     order is wrong. A plain test-only race is therefore not shown either.
2. The dump and the order note do not match. The dump file (`integration/evidence-int2-HANG-pyspy-dump.txt`, 55 lines) shows MainThread in
   `env` fixture teardown (conftest.py:124 -> `Env.close` -> `serve_in_thread.<locals>.stop`, lead_desk/server.py:1020), with ONE
   `serve_forever` thread alive (Thread-3370) and no other server thread. It does not show `test_restart_same_port_portal_open`
   (that test is id 1802 of 2922, far after "867 done"; the dots were probably buffered). The stopping server (the desk server of an `env` test) has no
   live loop thread and its event is not set: the server whose loop is gone is the one being shut down. Why its loop is gone: UNKNOWN.
3. The prefix run (evidence-h-9) is described at the end of this file (see section 6).
4. Product code: I did NOT change `src/`. `serve_in_thread.stop()` (src/lead_desk/server.py:1018-1022) calls `server.shutdown()` with no time
   limit, and is the frame in the dump. It is used only by tests (a program that builds a Desk). If the lead wants the product helper
   itself bounded, that is a core touch (needs approval); the test-side guard below bounds it without touching core.
5. `tests/test_hygiene.py` etc. were run on the final tree except: the full suite (not run by me; the lead's INT-2 on the head is the next gate).

## 2. The fix (test level, one shared helper, no core touch)

tests/support.py:
- `start_serving(srv)`: runs `serve_forever(0.05)` in a daemon thread and returns only after the loop has really run once
  (first `service_actions` call), else raises `ServerDidNotStop`. The 0.05 s poll also makes every stop about 10 times faster than the 0.5 s default.
- `stop_within(fn, what, seconds=20)`: runs a stop on a helper thread; on timeout prints the stack of every thread (faulthandler) and raises `ServerDidNotStop` (an AssertionError) instead of blocking.
- `stop_serving(srv, thread=None, what, seconds)`: shutdown + server_close + join, bounded by `stop_within`; fails if the thread is still alive.
tests/conftest.py: `Env.serve` and `Env.fakes` stops go through `stop_within`; `Env.close` still closes every other item, records stuck servers in `env.stuck`, and the `env` fixture raises the first one (a stuck server fails the test instead of hanging the run).
pyproject.toml: `faulthandler_timeout = 300` (built into pytest; pytest-timeout is not in requirements-dev.in; no lock change). Shown by `evidence-h-3-faulthandler.txt` (scratch hanging test, not committed).
New tests/test_server_stop_guard.py (6 tests): stuck stop fails fast with message and stack, the loop is awaited, a loop that never starts fails, errors pass through, the env fixture reports a stuck server after closing the rest.

## 3. Fails-before proof (R7)
- OLD form (stop_within reverted to a plain call, same new test): `timeout 60` -> exit 124, py-spy stack = BaseServer.shutdown / Event.wait (`evidence-h-1-old-hangs.txt`).
- NEW form: 6 passed in about 2 s (`evidence-h-2-new-passes.txt`); the same stuck stop fails after 0.5 s with "stuck server did not stop within 0.5 s".
- Limit: this proves the guard turns ANY such hang into a fast failure with stacks. It does not prove that the original hang cannot happen; it makes the next occurrence diagnosable (the dump names the server and the threads).

## 4. Sweep table (grep of tests/, demo_only/, load_tools/, scripts/, src/)
| where | shape | risk | action |
|---|---|---|---|
| tests/support.py StubServer (ThreadingHTTPServer) | thread + shutdown | unbounded wait | `start_serving` / `stop_serving` |
| tests/conftest.py Env.serve (product `serve_in_thread`), Env.fakes (`stop_fakes`) | product/demo stop | unbounded wait; the frame in the dump | wrapped in `stop_within`; fixture fails on stuck |
| tests/test_portal_api.py test_restart_same_port_portal_open | 20x start/stop in loop | unbounded wait | `start_serving` / `stop_serving` |
| test_load_tools.py (3 servers) | thread + shutdown | unbounded | helper |
| test_hubspot_probe.py Stub | same | unbounded | helper |
| test_live_claude.py model fixture | same | unbounded | helper |
| test_stamp_locks_and_budget.py (accept refuse test) | same, `get_request` patched to fail | unbounded | helper (loop proven by `service_actions` even when accept fails) |
| test_followup_edge_cases.py (TCPServer in `with`) | same | unbounded | helper |
| test_n8n_api_url.py (about 10 sites) | same | unbounded | helper (mechanical rewrite) |
| test_slow_sender.py Live | same | unbounded | helper |
| test_portal_demo.py Stub | same | unbounded | helper |
| test_crm_hubspot.py, test_mode_safety.py (`fh.stop` of the fake HubSpot) | demo_only stop | unbounded | `stop_within` |
| test_portal_api.py:526, test_server_hardening.py:214, test_stall_eviction.py:64, test_stamp_locks (2x) | `make_server` then `server_close()` only, never serve | no shutdown, no wait | safe, unchanged |
| test_claim_checks_and_crm_mode.py:135, test_server_main_reaper.py:25, test_stall_eviction.py:364 | stub classes that define their own `serve_forever` | not a real loop | safe, unchanged |
| demo_only/fakes_server.py, fake_hubspot.py, fake_model_server.py, load_tools/catcher.py, src/lead_desk/server.py | the product/demo stop functions | unbounded inside, called only from tests (now wrapped) or `main` (signal path) | not changed; core touch if the lead wants them bounded |

## 5. Gates (all on the final tree unless noted; evidence-h-4..8)
- ruff check and format: clean. mypy linux and win32: clean (project gate, 26 files). hygiene with gitleaks (GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1): 15 passed. gitleaks dir (tracked + new files) and git: no leaks.
- Touched files (11): 696 passed, 1 skipped (before the last conftest edit; the final conftest ran in section "portal x3").
- tests/test_portal_api.py + guard + crm_hubspot + mode_safety, 3 runs: 290 passed each, 154.2 s / 153.3 s / 153.7 s (`evidence-h-8-portal3.txt`). The restart test no longer shows in the slowest 3 (poll 0.05 s).
- Apply check: see `evidence-h-7-apply.txt`. hang-fix.patch applies on the head and after the speed patch; no overlap failure with any codeant2 runtime patch in either order, after I moved my conftest edit away from the hunk of codeant2-tests-hardening. `codeant2-scripts.patch` fails on this head with or without my patch (scripts/http_guard.py:10, already superseded by codeant3-scripts).

## 6. Not done / next steps
- Full suite on the fixed tree: not run (the lead's INT-2 on the new head). If a hang returns, the test now fails with "<name> did not stop within 20 s" and the stacks of all threads are on stderr, so the cause can finally be named.
- Product: a bounded `serve_in_thread.stop` is the only product-level option; not done without approval.
