# Fuzz of the desk read routes: facts only (EVIDENCE RUNNER, no pass or fail judgement)

Run: 2026-11-09 about 17:36-17:38 UTC (23:06-23:08 IST). Tree: /tmp/ag/fuzz (private copy). Script: /tmp/ag/fuzz_run.py. Full table: `fuzz-ui-routes-raw.txt` (2232 lines, 1400 request rows plus concurrency rows).
Desk and fake server: started fresh, loopback only, fake outbox mode "keyed", made-up leads only.

## What went wrong or is uncertain (first)
1. The first run wrote its raw file only up to the header cases (1402 lines, then nothing), although the same run finished and wrote its JSON. I do not know why. I re-ran the whole script and wrote the raw file to a local path, then copied it here. This report and the raw file are from the second run (the first run gave the same counts).
2. `/ui/` and `/ui/index.html` return 404 on every request: the tree has no `src/lead_desk/portal/` folder, so the fixed portal file list is empty. Serving of real static files, and path escape out of the portal folder, could NOT be tested. The 404s for `../`, `%2e%2e`, double-encoded and backslash paths are only 404s of an empty list.
3. `/api/demo/*` returns 404 (no demo extension loaded); not tested further.
4. Desk log shows tracebacks and "handler failed: BrokenPipeError" lines (details below).
5. Under 200 parallel GETs, most `/api/ui/*` JSON requests get 503 (busy). Every status of 500 or higher in the run was a 503 or a 501; there was no 500.

## Seeding and totals
300 POST /leads (270 distinct emails, 30 repeats): 270 x 201, 30 x 200. Request rows recorded: 1400 (hostile phase) + 630 (concurrency, 3 rounds x 210) + 91 slow-poll rows.

## Status counts per route (hostile phase, all cases)
| Route | 200 | 400 | 403 | 404 | 405 | 414 | 431 | 501 | 308 |
|---|---|---|---|---|---|---|---|---|---|
| /api/ui/summary | 12 | 202 | 26 | - | 12 | 11 | 4 | 5 | - |
| /api/ui/leads | 39 | 173 | 26 | - | 6 | 11 | - | 5 | - |
| /api/ui/review | 2 | 202 | - | - | 6 | 11 | - | 5 | - |
| /api/ui/log | 2 | 202 | - | - | 6 | 11 | - | 5 | - |
| /api/ui/data-map | 2 | 202 | - | - | 6 | 11 | - | 5 | - |
| /api/ui/leads/<id> (real id) | 2 | - | - | - | 6 | - | - | 5 | - |
| /ui/ and /ui/index.html | - | - | 26 | 13 | 12 | 1 | - | 10 | - |
| /ui (no slash) | - | - | - | - | 6 | - | - | 5 | 3 |
Other path cases (about 100 odd or escaping paths under /api/ui and /ui): all 404 except those that normalise to a real route (trailing slash, `//`, `#frag`, `%64ata-map`, `data%2dmap` gave 200; `leads/<id>/` 200; `/api/ui/leads/' OR 1=1--` gave 400).
Odd request targets: absolute-form `http://evil.test/api/ui/summary`, `//api/ui/summary`, `api/ui/summary` (no leading slash) all answered 200 with the summary JSON.
Case variants (`/API/UI/summary`, `/api/ui/SUMMARY`, upper-case lead id) gave 404. `/ui/` upper-case gave 404.

## Query strings
- `/api/ui/summary`, `review`, `log`, `data-map`: any parameter returned 400 `bad_query`, except an empty query (`&&&&`) which gave 200. (`log` accepts limit/before; values -1, 0, 19-digit and 5000-digit limit gave 400 `field: limit`.)
- `/api/ui/leads`: 200 for `offset=0` and for every `q=` value (unicode, lone surrogate %ED%A0%80, `%`, `%zz`, `%00` not in the 200 list, 101 and 102 characters, SQL-like text, `<script>`); 400 for the others.
- 4096 and 8192 character queries: 400 (parameter not listed). 64 KB value: 414. 1 MB: 414. 64 KB made of many parameters: 400; 1.1 MB: 414.
- No 5xx and no timeout for any query case. Slowest hostile case: 1.002 s (POST with a content-length of 23 digits, 405 answer).

## Methods
HEAD, OPTIONS, PUT, DELETE, PATCH, POST on every portal route: 405 (HEAD with an empty body; others `{"error":"method_not_allowed"}`). TRACE, CONNECT, FOO, PROPFIND, lowercase `get`: 501 `not_implemented`. POST/PUT with chunked body, with `Expect: 100-continue` and 1 MB announced length: 405 in 1 ms. GET with a 1 MB body: 200. GET announcing 5000 bytes but sending 3: 200.

## Host, Origin, Sec-Fetch-Site (summary, leads, /ui/)
- 403 `forbidden_host`: no Host, empty Host, space, `evil.test`, `127.0.0.1.evil.test`, port 99999, `host:port:1`, `0.0.0.0`, `127.0.0.2`, 5000-character host, `127.0.0.1\x00`, comma list, two Host headers.
- 200: `localhost:<port>`, `LOCALHOST` (no port), `[::1]:<port>`.
- 403 `forbidden_origin`: Origin `http://evil.test`, `null`, empty, other port, `https://`, trailing slash, 5000 characters, two Origin headers. 200: Origin equal to the desk's own `http://127.0.0.1:<port>` and `http://localhost:<port>`.
- Sec-Fetch-Site: 200 for `same-origin`, `SAME-ORIGIN`, `none`; 403 for `cross-site`, `same-site`, empty, `bogus`, two headers.

## Slow-header sockets
20 sockets open with a partial request line or partial headers, one byte added to each every second for 45 s. At 45 s all 20 were still open (none closed by the desk; the desk's per-request limit in code is 30 s). A normal client polled `/api/ui/summary` every 0.5 s during this: 91 polls, all 200, max 7 ms, p95 4.5 ms.
Big headers: 200 headers 431; one 100 KB header 431; 1000 headers 431; one 70 KB header 431 (all in under 20 ms).

## 200 parallel GETs + 10 parallel POST /leads, three rounds (routes: summary, leads x3 variants, review, log x2, data-map, /counts, /ui/, /ui/index.html)
| Round | requests | 503 | other 5xx | connection errors or timeouts | max latency | p95 latency |
|---|---|---|---|---|---|---|
| 1 | 210 | 118 | 0 | 0 | 0.42 s | 0.35 s |
| 2 | 210 | 122 | 0 | 0 | 0.40 s | 0.33 s |
| 3 | 210 | 106 | 0 | 0 | 0.43 s | 0.34 s |
503 only on `/api/ui/*` JSON routes (in code: at most 8 portal JSON replies at once). `/counts` 18 of 18 were 200 each round; POST /leads 10 of 10 were 201 each round; `/ui/` and `/ui/index.html` 404 (see item 2).
Reconciliation after each round (6 s wait), `/counts` vs `/api/ui/summary` vs fake server:
| After | received | new | duplicate | review | rejected | received minus (new+dup+review+rejected) | summary `reconciled` | CRM rows | distinct emails in CRM | emails sent | distinct recipients |
|---|---|---|---|---|---|---|---|---|---|---|---|
| seeding | 300 | 270 | 30 | 0 | 0 | 0 | true | 270 | 270 | 270 | 270 |
| hostile + slow phase | 300 | 270 | 30 | 0 | 0 | 0 | true | 270 | 270 | 270 | 270 |
| round 1 | 310 | 280 | 30 | 0 | 0 | 0 | true | 280 | 280 | 280 | 280 |
| round 2 | 320 | 290 | 30 | 0 | 0 | 0 | true | 290 | 290 | 290 | 290 |
| round 3 | 330 | 300 | 30 | 0 | 0 | 0 | true | 300 | 300 | 300 | 300 |
Open, pending, failed, unknown and sending follow-ups were 0 at every snapshot. The desk still answered 200 on `/api/ui/summary` at the end.

## Seeded-data strings in bodies
Patterns searched in every body: `seedlead<N>@example.test`, `555 7xxxx`, `SEEDMSG-`, `Seed Person`.
- Email and name appear in `/api/ui/leads` (every 200 reply). Email, phone, message and name appear in `/api/ui/leads/<id>` (200 replies for a real id). These replies are the lead data the route is meant to show; I did not judge it.
- `/api/ui/summary` and `/api/ui/log` bodies contain the name string (`Seed Person ...`) but no email, phone or message string.
- `/api/ui/review` and `/api/ui/data-map` bodies: no hits. No error body (400/403/404/405/414/431/501/503) contained any seeded string.

## Desk log (/tmp/ag/fuzz_data/desk.log, 147 lines)
- Line 1: `crm capability not re-read: CrmError` (at start, before any request).
- 15 lines `handler failed: BrokenPipeError`; 5 Python tracebacks (`BrokenPipeError` in `server.py send_error`, called from `http/server.py parse_request`, printed by socketserver as "Exception occurred during processing of request"). No other error class.
- Separate probe on a fresh desk (/tmp/ag/attrib.py) to find the cause, each case alone: a client that closes without reading after sending a 1 MB query gave 1 traceback (`ConnectionResetError`); after a 100 KB header gave 2 tracebacks (`BrokenPipeError`); a client that closes at once after a valid `GET /api/ui/leads?limit=200` gave 1 `handler failed: BrokenPipeError` line. Cases where the client read the answer (1 MB query, 100 KB header, 200 headers, 1 MB body, bogus content-length, TRACE) gave 0 log lines. So the log lines come from clients that close before reading the answer. In the main run I did not mark which request caused each line.

## Not tested
Real static file serving (no portal folder); `/api/demo/*`; HTTP keep-alive or pipelined requests; HTTPS; slow-body (rather than slow-header) attacks on GET routes; connection counts above 20 slow sockets plus 210 parallel; load for longer than about 90 s.

## Processes
Desk and fake server were killed by the script at the end of each run. Check (`ps aux | grep -E "lead_desk|fakes_server|fuzz_run|attrib"`) printed 0 matching lines. Other python processes visible (pytest runs and one final_gate tool) were not started by me and were left alone.
