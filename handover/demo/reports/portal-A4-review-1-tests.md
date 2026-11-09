# A4 review round 1, lens: tests and drift (egm-implementation-readiness, snapshot A4-r1)
Saved from the reviewer's inline report. Verdict: not ready. No shell: nothing run by the reviewer.
Could not check: test_portal_api.py ~1219, test_flow, schema.sql, frontend, any test output.

Majors (reviewer's order to fix)
- M1 server.py ~512-524 `_resolve`: `self.rfile.read` has no TimeoutError handler, so a slow body on POST /review/{id}/resolve now logs "handler failed: TimeoutError" and answers 500 `internal`. Evidence claim "existing read sites answer 408" is false here. No test for slow body on resolve or demo POST.
- M2 MAX_CONNECTIONS 64 vs tests: test_150_simultaneous_connections and test_300_... (test_server_hardening ~160-168) exceed 64; they still pass only because 503 is allowed, so no longer prove "all get an answer". Evidence "64 is above the app's own concurrency tests" is false. Cap and slot-leak tests read `_live` via getattr(..., -1), so on old code they fail on "attribute missing", not behaviour (fail-before for these is an artifact). Thread-start-failure release path untested; deadline-then-503 interplay untested.
- M3 column-drift map (test_portal_log): a careless edit can map a new column to any listed value; several mappings dishonest (ids -> "times"/"name"/"follow_up_state"; last_error is adapter error text that the stored list does not mention). Fix: each column -> a listed field or an explicit "internal: reason"; iterate sqlite_master so a new table is caught.
- M4 call-site test covers one path only (_label_step has 3 callers: desk.py 896, 1012, 1032). Add retry path: spy raises once, second call has same args; stored label means no further call. No mutation check shown.
- M5 `portal_actions`: test compares constant to a literal (tautology); `demo_controls` never checked and /api/demo/* is 404 without the demo extension, so the map overclaims. Make conditional on server.demo or word it conditionally.
- M6 docs: constants.py REQUEST_TIMEOUT_SECONDS comment, contract.md:75 and :90 still describe the old per-read timeout; contract does not state the 10 s header/body deadlines, the header-phase 408 body `{"error":"request_timeout"}` (no receipt_id), the 64 cap, nor the transport 503 `{"error":"busy"}` (no receipt_id, HTTP/1.0, no SECURITY_HEADERS).
- M9 behaviour change: an idle-timeout expiry in the header phase now writes 408 where it used to close silently; check tests patching `_Handler.timeout` (test_portal_api ~1219).
Minor/Nits
- N7 no validation of the 4 new constants; tests patch with raising=False (hides renames).
- N8 vanished-client test is race-dependent and uses a fixed sleep.
- Minor: settimeout(limit) left set after the last read; a reply write can inherit a tiny leftover timeout, and the swallowed OSError hides it.
- N10 two test names over 40 chars (already renamed by the cloud session).
Evidence claims not supported: "64 above the app's concurrency tests"; "existing sites answer 408" for _resolve; "test_reply_write_fails... fails identically on clean base" (no output attached); "261 passed" excludes 2 known-red; "no leak path"; fuzz evidence predates S1.
