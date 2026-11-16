# pdbind-6e6ae211-codebase-r2: part 2 (bind guard), head 6e6ae211, round 2, persona codebase details

Source: hand-back of the codebase reviewer (agent a86895cc9f49909da), saved by the lead (condensed). SECURITY / mode-safety path. Static read, nothing run. 0 Blocker, 0 Major, Minor 1-6, Nits 1-6. Snapshot /home/user/build/snap/pdbind-6e6ae211. Round-1 M1 (opt-in config) and M2 (custom code and egress) landed; round-1 M3 ("66 checks give the same answers on old code") is claimed in CHANGELOG but NOT reproduced in the independent evidence (fail-before for test_loopback_sites is an import error).

## Minor
- m1 receiver.py:111 and Approvals.config: a hand-built Approvals has config=None and serve refuses even loopback; CHANGELOG upgrade step must say hand-built Approvals now passes config= and that the attribute is plain (same-object trust). Not labelled Breaking: old positional serve(approvals, host, port) now raises TypeError.
- m2 CHANGELOG "66 behaviour checks give the same answers on the old code": the shim run (merge-base src plus stand-in netguard) is not in the independent evidence; cite as builder-run or have the runner reproduce it.
- m3 Python 3.12 untested (CI is 3.13 only; requires-python >=3.12): IPv6Address str for mapped addresses and is_loopback on mapped changed in 3.13; seeded fuzz not checked on 3.12. 3.12 is IMPOSSIBLE-NOW here (not installed).
- m4 server_sockets AST scan is a denylist (misses multiprocessing Listener, http.server.test, create_datagram_endpoint, aiohttp/hypercorn/waitress/app.run): soften "fails on any other" or widen.
- m5 listen has no hook for server options (backlog, timeout); the Q8a-2 receiver will need to extend listen (note for merge).
- m6 IPv6 never run on a real socket (Errno 97 here); CHANGELOG "::1 really works" rests on the mocked test.

## Nits
n1 receiver.py:103 return annotation changed ThreadingHTTPServer to BaseServer without reason (keep old); n2 guard/http.py and llm/common.py share the LOOPBACK list, not the function (docstring/CHANGELOG wording); n3 bindguard.py:321-329 re-derives the http-loopback rule that config.url_allowed holds; n4 upgrade step not labelled Breaking; n5 loose mutant expect fragments B20, B8/B9/B28, B31; n6 post-bind check unreachable except by monkeypatch and not run when a reason is given (CHANGELOG line unqualified).

## Checked and found accurate
Kind inventory 31 = 6 DEMO_ONLY + 2 NOT_PROD + 5 IN_PROCESS + 18 real; callers of serve (only tests/test_p7_tick.py:284), single ThreadingHTTPServer, single Approvals( in src (app.py:176); all _LOOPBACK copies replaced, store/postgres and tools.py pinned with reasons; egress entries cannot read loopback to bindguard but not to the egress guard; stdlib ipaddress behaviour; mutant killers reach the real rules (B15, B19, B21, B39, B36, B37, B25-B27).

## Not checked
Files outside the 18 snapshot files except greps; no run; the shim run; 3.12; real IPv6; Config or Approvals fields holding a real service not read by real_services; import cycle; Q8a-2 receiver; Slack route semantics.
