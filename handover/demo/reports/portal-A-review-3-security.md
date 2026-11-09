# WP-A round 3 security review (snapshot portal-A-r3), saved by the cloud session
Reviewer: egm-design (fresh, read-only; ran nothing).
Verdict: no Blocker, no Major, no real security finding. 3 Nits + 1 carry-over.
Checked clean: _skip_body / Expect: 100-continue (gate still first; handler is HTTP/1.0 so no 100 Continue; no new unbounded read; not a new thread-hold); config.is_unspecified (0, 00, 0.0, 000, 0x0, [::], ::, 0:0:...:0 all caught; decimal/short/mapped forms safe); non-lock OperationalError 503 (fixed body, no path in log, cannot hide a write, corrupt DB still 500); NaN/Infinity -> null and allow_nan=False (dumps runs before send_response, no half reply; 500 path unreachable from stored data); _snapshot (connection, now) still one read transaction, clock after snapshot start; ORDER 208 Retry on UNKNOWN (portal only emits an action descriptor, desk.retry gives 409 unknown_needs_person, row unchanged). Round-2 N-4 closed (clean cap mutant turns only test_over_the_cap_gets_503_busy red).
Nits:
N3-1 gate-denied path has no _flush_and_half_close: if a client sends Expect and then the body, unread bytes may RST the close and the 403 body can be lost (cosmetic).
N3-2 config.is_unspecified catches only OSError; socket.inet_aton raises ValueError for embedded NUL / surrogate => start-up traceback for such a DESK_BIND. Catch (OSError, ValueError).
N3-3 test_portal_api.py:1433 asserts "0" not in allowed hosts for bind "0.0" which also passes on old code; assert "0.0" and add "00", "0x0".
Carry-over (round 2 N-3): ThreadingHTTPServer has no thread cap; README grep finds no limit line (A said it added one; verify).
Also: test_stored_nan_never_reaches_the_page proves less than its docstring says (killed by the direct _object assertion at :1473 only).
