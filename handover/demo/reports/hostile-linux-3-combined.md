# Hostile matrix 3: fix-3 base + cloud patch fix4 (1933731) + the three server.py hook edits (scratch copy /tmp/dpld4). Evidence only.
Same harness and single runner as hostile-linux-2. Raw rows: hostile-linux-3-combined.rows.jsonl. Desk never died. 237 rows, 28 flagged (fix-3 unpatched: 237 rows, 31 flagged).
Changes versus fix-3 unpatched: the `CRM rows>leads` flag is gone from every class G and H row (blind CRM no longer gets a second row on 50 parallel posts of one request id). `mails>leads` still appears from the row `retry ... after final` on: the harness resolves the follow-up as sent, then a person's Retry sends again; this is person-driven and was in both earlier runs. Unchanged: 10 MB body BrokenPipeError (client side), HTTP/0.9 6.0 s wait, +50 Content-Length 408 after 30 s, 40 slowloris sockets closed after 33 s.
The server.py hook edits used here (not the lead's file): LockHeldError split, desk.start_background() before startup, desk.stop_background() first in finally.
## Flagged rows
- [B slowloris/connection] after 33 s: how many of the 40 stuck sockets were closed/answered by server =>  | 'closed_or_answered=40/40' | 33.00s closed | slow 33.0s; no reply
- [D email twins] email keys 'İ' lower() length twin: ß->ss? (done above) =>  | 'see rows above' | 0.00s closed | no reply
- [F routes/methods/trave] (state after all wrong-method calls) =>  | '' | 0.00s closed | no reply
- [F routes/methods/trave] HTTP/0.9 'GET /counts' (no version) =>  | '' | 6.01s timeout | slow 6.0s; conn timeout
- [F routes/methods/trave] HTTP/0.9 'GET /counts' LF only =>  | '' | 6.01s timeout | slow 6.0s; conn timeout
- [G concurrency/replay] 1000 distinct request ids, same email, 100 parallel workers =>  | "status counts {'200': 999, '201': 1}" | 2.37s closed | no reply
- [G concurrency/replay] re-sent the 0 non-2xx ids of the 1000 (up to 5 tries) =>  | 'retried=0' | 0.00s closed | no reply
- [G concurrency/replay] 50 parallel posts of ONE request id, same payload =>  | "{'HTTP/1.0 201 Created': 50}" | 0.00s closed | no reply
- [G concurrency/replay] 50 parallel posts of ONE request id, 50 different names =>  | "{'HTTP/1.0 201 Created': 50}" | 0.00s closed | no reply
- [G concurrency/replay] resolve FLa958e00bd2e4 10x concurrently (5 sent, 5 not_sent) =>  | 'Counter({(\'HTTP/1.0 409 Conflict\', \'{"error": "not_un | no reply
- [G concurrency/replay] retry FLa958e00bd2e4 after final => HTTP/1.0 200 OK | '{"item_id": "FLa958e00bd2e4", "state": "s | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: empty body => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: not json => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: decision list => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: decision SENT upper => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: decision ' sent' => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: decision with NUL => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: nested depth 10000 => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: duplicate keys => HTTP/1.0 200 OK | '{"item_id": "FLc5c2be535106", "state": "f | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: decision null => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: invalid utf8 => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: array body => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | mails>leads
- [G concurrency/replay] resolve FLc5c2be535106 body: 10 MB body =>  | '' | 0.00s err:BrokenPipeError | conn err:BrokenPipeError; mails>leads
- [G concurrency/replay] resolve on R/D/O/F-missing ids => HTTP/1.0 404 Not Found | '{"error": "not_found"}' | 0.00s cl | mails>leads
- [G concurrency/replay] retry F of sent lead / unknown => HTTP/1.0 200 OK | '{"item_id": "FLc5c2be535106", "state": "s | mails>leads
- [H kill and restart] kill -9 desk mid-burst (300 posts, 7 emails), restart same DB, resend all 300 ids =>  | "db before restart (receipts, open)=(209, 14); resend sta | no reply
- [A size/framing] body 10 MB of 'x' =>  | '' | 0.00s err:BrokenPipeError | conn err:BrokenPipeError
- [A size/framing] Content-Length larger than body (+50), client keeps socket open => HTTP/1.0 408 Request Timeout | '{"error": "request_timeout", | slow 30.0s
