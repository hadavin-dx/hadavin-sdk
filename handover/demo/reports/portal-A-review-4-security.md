# WP-A pass-3 delta, security and correctness review, round 4 (egm-design, read-only, snapshot portal-A-r4, bfb28cf + pass 3 + HTTP/0.9 fix, patch sha 837861473452)
Saved by the cloud session from the reviewer's inline report. Reviewer ran nothing; did not read desk.py, db.py, identity.py, loader.py, adapters, schema.sql, support.py, other tests, static assets, fixtures, full.diff.

Verdict: no Blocker, 2 Major, 8 Nit.

MAJOR
- M1 server.py finish()/_drain/_skip_body: drain has a per-recv timeout but no total deadline. A client sending one byte every ~40 ms keeps a thread about 11 hours; a gate refusal with Content-Length 1048576 and a byte every 29 s holds the thread (and the 403) for years; Content-Length 5 and silence delays the 403 by 30 s. No thread cap. Fix: one monotonic total deadline (about 1 s) for both drains.
- M2 portal_api.py 472-482, 511-512, 599 and test_portal_api.py 570-579: person-card wording is tested only against hand-written SQL (last_error written directly), never through the real Desk.resolve. CRM card and email card both post decision not_sent; if resolve maps both to "person: not sent" the CRM answerer sees "A person checked and marked that the email was not sent". _PERSON_TEXT is tested before maybe_sent, so "has not been tried yet" could show with ambiguous_prior=1; no test combines them. Fix: test through POST /review/F../resolve for both cards and with ambiguous_prior=1.

NIT
- N1 503 'unavailable' by substring of str(e) can hide real faults (typo "no such table", disk fault, fd exhaustion); contract.md:114 wording.
- N2 "every request passes _gate_error" is not literal: stdlib error paths (bad line, BREW, 414, 431) call send_error without the gate; fixed JSON, no leak. Say so in the contract or gate in send_error; contract.md:13 omits 414/431.
- N3 no direct test of a valid two-word `GET /counts` with Host after the 0.9 fix.
- N4 Expect 100-continue refusal relies on finish() 50 ms quiet window; timing-sensitive tests (:1499, :1479 < 3.0).
- N5 card "person: not sent" says "Retry sends it now" without the duplicate-email caveat of _NOT_SENT_CONFIRM.
- N6 allowed Origin always http://host:port; a desk on port 80 refuses its own page (fails closed).
- N7 contract.md:3 test count stale.
- N8 is_unspecified OK; DNS names resolving to all-zeros not caught (pre-existing).

Checked sound: gate order (first call in _dispatch), read-only connection and snapshot close, no SQL built from input, field cap, 500 shows only "internal", in-flight semaphore, _skip_body with Expect, int() cap.
