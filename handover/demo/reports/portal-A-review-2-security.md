# WP-A round 2 security review (snapshot portal-A-r2), saved by the cloud session
Reviewer: egm-design (fresh, read-only; ran nothing; test outcomes from builder evidence).
Verdict: no Blocker, no Major, no real security finding. 6 Nits + 1 carry-over.
Round-1 findings: S-M1 fixed (README warning, stderr warning for non-loopback bind, wildcard never an allowed Host). S-M2 fixed (review_rows inside the read-only snapshot; one-connection test). S-M3 fixed (gate tests incl. HEAD/OPTIONS/foreign Host on 11 routes). S-M4 fixed (one grouped repeats query, in-flight cap 8; 266 ms -> 1.7+0.8 ms). S-M5 not fixed by WP-A: same red set on clean baseline, lead-owned (desk follow-up TypeError near desk.py:994). N1 static map fixed. N2 demo door fixed (405/413/408/400). N3 documented. N4 fixed. N5 (opaque 500 when read-only open fails) NOT addressed. N6 fixed (loader before bind). N7 fixed (exceptions.txt back to {0,6}).
Lens: read-only proof sound; gate at _dispatch first for every route; replies leak nothing; extension isolation sound; desk.py additions are pure reads, Desk.review unchanged in behaviour.
Nits:
N-1 server.py:86-92 bind like DESK_BIND=0 is treated as a host name (Host: 0 accepted). Reject or normalise non-IP/non-grammar binds; treat all-digit names as unspecified.
N-2 server.py:231 Expect: 100-continue gets 100 before the gate runs (no leak; claim "gate first" slightly off).
N-3 ThreadingHTTPServer has no thread cap; a slow-byte client holds a thread; add one README limit line.
N-4 portal-A2-fail-before.txt:24 mutant M10 (no in-flight cap) looks broken (assert 500, KeyError); re-run as a clean one-line mutant and show test_over_the_cap_gets_503_busy goes red.
N-5 exceptions.txt:13 unused row for 0.0.0.0 in constants.py; remove it (or add a test that needs it).
N-6 portal_api.py:411-416 / server.py:148 json.dumps default allow_nan: NaN/Infinity in a stored payload could be echoed as bare NaN; check identity.check_payload or use allow_nan=False and map to null.
Also: demo POST with missing/invalid Content-Length is treated as empty body (server.py:313) whereas POST /leads gives 400 (harmless).
