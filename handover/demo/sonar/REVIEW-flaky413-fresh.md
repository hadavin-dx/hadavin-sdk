# rv31: independent review of flaky413-fix.patch  (verdict: flaky413-fix CLEAN, 4 Nits)
Base: fresh clone of the public repo at 9c53207 (venv from requirements-dev.txt, scratch /tmp/work/rv31-1). No pushes, no network writes, made-up data only. Preamble and HARD RULES read and obeyed (R-numbers: preamble only, bible folder not available here; rules used: 5, 6, 7, 8-style tooling, 19). EGM not run (cannot invoke egm:* here; the lead runs it).

## Failures first
None found in the patch. What I did NOT measure: Windows, CI, pytest-randomly/xdist, the browser tests (need a browser), the full suite without the delay injection.

## 1. Reproduction of the unfixed test (9c53207)
- Idle: 5 of 40 runs failed. Under two CPU hogs: 12 of 40 failed. Every one of the 17 failures has the single message `assert [] == [70000]` (Right contains one more item: 70000). No other message (no reset, no JSON error, no timeout).
- Root cause confirmed by own experiment: unfixed test plus a 0.25 s sleep right after the half-close = 10 of 10 fail with the same message. Builder's cause is right (test reads a server-filled list without waiting).
- Different/additional cause hunted: (a) `_resolve` calls `_drain(n)` synchronously on the handler thread before returning, `finish()` and the socket close come after, so `_drain` always completes before the close; no server race. (b) RST: reply is sent, write side shut, then n bytes are read, so no unread data at close for n up to DRAIN_MAX_BYTES within DRAIN_TOTAL_SECONDS (1.0 s wall clock); beyond that the RST risk is the documented design, not this test (70000 bytes already queued on loopback). The status+JSON assertion never failed in 17 failures, so no truncation was seen here. (c) Windows (reasoning, not measured): a close with unread data resets and can discard the unsent/unread reply, which is why the drain exists; the fix does not change that. The fix is platform neutral (Event.wait, bounded 5 s). With the 0.25 s hold the client's 70000-byte sendall may block until the server starts draining on a small-buffer stack; bounded by raw_http's 10 s timeout, so safe. Note raw_http swallows ConnectionResetError and returns partial bytes: a Windows reset would surface as a status/JSON assertion failure, not silently.
- Is the permanent 0.25 s pause a good idea? Yes, with caveats. It keeps testing the intended behaviour (drain happens after the reply, with the half-close preceding it) and makes the old assertion order fail every time (T1 below). Existing mutant `tests/test_mutants_more.py::test_mutant_resolve_413_no_drain` still dies (it passes, i.e. the mutant is caught). It does not mask a missing drain: S1 (no drain) and S2 (drain 0 bytes) are killed.

## 2. After the fix
- 100 of 100 pass idle; 100 of 100 pass under two CPU hogs. Whole tests/test_later_approval.py: 29 passed. Test call time 0.32 s.

## 3. Sibling sweep (widened)
- Deterministic method (stronger than repeating): in a copy with the unfixed test I injected a 0.2 s sleep after EVERY server half-close (the exact window where follow-up/drain/spies run after the client has the reply) and ran everything except the browser tests: 19 server/HTTP files (test_server_hardening, test_stall_eviction, test_slow_sender, test_http, test_portal_api, test_fakes_body_before_answer, test_lead_step_route, test_input_edge_cases, test_desk_http_edge_cases, test_portal_log, test_portal_demo, test_mode_safety, test_server_stop_guard, test_server_main_reaper, test_hung_adapter_calls, test_codeant_fakes, test_codeant_desk, test_portal_lead_pages, test_later_messages): 784 passed, 33 skipped. Rest of tests/ (browser files, later_approval excluded): 2288 passed, 163 skipped, 1 failed: test_clock_steps::test_wall_clock_is_only_used_for_calendar_stamps, which is my own injected `time.sleep` being flagged by the source scan (artifact, not a flaky test). Conclusion: no other test asserts on server-side state in that window.
- Repeat under load: 81 tests selected by -k (413/501/400/drain/large/refus/oversize/body/reset) from 7 files, 12 runs under two hogs: 0 failing runs. (Brief asked 30; 12 was the time budget at 71 s per run; the injection above is the stronger check.)

## 4. My 12 mutants (patched test file / server `_resolve`)
- T1 drop wait assert: KILLED. T3 wait bound 0: KILLED. T4 spy never sets event: KILLED. T6 wrong size: KILLED. S1 server no drain: KILLED. S2 server drains 0 bytes: KILLED.
- T2 keep wait, drop the assert on its result: SURVIVED, equivalent (empty list fails the next assert).
- T5 spy sets the event before the real drain: SURVIVED (test only proves `_drain` was entered, as before). Nit.
- T7 pause removed: SURVIVED (expected: the wait alone fixes it; the pause only makes a future wait-removal fail every run, shown by T1). T8 pause hook made a no-op: SURVIVED, same reason. Nit.
- S3 server drains BEFORE the half-close (reply delayed behind the drain): SURVIVED, and also survives test_later_approval, test_fakes_body_before_answer, test_slow_sender, test_server_hardening (139 passed). Pre-existing gap, not caused by the patch. Nit.
- S4 server drains in a detached 0.5 s timer thread: SURVIVED (spy fires from that thread). Same class of gap. Nit.

## 5. Gates and apply matrix
- ruff check, ruff format --check (151 files), mypy linux and win32 (27 files): all clean. test_hygiene with GITLEAKS_BIN=/tmp/work/gl/gitleaks (8.30.1), DPLD_REQUIRE_SCAN=1 after `git add -A`: 15 passed. bandit -ll on the test file: same 1 Medium as base (CI runs bandit on src/tools/scripts only).
- Applies with git apply --check on db54e13 and on 9c53207. Matrix on db54e13: all 120 orderings of {p1-v3.2, p2-v2.1, p3-v3, nodemo-fix-v3, flaky413-fix}: 0 failures; plus every ordering with p2-v2.2-delta after v2.1 and the fix anywhere: all ok. None of the other patches mention test_later_approval.

## Findings
- Blocker: none. Major: none.
- Nit 1: mutants T7/T8: nothing kills the loss of the pause itself (only T1 shows it works). Acceptable.
- Nit 2: test proves `_drain` is entered and finishes, not the order (half-close before drain) nor that it finishes before the close (S3, S4 survive). Optional: record "half_close" then "drain" in one list in the spy and assert the order.
- Nit 3: `test_mutant_resolve_413_no_drain` now takes about 5 s (waits the full bound) instead of about 0.3 s. Acceptable.
- Nit 4: the pause hook wraps the shared `_flush_and_half_close`, so finish() also pauses (0.5 s hold per request in this test); harmless.

Files: /tmp/work/rv31-report.md. Head under review: 9c53207 + flaky413-fix.patch (not committed).
