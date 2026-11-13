# NOTES-flaky413: test_resolve_413_drains_the_unread_body_like_post_leads fails now and then

Patch: flaky413-fix.patch (test only, one file: tests/test_later_approval.py, +21/-1). No change under src/. No optional core patch is needed: flaky413-core-optional.patch is NOT delivered because the server is not at fault (see below).

## What failed first (honest list)
- On plain db54e13 the test failed 12 of 30 separate runs here (evidence 1). The failure is always the same line: `assert [] == [70000]` (the list `drained` is still empty). The 413 status and JSON body assertion before it always passed.
- Not measured: the failure on Windows, the failure with pytest-randomly or xdist (not installed here), the full suite. I ran a 4-core shared box (load average about 15 from other jobs), so rates differ from the reviewer's 3 of 10.
- One slip: while the sibling sweep was running I briefly stashed the fix in the working tree, which could have contaminated that run; I killed it and re-ran the whole sweep on a separate copy (evidence 4 is the clean re-run).

## Root cause: class (a), a race in the TEST, not in the server
Two facts about the server (src/lead_desk/server.py, _resolve): after the 413 reply it calls `_flush_and_half_close()` (writes the reply, then `shutdown(SHUT_WR)`) and only afterwards `_drain(n)`. The client helper (tests/support.py raw_http) reads until the end of the stream, which is the half-close. So the client sees the complete reply plus end-of-stream BEFORE the server thread has necessarily executed the next line. The test then asserted at once on a list that the server thread fills (a spy on `_drain`). If the client thread wins the race, the list is empty. This is a plain missing synchronisation in the test about a server-side effect, not a reset problem: the reply arrives intact every time (the status assertion never failed), no ConnectionResetError was involved, and the drain itself works (when the list is filled it holds exactly [70000]).
- Proof by forcing the order (evidence 2): a 0.25 s pause added only right after the half-close makes the unfixed test fail 10 of 10 with the same message. No other change.
- Server drain (class b) ruled out: the server order (reply, half-close, drain) is deliberate and documented in finish() and _drain; nothing in it is wrong for the client.

## Fix (deterministic, no sleep as the fix)
The spy sets a `threading.Event` when `_drain` has finished; the test waits for it (`Event.wait(5.0)`, an upper bound, not a delay: returns as soon as the drain is done) before asserting `drained == [70000]`. Also the test now forces the unlucky order on every run, by pausing the server thread 0.25 s right after the half-close (a test hook via monkeypatch; this is what makes the old assertion order fail every time, so the test is a permanent fails-before guard of the class). Cost: about 0.25 s per run.

## Measurements after
- 100/100 passes idle and 100/100 under two busy loops (evidence 3).
- Mutants (evidence 5): drop the wait: killed; wait bound 0: killed; spy never sets the event: killed; wrong size: killed; server resolve 413 without drain (the existing test_mutants_more test): killed. One survivor, M2 (keep the wait but do not assert its result): equivalent, because an empty `drained` then fails the next assertion anyway; the explicit assert only gives a clearer message.
- Sibling sweep (evidence 4): 17 test ids (test_server_hardening 413, test_http, test_lead_step_route, test_input_edge_cases 501, test_portal_api 413/501/trickle, test_later_approval, all of test_fakes_body_before_answer, test_stall_eviction refusal/drain tests, test_slow_sender drain tests; 36 tests in all) x 30 runs: 0 failures. Why the siblings are safe: they assert on the wire (status and body read to the end) and never on a server-side effect right after the client's read. The only other server-side assertions use wait_for polling (tests/test_hung_adapter_calls.py `drained(rig)`, unrelated to the socket drain).
- Gates: ruff, format, mypy linux and win32, bandit, hygiene and gitleaks tests all green (evidence 6).

## Series compatibility
Applies on db54e13 alone and after every ordering of sonar-p1-quickwins-v3.2, sonar-p2-regex-http-bug-v2.1, sonar-p3-path-helper-v3 and nodemo-fix-v2 or v3 (evidence 6). It touches only tests/test_later_approval.py, which none of those patches touch.

## Rung table (R448)
| component | need | rung tried | evidence | what only our code gives | verdict |
| --- | --- | --- | --- | --- | --- |
| wait for the server thread | sync before asserting a server-side effect | stdlib threading.Event | evidence 2,3 | nothing more | CUT-TO-CONFIG+GLUE (4 lines) |
| pause hook | force the interleaving | monkeypatch | evidence 2 | nothing more | KEEP (test only) |
| server change | none needed | read of _resolve/_drain/finish | cause shown in the test | n/a | CUT |

R-numbers used: R6 (honesty, in the preamble), R7 (class-level: sibling sweep and fails-before), R448/R20 (rung table). I did not grep the studio bible folder (not available in this shell): R-numbers are cited from the preamble only.
Not run: the full suite, Windows, CI. EGM skipped for the review steps: I cannot invoke the egm:* reviewers here; the lead runs EGM on this patch.
