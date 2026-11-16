# Hostile-input harness, Linux run 1 (unpatched baseline 494244e)

EVIDENCE RUNNER output. Raw results only; no judgement beyond 'anomaly as flagged by the harness'.

## Lead items

- Harness crash: none. Both runs ended normally (class A run ended by my wrapper after class A's liveness check, see Method).
- Desk died: no row flagged `DESK DEAD`; every class-end liveness row says alive. (Class H deliberately kills the desk with kill -9 and restarts it; that is the attack.)
- Attacks that hung or ran slow (harness flag): see the anomaly list below.

## Anomalies as flagged by the harness (32 of 237 rows)

- [A size/framing] body 10 MB of 'x' -> **conn err:BrokenPipeError**
- [A size/framing] Content-Length larger than body (+50), client keeps socket open -> **5xx 500; slow 30.0s**
- [A size/framing] Content-Length: 99999999999999999999 -> **slow 10.0s; conn timeout**
- [B slowloris/connections] after 33 s: how many of the 40 stuck sockets were closed/answered by server -> **slow 33.0s; no reply**
- [D email twins] email keys 'İ' lower() length twin: ß->ss? (done above) -> **no reply**
- [F routes/methods/traversal] (state after all wrong-method calls) -> **no reply**
- [F routes/methods/traversal] HTTP/0.9 'GET /counts' (no version) -> **slow 6.0s; conn timeout**
- [F routes/methods/traversal] HTTP/0.9 'GET /counts' LF only -> **slow 6.0s; conn timeout**
- [G concurrency/replay] 1000 distinct request ids, same email, 100 parallel workers -> **no reply**
- [G concurrency/replay] re-sent the 0 non-2xx ids of the 1000 (up to 5 tries) -> **no reply**
- [G concurrency/replay] 50 parallel posts of ONE request id, same payload -> **no reply; CRM rows>leads**
- [G concurrency/replay] 50 parallel posts of ONE request id, 50 different names -> **no reply; CRM rows>leads**
- [G concurrency/replay] setup: lead with mail reply lost -> unknown follow-up -> **CRM rows>leads**
- [G concurrency/replay] resolve FLa57b0675394e 10x concurrently (5 sent, 5 not_sent) -> **no reply; CRM rows>leads**
- [G concurrency/replay] GET /leads for that lead -> **CRM rows>leads**
- [G concurrency/replay] resolve FLa57b0675394e again after final -> **CRM rows>leads**
- [G concurrency/replay] retry FLa57b0675394e after final -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: empty body -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: not json -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: decision list -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: decision SENT upper -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: decision ' sent' -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: decision with NUL -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: nested depth 10000 -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: duplicate keys -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: decision null -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: invalid utf8 -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: array body -> **CRM rows>leads**
- [G concurrency/replay] resolve FLb948e24b3291 body: 10 MB body -> **conn err:BrokenPipeError; CRM rows>leads**
- [G concurrency/replay] resolve on R/D/O/F-missing ids -> **CRM rows>leads**
- [G concurrency/replay] retry F of sent lead / unknown -> **CRM rows>leads; mails>leads**
- [H kill and restart] kill -9 desk mid-burst (300 posts, 7 emails), restart same DB, resend all 300 ids -> **no reply**

- Reading note (harness behaviour, not interpretation): `no reply` is printed whenever the status line is empty, which also happens for the harness's own summary rows (those with no HTTP request, e.g. the 1000-request batch, class D placeholder, class H summary). `CRM rows>leads` in class G first appears after the 1000-parallel batch and the 50-parallel same-id batches and stays on every later row of that class (the desk state is cumulative within the class).

## Setup

- Head commit: 494244e (git archive at /tmp/dpld-baseline; not a git repo on disk, so the sha is as given in the order, not re-checked with git).
- Host: 4 cores, 15 GiB RAM, Linux 6.18. Python: /tmp/dpld-venv/bin/python. Ports 18701/18702 were free before start.
- Run 1 (SKIPA=1, classes B-H): 2026-11-09T10:14:55Z to 2026-11-09T10:22:30Z (about 7.6 min).
- Run 2 (class A only): 2026-11-09T10:22:45Z to 2026-11-09T10:23:38Z.
- Only change to the harness copy (/tmp/dpld-baseline/hostile_run.py): line 6, `PY = "/tmp/dpld-venv/bin/python"`. The original was not edited.
- Method note: the harness has no way to run class A alone (unset SKIPA runs A then B-H). To avoid a second full run and avoid editing the copy, I used a wrapper /tmp/dpld-out/runA.py that imports the unedited copy, calls `classes()`, and stops after class A's `alive_note`. Rows are in the same format. Its first act truncates _hostile_rows.jsonl, so run 1's rows were saved first.
- The harness's own note: the server socket timeout is 30 s.

## Table (class A from run 2, then B-H from run 1)

| # | class | what was sent | response (status line, body up to 300 chars, time, connection) | desk state afterwards | anomaly |
|---|---|---|---|---|---|
| 1 | A size/framing | body exactly 65536 bytes (cap 65536), valid envelope but message>2000 | HTTP/1.0 202 Accepted \| '{"receipt_id": 1, "verdict": "review", "reason": "bad_field:message", "replayed": false}' \| 0.01s closed | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 2 | A size/framing | body 65537 bytes (cap+1) | HTTP/1.0 413 Request Entity Too Large \| '{"error": "too_large", "receipt_id": null}' \| 0.00s closed | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 3 | A size/framing | body 10 MB of 'x' |  \| '' \| 0.00s err:BrokenPipeError | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | conn err:BrokenPipeError |
| 4 | A size/framing | chunked, no Content-Length | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 5 | A size/framing | Content-Length larger than body (+50), client keeps socket open | HTTP/1.0 500 Internal Server Error \| '{"error": "internal"}' \| 30.03s closed | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | 5xx 500; slow 30.0s |
| 6 | A size/framing | Content-Length smaller than body (-10) | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 7 | A size/framing | Content-Length: -5 | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 8 | A size/framing | Content-Length: abc | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 9 | A size/framing | Content-Length: 99999999999999999999 |  \| '' \| 10.01s timeout | rcpt=1 open=0 leads=0 crm=0 mail=0 fu={} alive=True | slow 10.0s; conn timeout |
| 10 | A size/framing | two Content-Length headers (len, len+5) | HTTP/1.0 201 Created \| '{"receipt_id": 2, "verdict": "new", "lead_id": "Lbd4f4a166cff", "replayed": false}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 11 | A size/framing | no Content-Length on POST /leads | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 12 | A size/framing | Content-Length: 0 | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 13 | A size/framing | Content-Length with unicode digit (arabic-indic 5) | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 14 | A size/framing | header block 100 KB | HTTP/1.0 431 Request Header Fields Too Large \| '{"error": "request_header_fields_too_large"}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 15 | A size/framing | 200 headers | HTTP/1.0 431 Request Header Fields Too Large \| '{"error": "request_header_fields_too_large"}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 16 | A size/framing | request line 70 KB | HTTP/1.0 414 Request-URI Too Long \| '{"error": "request-uri_too_long"}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 17 | A size/framing | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 18 | B slowloris/connections | 20 stuck connections (partial header); GET /counts meanwhile | HTTP/1.0 200 OK \| '{"received": 0, "new": 0, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=0 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 19 | B slowloris/connections | 20 more stuck connections (slow body, CL 500); POST valid lead meanwhile | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L712f25f5bce1", "replayed": false}' \| 0.01s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 20 | B slowloris/connections | after 33 s: how many of the 40 stuck sockets were closed/answered by server [note: server socket timeout is 30 s] |  \| 'closed_or_answered=40/40' \| 33.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | slow 33.0s; no reply |
| 21 | B slowloris/connections | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 22 | B slowloris/connections | 200 idle connections left open (connected 200, failed 0); GET /counts | HTTP/1.0 200 OK \| '{"received": 1, "new": 1, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.01s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 23 | B slowloris/connections | same: POST valid lead | HTTP/1.0 201 Created \| '{"receipt_id": 2, "verdict": "new", "lead_id": "L3fd48efde2c0", "replayed": false}' \| 0.00s closed | rcpt=2 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 24 | B slowloris/connections | 200 idle sockets after 32 s; GET /counts | HTTP/1.0 200 OK \| '{"received": 2, "new": 2, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=2 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 25 | B slowloris/connections | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 26 | C encoding/parser | invalid UTF-8 in name (\xff\xfe) | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=0 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 27 | C encoding/parser | UTF-8 BOM before JSON | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=0 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 28 | C encoding/parser | NUL byte inside name (raw) | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=0 open=0 leads=0 crm=0 mail=0 fu={} alive=True | none printed |
| 29 | C encoding/parser | NUL escaped (\u0000) in name | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L1a55958c1ce6", "replayed": false}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 30 | C encoding/parser | NUL in source_ref | HTTP/1.0 201 Created \| '{"receipt_id": 2, "verdict": "new", "lead_id": "L85d82f7502d2", "replayed": false}' \| 0.00s closed | rcpt=2 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 31 | C encoding/parser | lone surrogate escape in name | HTTP/1.0 202 Accepted \| '{"receipt_id": 3, "verdict": "review", "reason": "bad_field:name", "replayed": false}' \| 0.00s closed | rcpt=3 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 32 | C encoding/parser | nested JSON depth 100 as whole body | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=3 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 33 | C encoding/parser | nested array depth 100 inside payload | HTTP/1.0 201 Created \| '{"receipt_id": 4, "verdict": "new", "lead_id": "L05b4160551b0", "replayed": false}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 34 | C encoding/parser | nested JSON depth 10000 as whole body | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 35 | C encoding/parser | nested array depth 10000 inside payload | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 36 | C encoding/parser | nested JSON depth 100000 as whole body | HTTP/1.0 413 Request Entity Too Large \| '{"error": "too_large", "receipt_id": null}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 37 | C encoding/parser | nested array depth 100000 inside payload | HTTP/1.0 413 Request Entity Too Large \| '{"error": "too_large", "receipt_id": null}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 38 | C encoding/parser | huge number 1e999 / 10^5000 digits in extra field | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 39 | C encoding/parser | huge int as name | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 40 | C encoding/parser | duplicate keys (email twice, different values) | HTTP/1.0 201 Created \| '{"receipt_id": 5, "verdict": "new", "lead_id": "Lbb6b5acf5d70", "replayed": false}' \| 0.00s closed | rcpt=5 open=0 leads=4 crm=4 mail=4 fu={'sent': 4} alive=True | none printed |
| 41 | C encoding/parser | duplicate source key (webhook then form) | HTTP/1.0 201 Created \| '{"receipt_id": 6, "verdict": "new", "lead_id": "Ldfbede3dcf1e", "replayed": false}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 42 | C encoding/parser | payload is list / string / null | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 43 | C encoding/parser | source_ref int / 129 chars / 128 chars / empty | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 44 | C encoding/parser | source_ref 129 chars | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 45 | C encoding/parser | source_ref 128 chars | HTTP/1.0 201 Created \| '{"receipt_id": 7, "verdict": "new", "lead_id": "Lf91656053fdd", "replayed": false}' \| 0.00s closed | rcpt=7 open=0 leads=6 crm=6 mail=6 fu={'sent': 6} alive=True | none printed |
| 46 | C encoding/parser | name is number / email is list | HTTP/1.0 202 Accepted \| '{"receipt_id": 8, "verdict": "review", "reason": "bad_field:name", "replayed": false}' \| 0.00s closed | rcpt=8 open=0 leads=6 crm=6 mail=6 fu={'sent': 6} alive=True | none printed |
| 47 | C encoding/parser | name 201 chars | HTTP/1.0 202 Accepted \| '{"receipt_id": 9, "verdict": "review", "reason": "bad_field:name", "replayed": false}' \| 0.00s closed | rcpt=9 open=0 leads=6 crm=6 mail=6 fu={'sent': 6} alive=True | none printed |
| 48 | C encoding/parser | message 2001 chars | HTTP/1.0 202 Accepted \| '{"receipt_id": 10, "verdict": "review", "reason": "bad_field:message", "replayed": false}' \| 0.00s closed | rcpt=10 open=0 leads=6 crm=6 mail=6 fu={'sent': 6} alive=True | none printed |
| 49 | C encoding/parser | Content-Type text/plain with valid JSON | HTTP/1.0 201 Created \| '{"receipt_id": 11, "verdict": "new", "lead_id": "Ld3521d39c72a", "replayed": false}' \| 0.00s closed | rcpt=11 open=0 leads=7 crm=7 mail=7 fu={'sent': 7} alive=True | none printed |
| 50 | C encoding/parser | JSON top-level array / string / number | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=11 open=0 leads=7 crm=7 mail=7 fu={'sent': 7} alive=True | none printed |
| 51 | C encoding/parser | empty object {} | HTTP/1.0 400 Bad Request \| '{"error": "bad_envelope", "receipt_id": null}' \| 0.00s closed | rcpt=11 open=0 leads=7 crm=7 mail=7 fu={'sent': 7} alive=True | none printed |
| 52 | C encoding/parser | emoji + RTL override in name | HTTP/1.0 201 Created \| '{"receipt_id": 12, "verdict": "new", "lead_id": "L52fbf26b5310", "replayed": false}' \| 0.00s closed | rcpt=12 open=0 leads=8 crm=8 mail=8 fu={'sent': 8} alive=True | none printed |
| 53 | C encoding/parser | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 54 | D email twins | base ada@example.test | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "Le83f4f046f3e", "replayed": false}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 55 | D email twins | ADA@EXAMPLE.TEST (uppercase) | HTTP/1.0 200 OK \| '{"receipt_id": 2, "verdict": "duplicate", "lead_id": "Le83f4f046f3e", "differing_fields": [], "replayed": false}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 56 | D email twins | ' ada@example.test ' (spaces) | HTTP/1.0 200 OK \| '{"receipt_id": 3, "verdict": "duplicate", "lead_id": "Le83f4f046f3e", "differing_fields": [], "replayed": false}' \| 0.00s closed | rcpt=3 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 57 | D email twins | tab-wrapped email | HTTP/1.0 200 OK \| '{"receipt_id": 4, "verdict": "duplicate", "lead_id": "Le83f4f046f3e", "differing_fields": [], "replayed": false}' \| 0.00s closed | rcpt=4 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 58 | D email twins | ada+tag@example.test (plus) | HTTP/1.0 201 Created \| '{"receipt_id": 5, "verdict": "new", "lead_id": "L3fce04875dd6", "replayed": false}' \| 0.00s closed | rcpt=5 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 59 | D email twins | a.da@example.test vs ada (dots) | HTTP/1.0 201 Created \| '{"receipt_id": 6, "verdict": "new", "lead_id": "Lc34c1d02a81b", "replayed": false}' \| 0.00s closed | rcpt=6 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 60 | D email twins | trailing CRLF in email (JSON \r\n) | HTTP/1.0 200 OK \| '{"receipt_id": 7, "verdict": "duplicate", "lead_id": "Le83f4f046f3e", "differing_fields": [], "replayed": false}' \| 0.00s closed | rcpt=7 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 61 | D email twins | CRLF injection a@b.com\r\nBcc: v@evil.test | HTTP/1.0 202 Accepted \| '{"receipt_id": 8, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=8 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 62 | D email twins | CRLF injection in name | HTTP/1.0 201 Created \| '{"receipt_id": 9, "verdict": "new", "lead_id": "L9a501ea215da", "replayed": false}' \| 0.00s closed | rcpt=9 open=0 leads=4 crm=4 mail=4 fu={'sent': 4} alive=True | none printed |
| 63 | D email twins | email with embedded space | HTTP/1.0 202 Accepted \| '{"receipt_id": 10, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=10 open=0 leads=4 crm=4 mail=4 fu={'sent': 4} alive=True | none printed |
| 64 | D email twins | NFC vs NFD: josé@example.test NFC | HTTP/1.0 201 Created \| '{"receipt_id": 11, "verdict": "new", "lead_id": "Lde33dd6b6e3a", "replayed": false}' \| 0.00s closed | rcpt=11 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 65 | D email twins | NFD josé@example.test (e + U+0301) | HTTP/1.0 201 Created \| '{"receipt_id": 12, "verdict": "new", "lead_id": "L671bb000b944", "replayed": false}' \| 0.00s closed | rcpt=12 open=0 leads=6 crm=6 mail=6 fu={'sent': 6} alive=True | none printed |
| 66 | D email twins | full-width @ (U+FF20): ada＠example.test | HTTP/1.0 202 Accepted \| '{"receipt_id": 13, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=13 open=0 leads=6 crm=6 mail=6 fu={'sent': 6} alive=True | none printed |
| 67 | D email twins | full-width letters ａｄａ@example.test | HTTP/1.0 201 Created \| '{"receipt_id": 14, "verdict": "new", "lead_id": "Lb98c5a0323d1", "replayed": false}' \| 0.00s closed | rcpt=14 open=0 leads=7 crm=7 mail=7 fu={'sent': 7} alive=True | none printed |
| 68 | D email twins | Turkish dotted İ: İ@example.test | HTTP/1.0 201 Created \| '{"receipt_id": 15, "verdict": "new", "lead_id": "L7ae21df2b9bb", "replayed": false}' \| 0.00s closed | rcpt=15 open=0 leads=8 crm=8 mail=8 fu={'sent': 8} alive=True | none printed |
| 69 | D email twins | dotless ı@example.test vs i@example.test | HTTP/1.0 201 Created \| '{"receipt_id": 16, "verdict": "new", "lead_id": "L638183d92857", "replayed": false}' \| 0.00s closed | rcpt=16 open=0 leads=9 crm=9 mail=9 fu={'sent': 9} alive=True | none printed |
| 70 | D email twins | i@example.test | HTTP/1.0 201 Created \| '{"receipt_id": 17, "verdict": "new", "lead_id": "L722c1c688fe9", "replayed": false}' \| 0.00s closed | rcpt=17 open=0 leads=10 crm=10 mail=10 fu={'sent': 10} alive=True | none printed |
| 71 | D email twins | zero-width space in local part | HTTP/1.0 202 Accepted \| '{"receipt_id": 18, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=18 open=0 leads=10 crm=10 mail=10 fu={'sent': 10} alive=True | none printed |
| 72 | D email twins | zero-width joiner / BOM in email | HTTP/1.0 202 Accepted \| '{"receipt_id": 19, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=19 open=0 leads=10 crm=10 mail=10 fu={'sent': 10} alive=True | none printed |
| 73 | D email twins | NBSP around email | HTTP/1.0 200 OK \| '{"receipt_id": 20, "verdict": "duplicate", "lead_id": "Le83f4f046f3e", "differing_fields": [], "replayed": false}' \| 0.00s closed | rcpt=20 open=0 leads=10 crm=10 mail=10 fu={'sent': 10} alive=True | none printed |
| 74 | D email twins | Kelvin sign K@example.test (lowercases to k) | HTTP/1.0 201 Created \| '{"receipt_id": 21, "verdict": "new", "lead_id": "L311377bd68f4", "replayed": false}' \| 0.00s closed | rcpt=21 open=0 leads=11 crm=11 mail=11 fu={'sent': 11} alive=True | none printed |
| 75 | D email twins | k@example.test | HTTP/1.0 200 OK \| '{"receipt_id": 22, "verdict": "duplicate", "lead_id": "L311377bd68f4", "differing_fields": [], "replayed": false}' \| 0.00s closed | rcpt=22 open=0 leads=11 crm=11 mail=11 fu={'sent': 11} alive=True | none printed |
| 76 | D email twins | ß@example.test vs SS@example.test | HTTP/1.0 201 Created \| '{"receipt_id": 23, "verdict": "new", "lead_id": "L4f386dff4d0e", "replayed": false}' \| 0.00s closed | rcpt=23 open=0 leads=12 crm=12 mail=12 fu={'sent': 12} alive=True | none printed |
| 77 | D email twins | IDN domain ada@exämple.test vs punycode | HTTP/1.0 201 Created \| '{"receipt_id": 24, "verdict": "new", "lead_id": "L161f478b279d", "replayed": false}' \| 0.00s closed | rcpt=24 open=0 leads=13 crm=13 mail=13 fu={'sent': 13} alive=True | none printed |
| 78 | D email twins | punycode ada@xn--exmple-cua.test | HTTP/1.0 201 Created \| '{"receipt_id": 25, "verdict": "new", "lead_id": "L3cd8dd94a551", "replayed": false}' \| 0.00s closed | rcpt=25 open=0 leads=14 crm=14 mail=14 fu={'sent': 14} alive=True | none printed |
| 79 | D email twins | email 254 chars | HTTP/1.0 201 Created \| '{"receipt_id": 26, "verdict": "new", "lead_id": "L0b4a1160411f", "replayed": false}' \| 0.00s closed | rcpt=26 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 80 | D email twins | email 255 chars | HTTP/1.0 202 Accepted \| '{"receipt_id": 27, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=27 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 81 | D email twins | email 300 chars | HTTP/1.0 202 Accepted \| '{"receipt_id": 28, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=28 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 82 | D email twins | email with angle brackets <a@b.com> | HTTP/1.0 202 Accepted \| '{"receipt_id": 29, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=29 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 83 | D email twins | email 'a@b' (no dot) | HTTP/1.0 202 Accepted \| '{"receipt_id": 30, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=30 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 84 | D email twins | two @ | HTTP/1.0 202 Accepted \| '{"receipt_id": 31, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.01s closed | rcpt=31 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 85 | D email twins | quoted local "a b"@x.com | HTTP/1.0 202 Accepted \| '{"receipt_id": 32, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=32 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 86 | D email twins | trailing dot ada@example.test. | HTTP/1.0 202 Accepted \| '{"receipt_id": 33, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=33 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | none printed |
| 87 | D email twins | email keys 'İ' lower() length twin: ß->ss? (done above) |  \| 'see rows above' \| 0.00s closed | rcpt=33 open=0 leads=15 crm=15 mail=15 fu={'sent': 15} alive=True | no reply |
| 88 | D email twins | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 89 | E SQL metachar/%00 | SQL in every field | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L51f7a7586aeb", "replayed": false}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 90 | E SQL metachar/%00 | SQL in email local part | HTTP/1.0 202 Accepted \| '{"receipt_id": 2, "verdict": "review", "reason": "invalid_email", "replayed": false}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 91 | E SQL metachar/%00 | SQL in source_ref | HTTP/1.0 201 Created \| '{"receipt_id": 3, "verdict": "new", "lead_id": "L0525464f153f", "replayed": false}' \| 0.00s closed | rcpt=3 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 92 | E SQL metachar/%00 | source_ref with %00 literal text and NUL | HTTP/1.0 201 Created \| '{"receipt_id": 4, "verdict": "new", "lead_id": "Lfd2ae5097de2", "replayed": false}' \| 0.00s closed | rcpt=4 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 93 | E SQL metachar/%00 | %00 in email field | HTTP/1.0 201 Created \| '{"receipt_id": 5, "verdict": "new", "lead_id": "La59e115054bc", "replayed": false}' \| 0.00s closed | rcpt=5 open=0 leads=4 crm=4 mail=4 fu={'sent': 4} alive=True | none printed |
| 94 | E SQL metachar/%00 | double quotes/backslash/LIKE chars % _ in name | HTTP/1.0 201 Created \| '{"receipt_id": 6, "verdict": "new", "lead_id": "L9d856aa28a35", "replayed": false}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 95 | E SQL metachar/%00 | GET /leads/L' OR '1'='1 | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 96 | E SQL metachar/%00 | GET /leads/%00 | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 97 | E SQL metachar/%00 | GET /leads/L%00abc | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 98 | E SQL metachar/%00 | GET /leads/ (trailing slash) | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 99 | E SQL metachar/%00 | GET /leads/%25 /leads/% | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 100 | E SQL metachar/%00 | GET /leads/<script> | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 101 | E SQL metachar/%00 | POST /review/F' OR 1=1--/resolve | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 102 | E SQL metachar/%00 | POST /review/R%00/retry | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 103 | E SQL metachar/%00 | GET /counts?expected=1;DROP | HTTP/1.0 400 Bad Request \| '{"error": "bad_expected"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 104 | E SQL metachar/%00 | GET /counts?expected=99999999999999999999999 | HTTP/1.0 200 OK \| '{"received": 6, "new": 5, "duplicate": 0, "review": 1, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": false, "ok": false}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 105 | E SQL metachar/%00 | GET /counts?expected=%00 | HTTP/1.0 400 Bad Request \| '{"error": "bad_expected"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 106 | E SQL metachar/%00 | GET /counts?expected=٥ (arabic digit) | HTTP/1.0 400 Bad Request \| '{"error": "bad_expected"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 107 | E SQL metachar/%00 | GET /counts?expected=5&expected=x | HTTP/1.0 200 OK \| '{"received": 6, "new": 5, "duplicate": 0, "review": 1, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": false, "ok": false}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 108 | E SQL metachar/%00 | GET /leads/ with 100k id | HTTP/1.0 414 Request-URI Too Long \| '{"error": "request-uri_too_long"}' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 109 | E SQL metachar/%00 | state after SQL attempts: GET /review | HTTP/1.0 200 OK \| '[{"item_id": "R2", "item_type": "receipt", "kind": "review", "reason": "invalid_email", "lead_id": null, "since": 1794219404, "source": "form"}]' \| 0.00s closed | rcpt=6 open=0 leads=5 crm=5 mail=5 fu={'sent': 5} alive=True | none printed |
| 110 | E SQL metachar/%00 | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 111 | F routes/methods/traversal | GET /review/../.. | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 112 | F routes/methods/traversal | GET /review/%2e%2e/ | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 113 | F routes/methods/traversal | GET /review/%2e%2e/%2e%2e/etc/passwd | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 114 | F routes/methods/traversal | GET /review/..%2f..%2fcounts | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 115 | F routes/methods/traversal | GET /leads/../counts | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 116 | F routes/methods/traversal | GET /leads/%2e%2e/counts | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 117 | F routes/methods/traversal | GET /review/..;/ | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 118 | F routes/methods/traversal | GET //review | HTTP/1.0 200 OK \| '[]' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 119 | F routes/methods/traversal | GET /review// | HTTP/1.0 200 OK \| '[]' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 120 | F routes/methods/traversal | GET /counts/ | HTTP/1.0 200 OK \| '{"received": 1, "new": 1, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 121 | F routes/methods/traversal | GET /counts/../review | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 122 | F routes/methods/traversal | GET /%2e%2e/%2e%2e/windows/win.ini | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 123 | F routes/methods/traversal | GET /leads/..\..\x | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 124 | F routes/methods/traversal | GET /review/F1/../retry | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 125 | F routes/methods/traversal | GET /review/%252e%252e/retry | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 126 | F routes/methods/traversal | GET /leads/a/b | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 127 | F routes/methods/traversal | GET /review/x/y/z | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 128 | F routes/methods/traversal | GET /COUNTS | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 129 | F routes/methods/traversal | GET /leads%00 | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 130 | F routes/methods/traversal | GET /counts%3Fexpected=1 | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 131 | F routes/methods/traversal | GET /  | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 132 | F routes/methods/traversal | GET /counts#frag | HTTP/1.0 200 OK \| '{"received": 1, "new": 1, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 133 | F routes/methods/traversal | GET http://evil.test/counts | HTTP/1.0 200 OK \| '{"received": 1, "new": 1, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 134 | F routes/methods/traversal | GET * | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 135 | F routes/methods/traversal | GET /leads | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 136 | F routes/methods/traversal | PUT /leads | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 137 | F routes/methods/traversal | DELETE /leads | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 138 | F routes/methods/traversal | PATCH /leads | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 139 | F routes/methods/traversal | HEAD /leads | HTTP/1.0 405 Method Not Allowed \| '' \| 0.00s closed | - | none printed |
| 140 | F routes/methods/traversal | OPTIONS /leads | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 141 | F routes/methods/traversal | TRACE /leads | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 142 | F routes/methods/traversal | CONNECT /leads | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 143 | F routes/methods/traversal | FOO /leads | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 144 | F routes/methods/traversal | POST /leads/Lxxxxxxxxxxxx | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 145 | F routes/methods/traversal | PUT /leads/Lxxxxxxxxxxxx | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 146 | F routes/methods/traversal | DELETE /leads/Lxxxxxxxxxxxx | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 147 | F routes/methods/traversal | PATCH /leads/Lxxxxxxxxxxxx | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 148 | F routes/methods/traversal | HEAD /leads/Lxxxxxxxxxxxx | HTTP/1.0 405 Method Not Allowed \| '' \| 0.00s closed | - | none printed |
| 149 | F routes/methods/traversal | OPTIONS /leads/Lxxxxxxxxxxxx | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 150 | F routes/methods/traversal | TRACE /leads/Lxxxxxxxxxxxx | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 151 | F routes/methods/traversal | CONNECT /leads/Lxxxxxxxxxxxx | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 152 | F routes/methods/traversal | FOO /leads/Lxxxxxxxxxxxx | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 153 | F routes/methods/traversal | POST /review | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 154 | F routes/methods/traversal | PUT /review | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 155 | F routes/methods/traversal | DELETE /review | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 156 | F routes/methods/traversal | PATCH /review | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 157 | F routes/methods/traversal | HEAD /review | HTTP/1.0 405 Method Not Allowed \| '' \| 0.00s closed | - | none printed |
| 158 | F routes/methods/traversal | OPTIONS /review | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 159 | F routes/methods/traversal | TRACE /review | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 160 | F routes/methods/traversal | CONNECT /review | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 161 | F routes/methods/traversal | FOO /review | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 162 | F routes/methods/traversal | GET /review/F1/retry | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 163 | F routes/methods/traversal | PUT /review/F1/retry | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 164 | F routes/methods/traversal | DELETE /review/F1/retry | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 165 | F routes/methods/traversal | PATCH /review/F1/retry | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 166 | F routes/methods/traversal | HEAD /review/F1/retry | HTTP/1.0 405 Method Not Allowed \| '' \| 0.00s closed | - | none printed |
| 167 | F routes/methods/traversal | OPTIONS /review/F1/retry | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 168 | F routes/methods/traversal | TRACE /review/F1/retry | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 169 | F routes/methods/traversal | CONNECT /review/F1/retry | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 170 | F routes/methods/traversal | FOO /review/F1/retry | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 171 | F routes/methods/traversal | GET /review/F1/resolve | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 172 | F routes/methods/traversal | PUT /review/F1/resolve | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 173 | F routes/methods/traversal | DELETE /review/F1/resolve | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 174 | F routes/methods/traversal | PATCH /review/F1/resolve | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 175 | F routes/methods/traversal | HEAD /review/F1/resolve | HTTP/1.0 405 Method Not Allowed \| '' \| 0.00s closed | - | none printed |
| 176 | F routes/methods/traversal | OPTIONS /review/F1/resolve | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 177 | F routes/methods/traversal | TRACE /review/F1/resolve | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 178 | F routes/methods/traversal | CONNECT /review/F1/resolve | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 179 | F routes/methods/traversal | FOO /review/F1/resolve | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 180 | F routes/methods/traversal | POST /counts | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 181 | F routes/methods/traversal | PUT /counts | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 182 | F routes/methods/traversal | DELETE /counts | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 183 | F routes/methods/traversal | PATCH /counts | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 184 | F routes/methods/traversal | HEAD /counts | HTTP/1.0 405 Method Not Allowed \| '' \| 0.00s closed | - | none printed |
| 185 | F routes/methods/traversal | OPTIONS /counts | HTTP/1.0 405 Method Not Allowed \| '{"error": "method_not_allowed"}' \| 0.00s closed | - | none printed |
| 186 | F routes/methods/traversal | TRACE /counts | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 187 | F routes/methods/traversal | CONNECT /counts | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 188 | F routes/methods/traversal | FOO /counts | HTTP/1.0 501 Not Implemented \| '{"error": "not_implemented"}' \| 0.00s closed | - | none printed |
| 189 | F routes/methods/traversal | (state after all wrong-method calls) |  \| '' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | no reply |
| 190 | F routes/methods/traversal | HTTP/0.9 'GET /counts' (no version) |  \| '' \| 6.01s timeout | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | slow 6.0s; conn timeout |
| 191 | F routes/methods/traversal | HTTP/0.9 'GET /counts' LF only |  \| '' \| 6.00s timeout | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | slow 6.0s; conn timeout |
| 192 | F routes/methods/traversal | garbage bytes | {"error": "bad_request"} \| '' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 193 | F routes/methods/traversal | HTTP/2 preface PRI * HTTP/2.0 | {"error": "http_version_not_supported"} \| '' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 194 | F routes/methods/traversal | HTTP/9.9 version | {"error": "http_version_not_supported"} \| '' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 195 | F routes/methods/traversal | pipelined: two GET /counts in one packet | HTTP/1.0 200 OK \| '{"received": 1, "new": 1, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 196 | F routes/methods/traversal | pipelined: two POST /leads in one packet (p1,p2) | HTTP/1.0 201 Created \| '{"receipt_id": 2, "verdict": "new", "lead_id": "Ld9aff808ba60", "replayed": false}' \| 0.00s closed | rcpt=2 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 197 | F routes/methods/traversal | smuggling: CL body followed by 2nd request inside body | HTTP/1.0 201 Created \| '{"receipt_id": 3, "verdict": "new", "lead_id": "Ldac74d5391ed", "replayed": false}' \| 0.00s closed | rcpt=3 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 198 | F routes/methods/traversal | header injection: bare LF in header / folded header | HTTP/1.0 200 OK \| '{"received": 3, "new": 3, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=3 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 199 | F routes/methods/traversal | header with CR only, NUL in header value | HTTP/1.0 200 OK \| '{"received": 3, "new": 3, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=3 open=0 leads=3 crm=3 mail=3 fu={'sent': 3} alive=True | none printed |
| 200 | F routes/methods/traversal | Expect: 100-continue on POST /leads | HTTP/1.0 201 Created \| '{"receipt_id": 4, "verdict": "new", "lead_id": "L8550ed810277", "replayed": false}' \| 0.00s closed | rcpt=4 open=0 leads=4 crm=4 mail=4 fu={'sent': 4} alive=True | none printed |
| 201 | F routes/methods/traversal | Host header missing / duplicate / huge | HTTP/1.0 200 OK \| '{"received": 4, "new": 4, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=4 open=0 leads=4 crm=4 mail=4 fu={'sent': 4} alive=True | none printed |
| 202 | F routes/methods/traversal | Connection: keep-alive then 2nd request on same socket | HTTP/1.0 200 OK \| '{"received": 4, "new": 4, "duplicate": 0, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=4 open=0 leads=4 crm=4 mail=4 fu={'sent': 4} alive=True | none printed |
| 203 | F routes/methods/traversal | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 204 | G concurrency/replay | replay: first g-rep | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L9786ce1d5f06", "replayed": false}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 205 | G concurrency/replay | replay same id, changed payload (phone 222, name Eve) | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L9786ce1d5f06", "replayed": true, "payload_matches": false}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 206 | G concurrency/replay | replay same id, changed email | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L9786ce1d5f06", "replayed": true, "payload_matches": false}' \| 0.00s closed | rcpt=1 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 207 | G concurrency/replay | replay same id, other source (webhook) same ref | HTTP/1.0 200 OK \| '{"receipt_id": 4, "verdict": "duplicate", "lead_id": "L9786ce1d5f06", "differing_fields": [], "replayed": false}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 208 | G concurrency/replay | replay same id, key order changed | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L9786ce1d5f06", "replayed": true, "payload_matches": true}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 209 | G concurrency/replay | replay same id, whitespace-changed values | HTTP/1.0 201 Created \| '{"receipt_id": 1, "verdict": "new", "lead_id": "L9786ce1d5f06", "replayed": true, "payload_matches": false}' \| 0.00s closed | rcpt=2 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 210 | G concurrency/replay | new id, same email, new phone | HTTP/1.0 200 OK \| '{"receipt_id": 7, "verdict": "duplicate", "lead_id": "L9786ce1d5f06", "differing_fields": ["phone"], "replayed": false}' \| 0.00s closed | rcpt=3 open=0 leads=1 crm=1 mail=1 fu={'sent': 1} alive=True | none printed |
| 211 | G concurrency/replay | 1000 distinct request ids, same email, 100 parallel workers |  \| "status counts {'200': 999, '201': 1}" \| 2.49s closed | rcpt=1003 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | no reply |
| 212 | G concurrency/replay | re-sent the 0 non-2xx ids of the 1000 (up to 5 tries) |  \| 'retried=0' \| 0.00s closed | rcpt=1003 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | no reply |
| 213 | G concurrency/replay | GET /counts?expected=1002 after 1000 + 2 earlier lead rows | HTTP/1.0 200 OK \| '{"received": 1003, "new": 2, "duplicate": 1001, "review": 0, "open": 0, "rejected_envelopes": 0, "pending_followups": 0, "expected_match": null, "ok": null}' \| 0.00s closed | rcpt=1003 open=0 leads=2 crm=2 mail=2 fu={'sent': 2} alive=True | none printed |
| 214 | G concurrency/replay | 50 parallel posts of ONE request id, same payload |  \| "{'HTTP/1.0 201 Created': 50}" \| 0.00s closed | rcpt=1004 open=0 leads=3 crm=10 mail=3 fu={'sent': 3} alive=True | no reply; CRM rows>leads |
| 215 | G concurrency/replay | 50 parallel posts of ONE request id, 50 different names |  \| "{'HTTP/1.0 201 Created': 50}" \| 0.00s closed | rcpt=1005 open=0 leads=4 crm=23 mail=4 fu={'sent': 4} alive=True | no reply; CRM rows>leads |
| 216 | G concurrency/replay | setup: lead with mail reply lost -> unknown follow-up [note: unknown items: ['FLa57b0675394e']] | HTTP/1.0 201 Created \| '{"receipt_id": 1108, "verdict": "new", "lead_id": "La57b0675394e", "replayed": false}' \| 0.01s closed | rcpt=1006 open=0 leads=5 crm=24 mail=5 fu={'sent': 4, 'unknown': 1} alive=True | CRM rows>leads |
| 217 | G concurrency/replay | resolve FLa57b0675394e 10x concurrently (5 sent, 5 not_sent) |  \| 'Counter({(\'HTTP/1.0 409 Conflict\', \'{"error": "not_unknown", "hint": "Only a\'): 9, (\'HTTP/1.0 200 OK\', \'{"item_id": "FLa57b0675394e", "state": "\'): 1})' \| 0.00s closed | rcpt=1006 open=0 leads=5 crm=24 mail=5 fu={'sent': 5} alive=True | no reply; CRM rows>leads |
| 218 | G concurrency/replay | GET /leads for that lead | HTTP/1.0 200 OK \| '{"lead": {"lead_id": "La57b0675394e", "receipt_id": 1108, "source": "form", "name": "Unk", "email": "unk@example.test", "phone": null, "company": null, "message": null, "created_at": 1794219463}, "followup": {"state": "sent", "ai_label": "warm", "attempts": 1, "last_error": "person: sent", "sent_at"' \| 0.00s closed | rcpt=1006 open=0 leads=5 crm=24 mail=5 fu={'sent': 5} alive=True | CRM rows>leads |
| 219 | G concurrency/replay | resolve FLa57b0675394e again after final | HTTP/1.0 409 Conflict \| '{"error": "not_unknown", "hint": "Only a follow-up in state unknown can be resolved."}' \| 0.00s closed | rcpt=1006 open=0 leads=5 crm=24 mail=5 fu={'sent': 5} alive=True | CRM rows>leads |
| 220 | G concurrency/replay | retry FLa57b0675394e after final | HTTP/1.0 409 Conflict \| '{"error": "not_retryable"}' \| 0.00s closed | rcpt=1006 open=0 leads=5 crm=24 mail=5 fu={'sent': 5} alive=True | CRM rows>leads |
| 221 | G concurrency/replay | resolve FLb948e24b3291 body: empty body | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'sent': 5, 'unknown': 1} alive=True | CRM rows>leads |
| 222 | G concurrency/replay | resolve FLb948e24b3291 body: not json | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'sent': 5, 'unknown': 1} alive=True | CRM rows>leads |
| 223 | G concurrency/replay | resolve FLb948e24b3291 body: decision list | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'sent': 5, 'unknown': 1} alive=True | CRM rows>leads |
| 224 | G concurrency/replay | resolve FLb948e24b3291 body: decision SENT upper | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'sent': 5, 'unknown': 1} alive=True | CRM rows>leads |
| 225 | G concurrency/replay | resolve FLb948e24b3291 body: decision ' sent' | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'sent': 5, 'unknown': 1} alive=True | CRM rows>leads |
| 226 | G concurrency/replay | resolve FLb948e24b3291 body: decision with NUL | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'sent': 5, 'unknown': 1} alive=True | CRM rows>leads |
| 227 | G concurrency/replay | resolve FLb948e24b3291 body: nested depth 10000 | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'sent': 5, 'unknown': 1} alive=True | CRM rows>leads |
| 228 | G concurrency/replay | resolve FLb948e24b3291 body: duplicate keys | HTTP/1.0 200 OK \| '{"item_id": "FLb948e24b3291", "state": "failed"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'failed': 1, 'sent': 5} alive=True | CRM rows>leads |
| 229 | G concurrency/replay | resolve FLb948e24b3291 body: decision null | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'failed': 1, 'sent': 5} alive=True | CRM rows>leads |
| 230 | G concurrency/replay | resolve FLb948e24b3291 body: invalid utf8 | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'failed': 1, 'sent': 5} alive=True | CRM rows>leads |
| 231 | G concurrency/replay | resolve FLb948e24b3291 body: array body | HTTP/1.0 400 Bad Request \| '{"error": "bad_decision"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'failed': 1, 'sent': 5} alive=True | CRM rows>leads |
| 232 | G concurrency/replay | resolve FLb948e24b3291 body: 10 MB body |  \| '' \| 0.00s err:BrokenPipeError | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'failed': 1, 'sent': 5} alive=True | conn err:BrokenPipeError; CRM rows>leads |
| 233 | G concurrency/replay | resolve on R/D/O/F-missing ids | HTTP/1.0 404 Not Found \| '{"error": "not_found"}' \| 0.00s closed | rcpt=1007 open=0 leads=6 crm=25 mail=6 fu={'failed': 1, 'sent': 5} alive=True | CRM rows>leads |
| 234 | G concurrency/replay | retry F of sent lead / unknown | HTTP/1.0 200 OK \| '{"item_id": "FLb948e24b3291", "state": "sent"}' \| 0.01s closed | rcpt=1007 open=0 leads=6 crm=26 mail=7 fu={'sent': 6} alive=True | CRM rows>leads; mails>leads |
| 235 | G concurrency/replay | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |
| 236 | H kill and restart | kill -9 desk mid-burst (300 posts, 7 emails), restart same DB, resend all 300 ids |  \| "db before restart (receipts, open)=(222, 14); resend statuses {'HTTP/1.0 200 OK': 293, 'HTTP/1.0 201 Created': 7}" \| 0.00s closed | rcpt=300 open=0 leads=7 crm=7 mail=7 fu={'sent': 7} alive=True | no reply |
| 237 | H kill and restart | [class end] liveness [note: restart needed: no] | /counts ok=True 0.00s | process alive=True | none printed |

## Totals

Rows: 237 (incl. 9 liveness rows). Rows with an anomaly flag: 32. Per class: {'A size/framing': 17, 'B slowloris/connections': 8, 'C encoding/parser': 28, 'D email twins': 35, 'E SQL metachar/%00': 22, 'F routes/methods/traversal': 93, 'G concurrency/replay': 32, 'H kill and restart': 2}.
Rows flagged `DESK DEAD`: 0. Liveness rows not OK: 0.

## Raw log tail, run 1 (classes B-H), last 60 lines

```
F routes/methods/traversal CONNECT /review/F1/resolve HTTP/1.0 501 Not Implemented []
F routes/methods/traversal FOO /review/F1/resolve HTTP/1.0 501 Not Implemented []
F routes/methods/traversal POST /counts HTTP/1.0 405 Method Not Allowed []
F routes/methods/traversal PUT /counts HTTP/1.0 405 Method Not Allowed []
F routes/methods/traversal DELETE /counts HTTP/1.0 405 Method Not Allowed []
F routes/methods/traversal PATCH /counts HTTP/1.0 405 Method Not Allowed []
F routes/methods/traversal HEAD /counts HTTP/1.0 405 Method Not Allowed []
F routes/methods/traversal OPTIONS /counts HTTP/1.0 405 Method Not Allowed []
F routes/methods/traversal TRACE /counts HTTP/1.0 501 Not Implemented []
F routes/methods/traversal CONNECT /counts HTTP/1.0 501 Not Implemented []
F routes/methods/traversal FOO /counts HTTP/1.0 501 Not Implemented []
F routes/methods/traversal (state after all wrong-method calls)  ['no reply']
F routes/methods/traversal HTTP/0.9 'GET /counts' (no version)  ['slow 6.0s', 'conn timeout']
F routes/methods/traversal HTTP/0.9 'GET /counts' LF only  ['slow 6.0s', 'conn timeout']
F routes/methods/traversal garbage bytes {"error": "bad_request"} []
F routes/methods/traversal HTTP/2 preface PRI * HTTP/2.0 {"error": "http_version_not_supported"} []
F routes/methods/traversal HTTP/9.9 version {"error": "http_version_not_supported"} []
F routes/methods/traversal pipelined: two GET /counts in one packet HTTP/1.0 200 OK []
F routes/methods/traversal pipelined: two POST /leads in one packet (p1,p2) HTTP/1.0 201 Created []
F routes/methods/traversal smuggling: CL body followed by 2nd request inside body HTTP/1.0 201 Created []
F routes/methods/traversal header injection: bare LF in header / folded header HTTP/1.0 200 OK []
F routes/methods/traversal header with CR only, NUL in header value HTTP/1.0 200 OK []
F routes/methods/traversal Expect: 100-continue on POST /leads HTTP/1.0 201 Created []
F routes/methods/traversal Host header missing / duplicate / huge HTTP/1.0 200 OK []
F routes/methods/traversal Connection: keep-alive then 2nd request on same socket HTTP/1.0 200 OK []
F routes/methods/traversal liveness True True
G concurrency/replay replay: first g-rep HTTP/1.0 201 Created []
G concurrency/replay replay same id, changed payload (phone 222, name Eve) HTTP/1.0 201 Created []
G concurrency/replay replay same id, changed email HTTP/1.0 201 Created []
G concurrency/replay replay same id, other source (webhook) same ref HTTP/1.0 200 OK []
G concurrency/replay replay same id, key order changed HTTP/1.0 201 Created []
G concurrency/replay replay same id, whitespace-changed values HTTP/1.0 201 Created []
G concurrency/replay new id, same email, new phone HTTP/1.0 200 OK []
G concurrency/replay 1000 distinct request ids, same email, 100 parallel workers  ['no reply']
G concurrency/replay re-sent the 0 non-2xx ids of the 1000 (up to 5 tries)  ['no reply']
G concurrency/replay GET /counts?expected=1002 after 1000 + 2 earlier lead rows HTTP/1.0 200 OK []
G concurrency/replay 50 parallel posts of ONE request id, same payload  ['no reply', 'CRM rows>leads']
G concurrency/replay 50 parallel posts of ONE request id, 50 different names  ['no reply', 'CRM rows>leads']
G concurrency/replay setup: lead with mail reply lost -> unknown follow-up HTTP/1.0 201 Created ['CRM rows>leads']
G concurrency/replay resolve FLa57b0675394e 10x concurrently (5 sent, 5 not_sent)  ['no reply', 'CRM rows>leads']
G concurrency/replay GET /leads for that lead HTTP/1.0 200 OK ['CRM rows>leads']
G concurrency/replay resolve FLa57b0675394e again after final HTTP/1.0 409 Conflict ['CRM rows>leads']
G concurrency/replay retry FLa57b0675394e after final HTTP/1.0 409 Conflict ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: empty body HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: not json HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: decision list HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: decision SENT upper HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: decision ' sent' HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: decision with NUL HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: nested depth 10000 HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: duplicate keys HTTP/1.0 200 OK ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: decision null HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: invalid utf8 HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: array body HTTP/1.0 400 Bad Request ['CRM rows>leads']
G concurrency/replay resolve FLb948e24b3291 body: 10 MB body  ['conn err:BrokenPipeError', 'CRM rows>leads']
G concurrency/replay resolve on R/D/O/F-missing ids HTTP/1.0 404 Not Found ['CRM rows>leads']
G concurrency/replay retry F of sent lead / unknown HTTP/1.0 200 OK ['CRM rows>leads', 'mails>leads']
G concurrency/replay liveness True True
H kill and restart kill -9 desk mid-burst (300 posts, 7 emails), restart same D  ['no reply']
H kill and restart liveness True True
```

## Raw log, run 2 (class A), last 20 lines

```
A size/framing body exactly 65536 bytes (cap 65536), valid envelope but mes HTTP/1.0 202 Accepted []
A size/framing body 65537 bytes (cap+1) HTTP/1.0 413 Request Entity Too Large []
A size/framing body 10 MB of 'x'  ['conn err:BrokenPipeError']
A size/framing chunked, no Content-Length HTTP/1.0 400 Bad Request []
A size/framing Content-Length larger than body (+50), client keeps socket o HTTP/1.0 500 Internal Server Error ['5xx 500', 'slow 30.0s']
A size/framing Content-Length smaller than body (-10) HTTP/1.0 400 Bad Request []
A size/framing Content-Length: -5 HTTP/1.0 400 Bad Request []
A size/framing Content-Length: abc HTTP/1.0 400 Bad Request []
A size/framing Content-Length: 99999999999999999999  ['slow 10.0s', 'conn timeout']
A size/framing two Content-Length headers (len, len+5) HTTP/1.0 201 Created []
A size/framing no Content-Length on POST /leads HTTP/1.0 400 Bad Request []
A size/framing Content-Length: 0 HTTP/1.0 400 Bad Request []
A size/framing Content-Length with unicode digit (arabic-indic 5) HTTP/1.0 400 Bad Request []
A size/framing header block 100 KB HTTP/1.0 431 Request Header Fields Too Large []
A size/framing 200 headers HTTP/1.0 431 Request Header Fields Too Large []
A size/framing request line 70 KB HTTP/1.0 414 Request-URI Too Long []
A size/framing liveness True True
class A done, stopping
```

## Where the rows are

- Combined rows: /home/user/hadavin-sdk/handover/demo/reports/hostile-linux-1.rows.jsonl (class A rows first, then B-H)
- Full logs: /tmp/dpld-out/hostile-run-BH.log, /tmp/dpld-out/hostile-run-A.log
- Original per-run rows: /tmp/dpld-out/rows-BH.jsonl and /tmp/dpld-baseline/_hostile_rows.jsonl (class A)
