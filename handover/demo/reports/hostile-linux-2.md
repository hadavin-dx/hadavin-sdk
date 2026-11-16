# Hostile matrix 2: dpld-fix3-303127b UNPATCHED (Linux, 4 cores). EVIDENCE only, no verdicts.
Run: handover/demo/tools/hostile_run.py (blind outbox + blind CRM, ports 18701/18702), classes B-H then class A, single runner. Raw rows: hostile-linux-2.rows.jsonl (237 rows). Desk never died. Flagged rows: 31 (list below).
Compared with hostile-linux-1 (aed689a, 32 flags): the Content-Length +50 case now answers 408 after 30 s (was 500 after 30 s); the 20-digit Content-Length no longer appears as a flag; the 10 MB body still gives a client-side BrokenPipeError (twice: lead post and resolve); HTTP/0.9 `GET /counts` still waits 6.0 s (both variants, as the lead noted); 40 slowloris sockets are all closed by the server after 33 s.
Open, unchanged by the server changes (desk core, F7): from the row "50 parallel posts of ONE request id, same payload" onward the harness flags `CRM rows>leads` (blind CRM puts twice), and `mails>leads` appears from "retry ... after final". The kill -9 row shows receipts/open (214, 9) before restart.
## Flagged rows
237 rows 31 flagged
- [B slowloris/connection] after 33 s: how many of the 40 stuck sockets were closed/answered by server =>  | 'closed_or_answered=40/40' | 33.00s closed | slow 33.0s; no reply
- [D email twins] email keys 'İ' lower() length twin: ß->ss? (done above) =>  | 'see rows above' | 0.00s closed | no reply
- [F routes/methods/trave] (state after all wrong-method calls) =>  | '' | 0.00s closed | no reply
- [F routes/methods/trave] HTTP/0.9 'GET /counts' (no version) =>  | '' | 6.01s timeout | slow 6.0s; conn timeout
- [F routes/methods/trave] HTTP/0.9 'GET /counts' LF only =>  | '' | 6.01s timeout | slow 6.0s; conn timeout
- [G concurrency/replay] 1000 distinct request ids, same email, 100 parallel workers =>  | "status counts {'200': 999, '201': 1}" | 2.48s closed | no reply
- [G concurrency/replay] re-sent the 0 non-2xx ids of the 1000 (up to 5 tries) =>  | 'retried=0' | 0.00s closed | no reply
- [G concurrency/replay] 50 parallel posts of ONE request id, same payload =>  | "{'HTTP/1.0 201 Created': 50}" | 0.00s closed | no reply; CRM rows>leads
- [G concurrency/replay] 50 parallel posts of ONE request id, 50 different names =>  | "{'HTTP/1.0 201 Created': 50}" | 0.00s closed | no reply; CRM rows>leads
- [G concurrency/replay] setup: lead with mail reply lost -> unknown follow-up => HTTP/1.0 201 Created | '{"receipt_id": 1108, "verdict": "new | CRM rows>leads
- [G concurrency/replay] resolve FL8262978323a0 10x concurrently (5 sent, 5 not_sent) =>  | 'Counter({(\'HTTP/1.0 409 Conflict\', \'{"error": "not_un | no reply; CRM rows>leads
- [G concurrency/replay] GET /leads for that lead => HTTP/1.0 200 OK | '{"lead": {"lead_id": "L8262978323a0", "re | CRM rows>leads
- [G concurrency/replay] resolve FL8262978323a0 again after final => HTTP/1.0 409 Conflict | '{"error": "not_unknown", "hint": "O | CRM rows>leads
- [G concurrency/replay] retry FL8262978323a0 after final => HTTP/1.0 200 OK | '{"item_id": "FL8262978323a0", "state": "s | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: empty body => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: not json => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: decision list => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: decision SENT upper => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: decision ' sent' => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: decision with NUL => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: nested depth 10000 => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: duplicate keys => HTTP/1.0 200 OK | '{"item_id": "FL7e3813de6523", "state": "f | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: decision null => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: invalid utf8 => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: array body => HTTP/1.0 400 Bad Request | '{"error": "bad_decision"}' | 0.0 | CRM rows>leads; mails>leads
- [G concurrency/replay] resolve FL7e3813de6523 body: 10 MB body =>  | '' | 0.00s err:BrokenPipeError | conn err:BrokenPipeError; CRM rows>leads; mails>leads
- [G concurrency/replay] resolve on R/D/O/F-missing ids => HTTP/1.0 404 Not Found | '{"error": "not_found"}' | 0.00s cl | CRM rows>leads; mails>leads
- [G concurrency/replay] retry F of sent lead / unknown => HTTP/1.0 200 OK | '{"item_id": "FL7e3813de6523", "state": "s | CRM rows>leads; mails>leads
- [H kill and restart] kill -9 desk mid-burst (300 posts, 7 emails), restart same DB, resend all 300 ids =>  | "db before restart (receipts, open)=(214, 9); resend stat | no reply; CRM rows>leads
- [A size/framing] body 10 MB of 'x' =>  | '' | 0.00s err:BrokenPipeError | conn err:BrokenPipeError
- [A size/framing] Content-Length larger than body (+50), client keeps socket open => HTTP/1.0 408 Request Timeout | '{"error": "request_timeout", | slow 30.0s
